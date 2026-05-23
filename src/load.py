import os
from google.cloud import bigquery
from google.oauth2 import service_account
from transform import StockRecord

print("--- GCP BIGQUERY LOADING ENGINE ---")

CREDENTIALS_PATH = "credentials.json"
if not os.path.exists(CREDENTIALS_PATH):
    raise FileNotFoundError(f"[!] Critical Error: {CREDENTIALS_PATH} not found in root directory!")


credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

DATASET_ID = f"{client.project}.finance_pipeline"
TABLE_ID = f"{DATASET_ID}.crypto_prices"


def setup_bigquery_infrastructure():
    """Creates the dataset and partitioned/clustered table if they don't exist."""

    try:
        client.get_dataset(DATASET_ID)
        print(f"[*] Dataset '{DATASET_ID}' already exist.")
    except Exception:
        print(f"[*] Creating new BigQuery dataset: '{DATASET_ID}'...")
        dataset = bigquery.Dataset(DATASET_ID)
        dataset.location = "EU"
        client.create_dataset(dataset, timeout=30)
        print("[V] Dataset created successfully.")
    
    try:
        client.get_table(TABLE_ID)
        print(f"[*] Table '{TABLE_ID}' already exist.")
    except Exception:
        print(f"[*] Creating new Partitioned & Clustered table: '{TABLE_ID}'...")

        schema=[
            bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("price", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED")
        ]

        table = bigquery.Table(TABLE_ID, schema=schema)

        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )

        table.clustering_fields = ["symbol"]

        client.create_table(table)
        print("[V] Table canfigured and created successfully!")


def load_records_to_bigquery(records: list[StockRecord]):
    """Loads validates StockRecord objects into BigQuery using free Batch Jobs."""
    print(f"[*] Preparing to load {len(records)} records to GCP (Batch Mode)...")

    rows_to_insert = [{
        "symbol": record.symbol,
        "price": record.price,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }
    for record in records
    ]

    job_config = bigquery.LoadJobConfig(
        source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    )

    try:
        job = client.load_table_from_json(
            rows_to_insert,
            TABLE_ID,
            job_config=job_config
        )

        job.result()

        print(f"[V] SUCCESS: Successfully injected {len(rows_to_insert)} rows via Batch Load!")

    except Exception as e:
        print(f"[!] Injection failed: {e}")

        if hasattr(job, 'errors') and job.errors:
            for err in job.errors:
                print(f"-> {err}")



if __name__ == "__main__":
    from datetime import datetime

    setup_bigquery_infrastructure()

    test_records = [
        StockRecord(symbol="BTCUSDT", price=76400.50, timestamp=datetime.now()),
        StockRecord(symbol="ETHUSDT", price=2450.75, timestamp=datetime.now())
    ]

    load_records_to_bigquery(test_records)