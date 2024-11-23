import os
import time
import threading
import requests
import pandas as pd
from dotenv import load_dotenv
from lightweight_charts import Chart

# Load environment variables
load_dotenv()

# Coinbase API endpoint
BASE_URL = "https://api.exchange.coinbase.com"

def fetch_historical_data(product_id, granularity=60, limit=300):
    try:
        interval_seconds = granularity
        now = int(time.time())
        start = now - (limit * interval_seconds)

        # API request to get candle data
        url = f"{BASE_URL}/products/{product_id}/candles"
        params = {
            'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(start)),
            'end': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
            'granularity': granularity,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        candles = response.json()

        # Prepare DataFrame
        df_candles = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        df_candles['time'] = pd.to_datetime(df_candles['time'], unit='s')
        df_candles = df_candles.sort_values(by='time')

        return df_candles

    except Exception as e:
        print(f"Error fetching data for {product_id}: {e}")
        return pd.DataFrame()

def get_bar_data(symbol, granularity=60, limit=300):
    return fetch_historical_data(symbol, granularity, limit)

def update_loop(charts, coins, interval=10):
    while True:
        for i, coin in enumerate(coins):
            df = get_bar_data(coin, 60, 300)
            if not df.empty:
                charts[i].set(df, True)
        time.sleep(interval)

def main():
    # Initialize main chart and subcharts
    chart = Chart(inner_width=0.5, inner_height=0.5)
    chart2 = chart.create_subchart(position='right', width=0.5, height=0.5)
    chart3 = chart.create_subchart(position='left', width=0.5, height=0.5)
    chart4 = chart3.create_subchart(position='right', width=0.5, height=0.5)

    # Coins to fetch data for
    coins = ['MATH-USD', 'DIA-USD', 'ASM-USD', 'KARRAT-USD']
    charts = [chart, chart2, chart3, chart4]

    for i, coin in enumerate(coins):
        df = get_bar_data(coin, 60, 300)
        if not df.empty:
            charts[i].set(df)
            charts[i].watermark(coin)

    # Start the thread to update charts periodically
    update_thread = threading.Thread(target=update_loop, args=(charts, coins), daemon=True)
    update_thread.start()

    # Display all charts without blocking the main thread
    chart.show(block=True)

if __name__ == '__main__':
    main()