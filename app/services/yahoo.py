# app/services/yahoo.py
import yfinance as yf
import pandas as pd

OHLCV = {"open", "high", "low", "close", "volume"}

def _flatten_multiindex_columns(cols) -> list[str]:
    """
    Achata colunas MultiIndex e tenta extrair o NOME OHLCV (open/high/low/close/volume),
    independentemente da ordem dos níveis (ex.: ('PETR4.SA','Open') ou ('Open','PETR4.SA')).
    Retorna lista de nomes simples (em minúsculas).
    """
    flat = []
    for c in cols:
        if isinstance(c, tuple):
            parts = [str(p).strip().lower() for p in c if p is not None]
            # tenta achar o primeiro token que esteja em OHLCV
            ohlcv_tokens = [p for p in parts if p in OHLCV]
            if ohlcv_tokens:
                flat.append(ohlcv_tokens[0])
            else:
                # fallback: junta tudo, mas manteremos só o que for OHLCV depois
                flat.append("_".join(parts))
        else:
            flat.append(str(c).strip().lower())
    return flat

def fetch_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,   
        progress=False,
        group_by="column",  
    )
    if df is None or df.empty:
        raise ValueError(f"Nenhum dado retornado para {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        flat = _flatten_multiindex_columns(df.columns)
        df.columns = flat
    else:
        df.columns = [str(c).strip().lower() for c in df.columns]

    if "volume" not in df.columns:
        df["volume"] = 0.0

    missing = [c for c in ["open", "high", "low", "close", "volume"] if c not in df.columns]
    if missing:
        raise ValueError(f"Coluna(s) {missing} ausentes para {ticker}. Colunas recebidas: {list(df.columns)}")

    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])

    df = df[["date", "open", "high", "low", "close", "volume"]].dropna(subset=["close"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
