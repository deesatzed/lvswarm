"""Run fixed-target rebalance arms under no-lookahead protocol."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dollarpath.env.portfolio import PortfolioEnv
from dollarpath.eval.metrics import compute_metrics
from dollarpath.prospective.protocol import asof_index, assert_asof_ok, info_slice
from dollarpath.rebalance.policies import RebalancePolicy, all_rebalance_policies
from dollarpath.rebalance.target import TargetSpec, distance_to_target, equal_weight_target


def run_rebalance_policy(
    prices: pd.DataFrame,
    policy: RebalancePolicy,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
) -> Tuple[pd.DataFrame, float, List[dict], dict]:
    env = PortfolioEnv(
        prices=prices,
        start_capital=start_capital,
        cost_bps_one_way=cost_bps_one_way,
    )
    policy.reset(env.n)
    env.reset()
    w_star = policy.target.as_array()
    rows = []
    decisions = []
    total_costs = 0.0
    te_sum = 0.0
    te_n = 0

    for step in range(env.n_steps):
        effective_t = env._i + 1
        asof_i = asof_index(effective_t)
        assert_asof_ok(asof_i, effective_t)
        prices_so_far = info_slice(prices, effective_t)
        action = policy.act(step, prices_so_far, env.state.weights.copy())
        state, info = env.step(action)
        total_costs += info.costs
        dist = distance_to_target(state.weights, w_star)
        te_sum += dist["l1"]
        te_n += 1
        rows.append(
            {
                "date": info.date,
                "wealth": info.wealth,
                "drawdown": info.drawdown,
                "exposure": float(np.sum(state.weights)),
                "turnover": info.turnover,
                "costs": info.costs,
                "reward": info.reward,
                "tracking_l1": dist["l1"],
                "tracking_max_abs": dist["max_abs"],
                "ruined": info.ruined,
            }
        )
        decisions.append(
            {
                "step": step,
                "date": info.date,
                "asof_date": str(prices.index[asof_i].date()),
                "asof_i": asof_i,
                "effective_i": effective_t,
                "train_end": str(prices.index[asof_i].date()),
                "arm_id": policy.policy_id,
                "action": None if action is None else np.asarray(action).tolist(),
                "weights": info.weights,
                "tracking_l1": dist["l1"],
            }
        )
        if state.ruined:
            break

    equity = pd.DataFrame(rows)
    extra = {"mean_tracking_l1": te_sum / max(te_n, 1)}
    return equity, total_costs, decisions, extra


def run_all_rebalance_arms(
    prices: pd.DataFrame,
    tickers: Optional[List[str]] = None,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    target: Optional[TargetSpec] = None,
    target_name: str = "equal_weight",
) -> Dict[str, Dict[str, Any]]:
    tickers = tickers or list(prices.columns)
    if target is None:
        target = equal_weight_target(tickers)
    results = {}
    for pol in all_rebalance_policies(target, cost_bps_one_way=cost_bps_one_way):
        equity, costs, dec, extra = run_rebalance_policy(
            prices, pol, start_capital=start_capital, cost_bps_one_way=cost_bps_one_way
        )
        metrics = compute_metrics(
            equity,
            start_capital,
            costs,
            pol.policy_id,
            {"target": target_name, "arm_id": pol.policy_id},
        )
        metrics["mean_tracking_l1"] = extra["mean_tracking_l1"]
        metrics["arm_id"] = pol.policy_id
        results[pol.policy_id] = {
            "metrics": metrics,
            "equity": equity,
            "decisions": dec,
            "policy_id": pol.policy_id,
        }
    return results
