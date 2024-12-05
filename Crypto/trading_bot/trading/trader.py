from external.coinbase_portfolio import PortfolioManager
from external.coinbase_make_transactions import place_market_order
from config.config import Config
from datetime import datetime
import pandas as pd
from utils.logger import setup_logger

class LiveTrader:
    def __init__(self, portfolio_manager: PortfolioManager, strategy, is_live_mode: bool = True):
        self.logger = setup_logger()
        self.portfolio_manager = portfolio_manager
        self.strategy = strategy
        self.is_live_mode = is_live_mode
        if self.is_live_mode:
            total_cash_balance = self.portfolio_manager.extract_total_cash_balance(self._fetch_portfolio_data())
            self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
        else:
            self.cash = Config.NON_LIVE_START_CASH        
        self.portfolio = {}  # {'coin': {'quantity': x, 'average_entry_price': y}}
        self.commission_rate = Config.COMMISSION_RATE
        self.trade_log = []
        self.last_purchase_info = {}
        self.update_portfolio()

    def _fetch_portfolio_data(self):
        portfolio_uuid = self.portfolio_manager.list_portfolio()
        return self.portfolio_manager.get_portfolio_breakdown(portfolio_uuid)

    def update_portfolio(self):
        portfolio_data = self._fetch_portfolio_data()
        # Log the portfolio data for debugging
        self.logger.debug(f"Fetched portfolio data: {portfolio_data}")
        print(portfolio_data)
        
        # Extract the positions list
        if not isinstance(portfolio_data, dict):
            self.logger.error("portfolio_data is not a dictionary.")
            return

        positions = portfolio_data.get('breakdown', {}).get('spot_positions', [])
        
        # Validate positions
        if not isinstance(positions, list):
            self.logger.error("Positions data is not a list.")
            return
        if not all(isinstance(position, dict) for position in positions):
            self.logger.error("Not all items in positions are dictionaries.")
            return

        self.portfolio = {}
        for position in positions:
            asset = position.get('asset')
            if not asset:
                self.logger.warning(f"Position without asset: {position}")
                continue
            coin = f"{asset}-USD"
            price_info = position.get('average_entry_price', {'value': '0', 'currency': 'USD'})
            try:
                average_entry_price = float(price_info.get('value', 0))
            except ValueError:
                self.logger.error(f"Invalid average_entry_price: {price_info.get('value')}")
                average_entry_price = 0.0
            quantity = position.get('total_balance_crypto', 0)
            try:
                quantity = float(quantity)
            except ValueError:
                self.logger.error(f"Invalid quantity for {coin}: {quantity}")
                quantity = 0.0
            self.portfolio[coin] = {
                'quantity': quantity,
                'average_entry_price': average_entry_price
            }
        if self.is_live_mode:
            # Extract the total cash balance using the configured percentage
            total_cash_balance = self.portfolio_manager.extract_total_cash_balance(portfolio_data)
            self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
        else:
            self.cash = Config.NON_LIVE_START_CASH  # Ensure consistency when not in live mode
            
        self.logger.info(f"Portfolio updated: {self.portfolio}")
        self.logger.info(f"Last purchase info updated: {self.last_purchase_info}")

    def calculate_total_portfolio_value(self, market_data: dict) -> float:
        if self.is_live_mode:
            self.update_portfolio()
        total_value = self.cash
        for coin, data in self.portfolio.items():
            quantity = data.get('quantity', 0)
            if quantity > 0 and coin in market_data and not market_data[coin].empty:
                price = market_data[coin]['close'].iloc[-1]
                total_value += quantity * price
        self.logger.info(f"Total portfolio value: {total_value:.2f}")
        return total_value

    def save_trade_log_to_csv(self, file_name: str = Config.TRADE_LOG_FILE):
        try:
            df_trade_log = pd.DataFrame(self.trade_log)
            df_trade_log.to_csv(file_name, index=False)
            self.logger.info(f"Trade log saved to {file_name}")
        except Exception as e:
            self.logger.error(f"Error saving trade log to CSV: {e}")

    def commission(self, amount: float) -> float:
        return amount * self.commission_rate

    def log_trade(self, action: str, coin: str, price: float, quantity: float, trade_datetime: datetime, profit: float = 0):
        commission_fee = self.commission(price * quantity)
        self.trade_log.append({
            'Datetime': trade_datetime,
            'Action': action,
            'Coin': coin,
            'Price': price,
            'Quantity': quantity,
            'Cash': self.cash,
            'Portfolio': self.portfolio.copy(),
            'Profit': profit,
            'Commission': commission_fee
        })
        self.logger.info(f"{action} {quantity:.6f} {coin} at {price:.2f}, Commission: {commission_fee:.2f}")

    def buy(self, coin: str, price: float, quantity: float):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
        trade_datetime = datetime.now()
        if self.cash >= total_cost:
            self.cash -= total_cost
            if coin in self.portfolio:
                current_entry = self.portfolio[coin]
                current_total_cost = current_entry['quantity'] * current_entry['average_entry_price']
                new_total_cost = current_total_cost + cost
                new_quantity = current_entry['quantity'] + quantity
                new_average_entry_price = new_total_cost / new_quantity
                self.portfolio[coin]['quantity'] = new_quantity
                self.portfolio[coin]['average_entry_price'] = new_average_entry_price
            else:
                self.portfolio[coin] = {
                    'quantity': quantity,
                    'average_entry_price': price
                }
            self.last_purchase_info[coin] = {
                'price': price,
                'quantity': quantity,
                'commission': commission_fee,
                'datetime': trade_datetime
            }
            # Round down quantity to 6 decimal places
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.is_live_mode:
                place_market_order(coin, rounded_quantity, 'BUY')
            self.log_trade('Buy', coin, price, rounded_quantity, trade_datetime)
        else:
            self.logger.warning(f"Not enough cash to complete the purchase for {coin}.")

    def sell(self, coin: str, price: float):
        quantity = self.portfolio.get(coin, {}).get('quantity', 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            profit = (price - purchase_price) * quantity - (purchase_info.get('commission', 0) + commission_fee)
            # Round down quantity to 6 decimal places
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.is_live_mode:
                place_market_order(coin, rounded_quantity, 'SELL')
            self.log_trade('Sell', coin, price, rounded_quantity, datetime.now(), profit)
            self.portfolio[coin]['quantity'] = 0
        else:
            self.logger.warning(f"No holdings to sell for {coin}.")

    def execute_strategy(self, coin: str, df_candles: pd.DataFrame):
        """
        Execute the strategy for a specific coin.

        :param coin: The trading pair, e.g., 'BTC-USD'.
        :param df_candles: DataFrame containing historical candle data for the coin.
        """
        actions = self.strategy.evaluate(coin, df_candles, self.portfolio, self.cash)
        if 'buy' in actions:
            buy_action = actions['buy']
            self.buy(buy_action['coin'], buy_action['price'], buy_action['quantity'])
        if 'sell' in actions:
            sell_action = actions['sell']
            self.sell(sell_action['coin'], sell_action['price'])