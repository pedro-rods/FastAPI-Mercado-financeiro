# tests/test_backtest_engine.py
from app.backtest_engine import run_backtest

def test_engine_runs_with_fake_data(monkeypatch, fake_prices_df):
    # monkeypatch direto no engine para usar nosso DF fake
    from app import services
    def _fake_fetch_prices(ticker, start, end):
        return fake_prices_df.copy()
    monkeypatch.setattr(services.yahoo, "fetch_prices", _fake_fetch_prices)

    res = run_backtest(
        ticker="FAKE3.SA",
        start="2021-01-01",
        end="2021-12-31",
        strategy_type="sma_cross",
        strategy_params={"fast": 5, "slow": 20, "risk_pct": 0.01, "stop_method": "atr"},
        initial_cash=100000.0,
        commission=0.001,
    )
    assert "metrics" in res
    assert "equity_curve" in res
    assert isinstance(res["metrics"]["total_return"], float)
