
import unittest
import pandas as pd
from strategies.probabilistic_strategy import ProbabilisticStrategy

class TestProbabilisticStrategy(unittest.TestCase):
    def test_evaluate_buy_signal(self):
        # Create sample data where a price drop occurs and meets criteria
        data = {
            'time': pd.date_range(start='2023-01-01', periods=5, freq='T'),
            'low': [100, 99, 98, 97, 96],
            'high': [101, 100, 99, 98, 97],
            'open': [100, 100, 99, 98, 97],
            'close': [100, 99, 98, 97, 100],  # Last close price jumps back
            'volume': [1, 1, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        strategy = ProbabilisticStrategy(price_move=0.05, profit_target=0.027, look_back=2, drop_threshold=-0.01)
        actions = strategy.evaluate('BTC-USD', df, portfolio={}, cash=1000)
        self.assertIn('buy', actions)

    def test_evaluate_sell_signal(self):
        # Create sample data where price meets sell criteria
        data = {
            'time': pd.date_range(start='2023-01-01', periods=5, freq='T'),
            'low': [100, 100, 100, 100, 100],
            'high': [100, 100, 100, 100, 100],
            'open': [100, 100, 100, 100, 100],
            'close': [100, 100, 100, 100, 109],  # Last close price increased by 9%
            'volume': [1, 1, 1, 1, 1]
        }
        df = pd.DataFrame(data)
        portfolio = {'BTC-USD': {'quantity': 1, 'average_entry_price': 100}}
        strategy = ProbabilisticStrategy(price_move=0.05, profit_target=0.027, look_back=2, drop_threshold=-0.01)
        actions = strategy.evaluate('BTC-USD', df, portfolio, cash=1000)
        self.assertIn('sell', actions)

if __name__ == '__main__':
    unittest.main()