import os
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from coinbase.rest import RESTClient  # Import RESTClient from coinbase.rest

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
api_key = os.getenv("COINBASE_API_KEY").strip()
api_secret = os.getenv("COINBASE_API_SECRET").strip()

# Create the REST client
client = RESTClient(api_key=api_key, api_secret=api_secret)

def fetch_historical_data(product_id, granularity='ONE_MINUTE', limit=300):
    try:
        # Calculate start and end times
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

        # Create the request URL and parameters
        url = f"/api/v3/brokerage/products/{product_id}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": granularity,
            "limit": limit
        }

        # Fetch candle data using RESTClient
        response = client.get(url, params=params)

        # Extract candles
        candles = response.get('candles', [])
        if not candles:
            print(f"No candle data returned for {product_id}")
            return pd.DataFrame()

        # Prepare DataFrame
        df_candles = pd.DataFrame(candles)

        # Convert 'start' to datetime
        df_candles['start'] = pd.to_datetime(df_candles['start'], unit='s')

        # Rename 'start' to 'time' to match previous code
        df_candles.rename(columns={'start': 'time'}, inplace=True)

        # Ensure correct data types
        float_columns = ['low', 'high', 'open', 'close', 'volume']
        df_candles[float_columns] = df_candles[float_columns].astype(float)

        # Reorder columns if necessary
        df_candles = df_candles[['time', 'low', 'high', 'open', 'close', 'volume']]

        # Sort the DataFrame by time
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

class PaperTrader:
    def __init__(self, initial_cash=10000, commission_rate=0.006, params=None):
        self.cash = initial_cash
        self.portfolio = {}
        self.commission_rate = commission_rate
        self.trade_log = []
        self.last_purchase_info = {}  # Use this to store purchase details
        self.params = params or {}
        self.params.setdefault('profit_target', 0.027)  # used to motivate our probability calculation
        self.params.setdefault('stop_loss', 0.010)  # NOT USED
        self.params.setdefault('price_move', 0.01)  # used to determine when to sell, after small raise
        self.params.setdefault('look_back', 10)  # used to determine how far back to look
        self.params.setdefault('drop_threshold', -0.005)  # used to determine when to buy
        self.params.setdefault('increase_threshold', 0.006)  # used to determine when to sell early

    def calculate_total_portfolio_value(self, market_data):
        total_value = self.cash  # Start with current cash balance
        for coin, quantity in self.portfolio.items():
            if quantity > 0:
                # Get the current market price for this coin
                if coin in market_data and not market_data[coin].empty:
                    price = market_data[coin]['close'].iloc[-1]
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

    def buy(self, coin, price, quantity):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
        trade_datetime = datetime.now()  # Capture current datetime
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.portfolio[coin] = self.portfolio.get(coin, 0) + quantity
            # Store purchase info including commission and datetime
            self.last_purchase_info[coin] = {
                'price': price,
                'quantity': quantity,
                'commission': commission_fee,
                'datetime': trade_datetime
            }
            # Log the trade with datetime
            self.log_trade('Buy', coin, price, quantity, trade_datetime)
            print(f"Bought {quantity:.4f} {coin} at {price}, including commission of {commission_fee:.2f}")
        else:
            print("Not enough cash to complete the purchase.")

    def sell(self, coin, price):
        quantity = self.portfolio.get(coin, 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            self.portfolio[coin] -= quantity
            trade_datetime = datetime.now()  # Capture current datetime
            # Get purchase info
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            purchase_commission = purchase_info.get('commission', 0)
            # Calculate profit: (Sell Price - Purchase Price) * Quantity - Total Commissions
            profit = (price - purchase_price) * quantity - (purchase_commission + commission_fee)
            # Log the trade with profit and datetime
            self.log_trade('Sell', coin, price, quantity, trade_datetime, profit)
            print(f"Sold {quantity:.4f} {coin} at {price}, with commission of {commission_fee:.2f}")
            # Remove last purchase info after selling
            self.last_purchase_info.pop(coin, None)
        else:
            print(f"No holdings to sell for {coin}.")

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

    def evaluate_trades(self, df_candles, coin):
        # Ensure we have enough data to compute indicators
        if len(df_candles) < 2:
            return
        # Get the latest data
        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]
        print(f"Latest: {latest['time']}, Close: {latest['close']}, Previous: {previous['time']}, Close: {previous['close']}")
        # Calculate price change
        price_change = (latest['close'] - previous['close']) / previous['close']
        drop_threshold = self.params.get('drop_threshold', -0.005)
        increase_threshold = self.params.get('increase_threshold', 0.006)
        price_move = self.params.get('price_move', 0.001)
        # Buy condition: significant price drop and not currently holding the coin
        if self.portfolio.get(coin, 0) == 0:
            # Calculate probability
            p = self.calculate_probability(df_candles)
            q = 1 - p
            b = self.params.get('profit_target', 0.02) / price_move
            f_star = (b * p - q) / b
            f_star = max(0, f_star)
            available_cash = self.cash
            max_quantity = (available_cash * f_star) / latest['close']
            if max_quantity > 0:
                self.buy(coin, latest['close'], max_quantity)
                print(f"BUY: {coin}, Price: {latest['close']}, Quantity: {max_quantity}")
        # Sell condition: price increase since purchase
        elif self.portfolio.get(coin, 0) > 0:
            if coin in self.last_purchase_info:
                purchase_info = self.last_purchase_info[coin]
                last_purchase_price = purchase_info.get('price', latest['close'])
            else:
                last_purchase_price = latest['close']
            price_increase = (latest['close'] - last_purchase_price) / last_purchase_price
            print(f"Price increase: {price_increase:.5f}")

            #print lastest close and original purchase price
            print(f"Latest close: {latest['close']}, Last purchase price: {last_purchase_price}")

            if price_increase >= price_move:
                self.sell(coin, latest['close'])

    def calculate_probability(self, df_candles):
        prices = df_candles['close'].values
        drop_threshold = self.params.get('drop_threshold', -0.005)
        increase_threshold = self.params.get('increase_threshold', 0.006)
        look_back = self.params.get('look_back', 10)
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

def main_trading_logic(coins):
    trader = PaperTrader(
        initial_cash=100000,
        params={
            'profit_target': 0.027,
            'stop_loss': 0.010,
            'price_move': 0.001,
            'look_back': 10,
            'drop_threshold': -0.005,
            'increase_threshold': 0.006,
        }
    )
    cumulative_data = {}
    # Initialize cumulative_data for each coin
    for coin in coins:
        df = get_bar_data(coin, 'ONE_MINUTE', 300)
        if not df.empty:
            df = df.sort_values(by='time').reset_index(drop=True)
            cumulative_data[coin] = df.copy()
            # Save initial market data to CSV
            save_market_data_to_csv(df, coin)
        else:
            print(f"No initial data for {coin}")
            cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    while True:
        try:
            market_data = {}
            for coin in coins:
                df_new = get_bar_data(coin, 'ONE_MINUTE', limit=1)
                if not df_new.empty:
                    df_new = df_new.sort_values(by='time').reset_index(drop=True)
                    last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                    new_time = df_new['time'].iloc[-1]
                    if last_time is None or new_time > last_time:
                        # Append the new data
                        cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                        cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                        cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                        # Save market data to CSV
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Appended new data for {coin}")
                    elif new_time == last_time:
                        # Replace the last candle
                        cumulative_data[coin].iloc[-1] = df_new.iloc[-1]
                        # Save market data to CSV
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        print(f"Replaced last candle for {coin}")
                    else:
                        print(f"No new data for {coin}. Latest time: {last_time}")
                    # Update market_data with the latest cumulative data
                    market_data[coin] = cumulative_data[coin].copy()
                    # Proceed to evaluate trades
                    trader.evaluate_trades(cumulative_data[coin], coin)
                else:
                    print(f"No data fetched for {coin}")
                    # Do not modify cumulative_data[coin]; use last known data
                    if coin in cumulative_data and not cumulative_data[coin].empty:
                        market_data[coin] = cumulative_data[coin].copy()
                        # Proceed to evaluate trades with existing data
                        
                        #print current portfolio
                        print(f"Current portfolio: {trader.portfolio}")

                        trader.evaluate_trades(cumulative_data[coin], coin)
                    else:
                        print(f"No historical data available for {coin}. Skipping.")
                        continue
            # Save trade logs
            trader.calculate_total_portfolio_value(market_data)
            trader.save_trade_log_to_csv()
            time.sleep(10)
        except Exception as e:
            print("Exception in main trading logic:")
            print(e)
            time.sleep(10)

if __name__ == '__main__':
    # Define the coins to trade
    coins = ['DIA-USD', 'KARRAT-USD', 'ASM-USD', 'MATH-USD']
    main_trading_logic(coins)