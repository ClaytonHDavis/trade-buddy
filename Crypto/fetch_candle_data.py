import os
import time
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Initialize an empty DataFrame to store candle data
columns = ['start', 'low', 'high', 'open', 'close', 'volume']
candle_data = pd.DataFrame(columns=columns)

# Function to fetch and append candle data for a specific coin
def fetch_and_append_candles(product_id='BTC-USD', granularity='ONE_MINUTE', limit=5):
    global candle_data  # Use the global DataFrame

    try:
        end = int(time.time())
        start = end - (limit * 60)  # Fetch past limit minutes
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        # Fetch candle data from the API
        candles = client.get(url, params=params)

        # Convert the candle data into a DataFrame
        new_candles = pd.DataFrame(candles['candles'])
        new_candles['start'] = pd.to_datetime(new_candles['start'], unit='s')  # Convert UNIX timestamp to datetime

        # Check for duplicates and append only new entries
        candle_data = pd.concat([candle_data, new_candles]).drop_duplicates(subset=['start']).reset_index(drop=True)

        # Sort the DataFrame by 'start' in descending order
        candle_data = candle_data.sort_values(by='start', ascending=False).reset_index(drop=True)

        # Print the updated DataFrame
        print(candle_data)

    except Exception as e:
        print(f"An error occurred: {e}")

# Main loop to continually fetch data
if __name__ == "__main__":
    while True:
        fetch_and_append_candles()
        time.sleep(60)  # Wait for 60 seconds before fetching again