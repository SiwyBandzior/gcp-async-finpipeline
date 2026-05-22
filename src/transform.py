from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@dataclass
class StockRecord:
    symbol: str
    price: float
    timestamp: datetime

    @classmethod
    def from_binance_api(cls, raw_data: dict):
        symbol = raw_data.get("symbol")
        raw_price = raw_data.get("price")

        if not symbol or not raw_price:
            raise ValueError(f"Missing critical fields in raw data: {raw_data}")
        
        try:
            price = float(raw_price)
        except ValueError:
            raise ValueError(f"Data Quality Error: Price is not a valid number - {raw_price}")
        
        if price <= 0:
            raise ValueError(f"Data Quality Error: Imposible price detected for {symbol}: {price}")
        
        return cls(
            symbol=symbol,
            price=price,
            timestamp=datetime.now()
        )
    
if __name__ == "__main__":
    print("--- TESTING DATA TRANSFORMATION ---")

    good_data = {"symbol": "BTCUSDT", "price": "76395.07"}
    bad_data = {"symbol": "ETHUSDT", "price": "ERROR_500"}

    try:
        clean_record = StockRecord.from_binance_api(good_data)
        print(f"[V] Successfully processed: {clean_record}")

        broken_record = StockRecord.from_binance_api(bad_data)
    except Exception as e:
        logging.error(f"Transformation failed -> {e}")