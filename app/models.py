# app/models.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Float
from app.db import Base
from datetime import datetime

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

class Backtest(Base):
    __tablename__ = "backtest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticker: Mapped[str] = mapped_column(String, index=True)
    start_date:Mapped[datetime]
    end_date: Mapped[datetime]
    strategy_type: Mapped[str] = mapped_column(String, index=True)

    # placeholder para futura implementação

    strategy_params_json: Mapped[str | None] = mapped_column(String, nullable=True)
    initial_cash: Mapped[float] = mapped_column(Float, default=10000.0)
    commission: Mapped[Float] = mapped_column(Float, default=10.0)
    timeframe: Mapped[str | None] = mapped_column(String, nullable = True)

    status: Mapped[str] = mapped_column(String, default = "created", index=True)
