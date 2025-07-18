import yfinance as yf, pandas_ta as ta, pandas as pd, numpy as np

ticker = "BYD"
df = yf.download(ticker, period="500d")["Close"].dropna()
print("Last close =", df.iloc[-1])

sma50 = df.rolling(50).mean().iloc[-1]
rsi14 = ta.rsi(df, length=14).iloc[-1]

print("SMA-50 =", sma50)
print("RSI-14 =", rsi14)