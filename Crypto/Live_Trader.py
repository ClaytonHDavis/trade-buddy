import os
import time
import requests
import pandas as pd
import asyncio
from dotenv import load_dotenv
from lightweight_charts import Chart
from coinbase.websocket import WSClient
import json
from datetime import datetime, timezone
import traceback

# Load environment variables
load_dotenv()

# Coinbase API endpoint
BASE_URL = "https://api.exchange.coinbase.com"

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

def fetch_historical_data(product_id, granularity=60, limit=300):
    try:
        interval_seconds = granularity
        now = int(time.time())
        start = now - (limit * interval_seconds)

        url = f"{BASE_URL}/products/{product_id}/candles"
        params = {
            'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(start)),
            'end': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
            'granularity': granularity,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        candles = response.json()

        df_candles = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='s', utc=True)
        
        #trim off anything past the previous 5 minute interval
        df_candles = df_candles[df_candles['time'] > df_candles['time'].iloc[-1].replace(second=0, microsecond=0)]

        return df_candles.sort_values(by='time')

    except Exception as e:
        print(f"Error fetching data for {product_id}: {e}")
        return pd.DataFrame()

class LiveData:
    def __init__(self):
        self.data = pd.DataFrame(columns=['timestamp', 'product_id', 'price'])
        self.candles = pd.DataFrame()

    def add_live_data(self, timestamp, product_id, price):
       try:
           # Process timestamp
           original_timestamp = timestamp
           # Log the raw timestamp
           print(f"Original timestamp received: {original_timestamp}")

           # Assuming timestamp comes in as a string timezone-aware ISO format.
           assert isinstance(timestamp, str), f"Timestamp should be in string format, but got {type(timestamp)}"
           timestamp = pd.to_datetime(timestamp, utc=True)

           new_data = pd.DataFrame([{
               'timestamp': timestamp,
               'product_id': product_id,
               'price': price
           }])
           self.data = pd.concat([self.data, new_data], ignore_index=True)
       except Exception as e:
           print(f"Exception when parsing timestamp: {e}")
           print(f"Faulty data: {timestamp}, {product_id}, {price}")

    def create_candles(self):
       if not self.data.empty:
           try:
               # Ensure data is recent relative to 'now'
               now = pd.Timestamp.now(tz=timezone.utc)
               self.data = self.data[self.data['timestamp'] <= now]

               price_data = self.data.groupby('product_id').resample('5min', on='timestamp').agg({
                   'price': ['first', 'max', 'min', 'last']
               }).reset_index()

               price_data.columns = ['product_id', 'start', 'open', 'high', 'low', 'close']
               self.candles = pd.concat([self.candles, price_data], ignore_index=True).drop_duplicates()
               
               # Order by start timestamps to avoid out-of-order data
               self.candles.sort_values(by='start', inplace=True)
           except Exception as e:
               print(f"Exception during candle creation: {e}")
               print(traceback.format_exc())

live_data = LiveData()

def on_message(msg):
    #print(f"Received message: {msg}")
    try:
        data = json.loads(msg)
        print(f"Received data: {data}")
        if data['channel'] == 'ticker':
            for event in data.get('events', []):
                for ticker in event.get('tickers', []):
                    timestamp = data['timestamp']
                    product_id = ticker['product_id']
                    price = float(ticker['price'])

                    print(f"Received data: {timestamp}, {product_id}, {price}")

                    live_data.add_live_data(timestamp, product_id, price)
        
        live_data.create_candles()

    except (KeyError, ValueError) as e:
        print(f"Error processing message: {e}")

async def update_chart_with_live_data(chart, product_ids):
    print("Starting live data update loop...")
    while chart.is_alive and not live_data.data.empty:
        try:
            live_data.create_candles()  # Create or update candles with the data
            if not live_data.candles.empty:
                for product_id in product_ids:
                    latest_candle = live_data.candles[live_data.candles['product_id'] == product_id].iloc[-1]

                    tick_data = pd.Series({
                        'time': latest_candle['start'],
                        'open': latest_candle['open'],
                        'high': latest_candle['high'],
                        'low': latest_candle['low'],
                        'close': latest_candle['close'],
                    }, name='TickData')

                    # Only update if new data is available
                    if chart.data.empty or tick_data['time'] > chart.data['time'].iloc[-1]:
                        print(f"Updating chart with tick data: {tick_data.to_dict()}")
                        chart.update_from_tick(tick_data)
                    elif tick_data['time'] == chart.data['time'].iloc[-1]:
                        # If the current candle is still being updated, use a different update method if available
                        chart.update_current_bar(tick_data)
        except Exception as e:
            print(f"Error during chart update: {e}")
        await asyncio.sleep(1)

async def main():
    chart = Chart(toolbox=True)
    chart.legend(True)

    # Start with historical data
    initial_symbol = 'BTC-USD'
    historical_data = fetch_historical_data(initial_symbol, 60)
    if not historical_data.empty:
        chart.set(historical_data)

    # Set up WebSocket and chart updates with live data
    ws_client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message)
    ws_client.open()
    product_ids = ['BTC-USD']
    ws_client.subscribe(product_ids=product_ids, channels=["ticker"])

    await asyncio.gather(chart.show_async(), update_chart_with_live_data(chart, product_ids))

if __name__ == '__main__':
    asyncio.run(main())