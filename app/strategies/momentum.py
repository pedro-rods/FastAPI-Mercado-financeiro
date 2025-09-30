import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = (("lookback", 60), ("threshold_pct", 70), ("risk", None))

    def __init__(self):
        self.ret = bt.ind.PercentChange(self.data.close, period=self.p.lookback)
        # ATR opcional no futuro com self.p.risk
    def next(self):
        # stub simples: compra se retorno positivo, vende se negativo
        if not self.position and self.ret[0] > 0:
            self.buy()
        elif self.position and self.ret[0] <= 0:
            self.close()
