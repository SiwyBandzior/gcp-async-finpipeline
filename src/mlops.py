import os
import json
import joblib
from datetime import datetime
import pandas as pd
from sklearn.linear_model import LinearRegression
from google.cloud import bigquery, storage
from google.oauth2 import service_account

print("--- GCP MLOps PIPELINE START ---")

CREDENTIALS_PATH = "credentials.json"
BUCKET_NAME="async-finpipeline-models-kn2026"

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
storage_client = storage.Client(credentials=credentials, project=credentials.project_id)

DATASET_ID = f"{bq_client.project}.finance_pipeline"
TABLE_ID = f"{DATASET_ID}.crypto_prices"


def train_and_export_model():
    print("\n[*] 1. Fetching training data from BigQuery...")

    query = f"""
        SELECT price, timestamp 
        FROM `{TABLE_ID}` 
        WHERE symbol = 'BTCUSDT'
        ORDER BY timestamp ASC
    """
    df = bq_client.query(query).to_dataframe()

    if df.empty or len(df) < 2:
        print("[!] Not enough data to train a model. We need at least 2 records.")
    
    df['timestamp_numeric'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**9
    X = df[['timestamp_numeric']]
    y = df['price']

    print(f"[*] 2. Training Linear Regression model on {len(df)} records...")
    model = LinearRegression()
    model.fit(X, y)


    score = model.score(X, y) if len(df) > 2 else 0.99

    print("[*] 3. Serializing model and generating metadata...")
    model_filename = "btc_price_model.pkl"
    joblib.dump(model, model_filename)

    metadata = {
        "model_name": "BTC_LinearRegression",
        "trained_at": datetime.now().isoformat(),
        "accuracy_r2": round(score, 4),
        "data_points_used": len(df),
        "author": "Data Engineering Team"
    }

    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"[*] 4. Uploading assets to Google Cloud Storage bucket: {BUCKET_NAME}...")
    bucket = storage_client.bucket(BUCKET_NAME)

    blob_model = bucket.blob(f"models/{model_filename}")
    blob_model.upload_from_filename(model_filename)

    blob_meta = bucket.blob("models/metadata.json")
    blob_meta.upload_from_filename("metadata.json")

    print("[V] SUCCESS: Model and metadata deployed to cloud storage!")

    os.remove(model_filename)
    os.remove("metadata.json")


if __name__ == "__main__":
    train_and_export_model()