# app/strategies/momentum.py
from app.strategies.atr_mixin import AtrRiskMixin

class MomentumStrategy(AtrRiskMixin):
    """
    Momentum por retorno acumulado (stub).
    Depois: retorno em janela 'lookback' e percentil 'threshold_pct'; ATR opcional.
    """
    def __init__(self, lookback: int = 60, threshold_pct: int = 70, risk: dict | None = None):
        self.lookback = lookback
        self.threshold_pct = threshold_pct
        self.risk_cfg = risk or {}
