"""Quota rebalance policies toward fixed fair shares."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class FairPolicy(ABC):
    policy_id: str = "base"

    def reset(self, n: int, w_star: np.ndarray) -> None:
        self.n = n
        self.w_star = np.asarray(w_star, dtype=float)
        self._init = False

    @abstractmethod
    def act(
        self,
        t: int,
        usage_share_asof: np.ndarray,
        current_q: np.ndarray,
        queue_asof: np.ndarray,
    ) -> Optional[np.ndarray]:
        ...


class NeverPolicy(FairPolicy):
    policy_id = "F0_never"

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        return None


class CalendarPolicy(FairPolicy):
    def __init__(self, every: int = 25, policy_id: str = "F1_calendar_25"):
        self.every = max(1, every)
        self.policy_id = policy_id

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        if t % self.every == 0:
            return self.w_star.copy()
        return None


class ThresholdPolicy(FairPolicy):
    """Rebalance quotas to w* if usage share drifts from w* by max abs > band."""

    def __init__(self, band: float = 0.05, policy_id: str = "F3_threshold_0.05"):
        self.band = float(band)
        self.policy_id = policy_id

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        dev = np.max(np.abs(usage_share_asof - self.w_star))
        if dev > self.band:
            return self.w_star.copy()
        return None


class PartialPolicy(FairPolicy):
    def __init__(self, alpha: float = 0.25, every: int = 25, policy_id: str = "F5_partial_0.25"):
        self.alpha = float(np.clip(alpha, 0, 1))
        self.every = max(1, every)
        self.policy_id = policy_id

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        if t % self.every == 0:
            return current_q + self.alpha * (self.w_star - current_q)
        return None


class CostAwarePolicy(FairPolicy):
    """
    Rebalance to w* if usage drift is large and benefit proxy > k * migration cost proxy.
    """

    def __init__(
        self,
        every: int = 25,
        band: float = 0.05,
        k: float = 2.0,
        cost_per_l1: float = 1.0,
        policy_id: str = "F7_cost_aware",
    ):
        self.every = max(1, every)
        self.band = band
        self.k = k
        self.cost_per_l1 = cost_per_l1
        self.policy_id = policy_id

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        if t % self.every != 0:
            return None
        dev = np.max(np.abs(usage_share_asof - self.w_star))
        if dev <= self.band:
            return None
        # migrate quotas toward w* (full)
        l1 = float(np.abs(self.w_star - current_q).sum())
        cost = l1 * self.cost_per_l1
        # benefit: reduce queue pressure imbalance
        benefit = float(np.sum(queue_asof) * dev)
        if benefit > self.k * cost + 1e-12:
            return self.w_star.copy()
        return None


class CostAwareV2Policy(FairPolicy):
    """
    F7b: calmer cost-aware — longer check interval, min turnover,
    benefit from queue imbalance * drift, require benefit > k * cost.
    """

    def __init__(
        self,
        every: int = 50,
        band: float = 0.05,
        k: float = 1.5,
        cost_per_l1: float = 1.0,
        min_l1: float = 0.05,
        policy_id: str = "F7b_cost_aware_v2",
    ):
        self.every = max(1, every)
        self.band = band
        self.k = k
        self.cost_per_l1 = cost_per_l1
        self.min_l1 = min_l1
        self.policy_id = policy_id

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        if t % self.every != 0:
            return None
        # Primary signal: how far quotas drifted from fair target (not queues —
        # work-conserving drift can keep queues empty while unfair).
        l1 = float(np.abs(self.w_star - current_q).sum())
        if l1 < self.min_l1:
            return None
        max_dev = float(np.max(np.abs(current_q - self.w_star)))
        if max_dev <= self.band:
            return None
        cost = l1 * self.cost_per_l1
        qsum = float(np.sum(queue_asof))
        # benefit: restore fairness + relieve any queue imbalance
        benefit = 10.0 * l1 + qsum * max_dev
        if benefit > self.k * cost + 1e-12:
            return self.w_star.copy()
        return None


class BandAlphaPolicy(FairPolicy):
    """If usage max-abs drift > band, move alpha toward w*."""

    def __init__(
        self,
        band: float = 0.05,
        alpha: float = 1.0,
        every: int = 5,
        policy_id: str | None = None,
    ):
        self.band = float(band)
        self.alpha = float(np.clip(alpha, 0, 1))
        self.every = max(1, every)
        self.policy_id = policy_id or f"Fba_b{band:g}_a{alpha:g}"

    def act(self, t, usage_share_asof, current_q, queue_asof):
        if not self._init:
            self._init = True
            return self.w_star.copy()
        if t % self.every != 0:
            return None
        dev = float(np.max(np.abs(usage_share_asof - self.w_star)))
        if dev <= self.band:
            return None
        return current_q + self.alpha * (self.w_star - current_q)


def all_policies(migration_cost_per_l1: float = 1.0) -> list:
    return [
        NeverPolicy(),
        CalendarPolicy(25, "F1_calendar_25"),
        CalendarPolicy(100, "F2_calendar_100"),
        ThresholdPolicy(0.05, "F3_threshold_0.05"),
        ThresholdPolicy(0.10, "F4_threshold_0.10"),
        PartialPolicy(0.25, 25, "F5_partial_0.25"),
        PartialPolicy(0.50, 25, "F6_partial_0.50"),
        CostAwarePolicy(25, 0.05, 2.0, migration_cost_per_l1, "F7_cost_aware"),
        CostAwareV2Policy(50, 0.05, 1.5, migration_cost_per_l1, 0.05, "F7b_cost_aware_v2"),
    ]


def policy_factories(migration_cost_per_l1: float = 1.0):
    """Fresh instances for multi-seed runs."""
    return [
        lambda: NeverPolicy(),
        lambda: CalendarPolicy(25, "F1_calendar_25"),
        lambda: CalendarPolicy(100, "F2_calendar_100"),
        lambda: ThresholdPolicy(0.05, "F3_threshold_0.05"),
        lambda: ThresholdPolicy(0.10, "F4_threshold_0.10"),
        lambda: PartialPolicy(0.25, 25, "F5_partial_0.25"),
        lambda: PartialPolicy(0.50, 25, "F6_partial_0.50"),
        lambda: CostAwarePolicy(25, 0.05, 2.0, migration_cost_per_l1, "F7_cost_aware"),
        lambda: CostAwareV2Policy(50, 0.05, 1.5, migration_cost_per_l1, 0.05, "F7b_cost_aware_v2"),
    ]

