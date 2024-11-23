import pandas as pd
import numpy as np
import psycopg2
import backtrader as bt
from datetime import datetime
import csv

def fetch_data_from_db():
    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "asheville",
        'host': "localhost",
        'port': "5433"
    }

    query = "SELECT * FROM public.simplified_trading_data where product_id = 'KARRAT-USD'  ORDER BY START ASC;"

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

class CustomStrategy(bt.Strategy):
    params = (
        ('ema_period', 200),
        ('sma_period', 100),  # SMA period
        ('rsi_period', 14), #14 default
        ('oversold_threshold', 40),
        ('overbought_threshold', 70),
        ('volume_multiplier', 3.5), # Parameter to determine how significantly higher the volume should be
        ('sma_lookback', 3),  # Lookback period for checking SMA trend
        ('bullmarket_long_lookback', 500),  # Lookback period for checking bull market
        ('order_size', 1),  # Correct purchase size NOT USED RIGHT NOW
    )

    def __init__(self):
        self.dataclose = self.data.close
        self.ema200 = bt.indicators.EMA(self.data.close, period=self.params.ema_period)
        self.sma100 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)
        self.rsi = bt.indicators.RSI_Safe(self.data.close, period=self.params.rsi_period)
        self.average_volume = bt.indicators.SMA(self.data.volume, period=self.params.sma_period)
        self.trades = []

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
            self.trades[-1].update({'profit': trade.pnl, 'net_profit': trade.pnlcomm})

    def next(self):
        if len(self.data) <= 24:
            return
        
        if self.check_buy_conditions():
            self.perform_buy()

        if self.check_sell_conditions():
            self.perform_sell()

    def sma_trending_up(self, lookback):
        # Check if the SMA trend is upwards
        for i in range(lookback):
            if self.sma[0 - i] <= self.sma[-1 - i]:
                return False
        return True

    def sma_trending_down(self, lookback):
        # Check if the SMA trend is downwards
        for i in range(lookback):
            if self.sma[0 - i] >= self.sma[-1 - i]:
                return False
        return True

    def check_buy_conditions(self):
        return (self.buy_condition_above_ema(self.dataclose[0], self.ema200[0]) and
                #self.buy_condition_oversold_rsi(self.rsi[0], self.params.oversold_threshold) and
                self.buy_condition_ema_slope(self.ema200, -5, -14) and
                #self.buy_condition_sma_increasing(self.sma100, lookback=50) and  # Look for an upswing
                self.buy_bull_market(self.sma100, long_term_lookback=self.params.bullmarket_long_lookback) and  # New bull market condition
                #self.buy_condition_high_volume(self.data.volume[0], self.average_volume[0]) and # New volume condition
                not self.position)

    def buy_condition_above_ema(self, current_price, current_ema):
        return current_price > current_ema

    def buy_condition_oversold_rsi(self, current_rsi, oversold_threshold):
        return current_rsi < oversold_threshold

    def buy_condition_ema_slope(self, ema_series, leading_window, lagging_window):
        return ema_series[leading_window] > ema_series[lagging_window]

    def buy_condition_sma_increasing(self, sma_series, lookback=3):
        for i in range(lookback):
            if sma_series[0 - i] <= sma_series[-1 - i]:
                return False
        return True

    def buy_bull_market(self, sma_series, long_term_lookback=6000):
        #check if there's even history at long term lookback
        if len(sma_series) > long_term_lookback:  
            if sma_series[-long_term_lookback] < sma_series[-1]:
                print(sma_series[-long_term_lookback])
                print(sma_series[-1])
                return True
        return False    

    def buy_condition_high_volume(self, current_volume, average_volume):
        # Check if the current volume is significantly higher than the average volume
        return current_volume > self.params.volume_multiplier * average_volume

    def perform_buy(self):
        available_cash = self.broker.get_cash() * 0.993
        self.log(f'BUY CREATE {self.dataclose[0]:.2f}, Cash: {self.broker.get_cash()}')
        self.buy(size=available_cash / self.dataclose[0])
        self.trades.append({
            'action': 'buy',
            'price': self.dataclose[0],
            'date': self.datas[0].datetime.date(0),
            'cash_before': self.broker.get_cash()
        })

    def check_sell_conditions(self):
        return (
            self.position 
            and self.sell_after_2p()
            #or self.sell_before_1p()
            # and self.sell_condition_below_ema(self.dataclose[0], self.ema200[0]) 
            #and self.sell_condition_overbought_rsi(self.rsi[0], self.params.overbought_threshold) 
            #and self.sell_condition_sma_decreasing(self.sma100, lookback=self.params.sma_lookback)  # New SMA decreasing condition
        )

    def sell_condition_below_ema(self, current_price, current_ema):
        return current_price < current_ema

    def sell_condition_overbought_rsi(self, current_rsi, overbought_threshold):
        return current_rsi > overbought_threshold
    
    def sell_after_2p(self):
        # Access the last buy price correctly
        if len(self.trades) > 0 and 'price' in self.trades[-1]:
            buy_price = self.trades[-1]['price']
            return self.dataclose[0] >= buy_price * 1.02
        return False
    
    def sell_before_1p(self):
        # Access the last buy price correctly
        if len(self.trades) > 0 and 'price' in self.trades[0]:
            buy_price = self.trades[0]['price']
            return self.dataclose[0] <= buy_price * 0.99
        return False
    
    def sell_condition_sma_decreasing(self, sma_series, lookback=3):
        # Check if the SMA is decreasing over the lookback period
        for i in range(lookback):
            if sma_series[-1 - i] <= sma_series[0 - i]:
                return False
        return True

    def perform_sell(self):
        self.log(f'SELL CREATE {self.dataclose[0]:.2f}, Cash: {self.broker.get_cash()}')
        self.sell(size=self.position.size)
        self.trades.append({
            'action': 'sell',
            'price': self.dataclose[0],
            'date': self.datas[0].datetime.date(0),
            'cash_before': self.broker.get_cash()
        })

    def log(self, message):
        # Implement logging logic here
        print(message)


    def stop(self):
        ending_cash = self.broker.get_cash()
        ending_value = self.broker.get_value()
        self.log(f'Final Portfolio Value: {ending_value:.2f}')
        self.log(f'Total Cash Remaining: {ending_cash:.2f}')

        total_trades = len(self.trades) // 2  # Assume each complete (buy + sell) counts as a single trade
        total_profit = sum([t.get('profit', 0) for t in self.trades if 'profit' in t])
        
        # Calculate profit per trade only if we have trades
        profit_per_trade = total_profit / total_trades if total_trades else 0

        summary = {
        'total_trades': total_trades,
        'total_profit': total_profit,
        'profit_per_trade': profit_per_trade,
        }

        # Write to CSV
        with open('trading_journal.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Action', 'Price', 'Cash Before', 'Cash After', 'Profit', 'Net Profit'])
            for idx, trade in enumerate(self.trades):
                cash_after = trade['cash_before'] - self.broker.get_cash()
                writer.writerow([
                    trade['date'], trade['action'], trade['price'],
                    trade['cash_before'], cash_after,
                    trade.get('profit', 0), trade.get('net_profit', 0)
                ])

            writer.writerow([])
            writer.writerow(['Total Trades', 'Total Profit', 'Profit per Trade'])
            writer.writerow([summary['total_trades'], summary['total_profit'], summary['profit_per_trade']])

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CustomStrategy)

    raw_data = fetch_data_from_db()

    if not raw_data.empty:
        raw_data['start'] = pd.to_datetime(raw_data['start'])

        data = bt.feeds.PandasData(
            dataname=raw_data,
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

        cerebro.plot()
    else:
        print("No data fetched to run the backtest.")