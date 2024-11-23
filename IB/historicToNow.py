import datetime
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('TSLA', 'SMART', 'USD')

dt = '20240801 00:00:00'
barsList = []

bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='5 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=False,
    keepUpToDate=True)

barsList.append(bars)
dt = bars[0].date
# print(bars[0])

# save to CSV file
allBars = [b for bars in reversed(barsList) for b in bars]
df = util.df(allBars)
df.to_csv(contract.symbol + '.csv', index=False)
print(df)