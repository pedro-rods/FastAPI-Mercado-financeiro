from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class ItemBase(BaseModel):
    name: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True

# -- REQUESTS --

class RunBacktestRequest(BaseModel):
    ticker: str = Field(..., example="PETR4.SA")
    start_date: str = Field(..., example="2021-01-01")
    end_date: str = Field(..., example="2021-01-10")
    strategy_type: str = Field(..., example="sma_cross")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, example={"fast":50, "slow":200})
    initial_cash: float = Field(default = 1000.0, example = 1000.0)
    comission: float = Field(default=0.0, example = 0.0)
    timeframe: Optional[str] = Field(default="1d", example="1d")

class UpdateIndicatorsRequest(BaseModel):
    ticker: str = Field(..., example="PETR4.SA")
    start_date: str = Field(..., example="2021-01-01")
    end_date: str = Field(..., example="2021-01-10")

# -- RESPONSES -- 

class RunBacktestResponse(BaseModel):
    id: int
    status: str = Field(example="created")

class BackTestListItem(BaseModel):
    id:int
    created_at:str
    ticker:str
    strategy_type: str
    status: str

class ResultMetrics(BaseModel):
    total_returns: float = 0.0
    sharpe: float = 0.0
    max_drawndown = float = 0.0
    win_rate: float | None=None
    avg_trade_return: float | None=None

class Trade(BaseModel):
    date:str
    side:str
    price:float
    size:float
    commission:float | None = 0.0
    pnl:float | None = 0.0

class DailyPosition(BaseModel):
    date: str
    position_size: float
    cash: float
    equity: float
    drawdown: float

class EquityPoint(BaseModel):
    date: str
    equity: float

class BacktestResults(BaseModel):
    backtest_id: int
    metrics: ResultMetrics
    trades: List[Trade]
    daily_positions: List[DailyPosition]
    equity_curve: List[EquityPoint]

# -- HEALTH --
class HealthResponse(BaseModel):
    status: str
    db: str