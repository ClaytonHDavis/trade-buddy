import pandas as pd
import psycopg2
import backtrader as bt
import csv
import numpy as np
import os

def fetch_data_from_db():
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }

    query = """
    SELECT * FROM public.simplified_trading_data 
    WHERE product_id = 'STRK-USD' 
    ORDER BY start ASC;
    """

    try:
        connection = psycopg2.connect(**connection_params)
        dataframe = pd.read_sql_query(query, connection)
        print("Data fetched successfully.")
    except Exception as e:
        print(f"Failed to fetch data from database: {e}")
        dataframe = pd.DataFrame()
    finally:
        connection.close()

    return dataframe

def transform_data(dataframe):
    """Perform all necessary data transformations on raw data."""
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

    return dataframe

class CustomPandasData(bt.feeds.PandasData):
    # Define lines
    lines = ('ema5', 'ema8', 'ema13', 'ema50', 'ema100', 'ema200',
             'std_dev5', 'std_dev10', 'std_dev100',
             'slope_level_detection', 'std_percent_100', 'std_percent_to_slope',
             'sts_std5', 'sts_std10', 'sts_std100')

    # Define parameters
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
        ('profit_target', 0.20),
        ('stop_loss', 0.010),
    )

    def __init__(self):
        self.dataclose = self.data.close
        self.data_log = []
        self.trades = []

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
                self.trades[-1].update({'success': True})
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
                self.trades[-1].update({'success': True})
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            if self.trades:
                self.trades[-1].update({'success': False})

    def log(self, msg):
        bar_date = self.datas[0].datetime.date(0)
        print(f'{bar_date}: {msg}')

    def next(self):
        # Store data into log for inspection
        self.data_log.append({
            'datetime': self.datas[0].datetime.datetime(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0],
            'ema5': self.data.ema5[0],
            'ema8': self.data.ema8[0],
            'ema13': self.data.ema13[0],
            'ema50': self.data.ema50[0],
            'ema100': self.data.ema100[0],
            'ema200': self.data.ema200[0],
            'std_dev5': self.data.std_dev5[0],
            'std_dev10': self.data.std_dev10[0],
            'std_dev100': self.data.std_dev100[0],
            'slope_level_detection': self.data.slope_level_detection[0],
            'std_percent_100': self.data.std_percent_100[0],
            'std_percent_to_slope': self.data.std_percent_to_slope[0],
            'sts_std5': self.data.sts_std5[0],
            'sts_std10': self.data.sts_std10[0],
            'sts_std100': self.data.sts_std100[0],
        })

        # Buy logic
        if not self.position and self.check_buy_conditions():
            self.perform_buy()

        # Sell logic
        if self.position:
            self.check_sell_conditions()

    def check_buy_conditions(self):
        trending_up = all(self.data.ema5[-i] < self.data.ema5[-i + 1] for i in range(1, 6)) and \
                      all(self.data.ema8[-i] < self.data.ema8[-i + 1] for i in range(1, 6)) and \
                      all(self.data.ema13[-i] < self.data.ema13[-i + 1] for i in range(1, 6)) and \
                      all(self.data.ema50[-i] < self.data.ema50[-i + 1] for i in range(1, 6)) and \
                      all(self.data.ema100[-i] < self.data.ema100[-i + 1] for i in range(1, 6)) and \
                      all(self.data.ema200[-i] < self.data.ema200[-i + 1] for i in range(1, 6))

        above_ema200 = (self.data.ema5[0] > self.data.ema200[0] and
                        self.data.ema8[0] > self.data.ema200[0] and
                        self.data.ema13[0] > self.data.ema200[0] and
                        self.data.ema50[0] > self.data.ema200[0] and
                        self.data.ema100[0] > self.data.ema200[0])

        slope_level_detection_bool = self.data.std_percent_to_slope[0] > self.data.sts_std100[0] and self.data.std_percent_to_slope[0] > 0

        #average std_percet over X bars
        average_std_percent_50 = np.mean(self.data.std_percent_100.get(size=20))

        #recent std_percent is higher than average
        average_std_percent_10 = np.mean(self.data.std_percent_100.get(size=10))

        #1 percent price gain last x bars
        price_gain = (self.data.close[0] - self.data.close[-1]) / self.data.close[-1] > 0.05

        price_drop = (self.data.close[0] - self.data.close[-1]) / self.data.close[-1] < -0.05

        #get max price change in last 5 bars
        #max_price_change = np.max(self.data.close.get(size=5)) - np.min(self.data.close.get(size=5)) >= 0.05

        high_standard_deviation = average_std_percent_10 > average_std_percent_50

        return price_drop

    def perform_buy(self):
        available_cash = self.broker.get_cash()
        self.log(f'BUY CREATE {self.dataclose[0]:.2f}, Cash: {available_cash}')
        
        comminfo = self.broker.getcommissioninfo(self.data)
        commission_rate = comminfo.p.commission

        size = available_cash*.99 / self.dataclose[0] * (1 - commission_rate)

        self.buy(size=size)

        data_row = {
            'datetime': self.datas[0].datetime.datetime(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0],
            'ema5': self.data.ema5[0],
            'ema8': self.data.ema8[0],
            'ema13': self.data.ema13[0],
            'ema50': self.data.ema50[0],
            'ema100': self.data.ema100[0],
            'ema200': self.data.ema200[0],
            'std_dev5': self.data.std_dev5[0],
            'std_dev10': self.data.std_dev10[0],
            'std_dev100': self.data.std_dev100[0],
            'size': size,
            'success': None,  # Initially the success status is unknown
            'portfolio_value': self.broker.getvalue(),
            'cash': self.broker.get_cash(),
            'slope_level_detection': self.data.slope_level_detection[0],
            'std_percent_100': self.data.std_percent_100[0],
            'std_percent_to_slope': self.data.std_percent_to_slope[0],
            'sts_std5': self.data.sts_std5[0],
            'sts_std10': self.data.sts_std10[0],
            'sts_std100': self.data.sts_std100[0],
        }

        self.trades.append({
            'action': 'buy',
            'price': self.dataclose[0],
            'cash_before': available_cash,
            **data_row
        })

    def check_sell_conditions(self):
        slope_level_detection_bool = self.data.std_percent_to_slope[0] < -3 * self.data.sts_std100[0] and self.data.std_percent_to_slope[0] < 0

        #price of previous trade
        previous_trade_price = self.trades[-1]['price']

        #price of current bar 
        price_increase = (self.data.close[0] - previous_trade_price) / previous_trade_price > 0.05        

        if price_increase:
            self.perform_sell()

    def perform_sell(self):
        self.log(f'SELL CREATE {self.dataclose[0]:.2f}, Cash: {self.broker.get_cash()}')
        self.sell(size=self.position.size)

        data_row = {
            'datetime': self.datas[0].datetime.datetime(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0],
            'ema5': self.data.ema5[0],
            'ema8': self.data.ema8[0],
            'ema13': self.data.ema13[0],
            'ema50': self.data.ema50[0],
            'ema100': self.data.ema100[0],
            'ema200': self.data.ema200[0],
            'std_dev5': self.data.std_dev5[0],
            'std_dev10': self.data.std_dev10[0],
            'std_dev100': self.data.std_dev100[0],
            'size': self.position.size,
            'success': None,  # Initially the success status is unknown
            'portfolio_value': self.broker.getvalue(),
            'cash': self.broker.get_cash(),
            'slope_level_detection': self.data.slope_level_detection[0],
            'std_percent_100': self.data.std_percent_100[0],
            'std_percent_to_slope': self.data.std_percent_to_slope[0],
            'sts_std5': self.data.sts_std5[0],
            'sts_std10': self.data.sts_std10[0],
            'sts_std100': self.data.sts_std100[0],
        }

        self.trades.append({
            'action': 'sell',
            'price': self.dataclose[0],
            'cash_before': self.broker.get_cash(),
            **data_row
        })

    def stop(self):
        with open('trading_journal.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'Date', 'Action', 'Price', 'Size', 'Open', 'High', 'Low',
                'Close', 'Volume', 'EMA5', 'EMA8', 'EMA13', 'EMA50', 'EMA100',
                'EMA200', 'StdDev5', 'StdDev10', 'StdDev100', 'Success', 'Portfolio Value', 'Cash', 
                'slope_level_detection', 'sts_std5', 'sts_std10', 'sts_std100'
            ])
            writer.writeheader()

            for trade in self.trades:
                writer.writerow({
                    'Date': trade['datetime'],
                    'Action': trade['action'],
                    'Price': trade['price'],
                    'Size': trade['size'],
                    'Open': trade['open'],
                    'High': trade['high'],
                    'Low': trade['low'],
                    'Close': trade['close'],
                    'Volume': trade['volume'],
                    'EMA5': trade['ema5'],
                    'EMA8': trade['ema8'],
                    'EMA13': trade['ema13'],
                    'EMA50': trade['ema50'],
                    'EMA100': trade['ema100'],
                    'EMA200': trade['ema200'],
                    'StdDev5': trade['std_dev5'],
                    'StdDev10': trade['std_dev10'],
                    'StdDev100': trade['std_dev100'],
                    'Success': trade.get('success', False),
                    'Portfolio Value': trade['portfolio_value'],
                    'Cash': trade['cash'],
                    'slope_level_detection': trade['slope_level_detection'],
                    'sts_std5': trade['sts_std5'],
                    'sts_std10': trade['sts_std10'],
                    'sts_std100': trade['sts_std100']
                })

            writer.writerow({})
            writer.writerow({'Date': 'Summary', 'Action': 'Total Trades', 'Size': len(self.trades) // 2})
            writer.writerow({'Date': 'Summary', 'Action': 'Final Portfolio Value', 'Price': self.broker.getvalue()})

        with open('full_data_log.csv', mode='w', newline='') as file:
            fieldnames = [
                'datetime', 'open', 'high', 'low', 'close', 'volume',
                'ema5', 'ema8', 'ema13', 'ema50', 'ema100', 'ema200',
                'std_dev5', 'std_dev10', 'std_dev100', 
                'slope_level_detection', 'std_percent_100', 'std_percent_to_slope',
                'sts_std5', 'sts_std10', 'sts_std100'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for data_row in self.data_log:
                writer.writerow(data_row)

        self.log('Finished writing all data to CSV.')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(EMARibbonStrategy)

    raw_data = fetch_data_from_db()

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

        cerebro.adddata(data)
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.006)

        print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
        cerebro.run()
        print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
        cerebro.plot(style='candle')
    else:
        print("No data fetched to run the backtest.")