
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

        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]

        # Initialize actions dictionary
        actions = {}

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