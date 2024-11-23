#LIVE DATAFEED WORKING BUT NOT WITH A CHART

import os
import time
import pandas as pd
from dotenv import load_dotenv
from coinbase.websocket import WSClient
from coinbase.rest import RESTClient
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Initialize the REST client
rest_client = RESTClient(api_key=api_key, api_secret=api_secret)

# Initialize an empty DataFrame to store historical candles
columns = ['start', 'low', 'high', 'open', 'close', 'volume', 'product_id']
historical_candles = pd.DataFrame(columns=columns)


# Function to fetch historical data
def fetch_historical_data(product_id, granularity='FIVE_MINUTE', limit=100):
    print(f"Fetching historical data for {product_id}")
    try:
        # Assume 'FIVE_MINUTE' granularity corresponds to a fixed interval (here 5 minutes as 300 seconds)
        interval_seconds = 300
        now = int(time.time())
        start = now - (limit * interval_seconds)
        
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": now,
            "granularity": granularity,
            "limit": limit
        }

        candles = rest_client.get(url, params=params)
        if not candles:
            return pd.DataFrame(columns=columns)
        
        new_candles = pd.DataFrame(candles['candles'])
        new_candles['start'] = pd.to_datetime(new_candles['start'], unit='s')
        new_candles['product_id'] = product_id
        
        numeric_columns = ['low', 'high', 'open', 'close', 'volume']
        for col in numeric_columns:
            new_candles[col] = pd.to_numeric(new_candles[col], errors='coerce')

        return new_candles
    except Exception as e:
        print(f"An error occurred while fetching historical data: {e}")
        return pd.DataFrame(columns=columns)
    
# Retrieve historical data for each asset
product_ids = ['MATH-USD', 'DIA-USD', 'ASM-USD', 'ORN-USD', 'KARRAT-USD']
for product_id in product_ids:
    historical_candles = pd.concat([historical_candles, fetch_historical_data(product_id)], ignore_index=True)

class LiveData:
    def __init__(self):
        self.data = pd.DataFrame(columns=['timestamp', 'product_id', 'price'])
        self.candles = pd.DataFrame(columns=columns)

    def add_live_data(self, timestamp, product_id, price):
        # Create a new row DataFrame
        new_data = pd.DataFrame([{
            'timestamp': pd.to_datetime(timestamp),
            'product_id': product_id,
            'price': price
        }])
        # Use pd.concat instead of append
        self.data = pd.concat([self.data, new_data], ignore_index=True)

    def create_candles(self):
        price_data = self.data.groupby('product_id').resample('5T', on='timestamp').agg({
            'price': ['first', 'max', 'min', 'last']
        }).reset_index()

        price_data.columns = ['product_id', 'start', 'open', 'high', 'low', 'close']
        self.candles = pd.concat([self.candles, price_data], ignore_index=True).drop_duplicates()

def on_message(msg):
    try:
        data = json.loads(msg)
        
        if data['channel'] == 'ticker':
            for event in data.get('events', []):
                for ticker in event.get('tickers', []):
                    timestamp = data['timestamp']
                    product_id = ticker['product_id']
                    price = float(ticker['price'])
                    
                    live_data.add_live_data(timestamp, product_id, price)
                
        # Optional: Print or process live 5-minute candles
        live_data.create_candles()
        print(live_data.candles)
        
    except KeyError as e:
        print(f"Key error: {e}")
    except ValueError as e:
        print(f"JSON error: {e}")

def on_open():
    print("Connection opened!")

# Initialize live data outside of try block for clarity
live_data = LiveData()

# Ensure keys are correct and network connection is stable for WSClient
if __name__ == "__main__":
    ws_client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, on_open=on_open)

    try:
        ws_client.open()
        ws_client.subscribe(product_ids=product_ids, channels=["ticker"])
        
        # Run indefinitely to keep WebSocket connection alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ws_client.unsubscribe(product_ids=product_ids, channels=["ticker"])
        ws_client.close()
    except Exception as e:
        print(f"An error occurred: {e}")

