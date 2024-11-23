import yfinance as yf
import pandas as pd

def get_top_gainers():
    # Create a list of companies in S&P 500 for comparison
    sp500_symbols = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    
    stock_data = []

    # Loop through each symbol and get the price data
    for symbol in sp500_symbols:
        try:
            stock_info = yf.Ticker(symbol)
            # Get historical market data
            hist = stock_info.history(period='ytd')
            
            # Check if historical data is empty
            if hist.empty or len(hist) < 2:
                print(f"No historical data found for {symbol}. Skipping.")
                continue

            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            change_percentage = ((end_price - start_price) / start_price) * 100
            stock_data.append((symbol, change_percentage))
        
        except Exception as e:
            print(f"Could not retrieve data for {symbol}: {e}")

    # Create a DataFrame from the data collected
    df = pd.DataFrame(stock_data, columns=['Symbol', 'Change (%)'])
    
    # Get the top 50 gainers
    top_gainers = df.sort_values(by='Change (%)', ascending=False).head(50)
    
    # save to CSV
    top_gainers.to_csv('top_gainers.csv', index=False)

    return top_gainers

top_gainers = get_top_gainers()
print(top_gainers)