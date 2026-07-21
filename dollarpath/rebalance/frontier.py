"""Frontier batteries for GOAL_REBAL_V3."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from dollarpath.rebalance.band_alpha import BandAlphaRebalancePolicy
from dollarpath.rebalance.policies import (
    CalendarRebalanceToTarget,
    CostAwareRebalanceV2Policy,
    NeverRebalancePolicy,
)
from dollarpath.rebalance.runner import run_rebalance_policy
from dollarpath.rebalance.target import equal_weight_target


def _metrics_row(policy_id: str, equity: pd.DataFrame, costs: float, extra: dict, capital: float) -> dict:
    from dollarpath.eval.metrics import compute_metrics

    m = compute_metrics(equity, capital, costs, policy_id, {"arm_id": policy_id})
    m["mean_tracking_l1"] = extra.get("mean_tracking_l1")
    m["policy_id"] = policy_id
    return m


def run_policy_metrics(
    prices: pd.DataFrame,
    policy,
    capital: float = 100_000.0,
    cost_bps: float = 2.5,
) -> dict:
    equity, costs, _, extra = run_rebalance_policy(
        prices, policy, start_capital=capital, cost_bps_one_way=cost_bps
    )
    return _metrics_row(policy.policy_id, equity, costs, extra, capital)


def fine_cost_grid(
    prices: pd.DataFrame,
    tickers: Sequence[str],
    cost_grid: Optional[List[float]] = None,
    capital: float = 100_000.0,
) -> Dict[str, Any]:
    cost_grid = cost_grid or [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
        1.25,
        1.5,
        1.75,
        2.0,
        2.25,
        2.5,
        3.0,
        4.0,
        5.0,
        7.5,
        10.0,
        15.0,
        25.0,
    ]
    target = equal_weight_target(tickers)
    rows = []
    break_even = None
    for bps in cost_grid:
        arms = [
            NeverRebalancePolicy(target),
            CalendarRebalanceToTarget(target, every=63, policy_id="R2_calendar_63"),
            CostAwareRebalanceV2Policy(target, cost_bps_one_way=bps, policy_id="R7b_cost_aware_v2"),
        ]
        metrics = {}
        for pol in arms:
            metrics[pol.policy_id] = run_policy_metrics(prices, pol, capital=capital, cost_bps=bps)
        r0 = metrics["R0_never"]["ending_wealth"]
        dyn_ids = [k for k in metrics if k != "R0_never"]
        best_id = max(dyn_ids, key=lambda k: metrics[k]["ending_wealth"])
        best_w = metrics[best_id]["ending_wealth"]
        edge = best_w >= r0 - 1e-9
        if edge and break_even is None:
            # first (lowest) bps where dynamic wins — scan ascending
            pass
        rows.append(
            {
                "cost_bps_one_way": bps,
                "R0_ending": r0,
                "best_dynamic_id": best_id,
                "best_dynamic_ending": best_w,
                "delta": best_w - r0,
                "wealth_edge": bool(best_w > r0),
                "metrics": {k: {"ending_wealth": v["ending_wealth"], "mean_tracking_l1": v["mean_tracking_l1"], "total_costs": v["total_costs"]} for k, v in metrics.items()},
            }
        )
    # break-even: smallest bps with wealth_edge True when scanning low→high;
    # also largest bps still True (edge region)
    edge_bps = [r["cost_bps_one_way"] for r in rows if r["wealth_edge"]]
    if edge_bps:
        break_even_max = max(edge_bps)  # rebalance can win up to this fee
        break_even_min = min(edge_bps)
    else:
        break_even_max = None
        break_even_min = None
    # first crossing from win to lose when fees rise
    cross = None
    for i in range(len(rows) - 1):
        if rows[i]["wealth_edge"] and not rows[i + 1]["wealth_edge"]:
            # interpolate roughly mid
            cross = 0.5 * (rows[i]["cost_bps_one_way"] + rows[i + 1]["cost_bps_one_way"])
            break
    return {
        "grid": rows,
        "edge_bps_list": edge_bps,
        "break_even_region_min_bps": break_even_min,
        "break_even_region_max_bps": break_even_max,
        "approx_cross_bps_to_never_wins": cross,
    }


def band_alpha_frontier(
    prices: pd.DataFrame,
    tickers: Sequence[str],
    bands: Optional[List[float]] = None,
    alphas: Optional[List[float]] = None,
    cost_bps: float = 2.5,
    capital: float = 100_000.0,
    check_every: int = 5,
) -> Dict[str, Any]:
    bands = bands or [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.12, 0.15, 0.20]
    alphas = alphas or [0.25, 0.5, 0.75, 1.0]
    target = equal_weight_target(tickers)
    points = []

    # anchors
    for pol in (
        NeverRebalancePolicy(target),
        CalendarRebalanceToTarget(target, every=63, policy_id="R2_calendar_63"),
        CostAwareRebalanceV2Policy(target, cost_bps_one_way=cost_bps, policy_id="R7b_cost_aware_v2"),
    ):
        m = run_policy_metrics(prices, pol, capital=capital, cost_bps=cost_bps)
        points.append(
            {
                "policy_id": m["policy_id"],
                "band": None,
                "alpha": None,
                "ending_wealth": m["ending_wealth"],
                "mean_tracking_l1": m["mean_tracking_l1"],
                "total_costs": m["total_costs"],
                "max_drawdown": m["max_drawdown"],
                "mean_turnover": m["mean_turnover"],
            }
        )

    for b in bands:
        for a in alphas:
            pol = BandAlphaRebalancePolicy(target, band=b, alpha=a, check_every=check_every)
            m = run_policy_metrics(prices, pol, capital=capital, cost_bps=cost_bps)
            points.append(
                {
                    "policy_id": pol.policy_id,
                    "band": b,
                    "alpha": a,
                    "ending_wealth": m["ending_wealth"],
                    "mean_tracking_l1": m["mean_tracking_l1"],
                    "total_costs": m["total_costs"],
                    "max_drawdown": m["max_drawdown"],
                    "mean_turnover": m["mean_turnover"],
                }
            )

    # Pareto: maximize wealth, minimize tracking_l1
    pareto = []
    for p in points:
        dominated = False
        for q in points:
            if q is p:
                continue
            # q dominates p if q wealth >= p wealth AND q track <= p track, strict in one
            if (
                q["ending_wealth"] >= p["ending_wealth"] - 1e-9
                and (q["mean_tracking_l1"] or 0) <= (p["mean_tracking_l1"] or 0) + 1e-12
                and (
                    q["ending_wealth"] > p["ending_wealth"] + 1e-9
                    or (q["mean_tracking_l1"] or 0) < (p["mean_tracking_l1"] or 0) - 1e-12
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto.append(p)

    pareto.sort(key=lambda x: -x["ending_wealth"])
    return {"cost_bps_one_way": cost_bps, "points": points, "pareto": pareto}


def _block_bootstrap_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Return index path of length n by sampling blocks with replacement."""
    if n <= 0:
        return np.array([], dtype=int)
    block = max(1, min(block, n))
    starts = np.arange(0, n - block + 1)
    if len(starts) == 0:
        starts = np.array([0])
        block = n
    out = []
    while len(out) < n:
        s = int(rng.choice(starts))
        out.extend(range(s, s + block))
    return np.array(out[:n], dtype=int)


def bootstrap_wealth_delta(
    prices: pd.DataFrame,
    tickers: Sequence[str],
    cost_bps: float = 2.5,
    capital: float = 100_000.0,
    n_boot: int = 200,
    block: int = 21,
    seed: int = 42,
    policy_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Block-bootstrap the *return path* and re-run R0 vs selected policies.
    Rebuilds a price path from bootstrapped simple returns (cumulative).
    """
    target = equal_weight_target(tickers)
    rng = np.random.default_rng(seed)
    rets = prices.pct_change().iloc[1:].to_numpy(dtype=float)
    rets = np.nan_to_num(rets, nan=0.0)
    n = rets.shape[0]
    p0 = prices.iloc[0].to_numpy(dtype=float)

    def make_prices(idx: np.ndarray) -> pd.DataFrame:
        path = [p0]
        for i in idx:
            path.append(path[-1] * (1.0 + rets[i]))
        arr = np.vstack(path)
        # dates fake sequential
        idx_dates = pd.bdate_range(prices.index[0], periods=len(arr))
        return pd.DataFrame(arr, index=idx_dates, columns=list(prices.columns))

    policies_factory = {
        "R0_never": lambda: NeverRebalancePolicy(target),
        "R2_calendar_63": lambda: CalendarRebalanceToTarget(target, every=63, policy_id="R2_calendar_63"),
        "R7b_cost_aware_v2": lambda: CostAwareRebalanceV2Policy(
            target, cost_bps_one_way=cost_bps, policy_id="R7b_cost_aware_v2"
        ),
    }
    # also best band-alpha at this cost from a quick default mid point
    policies_factory["Rba_b0.1_a0.5"] = lambda: BandAlphaRebalancePolicy(
        target, band=0.10, alpha=0.5, check_every=5, policy_id="Rba_b0.1_a0.5"
    )

    if policy_ids is None:
        policy_ids = ["R7b_cost_aware_v2", "R2_calendar_63", "Rba_b0.1_a0.5"]

    # point estimate on real path
    def wealth(pol_id: str, px: pd.DataFrame) -> float:
        pol = policies_factory[pol_id]()
        m = run_policy_metrics(px, pol, capital=capital, cost_bps=cost_bps)
        return float(m["ending_wealth"])

    w0_real = wealth("R0_never", prices)
    real_deltas = {}
    for pid in policy_ids:
        real_deltas[pid] = wealth(pid, prices) - w0_real

    boot = {pid: [] for pid in policy_ids}
    for _ in range(n_boot):
        idx = _block_bootstrap_indices(n, block, rng)
        px = make_prices(idx)
        w0 = wealth("R0_never", px)
        for pid in policy_ids:
            boot[pid].append(wealth(pid, px) - w0)

    summary = {}
    for pid in policy_ids:
        arr = np.asarray(boot[pid], dtype=float)
        lo, hi = np.quantile(arr, [0.05, 0.95])
        summary[pid] = {
            "real_delta": real_deltas[pid],
            "boot_mean": float(np.mean(arr)),
            "ci90_low": float(lo),
            "ci90_high": float(hi),
            "ci90_excludes_zero": bool(lo > 0 or hi < 0),
            "frac_boot_positive": float(np.mean(arr > 0)),
        }
    return {
        "cost_bps_one_way": cost_bps,
        "n_boot": n_boot,
        "block": block,
        "seed": seed,
        "R0_real_ending": w0_real,
        "deltas_vs_R0": summary,
    }
