# ai/nose_predictor.py

import tensorflow as tf
import numpy as np
import json
from PIL import Image
import io


class NosePredictor:

    def __init__(self):
        # Model load karo
        self.model = tf.saved_model.load("./ai/nose_model")

        # Class names load karo
        with open("./ai/class_names.json") as f:
            self.class_names = json.load(f)

        print(f"Nose AI loaded: {len(self.class_names)} cows registered")

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Image ko model ke liye ready karo"""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))  # 224x224 resize

        arr = np.array(img, dtype=np.float32) / 255.0  # Normalize 0-1
        return np.expand_dims(arr, axis=0)  # Shape: (1, 224, 224, 3)

    def identify(self, image_bytes: bytes) -> dict:
        """Photo se cow ID predict karo"""

        input_tensor = self.preprocess(image_bytes)

        predictions = self.model(input_tensor, training=False)
        probs = predictions.numpy()[0]

        # Best match
        top_idx = np.argmax(probs)
        confidence = float(probs[top_idx])
        cow_id = self.class_names[top_idx]

        # Top 3 matches
        top3_idx = np.argsort(probs)[-3:][::-1]

        top3 = [
            {"cow_id": self.class_names[i], "confidence": float(probs[i])}
            for i in top3_idx
        ]

        return {
            "cow_id": cow_id,
            "confidence": round(confidence * 100, 2),
            "match": confidence > 0.85,
            "top3": top3
        }


# Global singleton — model ek baar load hoga
predictor = NosePredictor()