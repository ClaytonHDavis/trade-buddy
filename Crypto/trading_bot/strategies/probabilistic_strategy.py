
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
        if len(df_candles) < 2:
            return {}
        # Ensure DataFrame is sorted in ascending order
        df_candles = df_candles.sort_values(by='time').reset_index(drop=True)
        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]
        #change since last candle
        price_change = (latest['close'] - previous['close']) / previous['close']
        total_value = 0


        actions = {}
        holding = portfolio.get(coin, {}).get('quantity', 0) > 0 
        if holding:
            total_value = portfolio[coin]['quantity'] * latest['close']

        #Sell
        if total_value >= 1:
            # Retrieve last purchase price properly
            if 'average_entry_price' in portfolio[coin]:
                print(f"Portfolio: {portfolio}")

                last_purchase_price = portfolio[coin]['average_entry_price']
                price_increase = (latest['close'] - last_purchase_price) / last_purchase_price
                print(f"Evaluating sell for {coin}")
                print(f"Current price: {latest['close']:.4f}")
                print(f"Last purchase price: {last_purchase_price:.4f}")
                print(f"Price increase: {price_increase:.4f}")
                print(f"Price move threshold: {self.price_move:.4f}")
                if price_increase >= self.price_move and total_value >= 1:
                    actions['sell'] = {
                        'coin': coin,
                        'quantity': portfolio[coin]['quantity'],  # Specify the quantity to sell
                        'price': latest['close']
                    }
            else:
                # Handle the case where average_entry_price is missing
                print(f"Average entry price not found for {coin} in portfolio.")

        #Buy
        else:
            #print evaluating buy
            print(f"Evaluating buy for {coin}")
            print(f"Current price: {latest['close']:.4f}")
            print(f"Previous price: {previous['close']:.4f}")
            print(f"Price drop threshold: {self.drop_threshold:.4f}")
            print(f"Price change: {price_change:.4f}")
            print(f"Available cash: {cash:.2f}")

            max_quantity = cash*.90/ latest['close']
            if max_quantity > 0 and price_change <= self.drop_threshold:
                actions['buy'] = {
                    'coin': coin,
                    'quantity': max_quantity,
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