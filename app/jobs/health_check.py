# app/jobs/health_check.py
from __future__ import annotations
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.crud import jobrun_start, jobrun_finish
import yfinance as yf

def run_health_check(db: Session):
    jr = jobrun_start(db, "health_check")
    try:
        # DB check
        t0 = time.time()
        db.execute(text("SELECT 1"))
        db_latency_ms = (time.time() - t0) * 1000

        # Yahoo latency
        t1 = time.time()
        _ = yf.download("AAPL", period="1d", interval="1d", progress=False, auto_adjust=True)
        ylat_ms = (time.time() - t1) * 1000

        msg = f"DB ok ({db_latency_ms:.1f} ms); Yahoo ok ({ylat_ms:.1f} ms)"
        jobrun_finish(db, jr.id, status="ok", message=msg)
    except Exception as e:
        jobrun_finish(db, jr.id, status="error", message=str(e))
        raise
