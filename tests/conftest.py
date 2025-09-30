# tests/conftest.py
import os
import json
import math
import pytest
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("BT_DEBUG", "0")  # logs silenciosos nos testes

# --- app imports
from app.main import app
from app.db import Base, get_db
from app import models

@pytest.fixture(scope="session")
def engine_sqlite():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine_sqlite):
    TestingSessionLocal = sessionmaker(bind=engine_sqlite, autoflush=False, autocommit=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    # Injeta sessão de teste no FastAPI
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def fake_prices_df():
    # Série simples e estável para backtest: 60 barras
    start = datetime(2021, 1, 1)
    rows = []
    price = 10.0
    for i in range(60):
        dt = start + timedelta(days=i+1)
        # “mercado” com leve tendência
        open_ = price
        high = price * 1.01
        low  = price * 0.99
        close = price * (1.0 + (0.002 if i > 20 else -0.001))  # cai no início, sobe depois
        vol = 1_000_000
        rows.append([dt, open_, high, low, close, vol])
        price = close
    return pd.DataFrame(rows, columns=["date","open","high","low","close","volume"])

@pytest.fixture
def patch_fetch_prices(monkeypatch, fake_prices_df):
    from app.services import yahoo as yfmod
    def _fake_fetch_prices(ticker, start, end, interval="1d"):
        # ignora argumentos e retorna a série fake
        return fake_prices_df.copy()
    monkeypatch.setattr(yfmod, "fetch_prices", _fake_fetch_prices)
    return True
