# app/strategies/__init__.py
from app.strategies.types import StrategyType
from app.strategies.registry import REGISTRY, validate_and_normalize_params

REGISTRY = {
    "sma_cross": {
        "name": "SMA Cross",
        "description": "Cruzamento de médias móveis com stop e sizing por risco",
        "default_params": {
            "fast": 20, "slow": 100,
            "risk_pct": 0.01, "stop_method": "atr",
            "atr_period": 14, "atr_mult": 2.0,
            "lot_size": 1, "use_trailing": False,
        },
    },
    "donchian": {
        "name": "Donchian Breakout",
        "description": "Rompimento de canal Donchian com stop e sizing por risco",
        "default_params": {
            "n": 20, "confirm_break": True,
            "risk_pct": 0.01, "stop_method": "atr",
            "atr_period": 14, "atr_mult": 2.0,
            "lot_size": 1, "use_trailing": False,
        },
    },
    "momentum": {
        "name": "Momentum",
        "description": "Entrada por momentum > thresh com stop e sizing por risco",
        "default_params": {
            "lookback": 60, "thresh": 0.0,
            "risk_pct": 0.01, "stop_method": "atr",
            "atr_period": 14, "atr_mult": 2.0,
            "ma_period": 100,
            "lot_size": 1, "use_trailing": False,
        },
    },
}


ALLOWED_KEYS = {"fast","slow","n","lookback",
                "risk_pct","stop_method","atr_period","atr_mult","lot_size","use_trailing"}

def validate_and_normalize_params(strategy_type: str, params: dict | None) -> dict:
    params = dict(params or {})
    defaults = REGISTRY[strategy_type]["default_params"]
    # filtra apenas chaves permitidas
    clean = {k: params.get(k, defaults.get(k)) for k in defaults.keys() if k in ALLOWED_KEYS or k in defaults}
    # sanity checks
    if clean.get("risk_pct", 0.01) <= 0 or clean["risk_pct"] > 0.05:
        # evita risco >5% por trade (ajuste se quiser)
        clean["risk_pct"] = 0.01
    if clean.get("atr_mult", 2.0) <= 0:
        clean["atr_mult"] = 2.0
    if clean.get("atr_period", 14) < 1:
        clean["atr_period"] = 14
    return clean