# Plot Candlestick Chart

import requests
import json
import arrow
import pandas as pd
import mplfinance as mpf
from datetime import timedelta
import datetime
import time

DELTA_OF_31_DAYS = timedelta(days=31)

isin = "US67066G1040"  # NVIDIA

mic = "XMUN"

time_step = "d1"  # Specify the type of data you want: m1, h1, or d1

TOKEN_KEY = "insert_your_token_here"  # please adapt to your token !

authorization = f"Bearer {TOKEN_KEY}"
datetime_today = datetime.datetime.today()
start_time = datetime_today - DELTA_OF_31_DAYS

# Do no request old data which are not available
if start_time < datetime.datetime(2021, 8, 1, 0, 0):
    start_time = datetime.datetime(2021, 8, 1, 0, 0)

start_time_str = str(int((time.mktime(start_time.timetuple())) * 1000))

end_time = datetime_today

# Do no request  data from the future
if end_time > datetime_today:
    end_time = datetime_today

end_time_str = str(int((time.mktime(end_time.timetuple())) * 1000))
request = requests.get(f"https://paper-data.lemon.markets/v1/ohlc/{time_step}/?mic={mic}&isin={isin}&to={end_time_str}&from={start_time_str}&epoch=True",
                       headers={"Authorization": authorization})
print(request)
parsed = json.loads(request.content)
print(json.dumps(parsed, indent=4, sort_keys=True))
length = len(parsed['results'])

column_names = ["Date", "Open", "High", "Low", "Close", "Volume"]
df = pd.DataFrame(columns=column_names, index=range(length))

for i in range(len(parsed['results'])):
    df.loc[i]["Date"] = arrow.get(parsed['results'][i]['t']).to('local').datetime
    df.loc[i]["Open"] = parsed['results'][i]['o']
    df.loc[i]["High"] = parsed['results'][i]['h']
    df.loc[i]["Low"] = parsed['results'][i]['l']
    df.loc[i]["Close"] = parsed['results'][i]['c']
    df.loc[i]["Volume"] = 0
df.Date = pd.to_datetime(df.Date)
df.Open = pd.to_numeric(df.Open)
df.High = pd.to_numeric(df.High)
df.Low = pd.to_numeric(df.Low)
df.Close = pd.to_numeric(df.Close)
df.Volume = pd.to_numeric(df.Volume)
df = df.set_index('Date')

print("df =", df)
print("df.info() =", df.info())
mpf.plot(df, type='candle', title="Stock: " + isin, tight_layout=False, style="yahoo")
mpf.show()
