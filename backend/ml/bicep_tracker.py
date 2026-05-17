import numpy as np
import time
from collections import deque
from .base_tracker import BaseTracker

class BicepTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.state = "down"
        self.DOWN_THRESHOLD = 150
        self.UP_THRESHOLD = 60
        self.DEPTH_THRESHOLD = 70
        self.SMOOTHING = 5
        
        self.angle_buffer = deque(maxlen=self.SMOOTHING)
        self.min_angle = 180
        self.max_angle = 0
        self.rep_log = []

    def process_landmarks(self, lm):
        shoulder_r = (lm[12].x, lm[12].y)
        elbow_r = (lm[14].x, lm[14].y)
        wrist_r = (lm[16].x, lm[16].y)

        shoulder_l = (lm[11].x, lm[11].y)
        elbow_l = (lm[13].x, lm[13].y)
        wrist_l = (lm[15].x, lm[15].y)

        angle_r = self.calculate_angle(shoulder_r, elbow_r, wrist_r)
        angle_l = self.calculate_angle(shoulder_l, elbow_l, wrist_l)

        angle = (angle_r + angle_l) / 2
        self.angle_buffer.append(angle)
        smooth_angle = np.mean(self.angle_buffer) if len(self.angle_buffer) > 0 else angle

        self.min_angle = min(self.min_angle, smooth_angle)
        self.max_angle = max(self.max_angle, smooth_angle)

        if self.state == "down" and smooth_angle < self.UP_THRESHOLD:
            self.state = "up"
            self.feedback_msg = "Curling"

        elif self.state == "up" and smooth_angle > self.DOWN_THRESHOLD:
            self.state = "down"

            full_curl = self.min_angle < self.DEPTH_THRESHOLD
            full_extension = self.max_angle > 140
            good_balance = abs(angle_r - angle_l) < 20

            if full_curl and full_extension and good_balance:
                self.rep_count += 1
                self.feedback_msg = "Good form"
                self.rep_log.append({"time": time.time(), "rep": self.rep_count})
            else:
                if not full_curl:
                    self.feedback_msg = "Curl higher"
                elif not full_extension:
                    self.feedback_msg = "Extend fully"
                elif not good_balance:
                    self.feedback_msg = "Balance both arms"
                else:
                    self.feedback_msg = "Control movement"

            self.min_angle = 180
            self.max_angle = 0

        quality = "GOOD" if self.feedback_msg == "Good form" else "BAD"

        return {
            "reps": self.rep_count,
            "posture": quality,
            "feedback": self.feedback_msg,
            "state": self.state,
            "angle": int(smooth_angle)
        }
