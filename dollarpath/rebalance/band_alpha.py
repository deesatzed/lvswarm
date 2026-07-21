"""No-trade band + partial alpha rebalance family (GOAL_REBAL_V3)."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from dollarpath.rebalance.policies import RebalancePolicy
from dollarpath.rebalance.target import TargetSpec, distance_to_target


class BandAlphaRebalancePolicy(RebalancePolicy):
    """
    Every check_every steps: if max_abs(w - w*) > band,
    set w <- w + alpha * (w* - w).
    """

    def __init__(
        self,
        target: TargetSpec,
        band: float,
        alpha: float,
        check_every: int = 5,
        policy_id: Optional[str] = None,
    ):
        super().__init__(target)
        self.band = float(band)
        self.alpha = float(np.clip(alpha, 0.0, 1.0))
        self.check_every = max(1, int(check_every))
        self.policy_id = policy_id or f"Rba_b{band:g}_a{alpha:g}"
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        super().reset(n_assets)
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        w_star = self.target.as_array()
        if not self._initialized:
            self._initialized = True
            return w_star.copy()
        if step_index % self.check_every != 0:
            return None
        cur = np.asarray(current_weights, dtype=float)
        d = distance_to_target(cur, w_star)
        if d["max_abs"] <= self.band + 1e-12:
            return None
        return cur + self.alpha * (w_star - cur)
