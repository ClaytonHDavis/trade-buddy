from strategies.base_strategy import BaseStrategy
import pandas as pd

class SMAStrategy(BaseStrategy):
    def __init__(self, short_window=10, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def evaluate(self, df_candles: pd.DataFrame, portfolio: dict, cash: float) -> dict:
        if len(df_candles) < self.long_window:
            return {}

        df_candles['short_ma'] = df_candles['close'].rolling(window=self.short_window).mean()
        df_candles['long_ma'] = df_candles['close'].rolling(window=self.long_window).mean()

        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]

        actions = {}

        # Golden cross: Buy signal
        if latest['short_ma'] > latest['long_ma'] and previous['short_ma'] <= previous['long_ma']:
            actions['buy'] = {'coin': 'BTC-USD', 'quantity': 0.01, 'price': latest['close']}

        # Death cross: Sell signal
        elif latest['short_ma'] < latest['long_ma'] and previous['short_ma'] >= previous['long_ma']:
            actions['sell'] = {'coin': 'BTC-USD', 'price': latest['close']}

        return actions