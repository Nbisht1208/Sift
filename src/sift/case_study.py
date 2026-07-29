import polars as pl
import os
from sift.chaos_monkey.polluter import ChaosMonkey

def create_messy_file():
    if not os.path.exists("data"):
        os.makedirs("data")

    print("Generating 'data/healthcare_messy.csv'...")

    df = pl.DataFrame({
        "patient_id": range(1000, 2000),
        "blood_pressure": ["120/80", "110/70", "130/85", "120/80", "999/999"] * 200,
        "weight_kg": [70.5, 80.0, 65.2, 90.1, 70.5] * 200,
        "diagnosis": ["Healthy", "Diabetes", "Hypertension", "Healthy", "Flu"] * 200,
        "insurance_provider": ["BlueCross", "Aetna", "bluecross", "AETNA", "Cigna"] * 200, # String clusters!
    })

    monkey = ChaosMonkey(seed=99)
    df = monkey.inject_nulls(df, ["weight_kg"], fraction=0.12)

    save_path = "data/healthcare_messy.csv"
    df.write_csv(save_path)
    print(f"✅ Saved case study data to: {os.path.abspath(save_path)}")

if __name__ == "__main__":
    create_messy_file()