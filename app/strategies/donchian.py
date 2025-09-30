import backtrader as bt

class DonchianBreakout(bt.Strategy):
    params = (("n_high", 20), ("n_low", 10), ("risk", None))

    def __init__(self):
        self.dch_high = bt.ind.Highest(self.data.high, period=self.p.n_high)
        self.dch_low  = bt.ind.Lowest(self.data.low, period=self.p.n_low)
        # ATR opcional no futuro com self.p.risk
    def next(self):
        if not self.position:
            if self.data.close[0] > self.dch_high[0]:
                self.buy()
        else:
            if self.data.close[0] < self.dch_low[0]:
                self.close()
