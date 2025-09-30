import backtrader as bt

class SmaCrossStrategy(bt.Strategy):
    params = (("fast", 50), ("slow", 200), ("risk", None))

    def __init__(self):
        sma_fast = bt.ind.SMA(period=self.p.fast)
        sma_slow = bt.ind.SMA(period=self.p.slow)
        self.crossover = bt.ind.CrossOver(sma_fast, sma_slow)
         # se quiser usar ATR/position sizing no futuro, use self.p.risk aqui

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()
