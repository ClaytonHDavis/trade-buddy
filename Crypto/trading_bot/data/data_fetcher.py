import time
import pandas as pd
from coinbase.rest import RESTClient
from config.config import Config

class DataFetcher:
    GRANULARITY_SECONDS_MAP = {
        'ONE_MINUTE': 60,
        'FIVE_MINUTE': 300,
        'FIFTEEN_MINUTE': 900,
        'THIRTY_MINUTE': 1800,
        'ONE_HOUR': 3600,
        'TWO_HOUR': 7200,
        'SIX_HOUR': 21600,
        'ONE_DAY': 86400,
    }

    def __init__(self):
        self.client = RESTClient(api_key=Config.COINBASE_API_KEY,
                                 api_secret=Config.COINBASE_API_SECRET)

    def fetch_historical_data(self, product_id, granularity='ONE_MINUTE', limit=Config.DATA_FETCH_LIMIT):
        try:
            now = int(time.time())
            if granularity not in self.GRANULARITY_SECONDS_MAP:
                raise ValueError(f"Unsupported granularity: {granularity}")

            interval_seconds = self.GRANULARITY_SECONDS_MAP[granularity]
            total_seconds = interval_seconds * limit
            start = now - total_seconds
            end = now
            url = f"/api/v3/brokerage/products/{product_id}/candles"
            params = {
                "start": start,
                "end": end,
                "granularity": granularity,
                "limit": limit
            }
            response = self.client.get(url, params=params)
            candles = response.get('candles', [])
            if not candles:
                print(f"No candle data returned for {product_id}")
                return pd.DataFrame()

            df_candles = pd.DataFrame(candles)
            df_candles['time'] = pd.to_datetime(df_candles['start'], unit='s')
            float_columns = ['low', 'high', 'open', 'close', 'volume']
            df_candles[float_columns] = df_candles[float_columns].astype(float)
            df_candles = df_candles[['time', 'low', 'high', 'open', 'close', 'volume']]
            df_candles = df_candles.sort_values(by='time').reset_index(drop=True)
            return df_candles
        except Exception as e:
            print(f"Error fetching data for {product_id}: {e}")
            return pd.DataFrame()

    def get_bar_data(self, symbol, granularity='ONE_MINUTE', limit=Config.DATA_FETCH_LIMIT):
        return self.fetch_historical_data(symbol, granularity, limit)