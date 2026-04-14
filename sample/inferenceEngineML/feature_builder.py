import pandas as pd
import numpy as np

def build_features(rows):

    df = pd.DataFrame(rows).copy()

    # ========================================================
    # 1. SAFE TYPE CONVERSION (VERY IMPORTANT)
    # ========================================================
    for col in ["GROSS_QUANTITY", "ORDERED_QUANTITY", "Density", "Net_Weight_Transformed", "Net_Weight_Expected"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # fill missing safely
    df["Density"] = df["Density"].fillna(1.0)
    df["GROSS_QUANTITY"] = df["GROSS_QUANTITY"].fillna(0)
    df["ORDERED_QUANTITY"] = df["ORDERED_QUANTITY"].fillna(0)

    # ========================================================
    # 2. TIME CONVERSION
    # ========================================================
    df["START_TIME"] = pd.to_datetime(df["START_TIME"], errors="coerce")
    df["END_TIME"] = pd.to_datetime(df["END_TIME"], errors="coerce")

    # ========================================================
    # 3. FEATURE ENGINEERING (TRAIN-CONSISTENT)
    # ========================================================
    df["Expected_Weight"] = df["Density"] * df["GROSS_QUANTITY"] / 1000
    df["Expected_Weight"] = df["Expected_Weight"].fillna(0)

    # net_original = df["Expected_Weight"].sum()
    
    net_original = df["Net_Weight_Expected"].iloc[0]

    net_transformed = (
        df["Net_Weight_Transformed"].iloc[0]
        if "Net_Weight_Transformed" in df.columns
        else net_original
    )

    df["Delta"] = net_transformed - net_original
    df["Delta_Norm"] = df["Delta"] / (net_original + 1e-6)

    df["Duration"] = (
        df["END_TIME"].max() - df["START_TIME"].min()
    ).total_seconds() / 60 if len(df) > 0 else 0

    # ========================================================
    # 4. FINAL FEATURE VECTOR (ORDER FIXED)
    # ========================================================
    X = pd.DataFrame([{
        "Expected_Weight": net_original,
        "Delta": df["Delta"].mean(),
        "Delta_Norm": df["Delta_Norm"].mean(),
        "Density": df["Density"].mean(),
        "Duration": df["Duration"].iloc[0]
    }])

    # enforce correct column order (VERY IMPORTANT)
    X = X[
        [
            "Expected_Weight",
            "Delta",
            "Delta_Norm",
            "Density",
            "Duration"
        ]
    ]
    
    print("------ DEBUG ML INPUT ------")
    print("Expected Total:", net_original)
    print("Transformed Total:", net_transformed)
    print("Delta:", df["Delta"])
    print("Delta_Norm:", df["Delta_Norm"])
    print("---------------------------")

    return X