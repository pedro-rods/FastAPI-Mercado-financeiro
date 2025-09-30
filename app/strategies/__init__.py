# app/strategies/__init__.py
from __future__ import annotations
from typing import Dict, Any

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

# ---- aliases por estratégia (entrada -> nome oficial) ----
ALIASES: Dict[str, Dict[str, str]] = {
    "sma_cross": {
        "fast_ma": "fast",
        "slow_ma": "slow",
    },
    "donchian": {
        "period": "n",
        "len": "n",
    },
    "momentum": {
        "threshold_pct": "thresh",
        "threshold": "thresh",
        "lb": "lookback",
        "lookback_period": "lookback",
    },
}

# ---- conjunto de chaves permitidas por estratégia ----
ALLOWED: Dict[str, set[str]] = {
    "sma_cross": set(REGISTRY["sma_cross"]["default_params"].keys()),
    "donchian":  set(REGISTRY["donchian"]["default_params"].keys()),
    "momentum":  set(REGISTRY["momentum"]["default_params"].keys()),
}

def _coerce_types(stype: str, p: dict) -> dict:
    """Coerções leves de tipo/sanity por estratégia."""
    def to_int(x): 
        try: return int(x)
        except: return x
    def to_float(x):
        try: return float(x)
        except: return x
    # comuns
    if "risk_pct" in p: p["risk_pct"] = to_float(p["risk_pct"])
    if "atr_period" in p: p["atr_period"] = to_int(p["atr_period"])
    if "atr_mult" in p: p["atr_mult"] = to_float(p["atr_mult"])
    if "lot_size" in p: p["lot_size"] = to_int(p["lot_size"])

    if stype == "sma_cross":
        if "fast" in p: p["fast"] = to_int(p["fast"])
        if "slow" in p: p["slow"] = to_int(p["slow"])

    if stype == "donchian":
        if "n" in p: p["n"] = to_int(p["n"])

    if stype == "momentum":
        if "lookback" in p: p["lookback"] = to_int(p["lookback"])
        if "thresh" in p:
            p["thresh"] = to_float(p["thresh"])
            # opcional: se vier como "5" e quiser tratar como 5%:
            # if p["thresh"] > 1: p["thresh"] /= 100.0
        if "ma_period" in p: p["ma_period"] = to_int(p["ma_period"])
    return p

def validate_and_normalize_params(strategy_type: str, params: dict | None) -> dict:
    if strategy_type not in REGISTRY:
        raise ValueError(f"Estratégia desconhecida: {strategy_type}")

    defaults = REGISTRY[strategy_type]["default_params"]
    params = dict(params or {})

    # 1) aplica aliases
    alias_map = ALIASES.get(strategy_type, {})
    remapped: Dict[str, Any] = {}
    for k, v in params.items():
        k2 = alias_map.get(k, k)
        remapped[k2] = v

    # 2) mantém só chaves permitidas
    allowed = ALLOWED[strategy_type]
    cleaned = {k: remapped.get(k, defaults.get(k)) for k in defaults.keys() if k in allowed}

    # 3) coerções e sanity
    cleaned = _coerce_types(strategy_type, cleaned)
    # risco limite
    rp = cleaned.get("risk_pct", 0.01)
    if not isinstance(rp, (int, float)) or rp <= 0 or rp > 0.05:
        cleaned["risk_pct"] = 0.01
    am = cleaned.get("atr_mult", 2.0)
    if not isinstance(am, (int, float)) or am <= 0:
        cleaned["atr_mult"] = 2.0
    ap = cleaned.get("atr_period", 14)
    if not isinstance(ap, int) or ap < 1:
        cleaned["atr_period"] = 14

    return cleaned
