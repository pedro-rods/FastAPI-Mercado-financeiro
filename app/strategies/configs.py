# app/strategies/configs.py
from pydantic import BaseModel, Field
from typing import Optional

"""
atr é opcional, fazer caso dê tempo
#TODO - verificar se ATR é válido de fazer
"""
class AtrRiskConfig(BaseModel):
    use_atr: bool = Field(default=False, description="Liga/desliga controle por ATR")
    atr_period: int = Field(default=14, ge=2, description="Período do ATR")
    risk_fraction: float = Field(default=0.01, gt=0, lt=1, description="Fração de risco por trade (0–1)")

class SmaCrossParams(BaseModel):
    fast: int = Field(default=50, ge=1)
    slow: int = Field(default=200, ge=2)
    risk: Optional[AtrRiskConfig] = Field(default=None)

class DonchianParams(BaseModel):
    n_high: int = Field(default=20, ge=1, description="Janela para rompimento da máxima")
    n_low: int = Field(default=10, ge=1, description="Janela para rompimento da mínima (saída)")
    risk: Optional[AtrRiskConfig] = Field(default=None)

class MomentumParams(BaseModel):
    lookback: int = Field(default=60, ge=2, description="Janela para retorno acumulado")
    threshold_pct: int = Field(default=70, ge=1, le=99, description="Percentil gatilho (1–99)")
    risk: Optional[AtrRiskConfig] = Field(default=None)
