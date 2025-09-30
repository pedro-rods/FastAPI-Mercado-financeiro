# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.db import engine, Base, get_db
from app import schemas, crud, models
from app.strategies import REGISTRY, validate_and_normalize_params
from app.services.yahoo import fetch_prices
from app.crud_prices import ensure_symbol, bulk_upsert_prices
from app.backtest_engine import run_backtest as bt_run
from app.ui import router as ui_router
from app.jobs.daily_indicators import run_daily_indicators
from app.jobs.health_check import run_health_check

from app.models import (
    Symbol, Price, Indicator, Backtest, Trade, DailyPosition, Metric, JobRun
)
from app.crud import (
    create_backtest_record, set_backtest_status,
    save_metrics, save_trades, save_daily_positions, get_results
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

# -- data visualization -- 
app.include_router(ui_router) # http://127.0.0.1:8000/ui/backtests/<ID>

# -------------- HEALTH --------------
@app.get("/health", response_model=schemas.HealthResponse)
def health(db: Session = Depends(get_db)):
    # Checagem simples de conexão com o DB
    try:
        db.execute("(SELECT 1)")
        return schemas.HealthResponse(status="ok", db="connected")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -- BACKTEST RUN --

@app.post("/backtests/run", response_model=schemas.RunBacktestResponse)
def run_backtest(req: schemas.RunBacktestRequest, db: Session = Depends(get_db)):
    # valida e normaliza parâmetros da estratégia (se você estiver usando o registry)
    try:
        normalized_params = validate_and_normalize_params(req.strategy_type, req.strategy_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # cria o registro do backtest com status "running"
    bt = create_backtest_record(
        db,
        ticker=req.ticker,
        start_date=req.start_date,
        end_date=req.end_date,
        strategy_type=req.strategy_type,
        strategy_params=normalized_params,
        initial_cash=req.initial_cash,
        commission=req.commission,
        timeframe=req.timeframe,
    )
    set_backtest_status(db, bt.id, "running")

    # roda, persiste e finaliza
    try:
        result = bt_run(
            req.ticker, req.start_date, req.end_date,
            req.strategy_type, normalized_params,
            req.initial_cash, req.commission
        )
        save_metrics(db, bt.id, result["metrics"])
        save_trades(db, bt.id, result["trades"])
        save_daily_positions(db, bt.id, result["daily_positions"])
        set_backtest_status(db, bt.id, "finished")
        return schemas.RunBacktestResponse(id=bt.id, status="finished")

    except KeyError as ke:
        set_backtest_status(db, bt.id, "error")
        raise HTTPException(status_code=400, detail=f"Coluna ausente no DataFrame: {ke}. Verifique o pré-processamento do fetch_prices.")
    except Exception as e:
        set_backtest_status(db, bt.id, "error")
        raise HTTPException(status_code=400, detail=str(e))



# -- RESULTADOS BACKTEST -- 
@app.get("/backtests/{backtest_id}/results", response_model=schemas.BacktestResults)
def get_backtest_results(backtest_id: int, db: Session = Depends(get_db)):
    res = get_results(db, backtest_id)
    if not res:
        raise HTTPException(status_code=404, detail="Backtest não encontrado")

    return schemas.BacktestResults(
        backtest_id=backtest_id,
        metrics=res["metrics"],
        trades=res["trades"],
        daily_positions=res["daily_positions"],
        equity_curve=res["equity_curve"],
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

@app.post("/data/indicators/update")
def update_indicators(req: schemas.UpdateIndicatorsRequest, db: Session = Depends(get_db)):
    try:
        symbol = ensure_symbol(db, req.ticker)
        df = fetch_prices(req.ticker, req.start_date, req.end_date)
        bulk_upsert_prices(db, symbol.id, df)
        return {
            "status": "ok",
            "rows": len(df),
            "ticker": req.ticker,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -- possibilidade de rodar os jobs manualmente    
    
@app.post("/jobs/daily_indicators")
def jobs_daily_indicators(tickers: list[str], background: BackgroundTasks, db: Session = Depends(get_db)):
    # dispara async (não trava o request)
    background.add_task(run_daily_indicators, db, tickers)
    return {"status": "accepted", "job": "daily_indicators", "tickers": tickers}

@app.post("/jobs/health_check")
def jobs_health_check(background: BackgroundTasks, db: Session = Depends(get_db)):
    background.add_task(run_health_check, db)
    return {"status": "accepted", "job": "health_check"}

