# app/strategies/atr_mixin.py
class AtrRiskMixin:
    """
    Mixin opcional para controle por ATR. Aqui só a interface (sem implementação).
    #TODO dimensionamento de posição pelo ATR e gatilho de stop.
    """
    def setup_atr_risk(self, atr_period: int, risk_fraction: float):
        """ #TODO Preparar indicadores/variáveis internas de risco (stub)."""
        pass
