from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd
from app.crud import jobrun_start, jobrun_finish
from app.services.yahoo import fetch_prices
# se tiver tabela symbols e indicators, importe seus CRUDs aqui

def run_daily_indicators(db: Session, tickers: list[str]):
    jr = jobrun_start(db, "daily_indicators", message=f"tickers={tickers}")
    try:
        # Exemplo simples: só atualiza OHLCV “do último mês”.
        end = datetime.utcnow().date()
        start = (end - timedelta(days=40)).strftime("%Y-%m-%d")
        end_s = end.strftime("%Y-%m-%d")

        updated = []
        for t in tickers:
            df = fetch_prices(t, start, end_s)
            # TODO: salvar em prices (e recalcular indicadores p/ indicators)
            # Ex.: save_prices(db, t, df) ; recalc_indicators(db, t, df)
            updated.append((t, len(df)))

        msg = "Atualizados: " + ", ".join([f"{t}({n})" for t, n in updated])
        jobrun_finish(db, jr.id, status="ok", message=msg)
    except Exception as e:
        jobrun_finish(db, jr.id, status="error", message=str(e))
        raise
