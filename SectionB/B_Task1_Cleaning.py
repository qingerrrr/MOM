import py7zr
import os
from pathlib import Path
import pandas as pd
import numpy as np

# --- Headers ---
def clean_headers(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"\(.*?\)", "", regex=True)
    )

    df = df.rename(columns=lambda x: COLUMN_MAPPING.get(x, x))
    return df

# --- Travel Date & Time ---
def clean_datetime(df):
    date_split = df["travel_date"].str.split(" TO ", expand=True)
    time_split = df["travel_time"].str.split(" TO ", expand=True)

    df["start_datetime"] = pd.to_datetime(
        date_split[0] + " " + time_split[0],
        dayfirst=True,
        errors="coerce"
    )

    df["end_datetime"] = pd.to_datetime(
        date_split[1] + " " + time_split[1],
        dayfirst=True,
        errors="coerce"
    )

    df["trip_duration_min"] = (
        df["end_datetime"] - df["start_datetime"]
    ).dt.total_seconds() / 60
    
    df = df.drop(columns=["travel_date", "travel_time"])

    return df

def combine_csv_files(folder_path):   
    folder_path = Path(folder_path)

    # Find all CSV files in the folder
    csv_files = folder_path.glob("*.csv")

    dfs = []

    for file in csv_files:
        print(f"Loading: {file.name}")
        df = pd.read_csv(file)

        df = clean_headers(df)
        df = df.drop(columns=[
            'pickup_x', 'pickup_y',
            'destination_x', 'destination_y'
        ], errors='ignore')
        df = df.replace(r"(?i)^\s*(nil|null)\s*$", pd.NA, regex=True)
        df = clean_datetime(df)
        df["total_fare"] = df["taxi_fare"] + df["admin"]

        
        df = df.dropna(subset=["distance_run"])
        df = df.replace({pd.NA: None})
        
        dfs.append(df)

    # Combine all DataFrames into one
    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df

# --- Extract CSV from 7z ---
DATA_PATH = r"D:\Assessment - SPTD Specialist AI_Data\SectionB_taxi trips_201501 to 201509.7z"
OUTPUT_PATH = r"D:\Assessment - SPTD Specialist AI_Data\SectionB_taxi trips_201501 to 201509"
COLUMN_MAPPING = {
    "cardno": "card_no",
    "card_no": "card_no"
}

os.makedirs(OUTPUT_PATH, exist_ok=True)

with py7zr.SevenZipFile(DATA_PATH, mode='r') as archive:
    csv_files = [f for f in archive.getnames() if f.lower().endswith("csv")]
    
    for f in csv_files:
        output_file = os.path.join(OUTPUT_PATH, f)
        if os.path.exists(output_file):
            os.remove(output_file)

    archive.extract(targets=csv_files, path=OUTPUT_PATH)

print(f"Extracted {len(csv_files)} CSV files to {OUTPUT_PATH}")

data = combine_csv_files(r"D:\Assessment - SPTD Specialist AI_Data\SectionB_taxi trips_201501 to 201509")
print(data.shape)
print(data.columns)
print(data.isnull().sum())
print(data.head(15))

print("\nSaved to CSV!")
data.to_csv("cleaned_taxi_data.csv", index=False)