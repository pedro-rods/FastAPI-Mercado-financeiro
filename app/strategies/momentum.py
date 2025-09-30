# app/strategies/momentum.py
import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = dict(
        lookback=60,            # janela para retorno acumulado
        thresh=0.0,             # só entra se retorno > thresh (0.0 = positivo)

        # risco / stop
        risk_pct=0.01,          # 1% do equity
        stop_method="atr",      # "atr" (padrão) ou "ma"
        atr_period=14,
        atr_mult=2.0,
        ma_period=100,          # se usar stop por média
        lot_size=1,
        use_trailing=False,     # opcional
    )

    def __init__(self):
        # simples momentum: retorno acumulado em janela (close / close[-lookback] - 1)
        self.mom = bt.ind.PercentChange(self.data.close, period=self.p.lookback)

        # stops auxiliares
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period) if self.p.stop_method == "atr" else None
        self.ma  = bt.ind.SMA(self.data.close, period=self.p.ma_period) if self.p.stop_method == "ma" else None

        self.entry_order = None
        self.stop_order  = None
        self._pending_stop_price = None

    # ---------------- sizing + stop calc ----------------
    def _calc_size_and_stop(self):
        price = float(self.data.close[0])

        if self.p.stop_method == "atr":
            if self.atr is None or self.atr[0] <= 0:
                return 0, None
            stop_price = price - float(self.p.atr_mult) * float(self.atr[0])
        else:
            # stop pela média móvel escolhida
            if self.ma is None or self.ma[0] <= 0:
                return 0, None
            stop_price = float(self.ma[0])

        risk_per_share = max(price - stop_price, 0.0)
        if risk_per_share <= 0:
            return 0, stop_price

        equity = float(self.broker.getvalue())
        cash   = float(self.broker.get_cash())
        risk_cash = equity * float(self.p.risk_pct)

        size_risk = int(risk_cash // risk_per_share)
        size_cash = int(cash // price)
        size = max(0, min(size_risk, size_cash))

        if size < self.p.lot_size:
            return 0, stop_price
        size = (size // self.p.lot_size) * self.p.lot_size
        return size, stop_price

    # ---------------- lógica de trading ----------------
    def _long_entry_signal(self) -> bool:
        # entra se momentum > thresh (por ex., >0 ⇒ desempenho positivo no lookback)
        if len(self.data) <= self.p.lookback:
            return False
        return float(self.mom[0]) > float(self.p.thresh)

    def _long_exit_signal(self) -> bool:
        # sai se momentum cai abaixo de 0 (ou do thresh) — regra simples
        return float(self.mom[0]) <= 0.0

    def next(self):
        if self.entry_order:
            return

        if not self.position:
            if self._long_entry_signal():
                size, stop_price = self._calc_size_and_stop()
                if size <= 0 or stop_price is None:
                    return
                self.entry_order = self.buy(size=size)
                self._pending_stop_price = stop_price
        else:
            if self._long_exit_signal():
                if self.stop_order:
                    self.cancel(self.stop_order)
                    self.stop_order = None
                self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.stop_order:
                    self.cancel(self.stop_order)
                if self._pending_stop_price:
                    self.stop_order = self.sell(
                        exectype=bt.Order.Stop,
                        price=self._pending_stop_price,
                        size=order.executed.size,
                    )
                self.entry_order = None

            elif order.issell():
                self.entry_order = None
                self.stop_order  = None
                self._pending_stop_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order is self.entry_order:
                self.entry_order = None
                self._pending_stop_price = None
