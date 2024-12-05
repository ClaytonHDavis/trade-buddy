
import time
import pandas as pd
from data.data_fetcher import DataFetcher
from data.data_utils import save_market_data_to_csv
from trading.trader import LiveTrader
from strategies.probabilistic_strategy import ProbabilisticStrategy
from config.config import Config
from utils.logger import setup_logger
from external.coinbase_portfolio import PortfolioManager  # Ensure correct import

def main_trading_logic(coins, is_live_mode):
    logger = setup_logger()
    portfolio_manager = PortfolioManager()
    data_fetcher = DataFetcher()

    # Initialize your ProbabilisticStrategy with parameters from Config
    strategy = ProbabilisticStrategy(
        price_move=Config.PRICE_MOVE,
        profit_target=Config.PROFIT_TARGET,
        look_back=Config.LOOK_BACK,
        drop_threshold=Config.DROP_THRESHOLD
    )

    trader = LiveTrader(
        portfolio_manager=portfolio_manager,
        strategy=strategy,
        is_live_mode=is_live_mode
    )

    # Initialize cumulative data for all coins
    cumulative_data = {}
    for coin in coins:
        df = data_fetcher.get_bar_data(coin, 'FIVE_MINUTE', Config.DATA_FETCH_LIMIT).copy()
        if not df.empty:
            cumulative_data[coin] = df
            save_market_data_to_csv(df, coin)
        else:
            logger.warning(f"No initial data for {coin}")
            cumulative_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

    # Start the trading loop
    while True:
        try:
            market_data = {}
            for coin in coins:
                df_new = data_fetcher.get_bar_data(coin, 'FIVE_MINUTE', limit=1)
                if not df_new.empty:
                    df_new = df_new.sort_values(by='time').reset_index(drop=True)
                    last_time = cumulative_data[coin]['time'].max() if not cumulative_data[coin].empty else None
                    new_time = df_new['time'].iloc[0]
                    if last_time is None or new_time > last_time:
                        cumulative_data[coin] = pd.concat([cumulative_data[coin], df_new], ignore_index=True)
                        cumulative_data[coin].drop_duplicates(subset='time', inplace=True)
                        cumulative_data[coin].sort_values(by='time', inplace=True, ignore_index=True)
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        logger.info(f"Appended new data for {coin}")
                    elif new_time == last_time:
                        cumulative_data[coin].iloc[-1] = df_new.iloc[0]
                        save_market_data_to_csv(cumulative_data[coin], coin)
                        logger.info(f"Replaced last candle for {coin}")
                    market_data[coin] = cumulative_data[coin].copy()
                else:
                    logger.warning(f"No new data for {coin}.")
                    if not cumulative_data[coin].empty:
                        market_data[coin] = cumulative_data[coin].copy()
                        logger.info(f"Using last known data for {coin}.")
                    else:
                        logger.warning(f"No historical data available for {coin}. Skipping.")
            
            # Execute strategy for each coin
            for coin in coins:
                if not cumulative_data[coin].empty:
                    trader.execute_strategy(coin, cumulative_data[coin])
            
            # Calculate portfolio value and log trades
            trader.calculate_total_portfolio_value(market_data)
            trader.save_trade_log_to_csv()
            
            # Sleep until next iteration (e.g., 60 seconds)
            time.sleep(60)
        
        except Exception as e:
            logger.error("Exception in main trading logic:")
            logger.error(e)
            time.sleep(60)

if __name__ == '__main__':
    # Define coins to trade and manage
    coins = ['DIA-USD', 'MATH-USD', 'ORN-USD','WELL-USD','KARRAT-USD']  # Example list; adjust as needed
    main_trading_logic(coins, is_live_mode=False)  # Toggle 'is_live_mode' as needed