import pandas as pd
from config.config import Config

def save_market_data_to_csv(df_candles: pd.DataFrame, coin: str, file_name_prefix: str = Config.MARKET_DATA_PREFIX):
    try:
        file_name = f"{file_name_prefix}_{coin.replace('-', '_')}.csv"
        df_candles.to_csv(file_name, index=False)
        print(f"Market data for {coin} saved to {file_name}")
    except Exception as e:
        print(f"Error saving market data for {coin} to CSV: {e}")