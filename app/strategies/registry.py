# app/strategies/registry.py
from typing import Any, Dict, Type
from app.strategies.types import StrategyType
from app.strategies.configs import SmaCrossParams, DonchianParams, MomentumParams

REGISTRY: Dict[str, Dict[str, Any]] = {
    StrategyType.SMA_CROSS.value: {
        "name": "Cruzamento de Médias (SMA)",
        "params_model": SmaCrossParams,
        "default_params": SmaCrossParams().model_dump(),
        "description": "Compra quando média curta cruza acima da longa; vende no contrário.",
    },
    StrategyType.DONCHIAN.value: {
        "name": "Breakout Donchian",
        "params_model": DonchianParams,
        "default_params": DonchianParams().model_dump(),
        "description": "Rompimento da máxima N períodos; saída por mínima M períodos.",
    },
    StrategyType.MOMENTUM.value: {
        "name": "Momentum (retorno acumulado)",
        "params_model": MomentumParams,
        "default_params": MomentumParams().model_dump(),
        "description": "Compra quando retorno lookback supera um percentil histórico.",
    },
}

def validate_and_normalize_params(strategy_type: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
    if strategy_type not in REGISTRY:
        raise ValueError(f"Estratégia desconhecida: {strategy_type}")
    model: Type = REGISTRY[strategy_type]["params_model"]
    obj = model(**(params or {}))
    return obj.model_dump()
