"""Discrete-time multi-tenant fair-share simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


def jain_fairness(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = np.clip(x, 0.0, None)
    if x.size == 0 or np.sum(x) <= 0:
        return 1.0
    return float((np.sum(x) ** 2) / (x.size * np.sum(x ** 2) + 1e-12))


@dataclass
class SimConfig:
    n_tenants: int = 5
    capacity: float = 100.0
    steps: int = 2000
    seed: int = 42
    migration_cost_per_l1: float = 1.0
    # demand
    base_rate: float = 8.0
    burst_every: int = 200
    burst_len: int = 30
    burst_mult: float = 4.0
    burst_tenant_cycle: int = 1  # which tenant gets bursts (rotates)
    # quota "market drift": sticky pressure toward recent usage (like price drift)
    drift_alpha: float = 0.08


class FairShareSim:
    """
    Each step:
      1. Demand arrives (stochastic given seed)
      2. Service each tenant at rate min(queue, quota_i * capacity)
      3. Optional quota update (policy) using *previous* usage signal (asof)
    """

    def __init__(self, cfg: SimConfig, target_shares: Optional[np.ndarray] = None):
        self.cfg = cfg
        self.n = cfg.n_tenants
        self.w_star = (
            np.ones(self.n) / self.n
            if target_shares is None
            else np.asarray(target_shares, dtype=float)
        )
        self.w_star = self.w_star / self.w_star.sum()
        self.rng = np.random.default_rng(cfg.seed)

    def demand_rates(self, t: int) -> np.ndarray:
        rates = np.full(self.n, self.cfg.base_rate, dtype=float)
        # rotate which tenant is hot
        if self.cfg.burst_every > 0:
            phase = (t // self.cfg.burst_every) % self.n
            pos = t % self.cfg.burst_every
            if pos < self.cfg.burst_len:
                rates[phase] *= self.cfg.burst_mult
        return rates

    def run(self, policy) -> Dict:
        cfg = self.cfg
        q = self.w_star.copy()  # quotas (shares)
        queue = np.zeros(self.n)
        served_hist = []
        queue_hist = []
        fairness_hist = []
        track_hist = []
        mig_cost_total = 0.0
        thrash_l1 = 0.0
        decisions = []
        prev_usage_share = self.w_star.copy()

        policy.reset(self.n, self.w_star)

        for t in range(cfg.steps):
            # --- asof decision: use state from end of t-1 (prev_usage_share, queue, q) ---
            new_q = policy.act(t, prev_usage_share, q, queue)
            if new_q is not None:
                new_q = np.asarray(new_q, dtype=float)
                new_q = np.clip(new_q, 0.0, None)
                s = new_q.sum()
                if s <= 1e-12:
                    new_q = self.w_star.copy()
                else:
                    new_q = new_q / s
                l1 = float(np.abs(new_q - q).sum())
                thrash_l1 += l1
                mig_cost_total += l1 * cfg.migration_cost_per_l1
                decisions.append(
                    {
                        "t": t,
                        "asof_t": t - 1,
                        "old_q": q.tolist(),
                        "new_q": new_q.tolist(),
                        "l1": l1,
                    }
                )
                q = new_q

            # arrivals + service (effective bar t)
            rates = self.demand_rates(t)
            arrivals = self.rng.poisson(rates)
            queue = queue + arrivals
            # capacity per tenant
            cap_i = q * cfg.capacity
            served = np.minimum(queue, cap_i)
            queue = queue - served
            served_hist.append(served.copy())
            queue_hist.append(queue.copy())
            # usage share this step
            tot = served.sum()
            if tot > 1e-12:
                prev_usage_share = served / tot
            else:
                prev_usage_share = self.w_star.copy()
            # drift quotas toward usage (pressure to abandon fair shares) — mirrors weight drift
            if cfg.drift_alpha > 0:
                q = (1.0 - cfg.drift_alpha) * q + cfg.drift_alpha * prev_usage_share
                q = np.clip(q, 0.0, None)
                q = q / (q.sum() + 1e-12)
            # fairness of *capacity shares* vs target (controller objective)
            # capacity-share fairness (how equal are quotas after drift/control)
            fairness_hist.append(jain_fairness(q + 1e-6))
            # tracking error to target shares
            track_hist.append(float(np.sum(np.abs(q - self.w_star))))

        served_arr = np.vstack(served_hist)
        queue_arr = np.vstack(queue_hist)
        lat = queue_arr.ravel()
        mean_served = served_arr.mean(axis=0)

        return {
            "jain_mean": float(np.mean(fairness_hist)),
            "jain_p10": float(np.quantile(fairness_hist, 0.10)),
            "mean_tracking_l1": float(np.mean(track_hist)),
            "mean_queue": float(np.mean(lat)),
            "p95_queue": float(np.quantile(lat, 0.95)),
            "migration_cost": float(mig_cost_total),
            "thrash_l1": float(thrash_l1),
            "mean_served_per_tenant": mean_served.tolist(),
            "n_rebalances": len(decisions),
            "utility": float(np.mean(fairness_hist) - 0.01 * mig_cost_total),
            "decisions": decisions,
            "fairness_series": fairness_hist,
        }
