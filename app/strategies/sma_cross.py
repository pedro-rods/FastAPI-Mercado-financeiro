# app/strategies/sma_cross.py
import backtrader as bt

class SmaCrossStrategy(bt.Strategy):
    params = dict(
        fast=20,
        slow=100,
        # --- risco / stop ---
        risk_pct=0.01,        # 1% do equity por trade
        stop_method="atr",    # "atr" ou "ma"
        atr_period=14,
        atr_mult=2.0,
        lot_size=1,           # arredondamento por lote (ex.: 100 na B3). Use 1 se aceitar fracionário.
        use_trailing=False,   # opcional (não implementado aqui)
    )

    def __init__(self):
        self.sma_fast = bt.ind.SMA(self.data.close, period=self.p.fast)
        self.sma_slow = bt.ind.SMA(self.data.close, period=self.p.slow)
        self.xover    = bt.ind.CrossOver(self.sma_fast, self.sma_slow)

        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period) if self.p.stop_method == "atr" else None

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
            # stop por média lenta (exemplo alternativo)
            stop_price = float(self.sma_slow[0])

        risk_per_share = max(price - stop_price, 0.0)
        if risk_per_share <= 0:
            return 0, stop_price

        equity = float(self.broker.getvalue())
        cash   = float(self.broker.get_cash())
        risk_cash = equity * float(self.p.risk_pct)

        size_risk = int(risk_cash // risk_per_share)
        size_cash = int(cash // price)
        size = max(0, min(size_risk, size_cash))

        # arredonda por lote
        if size < self.p.lot_size:
            return 0, stop_price
        size = (size // self.p.lot_size) * self.p.lot_size
        return size, stop_price

    # ---------------- lógica de trading ----------------
    def next(self):
        # evita enviar nova entrada se já temos ordem pendente
        if self.entry_order:
            return

        if not self.position:
            # sinal de compra: cruzamento fast > slow
            if self.xover > 0:
                size, stop_price = self._calc_size_and_stop()
                if size <= 0 or stop_price is None:
                    return
                # entra a mercado e registra stop desejado
                self.entry_order = self.buy(size=size)
                self._pending_stop_price = stop_price
        else:
            # sinal de saída: cruzou para baixo -> fecha e cancela stop
            if self.xover < 0:
                if self.stop_order:
                    self.cancel(self.stop_order)
                    self.stop_order = None
                self.close()  # vende para zerar

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                # assim que a compra executa, envia o stop
                if self.stop_order:
                    self.cancel(self.stop_order)
                stop_price = self._pending_stop_price
                if stop_price:
                    self.stop_order = self.sell(
                        exectype=bt.Order.Stop,
                        price=stop_price,
                        size=order.executed.size,
                    )
                # libera para aceitar novas entradas no futuro
                self.entry_order = None

            elif order.issell():
                # vendemos (por cruzamento ou stop) -> limpa controles
                self.entry_order = None
                self.stop_order  = None
                self._pending_stop_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order is self.entry_order:
                self.entry_order = None
                self._pending_stop_price = None
