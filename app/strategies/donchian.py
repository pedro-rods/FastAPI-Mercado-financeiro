# app/strategies/donchian.py
from app.strategies.atr_mixin import AtrRiskMixin

class DonchianBreakout(AtrRiskMixin):
    """
    Breakout Donchian (stub).
    Depois: máxima N para entrada; mínima M para saída; ATR opcional.
    """
    def __init__(self, n_high: int = 20, n_low: int = 10, risk: dict | None = None):
        self.n_high = n_high
        self.n_low = n_low
        self.risk_cfg = risk or {}
