"""Rebalance policies for a FIXED target w* (no allocation search)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import pandas as pd

from dollarpath.rebalance.target import TargetSpec, distance_to_target


class RebalancePolicy(ABC):
    policy_id: str = "base"

    def __init__(self, target: TargetSpec):
        self.target = target
        self._n = target.n

    def reset(self, n_assets: int) -> None:
        if n_assets != self._n:
            raise ValueError(f"n_assets {n_assets} != target n {self._n}")
        self._initialized = False

    @abstractmethod
    def act(
        self,
        step_index: int,
        prices_so_far: pd.DataFrame,
        current_weights: np.ndarray,
    ) -> Optional[np.ndarray]:
        ...


class NeverRebalancePolicy(RebalancePolicy):
    """R0: buy w* once, then drift forever."""

    policy_id = "R0_never"

    def __init__(self, target: TargetSpec):
        super().__init__(target)
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        super().reset(n_assets)
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        if not self._initialized:
            self._initialized = True
            return self.target.as_array().copy()
        return None


class CalendarRebalanceToTarget(RebalancePolicy):
    """R1/R2: every N sessions fully reset to w*."""

    def __init__(self, target: TargetSpec, every: int = 21, policy_id: str = "R1_calendar_21"):
        super().__init__(target)
        self.every = max(1, int(every))
        self.policy_id = policy_id
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        super().reset(n_assets)
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        if not self._initialized:
            self._initialized = True
            return self.target.as_array().copy()
        if step_index % self.every == 0:
            return self.target.as_array().copy()
        return None


class ThresholdRebalancePolicy(RebalancePolicy):
    """R3/R4: rebalance to w* when max abs drift exceeds band."""

    def __init__(self, target: TargetSpec, band: float = 0.05, policy_id: str = "R3_threshold_5"):
        super().__init__(target)
        self.band = float(band)
        self.policy_id = policy_id
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        super().reset(n_assets)
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        if not self._initialized:
            self._initialized = True
            return self.target.as_array().copy()
        d = distance_to_target(current_weights, self.target.as_array())
        if d["max_abs"] > self.band + 1e-12:
            return self.target.as_array().copy()
        return None


class PartialRebalancePolicy(RebalancePolicy):
    """R5/R6: every N sessions move fraction alpha toward w*."""

    def __init__(
        self,
        target: TargetSpec,
        alpha: float = 0.25,
        every: int = 21,
        policy_id: str = "R5_partial_0.25",
    ):
        super().__init__(target)
        self.alpha = float(np.clip(alpha, 0.0, 1.0))
        self.every = max(1, int(every))
        self.policy_id = policy_id
        self._initialized = False

    def reset(self, n_assets: int) -> None:
        super().reset(n_assets)
        self._initialized = False

    def act(self, step_index, prices_so_far, current_weights):
        w_star = self.target.as_array()
        if not self._initialized:
            self._initialized = True
            return w_star.copy()
        if step_index % self.every == 0:
            cur = np.asarray(current_weights, dtype=float)
            return cur + self.alpha * (w_star - cur)
        return None


class CostAwareRebalancePolicy(RebalancePolicy):
    """
    R7: every `check_every` sessions, rebalance fully to w* only if
    estimated benefit > estimated cost.
    """

    def __init__(
        self,
        target: TargetSpec,
        check_every: int = 5,
        cost_bps_one_way: float = 2.5,
        vol_lookback: int = 21,
        policy_id: str = "R7_cost_aware",
    ):
        super().__init__(target)
        self.check_every = max(1, int(check_every))
        self.cost_bps_one_way = float(cost_bps_one_way)
        self.vol_lookback = int(vol_lookback)
        self.policy_id = policy_id
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
        turnover = d["half_l1_turnover_to_target"]
        # cost as fraction of wealth
        cost_frac = turnover * (self.cost_bps_one_way / 10_000.0) * 2.0

        # benefit proxy: drift * recent equal-weight vol (scale-free)
        if len(prices_so_far) < self.vol_lookback + 1:
            vol = 0.01
        else:
            rets = prices_so_far.pct_change().iloc[-self.vol_lookback :]
            ew = np.ones(rets.shape[1]) / rets.shape[1]
            port = rets.to_numpy(dtype=float) @ ew
            port = port[~np.isnan(port)]
            vol = float(np.std(port, ddof=1)) if len(port) > 2 else 0.01
            vol = max(vol, 1e-6)

        # rough: benefit ~ 0.5 * L1_drift * vol (dimensionless proxy)
        benefit_frac = 0.5 * d["l1"] * vol * np.sqrt(self.check_every)

        if benefit_frac > cost_frac + 1e-12:
            return w_star.copy()
        return None


class CostAwareRebalanceV2Policy(RebalancePolicy):
    """
    R7b: calmer cost-aware rule (GOAL_REBAL).
    - check every 21 sessions
    - require max_abs drift > band
    - require benefit > k * cost
    - skip tiny turnover
    """

    def __init__(
        self,
        target: TargetSpec,
        check_every: int = 21,
        band: float = 0.05,
        k: float = 2.0,
        min_turnover: float = 0.02,
        cost_bps_one_way: float = 2.5,
        vol_lookback: int = 21,
        policy_id: str = "R7b_cost_aware_v2",
    ):
        super().__init__(target)
        self.check_every = max(1, int(check_every))
        self.band = float(band)
        self.k = float(k)
        self.min_turnover = float(min_turnover)
        self.cost_bps_one_way = float(cost_bps_one_way)
        self.vol_lookback = int(vol_lookback)
        self.policy_id = policy_id
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
        turnover = d["half_l1_turnover_to_target"]
        if turnover < self.min_turnover:
            return None

        cost_frac = turnover * (self.cost_bps_one_way / 10_000.0) * 2.0
        if len(prices_so_far) < self.vol_lookback + 1:
            vol = 0.01
        else:
            rets = prices_so_far.pct_change().iloc[-self.vol_lookback :]
            ew = np.ones(rets.shape[1]) / rets.shape[1]
            port = rets.to_numpy(dtype=float) @ ew
            port = port[~np.isnan(port)]
            vol = float(np.std(port, ddof=1)) if len(port) > 2 else 0.01
            vol = max(vol, 1e-6)

        benefit_frac = 0.5 * d["l1"] * vol * np.sqrt(self.check_every)
        if benefit_frac > self.k * cost_frac + 1e-12:
            return w_star.copy()
        return None


def all_rebalance_policies(
    target: TargetSpec,
    cost_bps_one_way: float = 2.5,
) -> list:
    return [
        NeverRebalancePolicy(target),
        CalendarRebalanceToTarget(target, every=21, policy_id="R1_calendar_21"),
        CalendarRebalanceToTarget(target, every=63, policy_id="R2_calendar_63"),
        ThresholdRebalancePolicy(target, band=0.05, policy_id="R3_threshold_5"),
        ThresholdRebalancePolicy(target, band=0.10, policy_id="R4_threshold_10"),
        PartialRebalancePolicy(target, alpha=0.25, every=21, policy_id="R5_partial_0.25"),
        PartialRebalancePolicy(target, alpha=0.50, every=21, policy_id="R6_partial_0.50"),
        CostAwareRebalancePolicy(
            target, check_every=5, cost_bps_one_way=cost_bps_one_way, policy_id="R7_cost_aware"
        ),
        CostAwareRebalanceV2Policy(
            target, cost_bps_one_way=cost_bps_one_way, policy_id="R7b_cost_aware_v2"
        ),
    ]
