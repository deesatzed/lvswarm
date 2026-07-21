"""GOAL_REBAL v2 sealed battery: cost grid, multi-target, multi-year."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from dollarpath.rebalance.runner import run_all_rebalance_arms
from dollarpath.rebalance.target import equal_weight_target, sixty_forty_target


def _summarize_arms(results: Dict[str, Dict[str, Any]]) -> List[dict]:
    rows = []
    for pid, pack in results.items():
        m = pack["metrics"]
        rows.append(
            {
                "policy_id": pid,
                "ending_wealth": m["ending_wealth"],
                "max_drawdown": m["max_drawdown"],
                "total_costs": m["total_costs"],
                "mean_turnover": m["mean_turnover"],
                "mean_tracking_l1": m.get("mean_tracking_l1"),
            }
        )
    rows.sort(key=lambda r: r["ending_wealth"], reverse=True)
    return rows


def _flags_from_ranking(ranking: List[dict]) -> Dict[str, Any]:
    r0 = next(r for r in ranking if r["policy_id"] == "R0_never")
    dyn = [r for r in ranking if r["policy_id"] != "R0_never"]
    best = dyn[0] if dyn else None
    wealth_edge = bool(best and best["ending_wealth"] > r0["ending_wealth"])
    # tracking value: among arms within 2% wealth of R0, min tracking
    near = [r for r in ranking if r["ending_wealth"] >= 0.98 * r0["ending_wealth"]]
    if near:
        track_best = min(near, key=lambda r: r["mean_tracking_l1"] or 1e9)
    else:
        track_best = min(ranking, key=lambda r: r["mean_tracking_l1"] or 1e9)
    return {
        "wealth_edge": wealth_edge,
        "r0_ending": r0["ending_wealth"],
        "best_dynamic_id": best["policy_id"] if best else None,
        "best_dynamic_ending": best["ending_wealth"] if best else None,
        "tracking_pick_id": track_best["policy_id"],
        "tracking_pick_l1": track_best["mean_tracking_l1"],
        "tracking_pick_ending": track_best["ending_wealth"],
    }


def run_cost_grid(
    prices: pd.DataFrame,
    tickers: Sequence[str],
    costs: Optional[List[float]] = None,
    start_capital: float = 100_000.0,
) -> Dict[str, Any]:
    costs = costs or [0.0, 1.0, 2.5, 5.0, 10.0, 25.0]
    target = equal_weight_target(tickers)
    grid = []
    any_dynamic_wins = False
    for bps in costs:
        res = run_all_rebalance_arms(
            prices,
            tickers=list(tickers),
            start_capital=start_capital,
            cost_bps_one_way=bps,
            target=target,
            target_name="T-EQ",
        )
        ranking = _summarize_arms(res)
        flags = _flags_from_ranking(ranking)
        if flags["wealth_edge"]:
            any_dynamic_wins = True
        grid.append({"cost_bps_one_way": bps, "ranking": ranking, "flags": flags})
    return {
        "target": "T-EQ",
        "grid": grid,
        "COST_REGIME_PASS": any_dynamic_wins,
    }


def run_target_snapshot(
    prices: pd.DataFrame,
    tickers: Sequence[str],
    target_name: str,
    cost_bps: float = 2.5,
    start_capital: float = 100_000.0,
) -> Dict[str, Any]:
    if target_name == "T-64":
        target = sixty_forty_target(tickers)
    else:
        target = equal_weight_target(tickers)
        target_name = "T-EQ"
    res = run_all_rebalance_arms(
        prices,
        tickers=list(tickers),
        start_capital=start_capital,
        cost_bps_one_way=cost_bps,
        target=target,
        target_name=target_name,
    )
    ranking = _summarize_arms(res)
    return {
        "target": target_name,
        "weights": list(target.weights),
        "tickers": list(target.tickers),
        "cost_bps_one_way": cost_bps,
        "ranking": ranking,
        "flags": _flags_from_ranking(ranking),
        "full_results_metrics": {k: v["metrics"] for k, v in res.items()},
        "_results": res,  # for optional arm dumps / audit
    }


def run_multi_year(
    prices_all: pd.DataFrame,
    tickers: Sequence[str],
    years: Optional[List[int]] = None,
    cost_bps: float = 2.5,
    start_capital: float = 100_000.0,
) -> Dict[str, Any]:
    years = years or [2020, 2021, 2022, 2023, 2024]
    target = equal_weight_target(tickers)
    records = []
    wins = 0
    n = 0
    for y in years:
        yp = prices_all.loc[f"{y}-01-01" : f"{y}-12-31"]
        if len(yp) < 40:
            records.append({"year": y, "skipped": True, "reason": "short year"})
            continue
        res = run_all_rebalance_arms(
            yp,
            tickers=list(tickers),
            start_capital=start_capital,
            cost_bps_one_way=cost_bps,
            target=target,
            target_name="T-EQ",
        )
        ranking = _summarize_arms(res)
        flags = _flags_from_ranking(ranking)
        n += 1
        if flags["wealth_edge"]:
            wins += 1
        records.append(
            {
                "year": y,
                "skipped": False,
                "ranking": ranking,
                "flags": flags,
            }
        )
    return {
        "target": "T-EQ",
        "cost_bps_one_way": cost_bps,
        "years": records,
        "fraction_years_dynamic_beats_r0": (wins / n) if n else None,
        "years_dynamic_beats_r0": wins,
        "years_evaluated": n,
    }
