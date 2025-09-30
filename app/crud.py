# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime
from app import models
import json
import pandas as pd

def create_backtest_record(
    db: Session,
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    strategy_type: str,
    strategy_params: dict | None,
    initial_cash: float,
    commission: float,
    timeframe: str | None,
) -> models.Backtest:
    bt = models.Backtest(
        ticker=ticker,
        start_date=datetime.fromisoformat(start_date),
        end_date=datetime.fromisoformat(end_date),
        strategy_type=strategy_type,
        strategy_params_json=json.dumps(strategy_params or {}),
        initial_cash=initial_cash,
        commission=commission,
        timeframe=timeframe,
        status="created",  # por enquanto "created"; atualizar depois
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)
    return bt

def list_backtests(
    db: Session,
    *,
    ticker: str | None,
    strategy_type: str | None,
    limit: int,
    offset: int,
) -> list[models.Backtest]:
    stmt = select(models.Backtest).order_by(desc(models.Backtest.created_at))
    if ticker:
        stmt = stmt.where(models.Backtest.ticker == ticker)
    if strategy_type:
        stmt = stmt.where(models.Backtest.strategy_type == strategy_type)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())

def get_backtest(db: Session, backtest_id: int) -> models.Backtest | None:
    return db.get(models.Backtest, backtest_id)
def set_backtest_status(db: Session, backtest_id: int, status: str):
    bt = db.get(models.Backtest, backtest_id)
    if not bt:
        return
    bt.status = status
    db.commit()

def save_metrics(db: Session, backtest_id: int, metrics: dict):
    m = models.Metric(
        backtest_id=backtest_id,
        total_return=metrics.get("total_return", 0.0),
        sharpe=metrics.get("sharpe", 0.0),
        max_drawdown=metrics.get("max_drawdown", 0.0),
        win_rate=metrics.get("win_rate"),
        avg_trade_return=metrics.get("avg_trade_return"),
    )
    db.add(m)
    db.commit()

def save_trades(db: Session, backtest_id: int, trades: list[dict]):
    for t in trades:
        db.add(models.Trade(
            backtest_id=backtest_id,
            date=pd.to_datetime(t["date"]).to_pydatetime(),
            side=t["side"],
            price=t["price"],
            size=t["size"],
            commission=t.get("commission", 0.0),
            pnl=t.get("pnl", 0.0),
        ))
    db.commit()

def save_daily_positions(db: Session, backtest_id: int, dps: list[dict]):
    for d in dps:
        db.add(models.DailyPosition(
            backtest_id=backtest_id,
            date=pd.to_datetime(d["date"]).to_pydatetime(),
            position_size=d["position_size"],
            cash=d["cash"],
            equity=d["equity"],
            drawdown=d["drawdown"],
        ))
    db.commit()

def get_results(db: Session, backtest_id: int):
    bt = db.get(models.Backtest, backtest_id)
    if not bt:
        return None
    metrics = db.execute(select(models.Metric).where(models.Metric.backtest_id == backtest_id)).scalars().all()
    trades = db.execute(select(models.Trade).where(models.Trade.backtest_id == backtest_id).order_by(models.Trade.date)).scalars().all()
    dps = db.execute(select(models.DailyPosition).where(models.DailyPosition.backtest_id == backtest_id).order_by(models.DailyPosition.date)).scalars().all()

    return {
        "backtest": {
            "id": bt.id,
            "ticker": bt.ticker,
            "start_date": bt.start_date.isoformat(),
            "end_date": bt.end_date.isoformat(),
            "strategy_type": bt.strategy_type,
            "status": bt.status,
        },
        "metrics": {
            "total_return": metrics[-1].total_return if metrics else 0.0,
            "sharpe": metrics[-1].sharpe if metrics else 0.0,
            "max_drawdown": metrics[-1].max_drawdown if metrics else 0.0,
            "win_rate": metrics[-1].win_rate if metrics else None,
            "avg_trade_return": metrics[-1].avg_trade_return if metrics else None,
        },
        "trades": [{
            "date": t.date.isoformat(), "side": t.side, "price": t.price, "size": t.size,
            "commission": t.commission, "pnl": t.pnl
        } for t in trades],
        "daily_positions": [{
            "date": d.date.isoformat(), "position_size": d.position_size, "cash": d.cash,
            "equity": d.equity, "drawdown": d.drawdown
        } for d in dps],
        "equity_curve": [{"date": d.date.isoformat(), "equity": d.equity} for d in dps],
    }

def jobrun_start(db: Session, job_name: str, message: str | None = None) -> models.JobRun:
    jr = models.JobRun(job_name=job_name, status="started", message=message or "")
    db.add(jr)
    db.commit()
    db.refresh(jr)
    return jr

def jobrun_finish(db: Session, jr_id: int, status: str, message: str | None = None):
    jr = db.query(models.JobRun).filter(models.JobRun.id == jr_id).first()
    if not jr:
        return
    jr.status = status
    jr.finished_at = datetime.utcnow()
    if message:
        jr.message = (jr.message or "") + ("\n" if jr.message else "") + message
    db.commit()