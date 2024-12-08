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

    def evaluate(self, coin: str, df_candles: pd.DataFrame, portfolio: dict, cash: float, last_purchase_info: dict) -> dict:
        if len(df_candles) < 2:
            return {}
        # Ensure DataFrame is sorted in ascending order
        df_candles = df_candles.sort_values(by='time').reset_index(drop=True)
        latest = df_candles.iloc[-1]
        previous = df_candles.iloc[-2]
        # Change since last candle
        price_change = (latest['close'] - previous['close']) / previous['close']
        total_value = 0
        actions = {}
        holding = portfolio.get(coin, {}).get('quantity', 0) > 0
        if holding:
            total_value = portfolio[coin]['quantity'] * latest['close']
            # Sell if holding over 1 day or price increase meets threshold
            if total_value >= 1:
                last_purchase_time = last_purchase_info.get(coin, {}).get('datetime', None)
                if last_purchase_time:
                    holding_duration = pd.Timestamp(latest['time']) - last_purchase_time
                    if holding_duration >= pd.Timedelta(days=1):
                        # Sell due to holding over 1 day
                        actions['sell'] = {
                            'coin': coin,
                            'quantity': portfolio[coin]['quantity'],
                            'price': latest['close']
                        }
                        print(f"Selling {coin} after holding for {holding_duration}")
                        return actions
                # Original sell logic based on price_move
                average_entry_price = portfolio[coin].get('average_entry_price')
                if average_entry_price:
                    price_increase = (latest['close'] - average_entry_price) / average_entry_price
                    if price_increase >= self.price_move and total_value >= 1:
                        actions['sell'] = {
                            'coin': coin,
                            'quantity': portfolio[coin]['quantity'],
                            'price': latest['close']
                        }
                        print(f"Selling {coin} due to price increase of {price_increase:.2%}")
                else:
                    print(f"Average entry price not found for {coin} in portfolio.")

        else:
            # Buy logic remains the same
            print(f"Evaluating buy for {coin}")
            print(f"Current price: {latest['close']:.4f}")
            print(f"Previous price: {previous['close']:.4f}")
            print(f"Price drop threshold: {self.drop_threshold:.4f}")
            print(f"Price change: {price_change:.4f}")
            print(f"Available cash: {cash:.2f}")
            max_quantity = cash * 0.90 / latest['close']
            if max_quantity > 0 and price_change <= self.drop_threshold:
                actions['buy'] = {
                    'coin': coin,
                    'quantity': max_quantity,
                    'price': latest['close']
                }
        return actions