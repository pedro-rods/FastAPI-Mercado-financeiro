# tests/test_jobs.py
from app.jobs.health_check import run_health_check
from app.jobs.daily_indicators import run_daily_indicators
from sqlalchemy import select
from app import models

def test_health_check_job(db_session, monkeypatch):
    # monkeypatch yfinance para não bater na rede
    import yfinance as yf
    def _fake_download(*args, **kwargs):
        import pandas as pd
        from datetime import datetime
        return pd.DataFrame({"Close":[1.0]}, index=[datetime(2024,1,1)])
    monkeypatch.setattr(yf, "download", _fake_download)

    run_health_check(db_session)
    rows = db_session.execute(select(models.JobRun).where(models.JobRun.job_name=="health_check")).scalars().all()
    assert len(rows) == 1
    assert rows[0].status in ("ok","error")

def test_daily_indicators_job(db_session, patch_fetch_prices):
    run_daily_indicators(db_session, tickers=["FAKE.SA"])
    rows = db_session.execute(select(models.JobRun).where(models.JobRun.job_name=="daily_indicators")).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "ok"
