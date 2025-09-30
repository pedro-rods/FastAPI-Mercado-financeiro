import math
import pandas as pd
import backtrader as bt
from datetime import datetime
from typing import Dict, Any

from app.strategies.sma_cross import SmaCrossStrategy
from app.strategies.donchian import DonchianBreakout
from app.strategies.momentum import MomentumStrategy
from app.services.yahoo import fetch_prices


# --- Funções auxiliares ---
def compute_metrics(equity_series: pd.Series, daily_returns: pd.Series) -> dict:
    if equity_series is None or equity_series.empty:
        return {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}
    total_return = equity_series.iloc[-1] / equity_series.iloc[0] - 1.0
    sharpe = 0.0
    if daily_returns is not None and not daily_returns.empty and daily_returns.std(ddof=0) > 0:
        sharpe = (daily_returns.mean() / daily_returns.std(ddof=0)) * math.sqrt(252)
    cummax = equity_series.cummax()
    drawdowns = equity_series / cummax - 1.0
    max_dd = float(drawdowns.min()) if len(drawdowns) else 0.0
    return {"total_return": float(total_return), "sharpe": float(sharpe), "max_drawdown": max_dd}


class Recorder(bt.Analyzer):
    def __init__(self):
        self.trades = []
        self.daily = []

    def _h_size(self, h) -> float:
        ev = getattr(h, "event", None)
        if ev is not None:
            return float(getattr(ev, "size", 0.0) or 0.0)
        return float(getattr(h, "size", 0.0) or 0.0)

    def _h_price(self, h) -> float:
        ev = getattr(h, "event", None)
        if ev is not None:
            return float(getattr(ev, "price", 0.0) or 0.0)
        return float(getattr(h, "price", 0.0) or 0.0)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        # Reconstrói entradas e saídas a partir do histórico (funciona com parciais)
        entry_qty = 0.0
        entry_cost = 0.0
        try:
            for h in getattr(trade, "history", []):
                sz = self._h_size(h)
                pr = self._h_price(h)
                if sz > 0:             # entradas de posição long
                    entry_cost += pr * sz
                    entry_qty  += sz
                elif sz < 0:
                    # saídas/realizações; não precisamos somar aqui p/ retorno %
                    pass
        except Exception:
            pass

        # Preço médio e tamanho “efetivo”
        avg_entry_price = (entry_cost / entry_qty) if entry_qty > 0 else float(getattr(trade, "price", 0.0) or 0.0)

        # no fechamento, trade.size costuma estar 0; use entry_qty como tamanho negociado
        effective_size = entry_qty if entry_qty > 0 else abs(float(getattr(trade, "size", 0.0) or 0.0))

        pnlcomm = float(getattr(trade, "pnlcomm", getattr(trade, "pnl", 0.0)) or 0.0)

        # retorno % do trade baseado no custo das entradas (robusto a parciais)
        denom = entry_cost if entry_cost > 0 else (avg_entry_price * effective_size if avg_entry_price and effective_size else 0.0)
        ret_pct = (pnlcomm / denom) if denom > 0 else None

        # Direção — best effort pelo primeiro evento não nulo
        side = "BUY"
        try:
            first_h = next((h for h in getattr(trade, "history", []) if self._h_size(h) != 0), None)
            if first_h and self._h_size(first_h) < 0:
                side = "SELL"
        except Exception:
            pass

        self.trades.append({
            "date": bt.num2date(trade.dtclose).date().isoformat(),
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
        cash = float(self.strategy.broker.get_cash())
        position_size = float(self.strategy.position.size)
        self.daily.append({
            "date": dt_iso,
            "position_size": position_size,
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
    cerebro.addanalyzer(Recorder, _name="recorder")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    results = cerebro.run()
    rec = results[0].analyzers.recorder
    ta = results[0].analyzers.ta.get_analysis()  # dict do TradeAnalyzer

    # --- 4) Equity curve & métricas ---
    equity_curve = pd.Series(
        [d["equity"] for d in rec.daily],
        index=pd.to_datetime([d["date"] for d in rec.daily])
    ).sort_index()

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
    avg_trade_return = None
    returns = [t.get("return_pct") for t in rec.trades if t.get("return_pct") is not None]
    metrics["avg_trade_return"] = float(sum(returns) / len(returns)) if returns else None

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
