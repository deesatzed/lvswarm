"""Baseline allocation policies (no learning)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import pandas as pd


class Policy(ABC):
    policy_id: str = "base"

    @abstractmethod
    def reset(self, n_assets: int) -> None:
        ...

    @abstractmethod
    def act(
        self,
        step_index: int,
        prices_so_far: pd.DataFrame,
        current_weights: np.ndarray,
    ) -> Optional[np.ndarray]:
        """Return target weights or None for no-op."""
        ...


class HoldPolicy(Policy):
    """Buy equal weight on first opportunity; hold forever."""

    policy_id = "hold_equal"

    def __init__(self):
        self._n = 0
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        self._n = n_assets
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        if not self._initialized:
            self._initialized = True
            return np.ones(self._n) / self._n
        return None


class CalendarRebalancePolicy(Policy):
    """Rebalance to equal weight every `every` trading days."""

    policy_id = "calendar_equal"

    def __init__(self, every: int = 21):
        self.every = max(1, int(every))
        self._n = 0

    def reset(self, n_assets: int) -> None:
        self._n = n_assets

    def act(self, step_index, prices_so_far, current_weights):
        if step_index % self.every == 0:
            return np.ones(self._n) / self._n
        return None


class VolTargetPolicy(Policy):
    """
    Equal-weight core, scale gross exposure so recent portfolio vol ~ target.
    Uses only past prices (as-of).
    """

    policy_id = "vol_target"

    def __init__(
        self,
        lookback: int = 21,
        target_annual: float = 0.10,
        every: int = 5,
        max_leverage: float = 1.0,
    ):
        self.lookback = lookback
        self.target_annual = target_annual
        self.every = max(1, every)
        self.max_leverage = max_leverage
        self._n = 0

    def reset(self, n_assets: int) -> None:
        self._n = n_assets

    def act(self, step_index, prices_so_far, current_weights):
        if step_index % self.every != 0:
            return None
        if len(prices_so_far) < self.lookback + 1:
            return np.ones(self._n) / self._n * 0.5
        rets = prices_so_far.pct_change().iloc[-self.lookback :]
        # equal-weight portfolio vol
        ew = np.ones(self._n) / self._n
        port = rets.to_numpy(dtype=float) @ ew
        vol = float(np.nanstd(port, ddof=1)) * np.sqrt(252.0)
        if vol < 1e-8:
            scale = self.max_leverage
        else:
            scale = min(self.max_leverage, self.target_annual / vol)
        scale = float(np.clip(scale, 0.0, self.max_leverage))
        return ew * scale
