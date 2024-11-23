import pandas as pd

df = pd.read_csv('coinbase_candles_5min.csv')

# filter the data on productID = SHIB-USD
df = df[df['product_id'] == 'MATH-USD']

#renamd the column start to time
df = df.rename(columns={'start': 'time'})

# narrow columns down to just - Make sure your CSV file's columns match the indices of `datetime`, `open`, `high`, `low`, `close`, `volume`
df = df[['time', 'low', 'high', 'open', 'close', 'volume']]

# sort data by time ascending
df = df.sort_values(by='time', ascending=True)

# save to new csv file
df.to_csv('MATH-USD.csv', index=False)
