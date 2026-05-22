import asyncio
import aiohttp
import time

ASSETS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "DOGEUSDT", "LINKUSDT"]

async def fetch_asset_data(session: aiohttp.ClientSession, asset: str) -> dict:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={asset}"

    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"[!] Error fetching {asset}: HTTP {response.status}")
                return None
    except Exception as e:
        print(f"[!] Network error for {asset}: {e}")
        return None


async def extract_data_async():
    print(f"[*] Initializing async extracion for {len(ASSETS)} assets...")
    start_time = time.time()

    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for asset in ASSETS:
            task = fetch_asset_data(session, asset)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"[V] Extraction complete in {end_time - start_time:.3f} seconds.")

    valid_records = [r for r in results if r is not None]
    return valid_records

if __name__ == "__main__":
    extracted_data = asyncio.run(extract_data_async())

    print("\n--- SAMPLE EXTRACTED DATA ---")
    if extracted_data:
        sample = extracted_data[0]
        print(f"Symbol: {sample['symbol']}")
        print(f"Price (USDT): ${float(sample['price']):.2f}")