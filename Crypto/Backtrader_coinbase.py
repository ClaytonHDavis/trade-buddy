from __future__ import (absolute_import, division, print_function, unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas as pd

# Import the backtrader platform
import backtrader as bt

class FullCash(bt.Sizer):
    params = (('commission_rate', 0.006),)  # Default value

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            price = data.close[0]
            max_cash = cash / (1 + self.params.commission_rate)
            size = int(max_cash / price)
            return max(size, 0)
        else:
            position = self.broker.getposition(data)
            return position.size

class SimpleMovingAverageCalculator:
    @staticmethod
    def calculate(data, period):
        if len(data) < period:
            return None
        return sum(data[-period:]) / period

class GoldenCrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 20),
        ('slow_period', 200),
        ('use_price_increase', True),
        ('use_trailing_stop', True),
        ('use_sharp_drop', False),
        ('price_increase_pct', 1.75),
        ('price_increase_bars', 10),
        ('trailing_stop_pct', 3.5),
        ('sharp_drop_pct', 1.0),
        ('sharp_drop_bars', 3),
        ('trend_bars', 5),  # Number of bars to consider for uptrend detection
        ('use_trend_based_buy', True),  # Toggle for trend-based buying
    )

    def __init__(self):
        self.dataclose = self.data.close
        self.fast_sma_values = []
        self.slow_sma_values = []
        self.highest_price = None
        self.order = None

        # Initialize a DataFrame for trade logging with an additional column for commission
        self.trade_data = pd.DataFrame(columns=['Datetime', 'Type', 'Price', 'Size', 'Commission', 'Profit (Net)'])

    def log(self, txt, dt=None):
        dt = dt or bt.num2date(self.datas[0].datetime[0])
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            commission = order.executed.comm  # Capture the commission

            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.8f}, Commission: {commission:.8f}')
                self.highest_price = order.executed.price
                new_data = pd.DataFrame([{
                    'Datetime': bt.num2date(self.data.datetime[0]),
                    'Type': 'BUY',
                    'Price': order.executed.price,
                    'Size': order.executed.size,
                    'Commission': commission
                }])
                self.trade_data = pd.concat([self.trade_data, new_data], ignore_index=True)
            else:  # Sell
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.8f}, Commission: {commission:.8f}')
                new_data = pd.DataFrame([{
                    'Datetime': bt.num2date(self.data.datetime[0]),
                    'Type': 'SELL',
                    'Price': order.executed.price,
                    'Size': order.executed.size,
                    'Commission': commission
                }])
                self.trade_data = pd.concat([self.trade_data, new_data], ignore_index=True)

            self.bar_executed = len(self)

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}')
        self.trade_data.at[self.trade_data.index[-1], 'Profit (Net)'] = trade.pnlcomm

    def next(self):
        self.fast_sma_values.append(self.dataclose[0])
        self.slow_sma_values.append(self.dataclose[0])

        fast_sma = SimpleMovingAverageCalculator.calculate(self.fast_sma_values, self.params.fast_period)
        slow_sma = SimpleMovingAverageCalculator.calculate(self.slow_sma_values, self.params.slow_period)

        if fast_sma and slow_sma:
            fast_sma_prev = SimpleMovingAverageCalculator.calculate(self.fast_sma_values[:-1], self.params.fast_period)
            slow_sma_prev = SimpleMovingAverageCalculator.calculate(self.slow_sma_values[:-1], self.params.slow_period)

            self.log(f'Close: {self.dataclose[0]:.8f}, Fast SMA: {fast_sma:.8f}, Slow SMA: {slow_sma:.8f}')

            sma_up_trend = fast_sma_prev and slow_sma_prev and fast_sma > fast_sma_prev and slow_sma > slow_sma_prev

            if not self.position:
                price_increased = self.params.use_price_increase and self.check_price_increase()
                trending_up = (self.params.use_trend_based_buy and self.is_trending_up(self.params.trend_bars)) or not self.params.use_trend_based_buy
                if fast_sma > slow_sma and sma_up_trend and trending_up and (not self.params.use_price_increase or price_increased):
                    self.log(f'BUY CREATE, {self.dataclose[0]:.8f}')
                    self.buy()
            else:
                self.highest_price = max(self.highest_price, self.dataclose[0])
                stop_loss_price = self.highest_price * (1 - self.params.trailing_stop_pct / 100)
                sharp_drop = self.params.use_sharp_drop and self.check_sharp_drop()

                if (self.params.use_trailing_stop and self.dataclose[0] < stop_loss_price) or sharp_drop:
                    self.log(f'SELL CREATE, {self.dataclose[0]:.8f}')
                    self.sell()

    def is_trending_up(self, bars):
        # Check sufficiency of data points to avoid out-of-range errors
        if len(self.fast_sma_values) < self.params.fast_period + bars:
            return False

        # List to accumulate recent SMA averages over the given span
        sma_values = []

        # Calculate SMA for each interval of 'fast_period' within the last 'bars' periods
        for i in range(-bars, 0):
            sma = SimpleMovingAverageCalculator.calculate(
                self.fast_sma_values[i - self.params.fast_period:i], self.params.fast_period
            )
            if sma is not None:
                sma_values.append(sma)

        # Ensure enough clean data is available for comparison
        if len(sma_values) < 2:
            return False

        # Verify trend increase by ensuring each SMA is greater than its predecessor
        return all(sma_values[i] < sma_values[i+1] for i in range(len(sma_values) - 1))

    def check_price_increase(self):
        if len(self.dataclose) < self.params.price_increase_bars + 1:
            return False

        prev_price = self.dataclose[-self.params.price_increase_bars]
        current_price = self.dataclose[0]
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        return price_change_pct >= self.params.price_increase_pct
    
    # price max in last x bars
    #HERE - trying to reduce buying when price is chopping around a lot
    def check_price_max(self):
        if len(self.dataclose) < self.params.price_increase_bars + 1:
            return False
        
        #get max price in last x bars
        max_price = max(self.dataclose[-self.params.price_increase_bars:])
        current_price = self.dataclose[0]

        return current_price >= max_price


    def check_sharp_drop(self):
        if len(self.dataclose) < self.params.sharp_drop_bars + 1:
            return False

        prev_price = self.dataclose[-self.params.sharp_drop_bars]
        current_price = self.dataclose[0]
        price_change_pct = ((prev_price - current_price) / prev_price) * 100
        return price_change_pct >= self.params.sharp_drop_pct
            
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCrossStrategy)

    datapath = 'MATH-USD.csv'

    df = pd.read_csv(datapath)
    df['time'] = pd.to_datetime(df['time'])

    min_date = df['time'].min()
    max_date = df['time'].max()

    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=min_date,
        todate=max_date,
        nullvalue=float('NaN'),
        dtformat=('%Y-%m-%d %H:%M:%S'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
        timeframe=bt.TimeFrame.Minutes,
        compression=1
    )

    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)

    commission_rate = 0.006
    cerebro.addsizer(FullCash, commission_rate=commission_rate)
    cerebro.broker.setcommission(commission=commission_rate)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.8f}')
    strategy_runs = cerebro.run()
    
    # Access the strategy instance and save trade data to a CSV
    strategy_instance = strategy_runs[0]
    strategy_instance.trade_data.to_csv('trade_journal.csv', index=False)

    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.8f}')
    cerebro.plot()