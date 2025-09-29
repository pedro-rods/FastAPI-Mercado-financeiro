# app/services/yahoo.py
import yfinance as yf
import pandas as pd

def fetch_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"Nenhum dado retornado para {ticker}")
    df = df.rename(columns=str.lower)  # open, high, low, close, volume
    df = df.reset_index()  # coloca Date como coluna
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "open", "high", "low", "close", "volume"]]
