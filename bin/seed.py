# bin/seed.py
import os
import json
from sqlalchemy import select
from app.db import SessionLocal
from app import models

DEFAULT_TICKERS = [
    {"ticker": "PETR4.SA", "name": "Petrobras PN", "exchange": "B3", "currency": "BRL"},
    {"ticker": "VALE3.SA", "name": "Vale ON", "exchange": "B3", "currency": "BRL"},
    {"ticker": "ITUB4.SA", "name": "Itaú Unibanco PN", "exchange": "B3", "currency": "BRL"},
    {"ticker": "AAPL", "name": "Apple Inc", "exchange": "NASDAQ", "currency": "USD"},
]

def upsert_symbols(db, rows):
    for r in rows:
        exists = db.execute(select(models.Symbol).where(models.Symbol.ticker == r["ticker"])).scalar_one_or_none()
        if not exists:
            s = models.Symbol(
                ticker=r["ticker"],
                name=r.get("name"),
                exchange=r.get("exchange"),
                currency=r.get("currency"),
            )
            db.add(s)
    db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        upsert_symbols(db, DEFAULT_TICKERS)
        print(f"Seed ok: {len(DEFAULT_TICKERS)} tickers.")
    finally:
        db.close()
