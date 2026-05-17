import os
import time
import numpy as np
import pandas as pd
from collections import deque
import joblib
from .base_tracker import BaseTracker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models/squat_model.pkl")

class SquatTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.state = "up"
        
        # Thresholds
        self.DOWN_THRESHOLD = 100
        self.UP_THRESHOLD = 165
        self.DEPTH_THRESHOLD = 100
        self.SMOOTHING_WINDOW = 7
        self.HOLD_TIME = 0.1
        
        self.last_state_change = time.time()
        self.knee_buffer = deque(maxlen=self.SMOOTHING_WINDOW)
        self.min_knee_angle = 180
        self.rep_log = []
        self.quality = "GOOD"
        
        self.FEATURE_NAMES = [
            "knee_angle_r", "knee_angle_l",
            "elbow_angle_r", "elbow_angle_l",
            "hip_angle_r", "hip_angle_l",
            "shoulder_angle_r", "shoulder_angle_l"
        ]
        
        self.model = None
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)

    def process_landmarks(self, lm):
        now = time.time()
        
        hip_r, knee_r, ankle_r = (lm[24].x, lm[24].y), (lm[26].x, lm[26].y), (lm[28].x, lm[28].y)
        hip_l, knee_l, ankle_l = (lm[23].x, lm[23].y), (lm[25].x, lm[25].y), (lm[27].x, lm[27].y)

        shoulder_r, elbow_r, wrist_r = (lm[12].x, lm[12].y), (lm[14].x, lm[14].y), (lm[16].x, lm[16].y)
        shoulder_l, elbow_l, wrist_l = (lm[11].x, lm[11].y), (lm[13].x, lm[13].y), (lm[15].x, lm[15].y)

        knee_angle_r = self.calculate_angle(hip_r, knee_r, ankle_r)
        knee_angle_l = self.calculate_angle(hip_l, knee_l, ankle_l)
        elbow_angle_r = self.calculate_angle(shoulder_r, elbow_r, wrist_r)
        elbow_angle_l = self.calculate_angle(shoulder_l, elbow_l, wrist_l)
        hip_angle_r = self.calculate_angle(shoulder_r, hip_r, knee_r)
        hip_angle_l = self.calculate_angle(shoulder_l, hip_l, knee_l)
        shoulder_angle_r = self.calculate_angle(elbow_r, shoulder_r, hip_r)
        shoulder_angle_l = self.calculate_angle(elbow_l, shoulder_l, hip_l)

        avg_knee = (knee_angle_r + knee_angle_l) / 2
        self.knee_buffer.append(avg_knee)
        smooth_knee = float(np.median(self.knee_buffer)) if len(self.knee_buffer) > 0 else avg_knee

        self.min_knee_angle = min(self.min_knee_angle, smooth_knee)
        confidence = 1.0

        if self.model:
            features = pd.DataFrame([[
                knee_angle_r, knee_angle_l,
                elbow_angle_r, elbow_angle_l,
                hip_angle_r, hip_angle_l,
                shoulder_angle_r, shoulder_angle_l
            ]], columns=self.FEATURE_NAMES)
            
            try:
                pred = self.model.predict(features)[0]
                if hasattr(self.model, "predict_proba"):
                    proba = self.model.predict_proba(features)[0]
                    confidence = float(max(proba))
                else:
                    confidence = 0.7
                self.quality = "GOOD" if int(pred) == 1 else "BAD"
            except Exception as e:
                print(f"Model prediction error: {e}")

        if self.state == "up" and smooth_knee < self.DOWN_THRESHOLD:
            if now - self.last_state_change > self.HOLD_TIME:
                self.state = "down"
                self.last_state_change = now

        elif self.state == "down" and smooth_knee > self.UP_THRESHOLD:
            if now - self.last_state_change > self.HOLD_TIME:
                if self.rep_log and (now - self.rep_log[-1]["time"]) < 0.8:
                    pass
                else:
                    self.state = "up"
                    self.last_state_change = now

                    valid_depth = self.min_knee_angle < self.DEPTH_THRESHOLD
                    good_symmetry = abs(knee_angle_r - knee_angle_l) < 20
                    good_back = hip_angle_r > 60 and hip_angle_l > 60
                    confident = confidence > 0.6

                    issues = []
                    if not valid_depth:
                        issues.append("Squat deeper! Improve knee angle.")
                    if not good_symmetry:
                        issues.append("Balance your legs equally.")
                    if not good_back:
                        issues.append("Straighten your back!")
                    if self.quality == "BAD" and not issues:
                        issues.append("Adjust overall posture. Keep chest up.")
                    if not confident and not issues:
                        issues.append("Camera can't see you clearly.")

                    if not issues:
                        self.feedback_msg = "Excellent squat!"
                        self.rep_count += 1
                        print(f"✅ Squat completed! Total reps: {self.rep_count}", flush=True)

                        self.rep_log.append({
                            "time": now,
                            "exercise": "squat",
                            "rep": self.rep_count,
                            "quality": self.quality,
                            "feedback": self.feedback_msg,
                        })
                    else:
                        self.feedback_msg = issues[0]

                    self.min_knee_angle = 180

        return {
            "reps": self.rep_count,
            "posture": self.quality,
            "feedback": self.feedback_msg,
            "state": self.state,
            "angle": int(smooth_knee)
        }
