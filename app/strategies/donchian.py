
import backtrader as bt

class DonchianBreakout(bt.Strategy):
    params = dict(
        # sinal
        n=20,                 
        confirm_break=True,     # exige rompimento acima da máxima anterior (true) ou usa banda atual

        # risco / stop
        risk_pct=0.01,          # 1% do equity
        stop_method="atr",      # "atr" (padrão) ou "channel"
        atr_period=14,
        atr_mult=2.0,
        lot_size=1,             # 1 se aceitar fracionário; use 100 p/ lote padrão B3
        use_trailing=False,     # trailing não implementado aqui (pode estender depois)
    )

    def __init__(self):
     
        self.dc_high = bt.ind.Highest(self.data.high, period=self.p.n)
        self.dc_low  = bt.ind.Lowest(self.data.low, period=self.p.n)

    
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
        
            stop_price = float(self.dc_low[0])

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
        # rompimento da banda superior:
        # - se confirm_break=True: exige fechamento acima da MÁXIMA dos últimos n-1 dias (dc_high[-1])
        # - caso contrário, usa a banda calculada no candle atual (dc_high[0])
        ref_high = self.dc_high[-1] if self.p.confirm_break and len(self) > self.p.n else self.dc_high[0]
        return float(self.data.close[0]) > float(ref_high)

    def _long_exit_signal(self) -> bool:
        # saída se fechar abaixo da banda inferior (ou você pode preferir abaixo da média do canal)
        return float(self.data.close[0]) < float(self.dc_low[0])

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
                # coloca stop assim que a compra executa
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
                # zerou posição (por stop ou por saída) -> limpa
                self.entry_order = None
                self.stop_order  = None
                self._pending_stop_price = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order is self.entry_order:
                self.entry_order = None
                self._pending_stop_price = None
