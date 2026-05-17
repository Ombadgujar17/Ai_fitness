import numpy as np

class BaseTracker:
    def __init__(self):
        self.rep_count = 0
        self.state = "up" # or down, depending on exercise
        self.feedback_msg = ""
        
    def calculate_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba, bc = a - b, c - b
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))

    def process_landmarks(self, landmarks):
        """
        Process the frame landmarks and update state.
        Should return a dict containing state, reps, feedback, etc.
        """
        raise NotImplementedError
