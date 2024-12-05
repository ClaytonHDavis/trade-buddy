from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    @abstractmethod
    def evaluate(self, coin: str, df_candles: pd.DataFrame, portfolio: dict, cash: float) -> dict:
        """
        Evaluate the strategy for a specific coin and decide on trades.

        :param coin: The trading pair, e.g., 'BTC-USD'.
        :param df_candles: DataFrame containing historical candle data for the coin.
        :param portfolio: Current portfolio holdings.
        :param cash: Available cash.
        :return: Dictionary with actions, e.g., {'buy': {'coin': 'BTC', 'quantity': 0.1}, 'sell': {'coin': 'ETH'}}
        """
        pass