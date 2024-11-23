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

class PaperTrader:
    def __init__(self, initial_cash=10000, commission_rate=0.006, price_change_threshold=0.001):
        self.cash = initial_cash
        self.portfolio = {}
        self.commission_rate = commission_rate
        self.trade_log = []
        self.last_purchase_price = {}
        self.price_change_threshold = price_change_threshold
        self.chart_map = {}  # Maps each coin to its chart

    def calculate_total_portfolio_value(self, market_data):
        total_value = self.cash  # Start with current cash balance
        for coin, quantity in self.portfolio.items():
            if quantity > 0:
                # Get the current market price for this coin
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

    def save_fundamental_data_to_csv(self, df_candles, coin, file_name="fundamental_data.csv"):
        try:
            df_candles['coin'] = coin  # Add a column for the coin symbol
            df_candles.to_csv(file_name, mode='a', header=not os.path.exists(file_name), index=False)
            print(f"Fundamental data for {coin} appended to {file_name}")
        except Exception as e:
            print(f"Error saving fundamental data to CSV: {e}")

    def attach_chart(self, coin, chart):
        self.chart_map[coin] = chart

    def buy(self, coin, price):
        available_cash_for_purchase = self.cash * (.99-self.commission_rate) # Commission buffer
        max_quantity = available_cash_for_purchase / price  # Calculate maximum quantity

        if max_quantity > 0:
            cost = price * max_quantity
            commission_fee = self.commission(cost)
            total_cost = cost + commission_fee  # Include commission in total

            print(f"Total cost: {total_cost:.2f}")

            if self.cash >= total_cost:
                self.cash -= total_cost  # Subtract the total cost including commission fee

                if coin in self.portfolio:
                    self.portfolio[coin] += max_quantity
                else:
                    self.portfolio[coin] = max_quantity

                self.log_trade('Buy', coin, price, max_quantity)
                self.place_marker(coin, price, max_quantity, 'Buy', 'red')
                print(f"Bought {max_quantity:.4f} {coin} at {price}, including commission of {commission_fee:.2f}")
            else:
                print("Not enough cash to cover purchase including commission.")

    def sell(self, coin, price):
        if coin in self.portfolio:
            quantity = self.portfolio[coin]
            if quantity > 0:
                revenue = price * quantity
                commission_fee = self.commission(revenue)
                total_revenue = revenue - commission_fee  # Deduct commission from revenue

                self.cash += total_revenue  # Add revenue minus commission to cash

                self.portfolio[coin] -= quantity
                self.log_trade('Sell', coin, price, quantity)
                self.place_marker(coin, price, quantity, 'Sell', 'green')
                print(f"Sold {quantity:.4f} {coin} at {price}, with commission of {commission_fee:.2f}")

    def commission(self, amount):
        return amount * self.commission_rate

    def log_trade(self, action, coin, price, quantity):
        profit = 0
        if action == 'Sell':
            initial_price = self.last_purchase_price.get(coin, 0)
            profit = (price - initial_price) * quantity
        self.trade_log.append({
            'Action': action,
            'Coin': coin,
            'Price': price,
            'Quantity': quantity,
            'Cash': self.cash,
            'Portfolio': self.portfolio.copy(),
            'Profit': profit,
            'Commission': self.commission(price * quantity)
        })

    def place_marker(self, coin, price, quantity, trade_type, color):
        chart = self.chart_map.get(coin)
        if chart:
            chart.marker(text=f'{trade_type} {quantity} at {price}', color=color)

    def evaluate_trades(self, df_candles, coin):

        #print current portfolio
        print(f"Current portfolio: {self.portfolio}")        

        portfolio_value = self.portfolio.get(coin, 0) * df_candles['close'].iloc[-1]
        print(f"Portfolio value: {portfolio_value}")
        
        #print current cash
        print(f"Current cash: {self.cash}")

        last_close = df_candles['close'].iloc[0]
        close_further = df_candles['close'].iloc[-1]
        print(f"Coin: {coin}")
        print(f"Last close price: {last_close}")
        print(f"Further close price: {close_further}")

        if close_further*.999 > last_close and self.cash > 1000:
            print(f"Evaluating trade for {coin}:")
            print(f"Last close price: {last_close}")
            print(f"Further close price: {close_further}")
            print(f"Evaluating trade for {coin}:")
            self.buy(coin, last_close)  # Remove the quantity argument

        elif self.portfolio.get(coin, 0) > 0 and close_further*1.001 < last_close:
            print(f"Evaluating trade for {coin}:")
            print(f"Last close price: {last_close}")
            print(f"Further close price: {close_further}")
            self.sell(coin, last_close)  # No need to specify quantity

def main_trading_logic(coins):
    trader = PaperTrader(initial_cash=100000)

    # Initialize main chart and subcharts with specific positions
    chart = Chart(inner_width=0.5, inner_height=0.5)
    chart2 = chart.create_subchart(position='right', width=0.5, height=0.5)
    chart3 = chart.create_subchart(position='left', width=0.5, height=0.5)
    chart4 = chart3.create_subchart(position='right', width=0.5, height=0.5)

    charts = [chart, chart2, chart3, chart4]
    coin_chart_map = {coin: charts[i] for i, coin in enumerate(coins)}

    # Update trader to handle multiple charts
    trader.chart_map = coin_chart_map

    for i, coin in enumerate(coins):
        df = get_bar_data(coin, 60, 300)
        if not df.empty:
            charts[i].set(df)
            charts[i].watermark(coin)

    def update_charts():
        cumulative_data = {coin: pd.DataFrame() for coin in coins}  # Initialize cumulative DataFrame for each coin
        
        while True:
            market_data = {}
            for coin, chart in coin_chart_map.items():
                df = get_bar_data(coin, 60, 300)
                if not df.empty:
                    market_data[coin] = df  # Store latest data frame for coin
                    chart.set(df, True)
                    trader.evaluate_trades(df, coin)
                    
                    # Append new data to the cumulative DataFrame for this coin
                    cumulative_data[coin] = pd.concat([cumulative_data[coin], df]).drop_duplicates(subset='time')

            # Save updated cumulative market data to CSVs periodically
            for coin, df in cumulative_data.items():
                file_name = f"{coin}_market_data.csv"
                df.to_csv(file_name, mode='a', header=not os.path.exists(file_name), index=False)

            # Update trade logs
            trader.save_trade_log_to_csv()
            
            # Calculate total portfolio value using the gathered market data
            trader.calculate_total_portfolio_value(market_data)

            time.sleep(10)

    update_thread = threading.Thread(target=update_charts, daemon=True)
    update_thread.start()

    chart.show(block=True)

if __name__ == '__main__':
    # Define the coins to trade
    coins = ['MATH-USD', 'DIA-USD', 'ASM-USD', 'KARRAT-USD']
    main_trading_logic(coins)