# Fully Implemented - Low Stakes

I got this new MacBook Air, which has been really nice. It's a sleak well-built machine that feels nice to use, and it's got impressive specs that makes it competitive with any other consumer laptop. I think the Mac-IOS integration will be one of the nice parts about using it though, so I look forward to getting use to that. I've used my iPad and iPhone so much for notes, that it's be extremely nice to be able seemlessly have all that work between devices. The computer was the last thing I needed to complete the ensemble. I think it will really improve my workflow, on top of being cool and shiny.

## The project November 23rd, 2024

Getting into trading and quantitative finance has been pretty interesting, over the last few months. I think that I've learned a lot actually, but it's still only scratched the surface. I'd say I kind of took an immersion-techinque with it, where I just listen to podcasts, read books, and articles as much as possible - also while persuing an active project along the way that worked to retrieve financial data and trade programatically.

I stumbled on a simple strategy but we're to the point where we need to implement something here - mainly to fully understand trading mechanics of the Coinbase API. I think we have a basic paper simulator we can run, but we haven't run it for any amount of time yet - I need to go head and deploy that on my desktop PC. That can be running all the time and while I research new techniques using the laptops. Now that I've got everything into Git, it's not too bad to move things to a new computer... other than this date-mining peice that's a little cumbersome to redo. But if the desktop is only used for running things in production, then it's not as big a deal to have that on there.

From listening to this Jack Schwagger "Unknown Market Wizards" book, it's pretty amazing what some people achieve in their trading. And especially since they are doing it manually. There is so much emphasis on regulating your emotions and not acting irrationally out of fear/greed, but the best traders still fail at this from time-to-time. Computers just solve that. Now, there's also incredible nuance to the art of trading well. These people have a true gift, and have honed in pattern regognitions and macroeconomic information processing to an amazing, but not scientific level. They often can't put certain things they do into words, or perhaps they can but they often refuse because revealing their technique will ruin there edge in the competitive marketplace. That's another interesting thing, it's a very secretive industry - no one wants to talk about what they are actually doing to make Money, unless they are selling you a class...

I think if I can get something up and running by the end of next week, that'd be good. It'd be cool to be able to have something I can run through december. I feel like the market is pretty hot right now, especially with Bitcoin taking off, and political sentiments shifting in favor of it. If I'm totally honest, I think that it's a cool technology with limited usefulness in a socioeconomic system that is centralized financially. It would be interesting if it somehow could rival other centralized currencies as a supior way to transfer value. That's really all that money does is transfer value across all mediums. And I think I struggled to think about how it could really be a real currency, and I guess the answer is that of course it can. Something is worth precisely what people are willing to pay for it - that's all that value is. So if enough people out there are willing to pay $80,000 for a BTC-USD coin, then it's worth that. There is no governement backing or enforcing this value. The coin does not provide any other utility or special properties, other than the ability to run an automated decentralized ledger to keep track of transactions. Yet, although no one enforces or backs the value, it can be reliable exchanged and has actually appreciated in value more than any other currency. Something else that's interesting, is that these digital currencies are also even more inflated in value and returns when paired against weaker currencies across the globe. Will it ever be listed on FOREX channels, like the US Dollar or Japanese Yen? And to think that the technology did spawn from the dark web, to support the worlds largest black market. Now you can do legitmate cypto-forex trading,which mirrors market actions, but doesn't require a $100,000 mininum order.

When I'm thinking about coming up with a trading strategy, after listening to these guys who are legends, it just seems really hard... but it's clearly possible. It's like finding a needle in a haystack. A needle in a haystack, you can only see it clearly after someone has already shown you where it is. Where are we most likely to find a needle in a haystack?

## Papercoin.py

```python
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
```

## Big Drop Buy

```Py
import pandas as pd
import psycopg2
import backtrader as bt
import csv
import numpy as np

# Define CSV file path
csv_file_path = "trading_Journal.csv"

# Create a global DataFrame for storing trades
trading_journal = pd.DataFrame(columns=[
    'Date/Time', 'Buy/Sell', 'Price', 'Position Size', 
    'Profit/Loss', 'Portfolio Value', 'product_id'
])

fields = ['Date/Time', 'Buy/Sell', 'Price', 'Position Size', 'Profit/Loss', 'Portfolio Value', 'product_id']
with open(csv_file_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

# Function to save trades to CSV
def save_trade_to_csv(trade):
    filtered_trade = {field: trade.get(field, '') for field in fields}
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writerow(filtered_trade)

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

def transform_data(dataframe):
    
    print("Before:",dataframe['start'][0], "After:", pd.to_datetime(dataframe['start'][0]), "Close:", dataframe['close'][0], "product_id:", dataframe['product_id'][0])    
    dataframe['start'] = pd.to_datetime(dataframe['start'])

    # Calculate EMAs and other indicators
    dataframe['ema5'] = dataframe['close'].ewm(span=5, adjust=False).mean()
    dataframe['ema8'] = dataframe['close'].ewm(span=8, adjust=False).mean()
    dataframe['ema13'] = dataframe['close'].ewm(span=13, adjust=False).mean()
    dataframe['ema50'] = dataframe['close'].ewm(span=50, adjust=False).mean()
    dataframe['ema100'] = dataframe['close'].ewm(span=100, adjust=False).mean()
    dataframe['ema200'] = dataframe['close'].ewm(span=200, adjust=False).mean()
    dataframe['std_dev5'] = dataframe['close'].rolling(window=5).std()
    dataframe['std_dev10'] = dataframe['close'].rolling(window=10).std()
    dataframe['std_dev100'] = dataframe['close'].rolling(window=100).std()
    dataframe['slope_level_detection'] = dataframe['ema100'].diff() / dataframe['ema100']
    dataframe['std_percent_100'] = dataframe['std_dev100'] / dataframe['ema100']
    dataframe['std_percent_to_slope'] = dataframe['slope_level_detection'] / dataframe['std_percent_100']
    dataframe['sts_std5'] = dataframe['std_percent_to_slope'].rolling(window=5).std()
    dataframe['sts_std10'] = dataframe['std_percent_to_slope'].rolling(window=10).std()
    dataframe['sts_std100'] = dataframe['std_percent_to_slope'].rolling(window=100).std()

    return dataframe

class CustomPandasData(bt.feeds.PandasData):
    lines = ('ema5', 'ema8', 'ema13', 'ema50', 'ema100', 'ema200',
             'std_dev5', 'std_dev10', 'std_dev100',
             'slope_level_detection', 'std_percent_100', 'std_percent_to_slope',
             'sts_std5', 'sts_std10', 'sts_std100')

    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
        ('ema5', -1),
        ('ema8', -1),
        ('ema13', -1),
        ('ema50', -1),
        ('ema100', -1),
        ('ema200', -1),
        ('std_dev5', -1),
        ('std_dev10', -1),
        ('std_dev100', -1),
        ('slope_level_detection', -1),
        ('std_percent_100', -1),
        ('std_percent_to_slope', -1),
        ('sts_std5', -1),
        ('sts_std10', -1),
        ('sts_std100', -1),
    )

class EMARibbonStrategy(bt.Strategy):
    params = (
        #('profit_target', 0.20), #NOT TRUE BUT PRODUCES EXCELLENT RESULTS HIGH RISK
        ('profit_target', 0.027), #TRUE TO STRATEGY AVERAGE RESULTS
        #('profit_target', 0.015), #TRUE TO STRATEGY LOW RISK
        ('stop_loss', 0.010),
        ('price_move', 0.05),
        ('look_back', 10),
        ('drop_threshold', -0.05),
        ('increase_threshold', 0.006),
    )

    def __init__(self):
        self.trades = {data._name: [] for data in self.datas}
        self.dataclose = {data: data.close for data in self.datas}

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')

        
    def log_trade(self, trade_details):
            global trading_journal  # Use the global DataFrame we created
            trade_details_df = pd.DataFrame([trade_details])
            trading_journal = pd.concat([trading_journal, trade_details_df], ignore_index=True)

    def notify_order(self, order):
        data_name = order.data._name
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')

            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')

            # Create a new trade record dictionary
            trade_details = {
                'Date/Time': order.data.datetime.datetime(0),
                'Buy/Sell': 'Buy' if order.isbuy() else 'Sell',
                'Price': order.executed.price,
                'Position Size': order.executed.size,
                'Profit/Loss': self.calculate_profit_loss(data_name, order),
                'Portfolio Value': self.broker.getvalue(),
                'product_id': data_name
            }

            # Log the trade
            self.log_trade(trade_details)

            #save_trade_to_csv(trade_details)

    def calculate_probability(self, data):
        prices = data.close.array  # Use array instead of get
        drop_count = 0
        increase_count = 0

        for i in range(1, len(prices)):
            price_drop = (prices[i] - prices[i - 1]) / prices[i - 1]
            if price_drop <= self.params.drop_threshold:
                drop_count += 1
                for j in range(i + 1, min(i + 1 + self.params.look_back, len(prices))):
                    price_increase = (prices[j] - prices[i]) / prices[i]
                    if price_increase >= self.params.increase_threshold:
                        increase_count += 1
                        break

        if drop_count == 0:
            return 0.0

        probability = increase_count / drop_count
        return probability

    def calculate_profit_loss(self, data_name, order):
        # Ensure valid calculation of profit/loss
        if order.isbuy():
            return 0
        elif order.issell() and len(self.trades[data_name]) > 0:
            last_trade_value = self.trades[data_name][-1]['Portfolio Value']
            current_value = self.broker.getvalue()
            return current_value - last_trade_value
        return 0

    def next(self):
        for data in self.datas:
            if not self.getposition(data) and self.check_buy_conditions(data):
                p = self.calculate_probability(data)
                self.log(f'Probability of increase after drop: {p:.2f}')
                
                b = self.params.profit_target / self.params.price_move if self.params.price_move != 0 else 1
                q = 1 - p
                f_star = (b * p - q) / b

                f_star = max(0, f_star)

                available_cash = self.broker.get_cash()
                position_size = available_cash * f_star / data.close[0]

                self.buy(data=data, size=position_size)
                self.log(f'BUY CREATE {data.close[0]:.2f}, Datetime: {data.datetime.datetime(0)}, Fraction of Portfolio: {f_star:.2f}')

                # Append a new trade record
                trade_details = {
                    'Ticker': data._name,
                    'Date/Time': data.datetime.datetime(0),
                    'Buy/Sell': 'Buy',  # Default to Buy, updated in notify_order if sell
                    'Price': data.close[0],
                    'Position Size': position_size,
                    'Total $$': data.close[0] * position_size,
                    'Commission': self.broker.getcommissioninfo(data).p.commission * data.close[0] * position_size,
                    'Profit/Loss': 0,
                    'Portfolio Value': self.broker.getvalue(),
                    'product_id': data._name,
                }
                self.trades[data._name].append(trade_details)

            if self.getposition(data) and self.check_sell_conditions(data):
                self.sell(data=data, size=self.getposition(data).size)

    def check_buy_conditions(self, data):
        # Modify to ensure correct threshold calculation
        price_drop = (data.close[0] - data.close[-1]) / data.close[-1] < self.params.drop_threshold
        return price_drop

    def check_sell_conditions(self, data):
        # Check if there's a valid position in the current data
        position = self.getposition(data)
        
        if not position or position.size <= 0:
            # If no position or position size is zero or negative, don't sell
            return False

        data_name = data._name
        previous_trade = self.trades[data_name][-1]

        # Ensure there's a previous buy trade to compare against
        if previous_trade['Buy/Sell'] != 'Buy':
            return False

        # Apply your existing logic to determine sell conditions
        # Calculate price increase from last trade price
        price_increase = (data.close[0] - previous_trade['Price']) / previous_trade['Price'] > self.params.price_move
        
        # Include additional conditions such as time checks between previous buy and current potential sell
        if (data.datetime.datetime(0) - previous_trade['Date/Time']).total_seconds() < 1500:
            price_increase_threshold = self.params.increase_threshold
        else:
            price_increase_threshold = self.params.price_move

        # Return whether sell conditions are met
        return price_increase

if __name__ == '__main__':
    token_list = ['MATH-USD', 'DIA-USD', 'ASM-USD','ORN-USD','KARRAT-USD']

    cerebro = bt.Cerebro()
    cerebro.addstrategy(EMARibbonStrategy)

    for token in token_list:
        raw_data = fetch_data_from_db(token)
        if not raw_data.empty:
            transformed_data = transform_data(raw_data)

            data = CustomPandasData(
                dataname=transformed_data,
                datetime='start',
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1,
            )

            cerebro.adddata(data, name=token)

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.006)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
    cerebro.run()
    trading_journal.to_csv('trading_journal.csv', index=False)
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
    cerebro.plot(style='candle')
```

## Probabilities

```python
import pandas as pd
import numpy as np
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy
import seaborn as sns
import matplotlib.pyplot as plt

def fetch_data_from_db():

    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }

    query = "SELECT * FROM public.simplified_trading_data WHERE product_id = 'DIA-USD' ORDER BY start ASC;"

    try:
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        print("Data fetched successfully.")
    except Exception as e:
        print(f"Failed to fetch data from the database: {e}")
        dataframe = pd.DataFrame()
    finally:
        connection.close()

    return dataframe

def transform_data(dataframe):
    dataframe['start'] = pd.to_datetime(dataframe['start'])

    # Calculate EMAs
    dataframe['ema5'] = dataframe['close'].ewm(span=5, adjust=False).mean()
    dataframe['ema8'] = dataframe['close'].ewm(span=8, adjust=False).mean()
    dataframe['ema13'] = dataframe['close'].ewm(span=13, adjust=False).mean()
    dataframe['ema50'] = dataframe['close'].ewm(span=50, adjust=False).mean()
    dataframe['ema100'] = dataframe['close'].ewm(span=100, adjust=False).mean()
    dataframe['ema200'] = dataframe['close'].ewm(span=200, adjust=False).mean()

    # Calculate Standard Deviations
    dataframe['std_dev5'] = dataframe['close'].rolling(window=5).std()
    dataframe['std_dev10'] = dataframe['close'].rolling(window=10).std()
    dataframe['std_dev100'] = dataframe['close'].rolling(window=100).std()

    # Calculate Slope Level Detection and Std Percent
    dataframe['slope_level_detection'] = dataframe['ema100'].diff() / dataframe['ema100']
    dataframe['std_percent_100'] = dataframe['std_dev100'] / dataframe['ema100']
    dataframe['std_percent_to_slope'] = dataframe['slope_level_detection'] / dataframe['std_percent_100']

    # Initialize buffers for rolling standard deviations calculation
    dataframe['sts_std5'] = dataframe['std_percent_to_slope'].rolling(window=5).std()
    dataframe['sts_std10'] = dataframe['std_percent_to_slope'].rolling(window=10).std()
    dataframe['sts_std100'] = dataframe['std_percent_to_slope'].rolling(window=100).std()

    # Drop NA values created by lagging or rolling calculations
    dataframe.dropna(inplace=True)

    return dataframe

# def preprocess_data(data):
#     data = transform_data(data)

#     # Define feature columns
#     features = ['ema5', 'ema8', 'ema13', 'ema50', 'ema100', 'ema200',
#                 'slope_level_detection', 
#                 'std_percent_100', 'std_percent_to_slope', 'sts_std5', 
#                 'sts_std10', 'sts_std100']
    
#     # Define the target for predicting gain or loss
#     data['next_close'] = data['close'].shift(-10)
#     data['gain_loss'] = (data['next_close'] > data['close']).astype(int)  # Binary classification target

#     # Drop the last row (which will have a NaN target due to shift)
#     data.dropna(inplace=True)

#     X = data[features]
#     y = data['gain_loss']

#     # Split data
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

#     return X_train, X_test, y_train, y_test, data

# def normalize_data(X_train, X_test):
#     scaler = StandardScaler()
#     X_train_scaled = scaler.fit_transform(X_train)
#     X_test_scaled = scaler.transform(X_test)
#     return X_train_scaled, X_test_scaled

# def train_and_evaluate_lstm(X_train, X_test, y_train, y_test, all_features_test):
#     num_features = X_train.shape[1]
    
#     # Reshape data for LSTM model
#     X_train_lstm = X_train.reshape((X_train.shape[0], 1, num_features))
#     X_test_lstm = X_test.reshape((X_test.shape[0], 1, num_features))
    
#     model = Sequential()
#     model.add(LSTM(50, activation='relu', input_shape=(1, num_features)))
#     model.add(Dropout(0.2))
#     model.add(Dense(1, activation='sigmoid'))  # Sigmoid activation for binary classification

#     model.compile(optimizer=Adam(), loss=BinaryCrossentropy(), metrics=['accuracy'])
#     model.fit(X_train_lstm, y_train, epochs=100, batch_size=10, validation_data=(X_test_lstm, y_test))

#     y_pred_prob = model.predict(X_test_lstm).flatten()
#     y_pred = (y_pred_prob > 0.5).astype(int)  # Convert probabilities to binary predictions
    
#     # Calculate accuracy
#     accuracy = np.mean(y_pred == y_test)
#     print('LSTM Model Accuracy: ', accuracy)

#     # Save results to CSV
#     results_df = all_features_test.iloc[y_train.size:].copy()
#     results_df['Predicted_Prob'] = y_pred_prob
#     results_df['Predicted'] = y_pred
#     results_df['Actual'] = y_test
    
#     # Select relevant columns for output
#     output_cols = ['Actual', 'Predicted', 'Predicted_Prob'] + list(results_df.columns)
#     results_df.to_csv('lstm_predictions_gain_or_loss.csv', columns=output_cols, index=False)
#     print("Predictions vs Actual saved to lstm_predictions_gain_or_loss.csv")

def calculate_price_change_metrics(dataframe, window=5):
    # Calculate price changes
    dataframe['price_change'] = (dataframe['close'] - dataframe['open']) / dataframe['open']

    # Calculate the max price change in the previous 5 bars
    max_change_prev = dataframe['price_change'].rolling(window=window).max()
    
    # Calculate the max price change in the next 5 bars
    max_change_future = dataframe['price_change'].rolling(window=window).max().shift(-window)
    
    dataframe['max_change_prev'] = max_change_prev
    dataframe['max_change_future'] = max_change_future

    #save to csv
    dataframe.to_csv('price_change_metrics.csv', index=False)

    return dataframe

def categorize_changes(dataframe):
    # Define bins and labels
    bins = [-np.inf, -0.05, -0.04, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, 0.04, 0.05, np.inf]
    labels = ['<-5%', '-4% to -5%', '-3% to -4%', '-2% to -3%', '-1% to -2%', '-1% to 0%',
              '0% to 1%', '1% to 2%', '2% to 3%', '3% to 4%', '4% to 5%', '>5%']
    
    dataframe['category_prev'] = pd.cut(dataframe['max_change_prev'], bins=bins, labels=labels)
    dataframe['category_future'] = pd.cut(dataframe['max_change_future'], bins=bins, labels=labels)

    dataframe.dropna(subset=['category_prev', 'category_future'], inplace=True)

    return dataframe

def create_probability_matrix(dataframe):
    dataframe = categorize_changes(dataframe)
    
    probability_matrix = pd.DataFrame(index=dataframe['category_prev'].cat.categories, 
                                      columns=dataframe['category_future'].cat.categories, data=0.0)

    for _, row in dataframe.iterrows():
        probability_matrix.loc[row['category_prev'], row['category_future']] += 1

    # Normalize each row to sum to 1
    probability_matrix = probability_matrix.div(probability_matrix.sum(axis=1), axis=0).fillna(0)

    return probability_matrix

def save_probability_matrix_to_csv(probability_matrix, filename="probability_matrix.csv"):
    probability_matrix.to_csv(filename)
    print(f"Probability matrix saved to {filename}")
    
def plot_heatmap(matrix):
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(matrix, annot=True, fmt=".2f", cmap="YlGnBu", cbar=True)
    ax.set_xlabel('Current Event')
    ax.set_ylabel('Previous Event')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title("Probability Matrix Heatmap (Max Change over 5 Bars)")
    plt.show()

def main():
    data = fetch_data_from_db()
    transformed_data = transform_data(data)
    calculated_data = calculate_price_change_metrics(transformed_data, window=5)
    probability_matrix = create_probability_matrix(calculated_data)
    save_probability_matrix_to_csv(probability_matrix)

    plot_heatmap(probability_matrix)

if __name__ == "__main__":
    main()
```

