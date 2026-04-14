import os, time, traceback
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

# Data Mapping for ML-variables & OPC-tags
def normalize_event(event):
    return {
        "TRAILER_CODE": event.get("SAP_trailer_code"),
        "ORDERED_QUANTITY": event.get("SAP_ordered_quantity"),
        "GROSS_QUANTITY": event.get("SAP_gross_quantity"),
        "Density": event.get("SAP_material_density"),
        "START_TIME": event.get("SAP_batch_start_time"),
        "END_TIME": event.get("SAP_batch_end_time"),
        "COMPARTMENT_NUMBER": event.get("SAP_compartment_number"),
        "Net_Weight_Transformed": event.get("SAP_trailer_net_weight"),
        "Net_Weight_Expected": event.get("SAP_expected_net_weight"),
        "NAME": event.get("SAP_compartment_name")
    }

# ML Inference Worker Function (Thread)
def ml_inference_worker(opc, engine):

    print("[ML] Inference worker started...")
    last_event = None

    while True:
        try:
            last_version = -1
            
            print("\n[ML] --- New Cycle ---")

            # Read State Safely
            raw_event = dict(state_manager.misc_tags["SAP_DATA"])
            print("[OPC RAW]", raw_event)
            
            # Data unavailability checks
            if not raw_event:
                time.sleep(0.5)
                continue
            event = normalize_event(raw_event)
            print("[ML] Raw event read:", event)
            if not event:
                print("[ML] No SAP_DATA available, waiting...")
                time.sleep(0.5)
                continue
            if "TRAILER_CODE" not in event:
                print("[ML] Missing TRAILER_CODE, skipping...")
                time.sleep(0.5)
                continue

            # Get trailer code
            trailer = event.get("TRAILER_CODE")
            print(f"[ML] Trailer detected: {trailer}")

            # Prevent reprocessing of same data
            last_event = event.copy()
            print("[ML] New event accepted for processing")

            # ML pre-run checks
            current_version = state_manager.get_sap_version()
            if current_version == last_version:
                time.sleep(0.2)
                continue
            last_version = current_version
            
            # Run ML prediction
            print("[ML] Sending event to PredictionEngine...")
            result = engine.process_event(event)
            
            # In-case of no prediction results
            if not result:
                print("[ML] No prediction triggered (buffer not ready or conditions not met)")
                time.sleep(0.5)
                continue
            print("[ML RESULT]", result)

            # Report ML prediction results to designated OPC-tags
            try:
                print("[ML] Writing results back to OPC...")
                opc.write_tag("SAP_DATA", "SAP_PREDICTED_CASE", result["PREDICTED_CASE"])
                print(f"[ML] Wrote PREDICTED_CASE: {result['PREDICTED_CASE']}")
                opc.write_tag("SAP_DATA", "SAP_PROB_NORMAL", float(result["PROB_NORMAL"]))
                print(f"[ML] Wrote PROB_NORMAL: {result['PROB_NORMAL']}")
                opc.write_tag("SAP_DATA", "SAP_PROB_DRIFT", float(result["PROB_DRIFT"]))
                print(f"[ML] Wrote PROB_DRIFT: {result['PROB_DRIFT']}")
                opc.write_tag("SAP_DATA", "SAP_PROB_THEFT", float(result["PROB_THEFT"]))
                print(f"[ML] Wrote PROB_THEFT: {result['PROB_THEFT']}")
                opc.write_tag("SAP_DATA", "SAP_PROB_MISSING", float(result["PROB_MISSING"]))
                print(f"[ML] Wrote PROB_MISSING: {result['PROB_MISSING']}")
                print("[ML] OPC write completed successfully")

            except Exception as e:
                print("[ML ERROR] OPC write failed:", e)

            time.sleep(0.5)

        except Exception as e:
            print("[ML ERROR] Exception:", repr(e))
            traceback.print_exc()
            time.sleep(1)