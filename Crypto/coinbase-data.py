import os
import time
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from json import dumps
from datetime import datetime


# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY")
api_secret = os.getenv("COINBASE_API_SECRET")

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Function to fetch and display account information
def fetch_account_data():
    try:
        # Get accounts
        accounts = client.get_accounts()
        print("Accounts:")
        print(dumps(accounts, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to fetch market data for a specific product
def fetch_market_data(product_id='BTC-USD'):
    try:
        # Get market data
        market_data = client.get_product(product_id=product_id)
        print(f"Market Data for {product_id}:")
        print(dumps(market_data, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to get trades for a specific coin
def fetch_trade_data(product_id='BTC-USD'):
    try:
        # Get market data
        market_trades = client.get("/api/v3/brokerage/products/BTC-USD/ticker", params={"limit": 5})
        print(f"Market trades for {product_id}:")
        print(dumps(market_trades, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")

import os
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from json import dumps
import time

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Function to get candles for a specific coin
def fetch_candles_data(product_id='BTC-USD', granularity='ONE_MINUTE', limit=5):
    try:
        end = int(time.time())
        start = end - (limit * 60)
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        candles = client.get(url, params=params)
        print(f"Candles for {product_id} (Granularity: {granularity}):")
        
        # Print info for each candle with readable times
        for candle in candles['candles']:
            start_time = datetime.utcfromtimestamp(int(candle['start'])).strftime('%Y-%m-%d %H:%M:%S')
            print(f"Start: {start_time}, Low: {candle['low']}, High: {candle['high']}, Open: {candle['open']}, Close: {candle['close']}, Volume: {candle['volume']}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main script execution
if __name__ == "__main__":
    fetch_account_data()
    fetch_market_data()
    fetch_trade_data()
    fetch_candles_data()