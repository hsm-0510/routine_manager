import joblib
from pathlib import Path


class ModelRunner:
    def __init__(self, model_path, encoder_path):

        # Load model
        self.model = joblib.load(model_path)

        # Load encoder
        self.encoder = joblib.load(encoder_path)

    def predict(self, X):
        
        X = X.astype(float)

        pred_class = self.model.predict(X)[0]
        label = self.encoder.inverse_transform([pred_class])[0]

        probs = self.model.predict_proba(X)[0]

        classes = self.encoder.classes_

        probs_dict = dict(zip(classes, probs))
        
        probs_dict_fixed = {
            "NORMAL": float(probs_dict.get("Normal", 0)),
            "DRIFT": float(probs_dict.get("Calibration_Drift", 0)),
            "THEFT": float(probs_dict.get("Theft", 0)),
            "MISSING": float(probs_dict.get("Missing_Fill", 0)),
        }

        return label, probs_dict_fixed