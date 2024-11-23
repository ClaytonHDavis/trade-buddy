from ib_insync import *
import pandas as pd
from datetime import datetime

# util.startLoop()  # uncomment this line when in a notebook

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

currencies = ['EURUSD', 'GBPUSD', 'USDJPY']
tickers = {}

# Request market depth for each currency
for currency in currencies:
    contract = Forex(currency)
    tickers[currency] = ib.reqMktDepth(contract)

# Initialize an empty DataFrame
df = pd.DataFrame(columns=['Currency', 'Ticker', 'Time', 'BidMin', 'BidMax', 'AskMin', 'AskMax'])

while ib.sleep(5):
    for currency, ticker in tickers.items():
        bid_prices = [d.price for d in ticker.domBids]
        ask_prices = [d.price for d in ticker.domAsks]
        
        if bid_prices and ask_prices:
            bid_min = min(bid_prices)
            bid_max = max(bid_prices)
            ask_min = min(ask_prices)
            ask_max = max(ask_prices)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Append new data to the DataFrame
            df = df._append({
                'Currency': currency,
                'Ticker': ticker.contract.symbol,
                'Time': current_time,
                'BidMin': bid_min,
                'BidMax': bid_max,
                'AskMin': ask_min,
                'AskMax': ask_max
            }, ignore_index=True)
            
            # Save the DataFrame to a CSV file
            df.to_csv('market_data.csv', index=False)
            
            # Get current min and max market price for the book as of today
            today = datetime.now().strftime('%Y-%m-%d')
            df['Date'] = pd.to_datetime(df['Time']).dt.strftime('%Y-%m-%d')
            today_data = df[(df['Date'] == today) & (df['Currency'] == currency)]
            
            if not today_data.empty:
                current_bid_min = today_data['BidMin'].min()
                current_bid_max = today_data['BidMax'].max()
                current_ask_min = today_data['AskMin'].min()
                current_ask_max = today_data['AskMax'].max()
                
                print(f"{currency} - Today's BidMin: {current_bid_min}, BidMax: {current_bid_max}, AskMin: {current_ask_min}, AskMax: {current_ask_max}")
            else:
                print(f"{currency} - No data for today.")
        
        print(f"{currency} - Bids: {bid_prices}, Asks: {ask_prices}")