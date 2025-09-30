from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# -- REQUESTS --

class RunBacktestRequest(BaseModel):
    ticker: str = Field(..., example="PETR4.SA")
    start_date: str = Field(..., example="2021-01-01")
    end_date: str = Field(..., example="2024-12-31")
    strategy_type: str = Field(..., example="sma_cross")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, example={"fast":50, "slow":200})
    initial_cash: float = Field(default = 100000.0, example = 100000.0)
    commission: float = Field(default=0.0, example = 0.0)
    timeframe: Optional[str] = Field(default="1d", example="1d")

class UpdateIndicatorsRequest(BaseModel):
    ticker: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


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
    total_return: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    win_rate: Optional[float]=None
    avg_trade_return: Optional[float]=None

class Trade(BaseModel):
    date:str
    side:str
    price:float
    size:float
    commission:Optional[float] = 0.0
    pnl:Optional[float] = 0.0

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