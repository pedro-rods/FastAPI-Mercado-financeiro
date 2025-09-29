# app/crud_prices.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models

def ensure_symbol(db: Session, ticker: str):
    sym = db.execute(select(models.Symbol).where(models.Symbol.ticker == ticker)).scalar_one_or_none()
    if sym:
        return sym
    sym = models.Symbol(ticker=ticker)
    db.add(sym)
    db.commit()
    db.refresh(sym)
    return sym

def bulk_upsert_prices(db: Session, symbol_id: int, df):
    for _, row in df.iterrows():
        obj = models.Price(
            symbol_id=symbol_id,
            date=row["date"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
        )
        db.merge(obj)  # merge = upsert-like
    db.commit()
