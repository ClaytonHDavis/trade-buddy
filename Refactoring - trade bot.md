# Refactoring - trade bot

## Original Code

```python
import os
import time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient
from coinbase_portfolio import PortfolioManager
from coinbase_make_transactions import place_market_order

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

def fetch_historical_data(product_id, granularity='ONE_MINUTE', limit=300):
    try:
        now = int(time.time())
        granularity_seconds_map = {
            'ONE_MINUTE': 60,
            'FIVE_MINUTE': 300,
            'FIFTEEN_MINUTE': 900,
            'THIRTY_MINUTE': 1800,
            'ONE_HOUR': 3600,
            'TWO_HOUR': 7200,
            'SIX_HOUR': 21600,
            'ONE_DAY': 86400,
        }
        if granularity not in granularity_seconds_map:
            raise ValueError(f"Unsupported granularity: {granularity}")
        
        interval_seconds = granularity_seconds_map[granularity]
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

        response = client.get(url, params=params)
        candles = response.get('candles', [])
        if not candles:
            print(f"No candle data returned for {product_id}")
            return pd.DataFrame()
        
        df_candles = pd.DataFrame(candles)
        df_candles['start'] = pd.to_datetime(df_candles['start'], unit='s')
        df_candles.rename(columns={'start': 'time'}, inplace=True)
        
        float_columns = ['low', 'high', 'open', 'close', 'volume']
        df_candles[float_columns] = df_candles[float_columns].astype(float)
        df_candles = df_candles[['time', 'low', 'high', 'open', 'close', 'volume']]
        df_candles = df_candles.sort_values(by='time').reset_index(drop=True)
        return df_candles
    except Exception as e:
        print(f"Error fetching data for {product_id}: {e}")
        return pd.DataFrame()

def get_bar_data(symbol, granularity='ONE_MINUTE', limit=300):
    return fetch_historical_data(symbol, granularity, limit)

def save_market_data_to_csv(df_candles, coin, file_name_prefix="market_data"):
    try:
        file_name = f"{file_name_prefix}_{coin.replace('-', '_')}.csv"
        df_candles.to_csv(file_name, index=False)
        print(f"Market data for {coin} saved to {file_name}")
    except Exception as e:
        print(f"Error saving market data for {coin} to CSV: {e}")

class LiveTrader:
    def __init__(self, portfolio_manager, commission_rate, params, is_live_mode=True):
        self.portfolio_manager = portfolio_manager
        self.is_live_mode = is_live_mode
        self.cash = max(10, self.portfolio_manager.extract_total_cash_balance(self._fetch_portfolio_data())) if self.is_live_mode else 10
        self.portfolio = {}  # Consistent structure: {'coin': {'quantity': x, 'average_entry_price': y}}
        self.commission_rate = commission_rate
        self.trade_log = []
        self.last_purchase_info = {}
        self.params = params
        self.update_portfolio()

    def _fetch_portfolio_data(self):
        portfolio_uuid = self.portfolio_manager.list_portfolio()
        return self.portfolio_manager.get_portfolio_breakdown(portfolio_uuid)

    def update_portfolio(self):
        portfolio_data = self._fetch_portfolio_data()
        filtered_positions = self.portfolio_manager.filter_portfolio(portfolio_data, ['BTC'], [], name_filter_mode='include')
        for position in filtered_positions:
            asset = position['asset']
            # Extract the average entry price as a float from the dictionary
            price_info = position.get('average_entry_price', {'value': '0', 'currency': 'USD'})
            average_entry_price = float(price_info['value'])  # Convert value from string to float
            self.portfolio[f"{asset}-USD"] = {
                'quantity': position['total_balance_crypto'],
                'average_entry_price': average_entry_price
            }
        if self.is_live_mode:
            self.cash = min(self.portfolio_manager.extract_total_cash_balance(portfolio_data), 10)
        print(f"Portfolio updated: {self.portfolio}")
        print(f"Last purchase info updated: {self.last_purchase_info}")

    def calculate_total_portfolio_value(self, market_data):
        if self.is_live_mode:
            self.update_portfolio()
        total_value = self.cash
        for coin, data in self.portfolio.items():
            quantity = data.get('quantity', 0)
            if quantity > 0 and coin in market_data and not market_data[coin].empty:
                price = market_data[coin]['close'].iloc[0]
                total_value += quantity * price
        print(f"Total portfolio value: {total_value:.2f}")
        return total_value

    def save_trade_log_to_csv(self, file_name="trade_log.csv"):
        try:
            df_trade_log = pd.DataFrame(self.trade_log)
            df_trade_log.to_csv(file_name, index=False)
            print(f"Trade log saved to {file_name}")
        except Exception as e:
            print(f"Error saving trade log to CSV: {e}")

    def commission(self, amount):
        return amount * self.commission_rate

    def log_trade(self, action, coin, price, quantity, trade_datetime, profit=0):
        commission_fee = self.commission(price * quantity)
        self.trade_log.append({
            'Datetime': trade_datetime,
            'Action': action,
            'Coin': coin,
            'Price': price,
            'Quantity': quantity,
            'Cash': self.cash,
            'Portfolio': self.portfolio.copy(),
            'Profit': profit,
            'Commission': commission_fee
        })

    def buy(self, coin, price, quantity):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
        trade_datetime = datetime.now()
        if self.cash >= total_cost:
            self.cash -= total_cost
            if coin in self.portfolio:
                current_entry = self.portfolio[coin]
                current_total_cost = current_entry['quantity'] * current_entry['average_entry_price']
                new_total_cost = current_total_cost + cost
                new_quantity = current_entry['quantity'] + quantity
                new_average_entry_price = new_total_cost / new_quantity
                self.portfolio[coin]['quantity'] = new_quantity
                self.portfolio[coin]['average_entry_price'] = new_average_entry_price
            else:
                self.portfolio[coin] = {
                    'quantity': quantity,
                    'average_entry_price': price
                }
            self.last_purchase_info[coin] = {
                'price': price,
                'quantity': quantity,
                'commission': commission_fee,
                'datetime': trade_datetime
            }

            print(quantity)
            # round down quantity to 4 decimal places
            quantity = int(quantity * 1000000) / 1000000
            print(quantity)
            if self.is_live_mode:
                place_market_order(coin, quantity, 'BUY')
            self.log_trade('Buy', coin, price, quantity, trade_datetime)
            print(f"Bought {quantity:.4f} {coin} at {price}, including commission of {commission_fee:.2f}")
        else:
            print("Not enough cash to complete the purchase.")

    def sell(self, coin, price):
        quantity = self.portfolio.get(coin, {}).get('quantity', 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            profit = (price - purchase_price) * quantity - (purchase_info.get('commission', 0) + commission_fee)
            self.log_trade('Sell', coin, price, quantity, datetime.now(), profit)

            #round down quantity to 4 decimal places
            quantity = int(quantity * 1000000) / 1000000

            if self.is_live_mode:
                place_market_order(coin, quantity, 'SELL')
            print(f"Sold {quantity:.4f} {coin} at {price}, with commission of {commission_fee:.2f}")
            self.portfolio[coin]['quantity'] = 0
        else:
            print(f"No holdings to sell for {coin}.")

    def evaluate_trades(self, df_candles, coin):
        if len(df_candles) < 2:
            return
        latest = df_candles.iloc[0]
        previous = df_candles.iloc[-1]
        print(f"Latest: {latest['time']}, Close: {latest['close']}, Previous: {previous['time']}, Close: {previous['close']}")
        price_move = self.params['price_move']
        profit_target = self.params['profit_target']
        if self.portfolio.get(coin, {}).get('quantity', 0) == 0:
            p = self.calculate_probability(df_candles)
            q = 1 - p
            b = profit_target / price_move
            f_star = (b * p - q) / b
            f_star = max(0, f_star)
            available_cash = self.cash
            max_quantity = (available_cash * f_star) / latest['close']
            if max_quantity > 0:
                self.buy(coin, latest['close'], max_quantity)
                print(f"BUY: {coin}, Price: {latest['close']}, Quantity: {max_quantity}")
        else:
            last_purchase_price = self.portfolio[coin].get('average_entry_price', latest['close'])
            price_increase = (latest['close'] - last_purchase_price) / last_purchase_price
            print(f"Price increase: {price_increase:.5f}")
            if price_increase >= price_move:
                self.sell(coin, latest['close'])

    def calculate_probability(self, df_candles):
        prices = df_candles['close'].values
        drop_threshold = self.params['drop_threshold']
        increase_threshold = self.params['price_move']
        look_back = self.params['look_back']
        drop_count = 0
        increase_count = 0
        for i in range(1, len(prices)):
            price_drop = (prices[i] - prices[i - 1]) / prices[i - 1]
            if price_drop <= drop_threshold:
                drop_count += 1
                for j in range(i + 1, min(i + 1 + look_back, len(prices))):
                    price_increase = (prices[j] - prices[i]) / prices[i]
                    if price_increase >= increase_threshold:
                        increase_count += 1
                        break
        if drop_count == 0:
            return 0.0
        probability = increase_count / drop_count
        return probability
       
def main_trading_logic(coins, is_live_mode):
    portfolio_manager = PortfolioManager()
    
    # Define the asset of interest
    asset_names = ['BTC-USD']  # Only include SOL in asset names
    uuid_list = []  # Include specific UUIDs if needed, else keep empty
    
    # Initialize portfolio with SOL filter
    portfolio_uuid = portfolio_manager.list_portfolio()
    portfolio_data = portfolio_manager.get_portfolio_breakdown(portfolio_uuid)
    filtered_positions = portfolio_manager.filter_portfolio(portfolio_data, asset_names, uuid_list, name_filter_mode='include')
    
    # Initialize LiveTrader focusing on just SOL
    trader = LiveTrader(
        portfolio_manager=portfolio_manager,
        commission_rate=0.0075,
        params={
            'profit_target': 0.027,
            'price_move': 0.00005,
            'look_back': 100,
            'drop_threshold': -0.00005,
        },
        is_live_mode=is_live_mode
    )

    # Only get data for BTC-USD
    cumulative_data = {}
    for coin in coins:
        if coin in asset_names:  # Ensure we only process the desired asset
            df = get_bar_data(coin, 'ONE_MINUTE', 300).copy()
            if not df.empty:
                cumulative_data[coin] = df
                save_market_data_to_csv(df, coin)
            else:
                print(f"No initial data for {coin}")
                cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    while True:
        try:
            market_data = {}
            for coin in coins:
                if coin not in asset_names:
                    continue  # Skip any asset not in our filter, though ideally 'coins' should only contain BTC-USD

                df_new = get_bar_data(coin, 'ONE_MINUTE', limit=1)
                if not df_new.empty:
                    df_new = df_new.sort_values(by='time').reset_index(drop=True)
                    last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                    new_time = df_new['time'].iloc[0]

                    if last_time is None or new_time > last_time:
                        cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                        cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                        cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Appended new data for {coin}")
                    
                    elif new_time == last_time:
                        cumulative_data[coin].iloc[0] = df_new.iloc[0]
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Replaced last candle for {coin}")

                    market_data[coin] = cumulative_data[coin].copy()
                else:
                    print(f"No new data for {coin}. Latest time: {last_time}")
                    if coin in cumulative_data and not cumulative_data[coin].empty:
                        market_data[coin] = cumulative_data[coin].copy()
                        print(f"Using last known data for {coin}.")
                    else:
                        print(f"No historical data available for {coin}. Skipping.")
                        continue
                
                print(f"Current portfolio: {trader.portfolio}")

                
                trader.evaluate_trades(cumulative_data[coin], coin)

            trader.calculate_total_portfolio_value(market_data)
            print(f"Current cash: {trader.cash:.2f}")
            trader.save_trade_log_to_csv()
            time.sleep(10)

        except Exception as e:
            print("Exception in main trading logic:")
            print(e)
            time.sleep(10)

if __name__ == '__main__':
    # Define coins to trade and manage
    coins = ['BTC-USD']  # Only include BTC-USD
    main_trading_logic(coins, is_live_mode=False)  # Toggle 'is_live_mode' as needed

```



## New Structure

````
Absolutely, I understand that transitioning a monolithic script to a modular architecture can seem overwhelming, especially when you've already developed a specific strategy. Let's focus on integrating **your existing strategy** into the modular structure I previously outlined. We'll break this down step-by-step to ensure clarity and manageability.

## **1. Understanding Your Existing Strategy**

From your original code, your strategy involves:

1. **Probability Calculation**: Determining the likelihood (`probability`) that after a price drop (`drop_threshold`), the price will increase (`price_move`) within a `look_back` period.
2. **Position Sizing**: Calculating the optimal fraction (`f_star`) of available cash to invest based on the Kelly Criterion-like formula.
3. **Trade Execution**:
   - **Buy**: If not holding the coin and `f_star` > 0, buy a calculated quantity.
   - **Sell**: If holding the coin and the price has increased by `price_move`, sell the entire position.

## **2. Integrating Your Strategy into the Modular Structure**

We'll incorporate your strategy into the `strategies` module by creating a new strategy class that adheres to the `BaseStrategy` interface. Here's how to proceed:

### **a. Directory Structure Revision**

We'll adjust the `strategies` directory to include your strategy. The revised structure will look like this:

```
trading_bot/
├── config/
│   └── __init__.py
│   └── config.py
├── data/
│   └── __init__.py
│   └── data_fetcher.py
│   └── data_utils.py
├── strategies/
│   └── __init__.py
│   └── base_strategy.py
│   └── probabilistic_strategy.py  # Your strategy
├── trading/
│   └── __init__.py
│   └── trader.py
├── utils/
│   └── __init__.py
│   └── logger.py
├── main.py
├── requirements.txt
└── .env
```

### **b. Implementing Your Strategy**

**File:** `strategies/probabilistic_strategy.py`

We'll create a new strategy class based on your existing logic. This class will inherit from `BaseStrategy` and implement the `evaluate` method.

```python
# strategies/probabilistic_strategy.py

from strategies.base_strategy import BaseStrategy
import pandas as pd

class ProbabilisticStrategy(BaseStrategy):
    def __init__(self, price_move, profit_target, look_back, drop_threshold):
        """
        Initialize the probabilistic trading strategy.

        :param price_move: The threshold for price movement to trigger a sell.
        :param profit_target: The target profit to determine position sizing.
        :param look_back: The number of past intervals to look back for probability calculation.
        :param drop_threshold: The threshold for price drop to consider a buy opportunity.
        """
        self.price_move = price_move
        self.profit_target = profit_target
        self.look_back = look_back
        self.drop_threshold = drop_threshold

    def evaluate(self, df_candles: pd.DataFrame, portfolio: dict, cash: float) -> dict:
        """
        Evaluate the strategy and decide on trades.

        :param df_candles: DataFrame containing historical candle data.
        :param portfolio: Current portfolio holdings.
        :param cash: Available cash.
        :return: Dictionary with actions, e.g., {'buy': {'coin': 'BTC-USD', 'quantity': 0.1}, 'sell': {'coin': 'ETH'}}
        """
        if len(df_candles) < 2:
            return {}

        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]

        # Initialize actions dictionary
        actions = {}

        # If not holding the coin, evaluate buy opportunity
        coin = 'BTC-USD'  # Assuming strategy is for BTC-USD; modify as needed
        holding = portfolio.get(coin, {}).get('quantity', 0) > 0

        if not holding:
            probability = self.calculate_probability(df_candles)
            q = 1 - probability
            b = self.profit_target / self.price_move
            f_star = (b * probability - q) / b
            f_star = max(0, f_star)  # Ensure non-negative

            available_cash = cash
            max_quantity = (available_cash * f_star) / latest['close']

            if max_quantity > 0:
                actions['buy'] = {
                    'coin': coin,
                    'quantity': max_quantity,
                    'price': latest['close']
                }

        else:
            last_purchase_price = portfolio[coin].get('average_entry_price', latest['close'])
            price_increase = (latest['close'] - last_purchase_price) / last_purchase_price

            if price_increase >= self.price_move:
                actions['sell'] = {
                    'coin': coin,
                    'price': latest['close']
                }

        return actions

    def calculate_probability(self, df_candles: pd.DataFrame) -> float:
        """
        Calculate the probability that after a price drop, there's a sufficient price increase within the look_back period.

        :param df_candles: DataFrame containing historical candle data.
        :return: Probability value between 0 and 1.
        """
        prices = df_candles['close'].values
        drop_threshold = self.drop_threshold
        increase_threshold = self.price_move
        look_back = self.look_back

        drop_count = 0
        increase_count = 0

        for i in range(1, len(prices)):
            price_drop = (prices[i] - prices[i - 1]) / prices[i - 1]
            if price_drop <= drop_threshold:
                drop_count += 1
                # Look ahead within look_back period
                look_ahead_end = min(i + 1 + look_back, len(prices))
                for j in range(i + 1, look_ahead_end):
                    price_increase = (prices[j] - prices[i]) / prices[i]
                    if price_increase >= increase_threshold:
                        increase_count += 1
                        break

        if drop_count == 0:
            return 0.0

        probability = increase_count / drop_count
        return probability
```

### **c. Updating the Trader to Use the New Strategy**

**File:** `trading/trader.py`

Ensure that the `LiveTrader` class remains agnostic to the specific strategy being used. This was handled in the initial refactored code, but double-check to confirm.

_No changes are needed here if you've followed the initial refactored structure._

### **d. Configuring Strategy Parameters**

**File:** `config/config.py`

Add your strategy-specific parameters to the configuration file for centralized management.

```python
# config/config.py

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
    PRICE_MOVE = 0.00005          # Example: 0.005%
    LOOK_BACK = 100
    DROP_THRESHOLD = -0.00005      # Example: -0.005%
    
    # Other configurations
    MARKET_DATA_PREFIX = "market_data"
    TRADE_LOG_FILE = "trade_log.csv"
    DATA_FETCH_LIMIT = 300
```

> **Note:** Adjust the `PROFIT_TARGET`, `PRICE_MOVE`, `LOOK_BACK`, and `DROP_THRESHOLD` values as per your strategy's requirements.

### **e. Updating the Main Module to Use Your Strategy**

**File:** `main.py`

Modify `main.py` to instantiate and use `ProbabilisticStrategy` instead of `SMAStrategy`.

```python
# main.py

import time
import pandas as pd
from data.data_fetcher import DataFetcher
from data.data_utils import save_market_data_to_csv
from trading.trader import LiveTrader
from strategies.probabilistic_strategy import ProbabilisticStrategy
from coinbase_portfolio import PortfolioManager
from config.config import Config
from utils.logger import setup_logger

def main_trading_logic(coins, is_live_mode):
    logger = setup_logger()
    portfolio_manager = PortfolioManager()
    data_fetcher = DataFetcher()
    
    # Initialize your ProbabilisticStrategy with parameters from Config
    strategy = ProbabilisticStrategy(
        price_move=Config.PRICE_MOVE,
        profit_target=Config.PROFIT_TARGET,
        look_back=Config.LOOK_BACK,
        drop_threshold=Config.DROP_THRESHOLD
    )
    
    trader = LiveTrader(
        portfolio_manager=portfolio_manager,
        strategy=strategy,
        is_live_mode=is_live_mode
    )
    
    # Initialize cumulative data
    cumulative_data = {}
    for coin in coins:
        df = data_fetcher.get_bar_data(coin, 'ONE_MINUTE', Config.DATA_FETCH_LIMIT).copy()
        if not df.empty:
            cumulative_data[coin] = df
            save_market_data_to_csv(df, coin)
        else:
            logger.warning(f"No initial data for {coin}")
            cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    
    # Start the trading loop
    while True:
        try:
            market_data = {}
            for coin in coins:
                df_new = data_fetcher.get_bar_data(coin, 'ONE_MINUTE', limit=1)
                if not df_new.empty:
                    df_new = df_new.sort_values(by='time').reset_index(drop=True)
                    last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                    new_time = df_new['time'].iloc[0]
                    if last_time is None or new_time > last_time:
                        cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                        cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                        cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        logger.info(f"Appended new data for {coin}")
                    elif new_time == last_time:
                        cumulative_data[coin].iloc[-1] = df_new.iloc[0]
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        logger.info(f"Replaced last candle for {coin}")
                    market_data[coin] = cumulative_data[coin].copy()
                else:
                    logger.warning(f"No new data for {coin}.")
                    if not cumulative_data[coin].empty:
                        market_data[coin] = cumulative_data[coin].copy()
                        logger.info(f"Using last known data for {coin}.")
                    else:
                        logger.warning(f"No historical data available for {coin}. Skipping.")
            
            # Execute strategy for each coin
            for coin in coins:
                if not cumulative_data[coin].empty:
                    trader.execute_strategy(cumulative_data[coin])
            
            # Calculate portfolio value and log trades
            trader.calculate_total_portfolio_value(market_data)
            trader.save_trade_log_to_csv()
            
            # Sleep until next iteration (e.g., 60 seconds)
            time.sleep(60)
        
        except Exception as e:
            logger.error("Exception in main trading logic:")
            logger.error(e)
            time.sleep(60)

if __name__ == '__main__':
    # Define coins to trade and manage
    coins = ['BTC-USD']
    main_trading_logic(coins, is_live_mode=False)  # Toggle 'is_live_mode' as needed
```

### **f. Ensuring Compatibility in Trader Class**

Review the `LiveTrader` class to ensure it expects the `evaluate` method from any strategy passed to it. The initial refactored code should already accommodate this, but here’s a quick check:

**File:** `trading/trader.py`

```python
# trading/trader.py

from coinbase_portfolio import PortfolioManager
from coinbase_make_transactions import place_market_order
from config.config import Config
from datetime import datetime
import pandas as pd
from utils.logger import setup_logger

class LiveTrader:
    def __init__(self, portfolio_manager: PortfolioManager, strategy, is_live_mode: bool = True):
        self.logger = setup_logger()
        self.portfolio_manager = portfolio_manager
        self.strategy = strategy
        self.is_live_mode = is_live_mode
        self.cash = max(10, self.portfolio_manager.extract_total_cash_balance(self._fetch_portfolio_data())) if self.is_live_mode else 10
        self.portfolio = {}  # {'coin': {'quantity': x, 'average_entry_price': y}}
        self.commission_rate = Config.COMMISSION_RATE
        self.trade_log = []
        self.last_purchase_info = {}
        self.update_portfolio()

    def _fetch_portfolio_data(self):
        portfolio_uuid = self.portfolio_manager.list_portfolio()
        return self.portfolio_manager.get_portfolio_breakdown(portfolio_uuid)

    def update_portfolio(self):
        portfolio_data = self._fetch_portfolio_data()
        # Filter for specific assets, e.g., BTC-USD
        asset_names = ['BTC-USD']
        filtered_positions = self.portfolio_manager.filter_portfolio(portfolio_data, asset_names, [], name_filter_mode='include')
        for position in filtered_positions:
            asset = position['asset']
            price_info = position.get('average_entry_price', {'value': '0', 'currency': 'USD'})
            average_entry_price = float(price_info['value'])
            self.portfolio[f"{asset}-USD"] = {
                'quantity': position['total_balance_crypto'],
                'average_entry_price': average_entry_price
            }
        if self.is_live_mode:
            self.cash = min(self.portfolio_manager.extract_total_cash_balance(portfolio_data), 10)
        self.logger.info(f"Portfolio updated: {self.portfolio}")
        self.logger.info(f"Last purchase info updated: {self.last_purchase_info}")

    def calculate_total_portfolio_value(self, market_data: dict) -> float:
        if self.is_live_mode:
            self.update_portfolio()
        total_value = self.cash
        for coin, data in self.portfolio.items():
            quantity = data.get('quantity', 0)
            if quantity > 0 and coin in market_data and not market_data[coin].empty:
                price = market_data[coin]['close'].iloc[-1]
                total_value += quantity * price
        self.logger.info(f"Total portfolio value: {total_value:.2f}")
        return total_value

    def save_trade_log_to_csv(self, file_name: str = Config.TRADE_LOG_FILE):
        try:
            df_trade_log = pd.DataFrame(self.trade_log)
            df_trade_log.to_csv(file_name, index=False)
            self.logger.info(f"Trade log saved to {file_name}")
        except Exception as e:
            self.logger.error(f"Error saving trade log to CSV: {e}")

    def commission(self, amount: float) -> float:
        return amount * self.commission_rate

    def log_trade(self, action: str, coin: str, price: float, quantity: float, trade_datetime: datetime, profit: float = 0):
        commission_fee = self.commission(price * quantity)
        self.trade_log.append({
            'Datetime': trade_datetime,
            'Action': action,
            'Coin': coin,
            'Price': price,
            'Quantity': quantity,
            'Cash': self.cash,
            'Portfolio': self.portfolio.copy(),
            'Profit': profit,
            'Commission': commission_fee
        })
        self.logger.info(f"{action} {quantity:.6f} {coin} at {price:.2f}, Commission: {commission_fee:.2f}")

    def buy(self, coin: str, price: float, quantity: float):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
        trade_datetime = datetime.now()
        if self.cash >= total_cost:
            self.cash -= total_cost
            if coin in self.portfolio:
                current_entry = self.portfolio[coin]
                current_total_cost = current_entry['quantity'] * current_entry['average_entry_price']
                new_total_cost = current_total_cost + cost
                new_quantity = current_entry['quantity'] + quantity
                new_average_entry_price = new_total_cost / new_quantity
                self.portfolio[coin]['quantity'] = new_quantity
                self.portfolio[coin]['average_entry_price'] = new_average_entry_price
            else:
                self.portfolio[coin] = {
                    'quantity': quantity,
                    'average_entry_price': price
                }
            self.last_purchase_info[coin] = {
                'price': price,
                'quantity': quantity,
                'commission': commission_fee,
                'datetime': trade_datetime
            }
            # Round down quantity to 6 decimal places
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.is_live_mode:
                place_market_order(coin, rounded_quantity, 'BUY')
            self.log_trade('Buy', coin, price, rounded_quantity, trade_datetime)
        else:
            self.logger.warning("Not enough cash to complete the purchase.")

    def sell(self, coin: str, price: float):
        quantity = self.portfolio.get(coin, {}).get('quantity', 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            profit = (price - purchase_price) * quantity - (purchase_info.get('commission', 0) + commission_fee)
            # Round down quantity to 6 decimal places
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.is_live_mode:
                place_market_order(coin, rounded_quantity, 'SELL')
            self.log_trade('Sell', coin, price, rounded_quantity, datetime.now(), profit)
            self.portfolio[coin]['quantity'] = 0
        else:
            self.logger.warning(f"No holdings to sell for {coin}.")

    def execute_strategy(self, df_candles: pd.DataFrame):
        actions = self.strategy.evaluate(df_candles, self.portfolio, self.cash)
        if 'buy' in actions:
            buy_action = actions['buy']
            self.buy(buy_action['coin'], buy_action['price'], buy_action['quantity'])
        if 'sell' in actions:
            sell_action = actions['sell']
            self.sell(sell_action['coin'], sell_action['price'])
```

### **f. Finalizing and Running the Refactored Bot**

1. **Ensure All Dependencies Are Met**

   Update your `requirements.txt` to include any new dependencies. For example, ensure `python-dotenv` is present if you're using environment variables.

   ```plaintext
   pandas
   python-dotenv
   coinbase
   ```
   
   *(Add other dependencies as needed.)*

2. **Set Up Environment Variables**

   Make sure your `.env` file contains the necessary API keys:

   ```dotenv
   COINBASE_API_KEY=your_api_key
   COINBASE_API_SECRET=your_api_secret
   ```

3. **Run the Bot**

   Navigate to your project directory and execute:

   ```bash
   python main.py
   ```

   Ensure that logging outputs are functioning correctly and that trades are being logged as expected.

## **3. Incremental Refactoring Tips**

To make this transition smoother, consider the following incremental steps:

1. **Start Small**: Instead of refactoring the entire codebase at once, begin by separating out one component (e.g., data fetching) into its own module. Test to ensure it works correctly.

2. **Implement and Test Your Strategy**: Before integrating into the broader system, ensure that your `ProbabilisticStrategy` class operates as intended with sample data.

3. **Use Version Control**: Keep track of changes using Git. This allows you to revert if something breaks during refactoring.

4. **Maintain Backward Compatibility**: Gradually replace parts of your original code with the new modular components, ensuring that each replacement doesn't disrupt existing functionality.

5. **Implement Unit Tests**: As you modularize, write unit tests for each module to ensure they work independently. This is crucial for long-term maintenance and scalability.

## **4. Additional Enhancements**

While integrating your strategy, you might also consider the following enhancements to further improve your bot:

### **a. Enhanced Logging**

Expand your logging to include more detailed information, such as:

- **Trade Outcomes**: Record whether trades were profitable.
- **Error Details**: Capture stack traces for exceptions.
- **Performance Metrics**: Track metrics like win rate, average profit per trade, etc.

### **b. Configuration Validation**

Implement validation for configuration parameters to ensure they are within reasonable ranges, reducing the risk of executing unintended trades.

### **c. Strategy Parameters Externalization**

Allow strategy parameters to be specified externally (e.g., via a configuration file or command-line arguments) to easily tweak without modifying code.

### **d. Multiple Strategy Support**

Design the system to support running multiple strategies simultaneously, possibly managing different portfolios or risk profiles.

## **5. Conclusion**

Transitioning to a modular architecture enhances the scalability, maintainability, and flexibility of your trading bot. By encapsulating your existing strategy within this structure, you set a strong foundation for future expansions, such as integrating new strategies, adding more assets, or incorporating additional data sources.
ß
Remember, the key to successful refactoring is to proceed incrementally, ensuring each new module functions correctly before moving on to the next. This approach minimizes disruptions and allows you to test and validate each component thoroughly.

Feel free to ask for further clarifications or assistance with specific parts of this refactoring process!
````

## Adding Backtesting mode

- Change main to include a new live_mode option. instead of a bool it's enum: live_mode, paper_mode, **backtest_mode**

- change to use different fetch data. data_historic

  - Point to SQL:

    ```sql
    # this will be used in data_historical.py
    def fetch_data_from_db(product_id):
        connection_params = {
            'dbname': "postgres",
            'user': "postgres",
            'password': "asheville",
            'host': "localhost",
            'port': "5433"
        }
    
        query = f"""
        SELECT * FROM trading_data 
        WHERE product_id = '{product_id}'
        ORDER BY start ASC;
        """
    
        try:
            connection = psycopg2.connect(**connection_params)
            dataframe = pd.read_sql_query(query, connection)
            #print head
            print(dataframe.head())
            print(f"Data fetched successfully for {product_id}.")
        except Exception as e:
            print(f"Failed to fetch data from database for {product_id}: {e}")
            dataframe = pd.DataFrame()
        finally:
            connection.close()
    
        return dataframe
    ```

- reuse the strategy and trader classes

  ```python
  #strategy example
  
  from strategies.base_strategy import BaseStrategy
  import pandas as pd
  
  class ProbabilisticStrategy(BaseStrategy):
      def __init__(self, price_move, profit_target, look_back, drop_threshold):
          """
          Initialize the probabilistic trading strategy.
  
          :param price_move: The threshold for price movement to trigger a sell.
          :param profit_target: The target profit to determine position sizing.
          :param look_back: The number of past intervals to look back for probability calculation.
          :param drop_threshold: The threshold for price drop to consider a buy opportunity.
          """
          self.price_move = price_move
          self.profit_target = profit_target
          self.look_back = look_back
          self.drop_threshold = drop_threshold
  
      def evaluate(self, coin: str, df_candles: pd.DataFrame, portfolio: dict, cash: float) -> dict:
          """
          Evaluate the strategy for a specific coin and decide on trades.
  
          :param coin: The trading pair, e.g., 'BTC-USD'.
          :param df_candles: DataFrame containing historical candle data for the coin.
          :param portfolio: Current portfolio holdings.
          :param cash: Available cash.
          :return: Dictionary with actions, e.g., {'buy': {'coin': 'BTC', 'quantity': 0.1}, 'sell': {'coin': 'ETH'}}
          """
          if len(df_candles) < 2:
              return {}
  
          latest = df_candles.iloc[0]
          previous = df_candles.iloc[-1]
          total_value = 0.0
  
          # Initialize actions dictionary
          actions = {}
  
          holding = portfolio.get(coin, {}).get('quantity', 0) > 0    
  
          if holding:
              total_value = portfolio[coin]['quantity'] * latest['close']    
  
          if total_value <= 1.00:
              probability = self.calculate_probability(df_candles)
              q = 1 - probability
              b = self.profit_target / self.price_move
              f_star = (b * probability - q) / b
              f_star = max(0, f_star)  # Ensure non-negative
  
              available_cash = cash
              max_quantity = (available_cash * f_star) / latest['close']
  
              if max_quantity > 0:
                  actions['buy'] = {
                      'coin': coin,
                      'quantity': max_quantity,
                      'price': latest['close']
                  }
  
          else:
              last_purchase_price = portfolio[coin].get('average_entry_price', latest['close'])
              price_increase = (latest['close'] - last_purchase_price) / last_purchase_price
  
              if price_increase >= self.price_move and total_value >= 1.00:
                  actions['sell'] = {
                      'coin': coin,
                      'price': latest['close']
                  }
  
          return actions
  
      def calculate_probability(self, df_candles: pd.DataFrame) -> float:
          """
          Calculate the probability that after a price drop, there's a sufficient price increase within the look_back period.
  
          :param df_candles: DataFrame containing historical candle data.
          :return: Probability value between 0 and 1.
          """
          prices = df_candles['close'].values
          drop_threshold = self.drop_threshold
          increase_threshold = self.price_move
          look_back = self.look_back
  
          drop_count = 0
          increase_count = 0
  
          for i in range(1, len(prices)):
              price_drop = (prices[i] - prices[i - 1]) / prices[i - 1]
              if price_drop <= drop_threshold:
                  drop_count += 1
                  # Look ahead within look_back period
                  look_ahead_end = min(i + 1 + look_back, len(prices))
                  for j in range(i + 1, look_ahead_end):
                      price_increase = (prices[j] - prices[i]) / prices[i]
                      if price_increase >= increase_threshold:
                          increase_count += 1
                          break
  
          if drop_count == 0:
              return 0.0
  
          probability = increase_count / drop_count
          return probability
  ```

  ```python
  ## strategy base class
  from abc import ABC, abstractmethod
  import pandas as pd
  
  class BaseStrategy(ABC):
      @abstractmethod
      def evaluate(self, coin: str, df_candles: pd.DataFrame, portfolio: dict, cash: float) -> dict:
          """
          Evaluate the strategy for a specific coin and decide on trades.
  
          :param coin: The trading pair, e.g., 'BTC-USD'.
          :param df_candles: DataFrame containing historical candle data for the coin.
          :param portfolio: Current portfolio holdings.
          :param cash: Available cash.
          :return: Dictionary with actions, e.g., {'buy': {'coin': 'BTC', 'quantity': 0.1}, 'sell': {'coin': 'ETH'}}
          """
          pass
  ```

  

  ```python
  #trader.py
  from external.coinbase_portfolio import PortfolioManager
  from external.coinbase_make_transactions import place_market_order
  from config.config import Config
  from datetime import datetime
  import pandas as pd
  from utils.logger import setup_logger
  
  class LiveTrader:
      def __init__(self, portfolio_manager: PortfolioManager, strategy, is_live_mode: bool = True):
          self.logger = setup_logger()
          self.portfolio_manager = portfolio_manager
          self.strategy = strategy
          self.is_live_mode = is_live_mode
          if self.is_live_mode:
              total_cash_balance = self.portfolio_manager.extract_total_cash_balance(self._fetch_portfolio_data())
              self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
          else:
              self.cash = Config.NON_LIVE_START_CASH        
          self.portfolio = {}  # {'coin': {'quantity': x, 'average_entry_price': y}}
          self.commission_rate = Config.COMMISSION_RATE
          self.trade_log = []
          self.last_purchase_info = {}
          self.update_portfolio()
  
      def _fetch_portfolio_data(self):
          portfolio_uuid = self.portfolio_manager.list_portfolio()
          return self.portfolio_manager.get_portfolio_breakdown(portfolio_uuid)
  
      def update_portfolio(self):
          portfolio_data = self._fetch_portfolio_data()
          # Log the portfolio data for debugging
          self.logger.debug(f"Fetched portfolio data: {portfolio_data}")
          print(portfolio_data)
          
          # Extract the positions list
          if not isinstance(portfolio_data, dict):
              self.logger.error("portfolio_data is not a dictionary.")
              return
  
          positions = portfolio_data.get('breakdown', {}).get('spot_positions', [])
          
          # Validate positions
          if not isinstance(positions, list):
              self.logger.error("Positions data is not a list.")
              return
          if not all(isinstance(position, dict) for position in positions):
              self.logger.error("Not all items in positions are dictionaries.")
              return
  
          self.portfolio = {}
          for position in positions:
              asset = position.get('asset')
              if not asset:
                  self.logger.warning(f"Position without asset: {position}")
                  continue
              coin = f"{asset}-USD"
              price_info = position.get('average_entry_price', {'value': '0', 'currency': 'USD'})
              try:
                  average_entry_price = float(price_info.get('value', 0))
              except ValueError:
                  self.logger.error(f"Invalid average_entry_price: {price_info.get('value')}")
                  average_entry_price = 0.0
              quantity = position.get('total_balance_crypto', 0)
              try:
                  quantity = float(quantity)
              except ValueError:
                  self.logger.error(f"Invalid quantity for {coin}: {quantity}")
                  quantity = 0.0
              self.portfolio[coin] = {
                  'quantity': quantity,
                  'average_entry_price': average_entry_price
              }
          if self.is_live_mode:
              # Extract the total cash balance using the configured percentage
              total_cash_balance = self.portfolio_manager.extract_total_cash_balance(portfolio_data)
              self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
          else:
              self.cash = Config.NON_LIVE_START_CASH  # Ensure consistency when not in live mode
              
          self.logger.info(f"Portfolio updated: {self.portfolio}")
          self.logger.info(f"Last purchase info updated: {self.last_purchase_info}")
  
      def calculate_total_portfolio_value(self, market_data: dict) -> float:
          if self.is_live_mode:
              self.update_portfolio()
          total_value = self.cash
          for coin, data in self.portfolio.items():
              quantity = data.get('quantity', 0)
              if quantity > 0 and coin in market_data and not market_data[coin].empty:
                  price = market_data[coin]['close'].iloc[-1]
                  total_value += quantity * price
          self.logger.info(f"Total portfolio value: {total_value:.2f}")
          return total_value
  
      def save_trade_log_to_csv(self, file_name: str = Config.TRADE_LOG_FILE):
          try:
              df_trade_log = pd.DataFrame(self.trade_log)
              df_trade_log.to_csv(file_name, index=False)
              self.logger.info(f"Trade log saved to {file_name}")
          except Exception as e:
              self.logger.error(f"Error saving trade log to CSV: {e}")
  
      def commission(self, amount: float) -> float:
          return amount * self.commission_rate
  
      def log_trade(self, action: str, coin: str, price: float, quantity: float, trade_datetime: datetime, profit: float = 0):
          commission_fee = self.commission(price * quantity)
          self.trade_log.append({
              'Datetime': trade_datetime,
              'Action': action,
              'Coin': coin,
              'Price': price,
              'Quantity': quantity,
              'Cash': self.cash,
              'Portfolio': self.portfolio.copy(),
              'Profit': profit,
              'Commission': commission_fee
          })
          self.logger.info(f"{action} {quantity:.6f} {coin} at {price:.2f}, Commission: {commission_fee:.2f}")
  
      def buy(self, coin: str, price: float, quantity: float):
          cost = price * quantity
          commission_fee = self.commission(cost)
          total_cost = cost + commission_fee
          trade_datetime = datetime.now()
          if self.cash >= total_cost:
              self.cash -= total_cost
              if coin in self.portfolio:
                  current_entry = self.portfolio[coin]
                  current_total_cost = current_entry['quantity'] * current_entry['average_entry_price']
                  new_total_cost = current_total_cost + cost
                  new_quantity = current_entry['quantity'] + quantity
                  new_average_entry_price = new_total_cost / new_quantity
                  self.portfolio[coin]['quantity'] = new_quantity
                  self.portfolio[coin]['average_entry_price'] = new_average_entry_price
              else:
                  self.portfolio[coin] = {
                      'quantity': quantity,
                      'average_entry_price': price
                  }
              self.last_purchase_info[coin] = {
                  'price': price,
                  'quantity': quantity,
                  'commission': commission_fee,
                  'datetime': trade_datetime
              }
              # Round down quantity to 6 decimal places
              rounded_quantity = int(quantity * 1_000_000) / 1_000_000
              if self.is_live_mode:
                  place_market_order(coin, rounded_quantity, 'BUY')
              self.log_trade('Buy', coin, price, rounded_quantity, trade_datetime)
          else:
              self.logger.warning(f"Not enough cash to complete the purchase for {coin}.")
  
      def sell(self, coin: str, price: float):
          quantity = self.portfolio.get(coin, {}).get('quantity', 0)
          if quantity > 0:
              revenue = price * quantity
              commission_fee = self.commission(revenue)
              total_revenue = revenue - commission_fee
              self.cash += total_revenue
              purchase_info = self.last_purchase_info.get(coin, {})
              purchase_price = purchase_info.get('price', 0)
              profit = (price - purchase_price) * quantity - (purchase_info.get('commission', 0) + commission_fee)
              # Round down quantity to 6 decimal places
              rounded_quantity = int(quantity * 1_000_000) / 1_000_000
              if self.is_live_mode:
                  place_market_order(coin, rounded_quantity, 'SELL')
              self.log_trade('Sell', coin, price, rounded_quantity, datetime.now(), profit)
              self.portfolio[coin]['quantity'] = 0
          else:
              self.logger.warning(f"No holdings to sell for {coin}.")
  
      def execute_strategy(self, coin: str, df_candles: pd.DataFrame):
          """
          Execute the strategy for a specific coin.
  
          :param coin: The trading pair, e.g., 'BTC-USD'.
          :param df_candles: DataFrame containing historical candle data for the coin.
          """
          actions = self.strategy.evaluate(coin, df_candles, self.portfolio, self.cash)
          if 'buy' in actions:
              buy_action = actions['buy']
              self.buy(buy_action['coin'], buy_action['price'], buy_action['quantity'])
          if 'sell' in actions:
              sell_action = actions['sell']
              self.sell(sell_action['coin'], sell_action['price'])
  ```

- backtest mode allows a simulation of buying and selling based on historic data. with the same logging and trade journalling outputs

  ```python
  # main.py
  import time
  import pandas as pd
  from data.data_fetcher import DataFetcher
  from data.data_utils import save_market_data_to_csv
  from trading.trader import LiveTrader
  from strategies.probabilistic_strategy import ProbabilisticStrategy
  from config.config import Config
  from utils.logger import setup_logger
  from external.coinbase_portfolio import PortfolioManager  # Ensure correct import
  
  def main_trading_logic(coins, is_live_mode):
      logger = setup_logger()
      portfolio_manager = PortfolioManager()
      data_fetcher = DataFetcher()
  
      # Initialize your ProbabilisticStrategy with parameters from Config
      strategy = ProbabilisticStrategy(
          price_move=Config.PRICE_MOVE,
          profit_target=Config.PROFIT_TARGET,
          look_back=Config.LOOK_BACK,
          drop_threshold=Config.DROP_THRESHOLD
      )
  
      trader = LiveTrader(
          portfolio_manager=portfolio_manager,
          strategy=strategy,
          is_live_mode=is_live_mode
      )
  
      # Initialize cumulative data for all coins
      cumulative_data = {}
      for coin in coins:
          df = data_fetcher.get_bar_data(coin, 'FIVE_MINUTE', Config.DATA_FETCH_LIMIT).copy()
          if not df.empty:
              cumulative_data[coin] = df
              save_market_data_to_csv(df, coin)
          else:
              logger.warning(f"No initial data for {coin}")
              cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])
  
      # Start the trading loop
      while True:
          try:
              market_data = {}
              for coin in coins:
                  df_new = data_fetcher.get_bar_data(coin, 'FIVE_MINUTE', limit=1)
                  if not df_new.empty:
                      df_new = df_new.sort_values(by='time').reset_index(drop=True)
                      last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                      new_time = df_new['time'].iloc[0]
                      if last_time is None or new_time > last_time:
                          cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                          cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                          cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                          save_market_data_to_csv(cumulative_data[coin], coin)
                          logger.info(f"Appended new data for {coin}")
                      elif new_time == last_time:
                          cumulative_data[coin].iloc[-1] = df_new.iloc[0]
                          save_market_data_to_csv(cumulative_data[coin], coin)
                          logger.info(f"Replaced last candle for {coin}")
                      market_data[coin] = cumulative_data[coin].copy()
                  else:
                      logger.warning(f"No new data for {coin}.")
                      if not cumulative_data[coin].empty:
                          market_data[coin] = cumulative_data[coin].copy()
                          logger.info(f"Using last known data for {coin}.")
                      else:
                          logger.warning(f"No historical data available for {coin}. Skipping.")
              
              # Execute strategy for each coin
              for coin in coins:
                  if not cumulative_data[coin].empty:
                      trader.execute_strategy(coin, cumulative_data[coin])
              
              # Calculate portfolio value and log trades
              trader.calculate_total_portfolio_value(market_data)
              trader.save_trade_log_to_csv()
              
              #if live_move print LIVE!!!!
              if is_live_mode:
                  logger.info("LIVE!!!")
  
              # Sleep until next iteration (e.g., 60 seconds)
              time.sleep(60)
          
          except KeyError as e:
              logger.error(f"KeyError: The key {e} was not found in a dictionary.")
              logger.exception("Traceback:")
              time.sleep(60)
          except Exception as e:
              logger.exception("Exception occurred in main trading logic")
              time.sleep(60)
  
  if __name__ == '__main__':
      # Define coins to trade and manage
      coins = ['DIA-USD', 'MATH-USD', 'ORN-USD','WELL-USD','KARRAT-USD']  # Example list; adjust as needed
      main_trading_logic(coins, is_live_mode=True)  # Toggle 'is_live_mode' as needed
  ```

  

---

## Abstracting Strategies to be written by OpenAI API

1) A user wants to create a detailed strategy they can immediately testout just by listing out the logic and describing things in plane english. Maybe they are a savvy trader without coding experience, or someone who is looking to speed up their strategy exploration process - this would be awesome, if it worked.

2) The AI processes the users logic and converts it to python, using the abstract base_strategy class as a template. This python is passed back to the local users machine or stored on a database.

3) The user can choose to run the code in:

   - back-test mode (coinbase account referrals)

   - paper mode (coinbase account referrals)

   - live mode (paid account)

   *Create a CLI version of this by Dec 31st*

   

## Alterantively the user builds the logic through a simple interface

1) probabilities based on passed events appear to help you find a strategy faster

2) select bar range (up to 300)

3) select bar history range (back X months)

4) select a strategy criteria

   - event based

   - Candle stick pattern based

   - technical indicator based

   - fundamentals based

5) arrange criteria nodes in a visual scripting based manner with basic operators
   - "*Blueprints*" for finance
   - create nodes
   - click and drag
   - basic logical and arithmetic operators
   - when saved --> converts to python function in background

## How to pass a function to function

So in this scenario, we've got a sweet tool where the user has messed around and create some stupid strategy they want to try. We want to pass this whole "My Strategy" function into our trader, to be able to run it. But it's like more python code, that was custom generated from the Open AI API or the UI tooling. So how can we pass a function to a function within our current framework.

### How trader.py needs to change:

### How main.py needs to change:

### How new my_strategy_file.py gets created:

![43A774C8-272A-4F12-983F-BD839A073688_1_201_a](/Users/claytondavis/Pictures/Photos Library.photoslibrary/resources/renders/4/43A774C8-272A-4F12-983F-BD839A073688_1_201_a.jpeg)

*See uploaded project structure screenshot.*

