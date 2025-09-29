# app/strategies/sma_cross.py
from app.strategies.atr_mixin import AtrRiskMixin

class SmaCrossStrategy(AtrRiskMixin):
    """
    Estratégia de Cruzamento de Médias (stub).
    Depois: implementar com Backtrader (SMA rápida/lenta + ATR opcional).
    """
    def __init__(self, fast: int = 50, slow: int = 200, risk: dict | None = None):
        self.fast = fast
        self.slow = slow
        self.risk_cfg = risk or {}
