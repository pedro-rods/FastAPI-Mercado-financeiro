# backtest_engine.py
import os
import math
import pandas as pd
import backtrader as bt
from datetime import datetime, date
from typing import Dict, Any
import logging
from app.strategies.sma_cross import SmaCrossStrategy
from app.strategies.donchian import DonchianBreakout
from app.strategies.momentum import MomentumStrategy
from app.services.yahoo import fetch_prices


logger = logging.getLogger("uvicorn.error")
DEBUG = os.getenv("BT_DEBUG", "0") == "1"
def dprint(*args):
    if DEBUG:
        logger.info("[BTDEBUG] " + " ".join(str(a) for a in args))

# --- Funções auxiliares ---

def _dt(obj):
    # string -> date
    if isinstance(obj, str):
        return pd.to_datetime(obj).date()
    # datetime -> date
    if isinstance(obj, datetime):
        return obj.date()
    # date já é date
    if isinstance(obj, date):
        return obj
    # pandas Timestamp -> date
    try:
        return pd.to_datetime(obj).date()
    except Exception:
        # último fallback: melhor levantar erro explícito p/ debugar
        raise TypeError(f"Não consegui converter {type(obj)} para date: {obj!r}")

def _sum_entry_cost_and_qty(tx_dict, dt_open: date, dt_close: date):
    cost = 0.0
    qty  = 0.0
    # iteramos dias entre a abertura e o fechamento (inclusive)
    for dt, fills in tx_dict.items():
        d = _dt(dt)
        if d < dt_open or d > dt_close:
            continue
        # cada 'fills' é uma lista de tuplas/tipos; padrão: (size, price, sid, position, pnl, ...)
        for fill in fills:
            try:
                sz = float(fill[0])  # size
                pr = float(fill[1])  # price
            except Exception:
                # fallback para objetos/AutoOrderedDict
                sz = float(getattr(fill, "size", 0.0) or 0.0)
                pr = float(getattr(fill, "price", 0.0) or 0.0)
            if sz > 0:  # entradas (long). (se operar short, tratar sz < 0 como entrada de short)
                cost += pr * sz
                qty  += sz
    return cost, qty

def compute_metrics(equity_series: pd.Series, daily_returns: pd.Series) -> dict:
    if equity_series is None or equity_series.empty:
        dprint("compute_metrics: equity_series VAZIA")
        return {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}
    total_return = equity_series.iloc[-1] / equity_series.iloc[0] - 1.0
    sharpe = 0.0
    if daily_returns is not None and not daily_returns.empty and daily_returns.std(ddof=0) > 0:
        sharpe = (daily_returns.mean() / daily_returns.std(ddof=0)) * math.sqrt(252)
    cummax = equity_series.cummax()
    drawdowns = equity_series / cummax - 1.0
    max_dd = float(drawdowns.min()) if len(drawdowns) else 0.0
    dprint(f"compute_metrics: total_return={total_return:.6f} sharpe={sharpe:.6f} max_dd={max_dd:.6f}")
    return {"total_return": float(total_return), "sharpe": float(sharpe), "max_drawdown": max_dd}


class Recorder(bt.Analyzer):
    def __init__(self, debug: bool = False):
        self.trades = []
        self.daily = []
        self.debug = debug

    def _get(self, obj, name, default=0.0):
        try:
            return float(getattr(obj, name, default) or default)
        except Exception:
            return default

    def _h_parts(self, h):
        ev = getattr(h, "event", None)
        if ev is not None:
            return self._get(ev, "size"), self._get(ev, "price")
        return self._get(h, "size"), self._get(h, "price")

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        dtc = bt.num2date(trade.dtclose)
        if self.debug:
            logger.info(f"[BTDEBUG] trade closed dtclose={dtc} pnl={getattr(trade,'pnl',None)} "
                        f"pnlcomm={getattr(trade,'pnlcomm',None)} size_attr={getattr(trade,'size',None)} "
                        f"price_attr={getattr(trade,'price',None)} hist_len={len(getattr(trade,'history',[]))}")

        entry_qty = 0.0
        entry_cost = 0.0
        hist = getattr(trade, "history", [])
        for i, h in enumerate(hist):
            sz, pr = self._h_parts(h)
            if self.debug:
                attrs = [a for a in dir(h) if not a.startswith("_")]
                ev = getattr(h, "event", None)
                ev_attrs = [a for a in dir(ev) if not a.startswith("_")] if ev else None
                logger.info(f"[BTDEBUG]   hist[{i}] attrs={attrs} ev_attrs={ev_attrs} size={sz} price={pr}")
            if sz > 0:  # entradas long
                entry_cost += pr * sz
                entry_qty  += sz

        avg_entry_price = (entry_cost / entry_qty) if entry_qty > 0 else self._get(trade, "price")
        fallback_size   = abs(self._get(trade, "size"))
        effective_size  = entry_qty if entry_qty > 0 else fallback_size
        pnlcomm         = float(getattr(trade, "pnlcomm", getattr(trade, "pnl", 0.0)) or 0.0)

        denom  = entry_cost if entry_cost > 0 else (avg_entry_price * effective_size if avg_entry_price and effective_size else 0.0)
        ret_pct = (pnlcomm / denom) if denom > 0 else None

        side = "BUY"
        for h in hist:
            sz, _ = self._h_parts(h)
            if sz != 0:
                if sz < 0:
                    side = "SELL"
                break

        if self.debug:
            logger.info(f"[BTDEBUG]   computed entry_qty={entry_qty} entry_cost={entry_cost} "
                        f"avg_entry={avg_entry_price} eff_size={effective_size} pnlcomm={pnlcomm} "
                        f"denom={denom} return_pct={ret_pct}")

        self.trades.append({
    "date": bt.num2date(trade.dtclose).date().isoformat(),
    "open_date": bt.num2date(trade.dtopen).date().isoformat(),
    "side": side,
    "price": float(avg_entry_price),
    "size": float(effective_size),
    "commission": float(getattr(trade, "commission", 0.0) or 0.0),
    "pnl": float(pnlcomm),
    "return_pct": float(ret_pct) if ret_pct is not None else None,
})

    def next(self):
        dt_iso = self.strategy.data.datetime.date(0).isoformat()
        value = float(self.strategy.broker.getvalue())
        cash  = float(self.strategy.broker.get_cash())
        pos   = float(self.strategy.position.size)
        if self.debug and (len(self.daily) in (0, 1) or len(self.daily) % 250 == 0):
            logger.info(f"[BTDEBUG] next: {dt_iso} value={value:.2f} cash={cash:.2f} pos={pos}")
        self.daily.append({
            "date": dt_iso,
            "position_size": pos,
            "cash": cash,
            "equity": value,
            "drawdown": 0.0,
        })


# --- Função principal ---
def run_backtest(
    ticker: str,
    start: str,
    end: str,
    strategy_type: str,
    strategy_params: dict,
    initial_cash: float = 100000.0,
    commission: float = 0.0,
) -> Dict[str, Any]:
    # --- 1) Buscar dados ---
    df = fetch_prices(ticker, start, end)
    if df.empty:
        raise ValueError("Sem dados para o período escolhido")

    dprint("DF Yahoo:",
           {"shape": df.shape, "cols": list(df.columns),
            "date_min": str(df["date"].min()), "date_max": str(df["date"].max())})
    if DEBUG:
        dprint("DF head:\n" + df.head(3).to_string(index=False))

    data_feed = bt.feeds.PandasData(
        dataname=df,
        datetime="date",
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=-1,
    )

    # --- 2) Configurar cerebro ---
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    if commission:
        cerebro.broker.setcommission(commission=commission)

    if strategy_type == "sma_cross":
        cerebro.addstrategy(SmaCrossStrategy, **(strategy_params or {}))
    elif strategy_type == "donchian":
        cerebro.addstrategy(DonchianBreakout, **(strategy_params or {}))
    elif strategy_type == "momentum":
        cerebro.addstrategy(MomentumStrategy, **(strategy_params or {}))
    else:
        raise ValueError(f"Estratégia desconhecida: {strategy_type}")

    cerebro.adddata(data_feed)

    # --- 3) Executar ---
    cerebro.addanalyzer(Recorder, _name="recorder", debug=DEBUG)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="tx")  # ⬅️ novo
    results = cerebro.run()
    strat = results[0]
    rec = strat.analyzers.recorder
    ta  = strat.analyzers.ta.get_analysis()
    tx  = strat.analyzers.tx.get_analysis() 
    dprint("TradeAnalyzer RAW:", ta)

    # --- 4) Equity curve & métricas ---
    equity_curve = pd.Series(
        [d["equity"] for d in rec.daily],
        index=pd.to_datetime([d["date"] for d in rec.daily])
    ).sort_index()

    dprint(f"run_backtest: bars={len(rec.daily)} trades_closed={len(rec.trades)}")
    if DEBUG and rec.trades:
        dprint("first_trades:\n" + "\n".join(str(t) for t in rec.trades[:3]))

    daily_ret = equity_curve.pct_change().dropna()
    metrics = compute_metrics(equity_curve, daily_ret)
    metrics["win_rate"] = _extract_win_rate(ta)

    # Atualizar drawdowns diários
    cummax = equity_curve.cummax()
    dd = equity_curve / cummax - 1.0
    daily_positions = []
    for d in rec.daily:
        ts = pd.to_datetime(d["date"])
        d["drawdown"] = float(dd.loc[ts]) if ts in dd.index else 0.0
        daily_positions.append(d)
    
    filled = 0
    for t in rec.trades:
        if t.get("return_pct") is not None:
            continue
        dt_open  = _dt(t.get("open_date"))
        dt_close = _dt(t.get("date"))
        entry_cost, entry_qty = _sum_entry_cost_and_qty(tx, dt_open, dt_close)
        denom = entry_cost if entry_cost > 0 else 0.0
        if denom > 0:
            t["return_pct"] = float(t["pnl"]) / denom
            if (not t.get("size")) and entry_qty > 0:
                t["size"] = float(entry_qty)
            filled += 1
    dprint(f"filled return_pct via Transactions: {filled}/{len(rec.trades)}")

    returns = [t.get("return_pct") for t in rec.trades if t.get("return_pct") is not None]
    metrics["avg_trade_return"] = float(sum(returns) / len(returns)) if returns else None

    logger.info(
        f"[BT] done ticker={ticker} bars={len(rec.daily)} trades_closed={len(rec.trades)} "
        f"start={df['date'].min()} end={df['date'].max()} "
        f"equity0={rec.daily[0]['equity'] if rec.daily else 'NA'} "
        f"equityN={rec.daily[-1]['equity'] if rec.daily else 'NA'}"
    )
    return {
        "metrics": metrics,
        "trades": rec.trades,
        "daily_positions": daily_positions,
        "equity_curve": [
            {"date": k.strftime("%Y-%m-%d"), "equity": float(v)}
            for k, v in equity_curve.items()
        ],
    }

def _extract_win_rate(ta_dict) -> float | None:
    try:
        total = int(ta_dict.get("total", {}).get("total", 0) or 0)
        won   = int(ta_dict.get("won",   {}).get("total", 0) or 0)
        return (won / total) if total > 0 else None
    except Exception:
        return None
