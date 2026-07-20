"""
Lightweight AR(1) regime detector (DollarPath-local).

Mirrors the spirit of naked_straddle_sim ace_core UniversalRegimeDetector
without hard-coupling that repo path. Uses only past returns (as-of).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class RegimeState:
    current_rho: float
    historical_rho: float
    regime_type: str
    confidence: float
    regime_change_detected: bool

    def as_dict(self) -> Dict:
        return {
            "current_rho": self.current_rho,
            "historical_rho": self.historical_rho,
            "regime_type": self.regime_type,
            "confidence": self.confidence,
            "regime_change_detected": self.regime_change_detected,
        }


def _ar1_rho(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 5:
        return 0.0
    a, b = x[:-1], x[1:]
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


class SimpleRegimeDetector:
    def __init__(
        self,
        window: int = 30,
        historical_window: int = 90,
        change_threshold: float = 0.3,
        stable_threshold: float = 0.7,
        volatile_threshold: float = 0.5,
    ):
        self.window = window
        self.historical_window = historical_window
        self.change_threshold = change_threshold
        self.stable_threshold = stable_threshold
        self.volatile_threshold = volatile_threshold
        self._last_rho: float | None = None

    def detect(self, prices_so_far: pd.DataFrame) -> RegimeState:
        if len(prices_so_far) < 3:
            return RegimeState(0.0, 0.0, "unknown", 0.0, False)
        # equal-weight portfolio log returns proxy
        rets = prices_so_far.pct_change().dropna()
        ew = np.ones(rets.shape[1]) / rets.shape[1]
        series = (rets.to_numpy(dtype=float) @ ew).astype(float)

        recent = series[-self.window :]
        hist = series[-self.historical_window :]
        rho = _ar1_rho(recent)
        rho_h = _ar1_rho(hist)
        change = False
        if self._last_rho is not None and abs(rho - self._last_rho) >= self.change_threshold:
            change = True
        self._last_rho = rho

        if rho >= self.stable_threshold:
            rtype = "stable"
        elif rho <= self.volatile_threshold:
            rtype = "volatile"
        else:
            rtype = "transitioning"

        conf = float(min(1.0, len(recent) / float(self.window)))
        return RegimeState(rho, rho_h, rtype, conf, change)
