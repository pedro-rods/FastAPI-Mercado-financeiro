# tests/test_backtests_endpoints.py
import json

def test_run_backtest_sma_cross(client, patch_fetch_prices):
    payload = {
        "ticker": "FAKE.SA",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "strategy_type": "sma_cross",
        "strategy_params": {"fast": 5, "slow": 20, "risk_pct": 0.01, "stop_method": "atr"},
        "initial_cash": 100000,
        "commission": 0.001,
        "timeframe": "1d"
    }
    r = client.post("/backtests/run", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data and "status" in data
    bt_id = data["id"]

    r2 = client.get(f"/backtests/{bt_id}/results")
    assert r2.status_code == 200
    res = r2.json()
    assert res["backtest_id"] == bt_id
    assert "metrics" in res and "equity_curve" in res and "trades" in res

def test_list_backtests(client, patch_fetch_prices):
    # cria um
    payload = {
        "ticker": "FAKE2.SA",
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "strategy_type": "donchian",
        "strategy_params": {"n": 10, "risk_pct": 0.01, "stop_method": "atr"},
        "initial_cash": 100000,
        "commission": 0.0,
        "timeframe": "1d"
    }
    r = client.post("/backtests/run", json=payload)
    assert r.status_code == 200
    # lista
    r2 = client.get("/backtests?limit=10&offset=0")
    assert r2.status_code == 200
    arr = r2.json()
    assert isinstance(arr, list)
    assert len(arr) >= 1
