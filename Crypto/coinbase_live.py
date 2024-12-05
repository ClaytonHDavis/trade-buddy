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
