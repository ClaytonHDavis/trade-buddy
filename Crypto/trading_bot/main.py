# main.py
import time
import pandas as pd
from data.data_fetcher import DataFetcher
from data.data_utils import save_market_data_to_csv
from trading.trader import Trader  # Renamed from LiveTrader to Trader
from strategies.probabilistic_strategy import ProbabilisticStrategy
from config.config import Config
from utils.logger import setup_logger
from data.data_historical import fetch_data_from_db
from trading.modes import Mode
from external.coinbase_portfolio import PortfolioManager  # Ensure correct import

def main_trading_logic(coins, mode):
    logger = setup_logger()
    data_fetcher = DataFetcher(mode)

    # Initialize your ProbabilisticStrategy with parameters from Config
    strategy = ProbabilisticStrategy(
        price_move=Config.PRICE_MOVE,
        profit_target=Config.PROFIT_TARGET,
        look_back=Config.LOOK_BACK,
        drop_threshold=Config.DROP_THRESHOLD
    )

    # Initialize Trader with the appropriate mode
    if mode == Mode.LIVE:
        portfolio_manager = PortfolioManager()
        trader = Trader(strategy=strategy, mode=mode, portfolio_manager=portfolio_manager)
    else:
        trader = Trader(strategy=strategy, mode=mode)

    if mode == Mode.BACKTEST:
        # Fetch all historical data for backtesting
        historical_data = {}
        for coin in coins:
            df = fetch_data_from_db(coin)
            if not df.empty:
                # Ensure 'start' column is renamed to 'time' if necessary
                df = df.rename(columns={'start': 'time'}).sort_values('time').reset_index(drop=True)
                historical_data[coin] = df
                save_market_data_to_csv(df, coin)  # Save data for analysis if needed
            else:
                logger.warning(f"No historical data found for {coin}")
                historical_data[coin] = pd.DataFrame(columns=['time', 'low', 'high', 'open', 'close', 'volume'])

        # Determine the common time range across all coins
        start_times = [df['time'].min() for df in historical_data.values() if not df.empty]
        end_times = [df['time'].max() for df in historical_data.values() if not df.empty]
        if not start_times or not end_times:
            logger.error("No historical data available for backtesting.")
            return

        global_start = max(start_times)
        global_end = min(end_times)

        # Create a common timeline
        time_index = pd.date_range(start=global_start, end=global_end, freq='5min')  # Adjust frequency as needed

        # Run the backtest
        for current_time in time_index:
            market_data = {}
            for coin in coins:
                # Get data up to current_time for this coin
                df_coin = historical_data[coin]
                df_current = df_coin[df_coin['time'] <= current_time]
                if not df_current.empty:
                    print(df_current)
                    # Pass the data up to the current time to the strategy
                    print(coin)
                    trader.execute_strategy(coin, df_current)  ## INVESTIGATE THIS
                    # For portfolio value calculation
                    market_data[coin] = df_current
            # Calculate portfolio value at current time
            trader.calculate_total_portfolio_value(market_data)
            # Log current time if desired
            logger.info(f"Backtest at time {current_time}")

        # After backtest, save trade log
        trader.save_trade_log_to_csv()

    else:
        # Live or Paper Trading Mode
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
                        print(market_data[coin])
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

                if mode == Mode.LIVE:
                    logger.info("LIVE!!!")  

                # Sleep until next iteration (e.g., 60 seconds)
                time.sleep(60)
            except KeyError as e:
                logger.error(f"KeyError: The key {e} was not found in a dictionary.")
                logger.exception("Traceback:")
                time.sleep(60)
            except Exception as e:
                logger.exception("Exception occurred in main trading logic")
                time.sleep(60)

if __name__ == '__main__':
    # Define coins to trade and manage
    coins = ['DIA-USD', 'MATH-USD', 'ORN-USD', 'WELL-USD', 'KARRAT-USD']  # Adjust as needed
    mode = Mode.BACKTEST  # Change to Mode.LIVE or Mode.PAPER as needed
    main_trading_logic(coins, mode)