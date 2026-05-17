import base64
import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.squat_tracker import SquatTracker
from ml.bicep_tracker import BicepTracker
from ml.shoulder_tracker import ShoulderTracker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)

# Global session trackers (in memory, simplified for demo)
trackers = {
    "squat": SquatTracker(),
    "bicep": BicepTracker(),
    "shoulder": ShoulderTracker(),
}

class PredictRequest(BaseModel):
    image: str
    exercise: str

@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        # Decode base64 image
        img_data = base64.b64decode(req.image)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid image"}

        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        
        # Get appropriate tracker
        tracker = trackers.get(req.exercise.lower())
        
        if not tracker:
            return {"error": "Invalid exercise type"}
            
        if results.pose_landmarks:
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing_styles = mp.solutions.drawing_styles
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            annotated_b64 = base64.b64encode(buffer).decode('utf-8')

            # Process frame using the tracker
            res = tracker.process_landmarks(results.pose_landmarks.landmark)
            res["annotated_image"] = annotated_b64
            return res
            
        return {
            "reps": tracker.rep_count,
            "posture": "BAD",
            "feedback": "Adjust camera / Person not found",
            "state": tracker.state,
            "angle": 0
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/reset")
async def reset(exercise: str):
    ex = exercise.lower()
    if ex == "squat":
        trackers["squat"] = SquatTracker()
    elif ex == "bicep":
        trackers["bicep"] = BicepTracker()
    elif ex == "shoulder":
        trackers["shoulder"] = ShoulderTracker()
    return {"status": "reset successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
