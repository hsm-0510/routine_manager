import socket
import json
import threading
import time
import traceback
from sample.opcua.opcua_client import PSOWeighbridgeClient
from sample.opcua import opcua_update
from sample.opcua import opcua_client
from sample.tcpClient import tcp_client
from sample.tcpClient import tcp_connection_manager
from sample.utils import config_loader
from sample.core import state_manager
from sample.core import controller
from sample.inferenceEngineML.prediction import PredictionEngine

# ============================
# GLOBAL ML ENGINE
# ============================
engine = PredictionEngine()

def normalize_event(event):
    def safe_float(x, default=0.0):
        try:
            if x is None:
                return default
            return float(x)
        except:
            return default

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

# ============================
# ML INFERENCE WORKER THREAD
# ============================
def ml_inference_worker(opc):

    print("[ML] Inference worker started...")

    last_event = None

    while True:
        try:
            last_version = -1
            
            print("\n[ML] --- New Cycle ---")

            # -------------------------------
            # READ STATE SAFELY
            # -------------------------------
            raw_event = dict(state_manager.misc_tags["SAP_DATA"])
            print("[OPC RAW]", raw_event)
            
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

            trailer = event.get("TRAILER_CODE")
            print(f"[ML] Trailer detected: {trailer}")

            # # -------------------------------
            # # PREVENT REPROCESSING SAME DATA
            # # -------------------------------
            # if event == last_event:
            #     print("[ML] Duplicate event detected, skipping...")
            #     time.sleep(0.5)
            #     continue

            last_event = event.copy()
            print("[ML] New event accepted for processing")

            # -------------------------------
            # RUN ML
            # -------------------------------
            
            current_version = state_manager.get_sap_version()

            if current_version == last_version:
                time.sleep(0.2)
                continue

            last_version = current_version
            
            print("[ML] Sending event to PredictionEngine...")
            result = engine.process_event(event)

            if not result:
                print("[ML] No prediction triggered (buffer not ready or conditions not met)")
                time.sleep(0.5)
                continue

            print("[ML RESULT]", result)

            # -------------------------------
            # WRITE BACK TO OPC
            # -------------------------------
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

def main():
    # Keep main thread alive
    try:
        # Establish OPC Connection as Client
        opc.connect()
        
        # Start reconnect manager
        threading.Thread(target=conn_mgr.connect, daemon=True).start()
        
        # Serial Data-in Thread
        threading.Thread(target=controller.routine1, args=(opc,), daemon=True).start()
        
        # TCP send & receive threads
        threading.Thread(target=tcp_client.send_data, args=(conn_mgr, state_manager.tcp_payload,), daemon=True).start()
        threading.Thread(target=tcp_client.receive_data, args=(conn_mgr,), daemon=True).start()
        
        # ML Inference Thread
        threading.Thread(target=ml_inference_worker, args=(opc,), daemon=True).start()
        
        while True: # TCP/OPCUA Data-transfer
            opcua_update.update_opc_elements(opc)
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nClosing Connection...")
        conn_mgr.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn_mgr.close()
        opc.disconnect()

if __name__ == "__main__":
    # OPCUA Client Object
    opc = PSOWeighbridgeClient(
        endpoint=config_loader.opc_config_load("endpoint", 0),
        namespace_uri=config_loader.opc_config_load("namespaceUri", 0),
        server_object_name=config_loader.opc_config_load("serverObjectName", 0)
    )
    
    # Establishing TCP Connection Manager
    conn_mgr = tcp_connection_manager.TCPConnectionManager(tcp_client.SERVER_IP, tcp_client.SERVER_PORT)
    
    # OPCUA Update Thread
    # threading.Thread(target=opcua_update.update_opc_elements, args=(opc, sock,), daemon=True).start()
    
    #Run Main()
    main()