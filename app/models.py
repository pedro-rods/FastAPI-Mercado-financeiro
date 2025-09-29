# app/models.py
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, DateTime, Float, ForeignKey,
    UniqueConstraint, Index, Text
)
class Symbol(Base):
    __tablename__ = "symbols"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(40), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Price(Base):
    __tablename__ = "prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("symbol_id", "date", name="uq_prices_symbol_date"),
        Index("ix_prices_symbol_date", "symbol_id", "date"),
    )

__table_args__ = (
        UniqueConstraint("symbol_id", "date", name="uq_prices_symbol_date"),
        Index("ix_prices_symbol_date", "symbol_id", "date"),
    )

class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    name: Mapped[str] = mapped_column(String(60))
    value: Mapped[float] = mapped_column(Float)
    params_hash: Mapped[str] = mapped_column(String(64))  # ex.: sha256 truncado

    __table_args__ = (
        UniqueConstraint("symbol_id", "date", "name", "params_hash", name="uq_indicators_unique_row"),
        Index("ix_indicators_symbol_date", "symbol_id", "date"),
    )

class Backtest(Base):
    __tablename__ = "backtests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticker: Mapped[str] = mapped_column(String(40), index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    strategy_type: Mapped[str] = mapped_column(String(40), index=True)

    strategy_params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_cash: Mapped[float] = mapped_column(Float, default=100000.0)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)

    # Campo extra que incluímos no projeto (ok manter):
    timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)

class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtests.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    side: Mapped[str] = mapped_column(String(4))  # "BUY" / "SELL"
    price: Mapped[float] = mapped_column(Float)
    size: Mapped[float] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)

class DailyPosition(Base):
    __tablename__ = "daily_positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtests.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    position_size: Mapped[float] = mapped_column(Float)
    cash: Mapped[float] = mapped_column(Float)
    equity: Mapped[float] = mapped_column(Float)      # curva de evolução da carteira
    drawdown: Mapped[float] = mapped_column(Float)    # queda máxima relativa ao pico (valor diário)

    __table_args__ = (
        Index("ix_daily_positions_bt_date", "backtest_id", "date"),
    )

class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtests.id", ondelete="CASCADE"), index=True)
    total_return: Mapped[float] = mapped_column(Float)
    sharpe: Mapped[float] = mapped_column(Float)
    max_drawdown: Mapped[float] = mapped_column(Float)
    win_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_trade_return: Mapped[float | None] = mapped_column(Float, nullable=True)

class JobRun(Base):
    __tablename__ = "job_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(60))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="started")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)    