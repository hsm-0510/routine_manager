import joblib
from pathlib import Path


class ModelRunner:
    def __init__(self, model_path, encoder_path):
        # Paths only - the pickle is NOT loaded here. Unpickling the
        # XGBClassifier requires the xgboost/sklearn packages, which are not
        # bundled into the frozen EXE. Loading is deferred until predict() so
        # ML stays available in source mode and never breaks startup.
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.model = None
        self.encoder = None

    def _ensure_loaded(self):
        if self.model is None:
            self.model = joblib.load(self.model_path)
        if self.encoder is None:
            self.encoder = joblib.load(self.encoder_path)
        return self.model, self.encoder

    def predict(self, X):
        # First real inference call triggers the (optional) model load.
        model, encoder = self._ensure_loaded()

        X = X.astype(float)

        pred_class = model.predict(X)[0]
        label = encoder.inverse_transform([pred_class])[0]

        probs = model.predict_proba(X)[0]

        classes = encoder.classes_

        probs_dict = dict(zip(classes, probs))
        
        probs_dict_fixed = {
            "NORMAL": float(probs_dict.get("Normal", 0)),
            "DRIFT": float(probs_dict.get("Calibration_Drift", 0)),
            "THEFT": float(probs_dict.get("Theft", 0)),
            "MISSING": float(probs_dict.get("Missing_Fill", 0)),
        }

        return label, probs_dict_fixed