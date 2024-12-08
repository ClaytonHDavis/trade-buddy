# trader.py
from config.config import Config
from datetime import datetime
import pandas as pd
from utils.logger import setup_logger
from trading.modes import Mode
from external.coinbase_portfolio import PortfolioManager
from external.coinbase_make_transactions import place_market_order  # Only needed for live mode

class Trader:
    def __init__(self, strategy, mode: Mode, portfolio_manager: PortfolioManager = None):
        self.logger = setup_logger()
        self.strategy = strategy
        self.mode = mode
        self.commission_rate = Config.COMMISSION_RATE
        self.trade_log = []
        self.last_purchase_info = {}

        if self.mode == Mode.LIVE:
            if portfolio_manager is None:
                raise ValueError("PortfolioManager must be provided in live mode.")
            self.portfolio_manager = portfolio_manager
            total_cash_balance = self.portfolio_manager.extract_total_cash_balance(self._fetch_portfolio_data())
            self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
            self.update_portfolio()
        else:
            self.cash = Config.NON_LIVE_START_CASH
            self.portfolio = {}  # {'coin': {'quantity': x, 'average_entry_price': y}}

    def _fetch_portfolio_data(self):
        portfolio_uuid = self.portfolio_manager.list_portfolio()
        return self.portfolio_manager.get_portfolio_breakdown(portfolio_uuid)

    def update_portfolio(self):
        if self.mode == Mode.LIVE:
            portfolio_data = self._fetch_portfolio_data()
            # Log the portfolio data for debugging
            #self.logger.debug(f"Fetched portfolio data: {portfolio_data}")
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
            # Extract the total cash balance using the configured percentage
            total_cash_balance = self.portfolio_manager.extract_total_cash_balance(portfolio_data)
            self.cash = total_cash_balance * Config.TRADING_CASH_PERCENTAGE
            self.logger.info(f"Portfolio updated: {self.portfolio}")
            self.logger.info(f"Last purchase info updated: {self.last_purchase_info}")
        else:
            # In paper or backtest mode, the portfolio is managed locally
            pass

    def calculate_total_portfolio_value(self, market_data: dict) -> float:
        if self.mode == Mode.LIVE:
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

    def log_trade(self, action: str, coin: str, price: float, quantity: float, trade_datetime, profit: float = 0):
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

    def buy(self, coin: str, price: float, quantity: float, trade_datetime):
        cost = price * quantity
        commission_fee = self.commission(cost)
        total_cost = cost + commission_fee
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
            # Round down quantity to 6 decimal places for live trading
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.mode == Mode.LIVE:
                place_market_order(coin, rounded_quantity, 'BUY')
            self.log_trade('Buy', coin, price, quantity, trade_datetime)
        else:
            self.logger.warning(f"Not enough cash to complete the purchase for {coin}.")

    def sell(self, coin: str, price: float, trade_datetime):
        quantity = self.portfolio.get(coin, {}).get('quantity', 0)
        if quantity > 0:
            revenue = price * quantity
            commission_fee = self.commission(revenue)
            total_revenue = revenue - commission_fee
            self.cash += total_revenue
            purchase_info = self.last_purchase_info.get(coin, {})
            purchase_price = purchase_info.get('price', 0)
            profit = (price - purchase_price) * quantity - (purchase_info.get('commission', 0) + commission_fee)
            # Round down quantity to 6 decimal places for live trading
            rounded_quantity = int(quantity * 1_000_000) / 1_000_000
            if self.mode == Mode.LIVE:
                place_market_order(coin, rounded_quantity, 'SELL')
            self.log_trade('Sell', coin, price, quantity, trade_datetime, profit)
            self.portfolio[coin]['quantity'] = 0
        else:
            self.logger.warning(f"No holdings to sell for {coin}.")

    
    def execute_strategy(self, coin: str, df_candles: pd.DataFrame):
        """Execute the strategy for a specific coin."""
        actions = self.strategy.evaluate(coin, df_candles, self.portfolio, self.cash,self.last_purchase_info)
        # Extract the trade datetime from the last candlestick
        trade_datetime = df_candles['time'].iloc[-1]
        if 'buy' in actions:
            buy_action = actions['buy']
            price = buy_action.get('price', df_candles['close'].iloc[-1])
            quantity = buy_action['quantity']
            self.buy(buy_action['coin'], price, quantity, trade_datetime)
        if 'sell' in actions:
            sell_action = actions['sell']
            price = sell_action.get('price', df_candles['close'].iloc[-1])
            self.sell(sell_action['coin'], price, trade_datetime)