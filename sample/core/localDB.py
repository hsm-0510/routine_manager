import pandas as pd
import time, os, sqlite3

script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"[SCRIPT DIR]: {script_dir}")
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
print(f"[PROJECT ROOT]: {project_root}")
#dB_path = os.path.join(project_root, "sample\core", "Weighbridge_Local_Database.xlsx")
dB_path = os.path.join(script_dir, "Weighbridge_Local_Database.xlsx")
print(f"[DB PATH]: {dB_path}")

DB_PATH = os.path.join(project_root, "sample\core", "weighbridge.db")

#################################### SQLITE BASED ################################################
# Initialize Database (Must Include in Main)
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weighments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_data TEXT,
        card_data TEXT,
        tare_weight REAL,
        gross_weight REAL NULL,
        net_weight REAL NULL
    )
                   """)
    conn.commit()
    conn.close()

# Save Tare Weight in DB
def save_tare(rfid_data, card_data, tare_weight):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weighments
        (
            rfid_data,
            card_data,
            tare_weight,
            gross_weight,
            net_weight
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            rfid_data,
            card_data,
            tare_weight,
            0,
            0
        ))
    conn.commit()
    conn.close()

# Save Gross Weight and Net Weight in DB
def save_gross(rfid_data, card_data, tare_weight, gross_weight):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, tare_weight
        FROM weighments
        WHERE rfid_data = ?
        ORDER BY id DESC
        LIMIT 1
        """, (rfid_data,))
    
    record = cursor.fetchone()
    
    if record is None:
        conn.close()
        raise Exception("[DATABASE_ERROR]: No Tare Record Found")
    
    weighment_id = record[0]
    tare_weight = record[1]
    
    net_weight = int(gross_weight) - int(tare_weight)
    
    cursor.execute("""
        UPDATE weighments
        SET gross_weight=?,
        net_weight=?
        WHERE id=?
        """,
        (
            gross_weight,
            net_weight,
            weighment_id
        ))
    
    conn.commit()
    conn.close()

# Get Tare Weight (use just tare as variable to store)
def get_tare(rfid_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tare_weight
        FROM weighments
        WHERE rfid_data = ?
        ORDER BY id DESC
        LIMIT 1
        """, (rfid_data,))   
    row = cursor.fetchone()
    conn.close()
    return row[0]

# Get Final Weights (use tare, gross, net as variables to store)
def get_weights(rfid_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tare_weight,
        gross_weight,
        net_weight
        FROM weighments
        WHERE rfid_data = ?
        ORDER BY id DESC
        LIMIT 1
        """, (rfid_data,))   
    row = cursor.fetchone()
    conn.close()
    return row
    
##################################### EXCEL BASED ################################################

# Create Database Column Titles
def create_database():
    df = pd.read_excel(dB_path)
    df.columns = ["S.No", "RFID Data", "Card Data", "Tare Weight", "Gross Weight", "Net Weight"]
    try:
        df.to_excel(dB_path, index=False)
    except PermissionError:
        print("File is open in Excel. Retrying in 2 seconds...")
        time.sleep(2)
        df.to_excel(dB_path, index=False)
    print("[DATABASE]: Created Database")

# Delete Database Entry
def delete_row(df, serialNo):
    df = df[df["S.No"] != serialNo]
    print("Database Cleared")
    return df
# Clear the Database
def clear_database(df):
    return df.iloc[0:0]
# Data entry in Database
def dataEntry(df, tare_weight, rfid_data, card_data):
    if df.empty or df["S.No"].isna().all():
        new_serial_no = 1
    else:
        new_serial_no = int(df["S.No"].iloc[-1]) + 1
    new_row = {
        "S.No": new_serial_no,
        "RFID Data": rfid_data,
        "Card Data": card_data,
        "Tare Weight": tare_weight,
        "Gross Weight": None,
        "Net Weight": None
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    print("[DATABASE]: New Data Entered")
    return df
# Extact Data from Database
def extractData(df, rfid_data, card_data, extract_data):
    row = df[(df["RFID Data"] == rfid_data) and (df["Card Data"] ==  card_data)]
    if row.empty:
        return None
    print("[DATABASE]: Data extracted from Database")
    return row.iloc[0][extract_data]
# Update the Database
def updateData(df, rfid_data, card_data, tare_weight, gross_weight, net_weight):
    mask = (df["RFID Data"] == rfid_data) and (df["Card Data"] == card_data)
    if not mask.any():
        return df
    df.loc[mask, "Gross Weight"] = gross_weight
    df.loc[mask, "Net Weight"] = net_weight
    print("[DATABASE]: Database Updated")
    return df