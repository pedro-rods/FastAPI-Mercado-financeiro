# app/strategies/types.py
from enum import Enum

class StrategyType(str, Enum):
    SMA_CROSS = "sma_cross"
    DONCHIAN = "donchian"
    MOMENTUM = "momentum"
