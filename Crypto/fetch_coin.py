import sys
import os

# Add the directory containing CandleDataFetcher to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from CandleDataFetcher import CandleDataFetcher

# Create an instance of CandleDataFetcher
fetcher = CandleDataFetcher()

# Fetch candle data for a specific coin
data = fetcher.fetch_candles(product_id='ETH-USD', granularity='FIVE_MINUTES', days_back=3)

# Print the fetched data
print(data)

# Create an instance of CandleDataFetcher
fetcher = CandleDataFetcher()

# Fetch candle data for a specific coin
data = fetcher.fetch_candles(product_id='ETH-USD', granularity='FIVE_MINUTES', days_back=3)

# Print the fetched data
print(data)