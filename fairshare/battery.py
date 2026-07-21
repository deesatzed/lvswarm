"""Sealed batteries for fairshare lab."""

from __future__ import annotations

from typing import Any, Dict, List

from fairshare.policies import policy_factories
from fairshare.sim import FairShareSim, SimConfig


def run_arm(policy, cfg: SimConfig) -> Dict[str, Any]:
    sim = FairShareSim(cfg)
    out = sim.run(policy)
    return {
        "policy_id": policy.policy_id,
        "jain_mean": out["jain_mean"],
        "jain_p10": out["jain_p10"],
        "mean_tracking_l1": out["mean_tracking_l1"],
        "mean_queue": out["mean_queue"],
        "p95_queue": out["p95_queue"],
        "migration_cost": out["migration_cost"],
        "thrash_l1": out["thrash_l1"],
        "n_rebalances": out["n_rebalances"],
        "utility": out["utility"],
        "decisions": out["decisions"],
    }


def run_all(cfg: SimConfig) -> List[Dict[str, Any]]:
    rows = []
    for fac in policy_factories(cfg.migration_cost_per_l1):
        rows.append(run_arm(fac(), cfg))
    rows.sort(key=lambda r: (-r["jain_mean"], r["migration_cost"]))
    return rows


def cost_grid(costs: List[float], base: SimConfig) -> Dict[str, Any]:
    grid = []
    any_fair = False
    for c in costs:
        cfg = SimConfig(
            n_tenants=base.n_tenants,
            capacity=base.capacity,
            steps=base.steps,
            seed=base.seed,
            migration_cost_per_l1=c,
            base_rate=base.base_rate,
            burst_every=base.burst_every,
            burst_len=base.burst_len,
            burst_mult=base.burst_mult,
        )
        ranking = run_all(cfg)
        f0 = next(r for r in ranking if r["policy_id"] == "F0_never")
        dyn = [r for r in ranking if r["policy_id"] != "F0_never"]
        best = dyn[0]
        slim = [{k: v for k, v in r.items() if k != "decisions"} for r in ranking]
        edge = best["jain_mean"] > f0["jain_mean"] + 1e-4
        lat_ok = best["p95_queue"] <= f0["p95_queue"] * 1.1 + 1e-9
        if edge:
            any_fair = True
        grid.append(
            {
                "migration_cost_per_l1": c,
                "fairness_edge": edge,
                "latency_ok_for_best": lat_ok,
                "F0_jain": f0["jain_mean"],
                "best_id": best["policy_id"],
                "best_jain": best["jain_mean"],
                "F0_p95_queue": f0["p95_queue"],
                "best_p95_queue": best["p95_queue"],
                "ranking": slim,
            }
        )
    return {"grid": grid, "COST_REGIME_PASS": any_fair}
