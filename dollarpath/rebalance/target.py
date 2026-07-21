"""Fixed strategic target mix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np


@dataclass(frozen=True)
class TargetSpec:
    tickers: tuple
    weights: tuple  # same length, sum ~ 1

    def as_array(self) -> np.ndarray:
        return np.asarray(self.weights, dtype=float)

    @property
    def n(self) -> int:
        return len(self.tickers)


def equal_weight_target(tickers: Sequence[str]) -> TargetSpec:
    n = len(tickers)
    w = tuple(1.0 / n for _ in range(n))
    return TargetSpec(tickers=tuple(tickers), weights=w)


def sixty_forty_target(tickers: Sequence[str]) -> TargetSpec:
    """
    Frozen strategic mix for U5 = SPY,QQQ,IWM,TLT,GLD.
    Stocks ~60%, defensive ~40%. NOT optimized on test data.
    """
    tickers = tuple(tickers)
    preset = {
        "SPY": 0.30,
        "QQQ": 0.20,
        "IWM": 0.10,
        "TLT": 0.25,
        "GLD": 0.15,
    }
    if set(tickers) != set(preset.keys()):
        # fall back: 60% equal among first 3, 40% equal among rest if n>=5
        n = len(tickers)
        if n < 2:
            return equal_weight_target(tickers)
        n_stock = max(1, int(round(0.6 * n)))
        w = []
        for i in range(n):
            if i < n_stock:
                w.append(0.6 / n_stock)
            else:
                w.append(0.4 / (n - n_stock))
        s = sum(w)
        w = tuple(x / s for x in w)
        return TargetSpec(tickers=tickers, weights=w)
    w = tuple(preset[t] for t in tickers)
    return TargetSpec(tickers=tickers, weights=w)


def distance_to_target(current: np.ndarray, target: np.ndarray) -> dict:
    """L1 / max abs deviation from target."""
    c = np.asarray(current, dtype=float)
    t = np.asarray(target, dtype=float)
    # pad/trim cash: compare invested weights on shared length
    n = min(c.size, t.size)
    c, t = c[:n], t[:n]
    abs_dev = np.abs(c - t)
    return {
        "l1": float(np.sum(abs_dev)),
        "max_abs": float(np.max(abs_dev)) if n else 0.0,
        "half_l1_turnover_to_target": float(0.5 * np.sum(abs_dev)),
    }
