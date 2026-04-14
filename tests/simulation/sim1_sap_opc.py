import pandas as pd
import tkinter as tk
from tkinter import filedialog
from opcua import Client
import threading
import time


SERVER_URL = "opc.tcp://127.0.0.1:5501"

TAG_MAP = {
    "SAP_trailer_code": "TRAILER_CODE",
    "SAP_ordered_quantity": "ORDERED_QUANTITY",
    "SAP_gross_quantity": "GROSS_QUANTITY",
    "SAP_batch_start_time": "START_TIME",
    "SAP_batch_end_time": "END_TIME",
    "SAP_compartment_number": "COMPARTMENT_NUMBER",
    "SAP_compartment_name": "NAME",
    "SAP_trailer_net_weight": "Net_Weight_Transformed",
    "SAP_material_density": "Density",
    "SAP_expected_net_weight": "Net_Weight_Original"
}


class OPCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OPC UA Data Sender")

        self.file_path = None
        self.running = False
        self.client = None
        self.nodes = {}

        tk.Button(root, text="Select Excel File", command=self.load_file).pack(pady=5)
        tk.Button(root, text="Start Sending", command=self.start).pack(pady=5)
        tk.Button(root, text="Stop", command=self.stop).pack(pady=5)

        self.status = tk.Label(root, text="Status: Idle")
        self.status.pack(pady=10)

    # =========================
    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        self.status.config(text=f"Loaded: {self.file_path}")

    # =========================
    def connect_opc(self):
        self.client = Client(SERVER_URL)
        self.client.connect()

        objects = self.client.get_objects_node()

        # -------------------------
        # Get correct namespace index
        # -------------------------
        ns_array = self.client.get_namespace_array()
        try:
            idx = ns_array.index("urn:pso:smart-weighbridge")
        except ValueError:
            raise Exception("Namespace not found in server")

        # -------------------------
        # Find root object
        # -------------------------
        root = objects.get_child([f"{idx}:PSO Smart Weighbridge"])

        # -------------------------
        # Access SAP_DATA folder
        # -------------------------
        sap_data = root.get_child([f"{idx}:SAP_DATA"])

        # -------------------------
        # Map tags
        # -------------------------
        self.nodes = {}

        for tag in TAG_MAP.keys():
            try:
                self.nodes[tag] = sap_data.get_child([f"{idx}:{tag}"])
            except Exception as e:
                print(f"Missing OPC tag: {tag} -> {e}")

    # =========================
    def start(self):
        if not self.file_path:
            self.status.config(text="Select Excel file first")
            return

        if self.running:
            return

        self.running = True
        self.status.config(text="Running...")

        thread = threading.Thread(target=self.run_loop, daemon=True)
        thread.start()

    # =========================
    def stop(self):
        self.running = False
        self.status.config(text="Stopped")

        if self.client:
            self.client.disconnect()
            self.client = None

    # =========================
    def run_loop(self):
        try:
            df = pd.read_excel(self.file_path)

            self.connect_opc()

            for _, row in df.iterrows():
                if not self.running:
                    break

                for tag, col in TAG_MAP.items():
                    value = str(row[col]) if col in row else ""

                    if tag in self.nodes:
                        print(f"Writing {tag} = {value}")
                        self.nodes[tag].set_value(value)

                time.sleep(1)

            self.status.config(text="Completed")

        except Exception as e:
            self.status.config(text=f"Error: {str(e)}")
            print("ERROR:", e)

        finally:
            self.running = False

            if self.client:
                self.client.disconnect()
                self.client = None


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = OPCApp(root)
    root.mainloop()