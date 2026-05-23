import asyncio
import logging
from extract import extract_data_async
from transform import  StockRecord
from load import setup_bigquery_infrastructure, load_records_to_bigquery

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def run_etl_pipeline():
    """Main Orchestrator function for the ETL Pipeline."""
    print("\n=== 🚀 STARTING GCP-ASYNC-FINPIPELINE ===")

    print("\n[STEP 0] Veryfiying Cloud Infrastructure...")
    setup_bigquery_infrastructure()

    print("\n[STEP 1] Extracting Data (Aync)...")
    raw_data_list = await extract_data_async()

    if not raw_data_list:
        print("[!] No data extracted. Pipeline stopped.")
        return
    
    print("\n[STEP 2] Transforming & Validating Data...")
    clean_records = []

    for raw_item in raw_data_list:
        try:
            record = StockRecord.from_binance_api(raw_item)
            clean_records.append(record)
        except Exception as e:
            logging.error(f"Skipping invalid record: {e}")
    
    print(f"[*] Successfully validated {len(clean_records)} out of {len(raw_data_list)} records.")


    if clean_records:
        print("\n[STEP 3] Loading Data to BigQuery...")
        load_records_to_bigquery(clean_records)
    else:
        print("[!] No valid records to load after transformation.")

    print("\n=== 🏁 PIPELINE EXECUTION COMPLETED ===")


if __name__ == "__main__":
    asyncio.run(run_etl_pipeline())