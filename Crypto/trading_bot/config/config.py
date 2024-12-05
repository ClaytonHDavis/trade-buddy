import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Coinbase API credentials
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY").strip()
    COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET").strip()
    
    # Trading parameters
    COMMISSION_RATE = 0.0075
    
    # Strategy parameters
    PROFIT_TARGET = 0.027        # Example: 2.7%
    PRICE_MOVE = 0.05          # Example: 0.005%
    LOOK_BACK = 100
    DROP_THRESHOLD = -0.05      # Example: -0.005%
    
    # Other configurations
    MARKET_DATA_PREFIX = "market_data"
    TRADE_LOG_FILE = "trade_log.csv"
    DATA_FETCH_LIMIT = 300