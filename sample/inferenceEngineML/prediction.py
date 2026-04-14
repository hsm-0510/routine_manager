import os
from sample.inferenceEngineML.buffer_manager import BufferManager
from sample.inferenceEngineML.feature_builder import build_features
from sample.inferenceEngineML.model_runner import ModelRunner
from sample.core  import state_manager


class PredictionEngine:

    def __init__(self):

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

        model_path = os.path.join(project_root, "sample/modelsML", "xgboost_trailer_model.pkl")
        encoder_path = os.path.join(project_root, "sample/modelsML", "label_encoder.pkl")

        self.buffer = BufferManager()
        self.model = ModelRunner(model_path, encoder_path)

        self.MIN_COMPARTMENTS = 1
        
        self.last_signature = None

    def process_event(self, event):
        
        
        signature = (
            event.get("COMPARTMENT_NUMBER"),
            event.get("GROSS_QUANTITY"),
            event.get("Net_Weight_Transformed")
        )
        
        # signature = tuple(sorted(event.items()))

        if signature == self.last_signature:
            return None

        self.last_signature = signature

        trailer = self.buffer.add_event(event)

        rows = self.buffer.get_buffer(trailer)
        
        if len(rows) < 1:
            return None

        # feature builder ALWAYS returns DataFrame
        X = build_features(rows)

        # prediction
        label, probs = self.model.predict(X)

        self.buffer.mark_processed(trailer)
        
        if self.buffer.size(trailer) < self.MIN_COMPARTMENTS:
            return None
        else:
            self.buffer.clear(trailer)

        return {
            "TRAILER_CODE": trailer,
            "PREDICTED_CASE": label,
            "PROB_NORMAL": probs["NORMAL"],
            "PROB_DRIFT": probs["DRIFT"],
            "PROB_THEFT": probs["THEFT"],
            "PROB_MISSING": probs["MISSING"]
        }