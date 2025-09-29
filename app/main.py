# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import engine, Base, get_db
from app import schemas, crud, models
from app.strategies import REGISTRY, validate_and_normalize_params
from app.services.yahoo import fetch_prices
from app.crud_prices import ensure_symbol, bulk_upsert_prices

from app.models import (
    Symbol, Price, Indicator, Backtest, Trade, DailyPosition, Metric, JobRun
)

# só depois de importar os modelos, crie as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trading Algorítmico API - Estrutura")

@app.on_event("startup")
def on_startup():
    from app.models import (
        Symbol, Price, Indicator, Backtest, Trade, DailyPosition, Metric, JobRun
    )
    Base.metadata.create_all(bind=engine)

# -------------- HEALTH --------------
@app.get("/health", response_model=schemas.HealthResponse)
def health(db: Session = Depends(get_db)):
    # Checagem simples de conexão com o DB
    try:
        db.execute("SELECT 1")
        return schemas.HealthResponse(status="ok", db="connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -- BACKTEST RUN --
@app.post("/backtests/run", response_model=schemas.RunBacktestResponse)
def run_backtest(req: schemas.RunBacktestRequest, db: Session = Depends(get_db)):
    # valida e normaliza parâmetros da estratégia
    try:
        normalized_params = validate_and_normalize_params(req.strategy_type, req.strategy_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    bt = crud.create_backtest_record(
        db,
        ticker=req.ticker,
        start_date=req.start_date,
        end_date=req.end_date,
        strategy_type=req.strategy_type,
        strategy_params=normalized_params,  # já normalizado
        initial_cash=req.initial_cash,
        commission=req.commission,
        timeframe=req.timeframe,
    )
    return schemas.RunBacktestResponse(id=bt.id, status=bt.status)


# -- RESULTADOS BACKTEST -- 
@app.get("/backtests/{backtest_id}/results", response_model=schemas.BacktestResults)
def get_backtest_results(backtest_id: int, db: Session = Depends(get_db)):
    """
    Stub de resultados.
    """
    bt = crud.get_backtest(db, backtest_id)
    if not bt:
        raise HTTPException(status_code=404, detail="Backtest não encontrado")


    return schemas.BacktestResults(
        backtest_id=bt.id,
        metrics=schemas.ResultMetrics(
            total_return=0.0,
            sharpe=0.0,
            max_drawdown=0.0,
            win_rate=None,
            avg_trade_return=None,
        ),
        trades=[],
        daily_positions=[],
        equity_curve=[],
    )


#-- LIST BACKTEST -- 
@app.get("/backtests")
def list_backtests(
    ticker: str | None = Query(default=None),
    strategy_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Lista backtests com filtros e paginação.
    """
    rows = crud.list_backtests(
        db,
        ticker=ticker,
        strategy_type=strategy_type,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "ticker": r.ticker,
            "strategy_type": r.strategy_type,
            "status": r.status,
        }
        for r in rows
    ]


# -- UPDATE INDICATORS -- 
@app.post("/data/indicators/update")
def update_indicators(req: schemas.UpdateIndicatorsRequest):
    """
    Só estrutura por enquanto. 
    #TODO - Fazer implementação no futuro
    """
    return {
        "status": "accepted",
        "ticker": req.ticker,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "message": "Atualização agendada (stub).",
    }

#endpoint para listar as estratégias

@app.get("/strategies")
def list_strategies():
    return [
        {
            "type": key,
            "name": meta["name"],
            "description": meta["description"],
            "default_params": meta["default_params"],
        }
        for key, meta in REGISTRY.items()
    ]

