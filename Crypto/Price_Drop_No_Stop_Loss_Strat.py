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