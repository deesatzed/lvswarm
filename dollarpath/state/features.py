"""As-of feature builder (no lookahead)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd


@dataclass
class FeatureSnapshot:
    step_index: int
    realized_vol: float
    mean_return: float
    drawdown: float
    days_since_rebalance: int
    current_weights: np.ndarray
    regime: str = "unknown"
    regime_rho: float = 0.0
    regime_confidence: float = 0.0

    def as_dict(self) -> Dict:
        return {
            "step_index": self.step_index,
            "realized_vol": self.realized_vol,
            "mean_return": self.mean_return,
            "drawdown": self.drawdown,
            "days_since_rebalance": self.days_since_rebalance,
            "regime": self.regime,
            "regime_rho": self.regime_rho,
            "regime_confidence": self.regime_confidence,
            "weights": self.current_weights.tolist(),
        }


def build_features(
    prices_so_far: pd.DataFrame,
    current_weights: np.ndarray,
    drawdown: float,
    step_index: int,
    days_since_rebalance: int,
    lookback: int = 21,
    regime: Optional[dict] = None,
) -> FeatureSnapshot:
    if len(prices_so_far) < 2:
        vol, mu = 0.0, 0.0
    else:
        rets = prices_so_far.pct_change().iloc[-lookback:]
        # equal-weight proxy portfolio return series
        ew = np.ones(prices_so_far.shape[1]) / prices_so_far.shape[1]
        port = rets.to_numpy(dtype=float) @ ew
        port = port[~np.isnan(port)]
        vol = float(np.std(port, ddof=1) * np.sqrt(252)) if len(port) > 1 else 0.0
        mu = float(np.mean(port) * 252) if len(port) else 0.0

    reg = regime or {}
    return FeatureSnapshot(
        step_index=step_index,
        realized_vol=vol,
        mean_return=mu,
        drawdown=float(drawdown),
        days_since_rebalance=int(days_since_rebalance),
        current_weights=np.asarray(current_weights, dtype=float),
        regime=str(reg.get("regime_type", "unknown")),
        regime_rho=float(reg.get("current_rho", 0.0)),
        regime_confidence=float(reg.get("confidence", 0.0)),
    )
