# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime
import json

from app import models

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
