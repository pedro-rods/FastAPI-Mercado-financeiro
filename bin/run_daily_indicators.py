from app.db import SessionLocal
from app.jobs.daily_indicators import run_daily_indicators

if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_daily_indicators(db, tickers=["PETR4.SA","VALE3.SA","AAPL"])
    finally:
        db.close()
