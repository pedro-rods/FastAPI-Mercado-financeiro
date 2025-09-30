# app/ui.py
from __future__ import annotations
import io
import base64
from typing import List, Dict, Any
from datetime import datetime
import json
from fastapi.responses import HTMLResponse
from app.strategies import validate_and_normalize_params

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app import models
from app.backtest_engine import run_backtest as engine_run

router = APIRouter(tags=["UI"])

# ---------- helpers ----------

def _fig_to_data_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{data}"

def _to_equity_series(points: List[Dict[str, Any]]) -> pd.Series:
    if not points:
        return pd.Series(dtype=float)
    idx = pd.to_datetime([p["date"] for p in points])
    vals = [p["equity"] for p in points]
    return pd.Series(vals, index=idx).sort_index()

def _compute_drawdown(equity: pd.Series) -> pd.Series:
    if equity.empty:
        return equity
    return equity / equity.cummax() - 1.0

def _fetch_prices_yf(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        ticker, start=start, end=end, interval="1d",
        auto_adjust=True, progress=False, group_by="column"
    )
    if df is None or df.empty:
        return pd.DataFrame()
    # normaliza colunas
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[-1]).lower() for c in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]
    keep = ["open","high","low","close","volume"]
    for k in keep:
        if k not in df.columns:
            df[k] = np.nan
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date"] + keep].dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
    return df

# ---------- charts ----------

def _chart_price_with_signals(prices: pd.DataFrame, trades: List[Dict[str, Any]]) -> str:
    fig = plt.figure()
    if not prices.empty:
        plt.plot(prices["date"], prices["close"], label="Fechamento")
    # trades: marcadores nas datas de fechamento do trade
    buys  = [t for t in (trades or []) if (t.get("side","BUY").upper() == "BUY")]
    sells = [t for t in (trades or []) if (t.get("side","BUY").upper() == "SELL")]
    if buys:
        bdates = pd.to_datetime([t["date"] for t in buys])
        bprices = [t.get("price", np.nan) for t in buys]
        plt.scatter(bdates, bprices, marker="^", label="BUY")
    if sells:
        sdates = pd.to_datetime([t["date"] for t in sells])
        sprices = [t.get("price", np.nan) for t in sells]
        plt.scatter(sdates, sprices, marker="v", label="SELL")
    plt.title("Preço com Sinais (fechamento de trades)")
    plt.xlabel("Data"); plt.ylabel("Preço")
    plt.legend()
    return _fig_to_data_uri(fig)

def _chart_equity(equity: pd.Series) -> str:
    fig = plt.figure()
    if not equity.empty:
        plt.plot(equity.index, equity.values, label="Equity")
        plt.legend()
    plt.title("Curva de Equity"); plt.xlabel("Data"); plt.ylabel("Equity")
    return _fig_to_data_uri(fig)

def _chart_returns_hist(equity: pd.Series) -> str:
    fig = plt.figure()
    if not equity.empty and len(equity) > 1:
        rets = equity.pct_change().dropna()
        if len(rets):
            plt.hist(rets.values, bins=30)
    plt.title("Distribuição de Retornos Diários")
    plt.xlabel("Retorno"); plt.ylabel("Frequência")
    return _fig_to_data_uri(fig)

def _chart_drawdown(equity: pd.Series) -> str:
    fig = plt.figure()
    dd = _compute_drawdown(equity)
    if not dd.empty:
        plt.plot(dd.index, dd.values, label="Drawdown")
        plt.legend()
    plt.title("Drawdown ao longo do tempo")
    plt.xlabel("Data"); plt.ylabel("Drawdown")
    return _fig_to_data_uri(fig)

# ---------- page ----------
@router.get(
    "/ui/backtests/{backtest_id}",
    summary="Visualização rápida do backtest (HTML simples)",
    response_class=HTMLResponse,
)
def ui_backtest(backtest_id: int, db: Session = Depends(get_db)):
    bt = db.query(models.Backtest).filter(models.Backtest.id == backtest_id).first()
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest não encontrado")

    # --- parse seguro do JSON do BD ---
    raw = getattr(bt, "strategy_params_json", None)
    if isinstance(raw, dict):
        params = dict(raw)
    elif isinstance(raw, str) and raw.strip():
        try:
            params = json.loads(raw)
        except Exception:
            params = {}
    else:
        params = {}

    # --- aliases mínimos para compatibilidade retroativa ---
    if bt.strategy_type == "momentum":
        if "threshold_pct" in params:
            params["thresh"] = params.pop("threshold_pct")
        if "threshold" in params and "thresh" not in params:
            params["thresh"] = params.pop("threshold")

    # --- normalização oficial (filtra chaves e corrige tipos) ---
    params = validate_and_normalize_params(bt.strategy_type, params)

    # --- roda o backtest com params normalizados ---
    res = engine_run(
        ticker=bt.ticker,
        start=bt.start_date.strftime("%Y-%m-%d"),
        end=bt.end_date.strftime("%Y-%m-%d"),
        strategy_type=bt.strategy_type,
        strategy_params=params,
        initial_cash=bt.initial_cash,
        commission=float(bt.commission or 0.0),
    )

    equity = _to_equity_series(res.get("equity_curve", []))
    trades = res.get("trades", []) or []

    # preços para o gráfico de preço+sinais
    prices = _fetch_prices_yf(
        bt.ticker,
        bt.start_date.strftime("%Y-%m-%d"),
        bt.end_date.strftime("%Y-%m-%d"),
    )

    img_price   = _chart_price_with_signals(prices, trades)
    img_equity  = _chart_equity(equity)
    img_hist    = _chart_returns_hist(equity)
    img_drawdown= _chart_drawdown(equity)

    m = res.get("metrics", {})
    # HTML super simples (sem template engine)
    html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <title>Backtest #{backtest_id} — {bt.ticker}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    h1 {{ margin-bottom: 4px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 24px; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; }}
    img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
    .metrics span {{ display: inline-block; margin-right: 12px; }}
    @media (min-width: 1000px) {{
      .grid {{ grid-template-columns: 1fr 1fr; }}
    }}
  </style>
</head>
<body>
  <h1>Backtest #{backtest_id} — {bt.ticker}</h1>
  <div class="meta">
    Período: {bt.start_date.date()} → {bt.end_date.date()} |
    Estratégia: <b>{bt.strategy_type}</b> |
    Caixa inicial: {bt.initial_cash:,.2f} | Comissão: {bt.commission or 0:.4f}
  </div>

  <div class="metrics">
    <span><b>Total Return:</b> {m.get('total_return', 0):.6f}</span>
    <span><b>Sharpe:</b> {m.get('sharpe', 0):.4f}</span>
    <span><b>Max DD:</b> {m.get('max_drawdown', 0):.4f}</span>
    <span><b>Win Rate:</b> {m.get('win_rate', None) if m.get('win_rate') is not None else '-'}</span>
    <span><b>Avg Trade Ret.:</b> {m.get('avg_trade_return', None) if m.get('avg_trade_return') is not None else '-'}</span>
  </div>

  <div class="grid">
    <div class="card">
      <h3>Preço + Sinais</h3>
      <img src="{img_price}" alt="price chart" />
    </div>
    <div class="card">
      <h3>Curva de Equity</h3>
      <img src="{img_equity}" alt="equity curve" />
    </div>
    <div class="card">
      <h3>Distribuição de Retornos</h3>
      <img src="{img_hist}" alt="returns histogram" />
    </div>
    <div class="card">
      <h3>Drawdown</h3>
      <img src="{img_drawdown}" alt="drawdown" />
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html) 
