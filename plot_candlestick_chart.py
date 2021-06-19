# Plot Candlestick Chart

import requests
import json
import arrow
import pandas as pd
import mplfinance as mpf

isin = "US67066G1040"  # NVIDIA

mic = "XMUN"

X1 = "d1"  # Specify the type of data you want: m1, h1, or d1

TOKEN_KEY = "insert_your_token_here"  # please adapt to your token !

authorization = f"Bearer {TOKEN_KEY}"

request = requests.get(f"https://paper.lemon.markets/rest/v1/trading-venues/{mic}/instruments/{isin}/data/ohlc/{X1}/",
                       headers={"Authorization": authorization})

print(request)
parsed = json.loads(request.content)
print(json.dumps(parsed, indent=4, sort_keys=True))
length = len(parsed['results'])

column_names = ["Date", "Open", "High", "Low", "Close", "Volume"]
df = pd.DataFrame(columns=column_names, index=range(length))

for i in range(len(parsed['results'])):
    date_p = arrow.get(parsed['results'][i]['t']).datetime
    df.loc[length - 1 - i]["Date"] = date_p
    df.loc[length - 1 - i]["Open"] = parsed['results'][i]['o']
    df.loc[length - 1 - i]["High"] = parsed['results'][i]['h']
    df.loc[length - 1 - i]["Low"] = parsed['results'][i]['l']
    df.loc[length - 1 - i]["Close"] = parsed['results'][i]['c']
    df.loc[length - 1 - i]["Volume"] = 0

df.Date = pd.to_datetime(df.Date)
df.Open = pd.to_numeric(df.Open)
df.High = pd.to_numeric(df.High)
df.Low = pd.to_numeric(df.Low)
df.Close = pd.to_numeric(df.Close)
df.Volume = pd.to_numeric(df.Volume)
df = df.set_index('Date')
print("df =", df)
print("df.info() =", df.info())
mpf.plot(df, type='candle', tight_layout=False, style="yahoo")
mpf.show()


