"""GOAL_FAIRSHARE_V2 batteries: Pareto, demand stress, multi-seed."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from fairshare.battery import run_all, run_arm
from fairshare.policies import (
    BandAlphaPolicy,
    CostAwarePolicy,
    CostAwareV2Policy,
    NeverPolicy,
    ThresholdPolicy,
    policy_factories,
)
from fairshare.sim import SimConfig


def _slim(r: dict) -> dict:
    return {k: v for k, v in r.items() if k != "decisions"}


def pareto_points(points: List[dict]) -> List[dict]:
    """Maximize jain_mean, minimize p95_queue and migration_cost (lex via pairwise)."""
    pareto = []
    for p in points:
        dominated = False
        for q in points:
            if q is p:
                continue
            better_or_eq = (
                q["jain_mean"] >= p["jain_mean"] - 1e-12
                and q["p95_queue"] <= p["p95_queue"] + 1e-12
                and q["migration_cost"] <= p["migration_cost"] + 1e-12
            )
            strict = (
                q["jain_mean"] > p["jain_mean"] + 1e-12
                or q["p95_queue"] < p["p95_queue"] - 1e-12
                or q["migration_cost"] < p["migration_cost"] - 1e-12
            )
            if better_or_eq and strict:
                dominated = True
                break
        if not dominated:
            pareto.append(p)
    pareto.sort(key=lambda x: (-x["jain_mean"], x["p95_queue"], x["migration_cost"]))
    return pareto


def run_frontier_at_cost(cfg: SimConfig) -> Dict[str, Any]:
    points = []
    for fac in policy_factories(cfg.migration_cost_per_l1):
        points.append(_slim(run_arm(fac(), cfg)))

    bands = [0.02, 0.05, 0.07, 0.10, 0.15]
    alphas = [0.25, 0.5, 1.0]
    for b in bands:
        for a in alphas:
            pol = BandAlphaPolicy(b, a, every=5)
            points.append(_slim(run_arm(pol, cfg)))

    return {
        "migration_cost_per_l1": cfg.migration_cost_per_l1,
        "points": points,
        "pareto": pareto_points(points),
    }


def demand_stress_battery(base: SimConfig) -> Dict[str, Any]:
    configs = [
        {"name": "baseline", "burst_mult": 4.0, "burst_len": 30, "burst_every": 200},
        {"name": "mild", "burst_mult": 2.0, "burst_len": 20, "burst_every": 250},
        {"name": "harsh", "burst_mult": 8.0, "burst_len": 50, "burst_every": 150},
        {"name": "long_burst", "burst_mult": 4.0, "burst_len": 80, "burst_every": 200},
        {"name": "frequent", "burst_mult": 4.0, "burst_len": 25, "burst_every": 80},
        {"name": "extreme", "burst_mult": 12.0, "burst_len": 40, "burst_every": 100},
    ]
    rows = []
    f3_beats = 0
    for c in configs:
        cfg = SimConfig(
            n_tenants=base.n_tenants,
            capacity=base.capacity,
            steps=base.steps,
            seed=base.seed,
            migration_cost_per_l1=base.migration_cost_per_l1,
            base_rate=base.base_rate,
            burst_every=c["burst_every"],
            burst_len=c["burst_len"],
            burst_mult=c["burst_mult"],
            drift_alpha=base.drift_alpha,
        )
        f0 = _slim(run_arm(NeverPolicy(), cfg))
        f3 = _slim(run_arm(ThresholdPolicy(0.05, "F3_threshold_0.05"), cfg))
        f7 = _slim(run_arm(CostAwarePolicy(25, 0.05, 2.0, cfg.migration_cost_per_l1), cfg))
        f7b = _slim(
            run_arm(
                CostAwareV2Policy(50, 0.05, 1.5, cfg.migration_cost_per_l1, 0.05),
                cfg,
            )
        )
        beats = f3["jain_mean"] > f0["jain_mean"] + 1e-4
        if beats:
            f3_beats += 1
        rows.append(
            {
                "name": c["name"],
                "params": c,
                "F0": f0,
                "F3": f3,
                "F7": f7,
                "F7b": f7b,
                "F3_beats_F0_jain": beats,
            }
        )
    return {
        "configs": rows,
        "STRESS_STABLE_frac": f3_beats / max(len(configs), 1),
        "STRESS_STABLE": f3_beats / max(len(configs), 1) >= 0.8,
    }


def multi_seed_ci(
    base: SimConfig,
    seeds: Optional[List[int]] = None,
) -> Dict[str, Any]:
    seeds = seeds if seeds is not None else list(range(20))
    d_jain = []
    d_p95 = []
    f7b_rebals = []
    f7_rebals = []
    for s in seeds:
        cfg = SimConfig(
            n_tenants=base.n_tenants,
            capacity=base.capacity,
            steps=base.steps,
            seed=int(s),
            migration_cost_per_l1=base.migration_cost_per_l1,
            base_rate=base.base_rate,
            burst_every=base.burst_every,
            burst_len=base.burst_len,
            burst_mult=base.burst_mult,
            drift_alpha=base.drift_alpha,
        )
        f0 = run_arm(NeverPolicy(), cfg)
        f3 = run_arm(ThresholdPolicy(0.05), cfg)
        f7 = run_arm(CostAwarePolicy(25, 0.05, 2.0, cfg.migration_cost_per_l1), cfg)
        f7b = run_arm(CostAwareV2Policy(50, 0.05, 1.5, cfg.migration_cost_per_l1), cfg)
        d_jain.append(f3["jain_mean"] - f0["jain_mean"])
        d_p95.append(f3["p95_queue"] - f0["p95_queue"])
        f7_rebals.append(f7["n_rebalances"])
        f7b_rebals.append(f7b["n_rebalances"])

    def summary(arr: List[float]) -> dict:
        a = np.asarray(arr, dtype=float)
        lo, hi = np.quantile(a, [0.05, 0.95])
        return {
            "mean": float(np.mean(a)),
            "std": float(np.std(a)),
            "ci90_low": float(lo),
            "ci90_high": float(hi),
            "frac_positive": float(np.mean(a > 0)),
        }

    return {
        "n_seeds": len(seeds),
        "seeds": seeds,
        "delta_jain_F3_minus_F0": summary(d_jain),
        "delta_p95_F3_minus_F0": summary(d_p95),
        "F7_mean_n_rebalances": float(np.mean(f7_rebals)),
        "F7b_mean_n_rebalances": float(np.mean(f7b_rebals)),
        "F7b_more_active_than_F7": float(np.mean(f7b_rebals)) > float(np.mean(f7_rebals)),
    }
