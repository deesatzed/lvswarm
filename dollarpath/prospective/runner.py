"""Multi-arm prospective historical replay under E1–E2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dollarpath.env.portfolio import PortfolioEnv
from dollarpath.eval.metrics import compute_metrics
from dollarpath.policies.baselines import CalendarRebalancePolicy, HoldPolicy, VolTargetPolicy
from dollarpath.prospective.arms import HoldQQQPolicy, select_template_on_history
from dollarpath.prospective.protocol import asof_index, assert_asof_ok, decision_indices, info_slice


@dataclass
class ProspectiveConfig:
    start_capital: float = 100_000.0
    cost_bps_one_way: float = 2.5
    decision_every: int = 5
    # Offline selection is expensive; re-select on this grid (still E1/E2).
    select_every: int = 21
    min_train_bars: int = 504
    max_weight_b2: float = 0.40
    min_names_b2: int = 3
    seed: int = 42


def _run_static_policy(
    prices: pd.DataFrame,
    policy,
    cfg: ProspectiveConfig,
) -> Tuple[pd.DataFrame, float, List[dict]]:
    """Run baseline policies with env; decisions logged with asof = step (env internal)."""
    env = PortfolioEnv(
        prices=prices,
        start_capital=cfg.start_capital,
        cost_bps_one_way=cfg.cost_bps_one_way,
    )
    policy.reset(env.n)
    env.reset()
    rows = []
    decisions = []
    total_costs = 0.0
    for step in range(env.n_steps):
        # env step index: at step s we apply action then move using return of bar s+1
        # Map to protocol: effective bar index in prices = env._i + 1 after... 
        # Before step, env._i is current index; step uses return iloc[_i+1]
        effective_t = env._i + 1  # bar index whose return we earn this step
        asof_i = asof_index(effective_t)
        assert_asof_ok(asof_i, effective_t)
        prices_so_far = info_slice(prices, effective_t)  # iloc[:effective_t] = through asof
        action = policy.act(step, prices_so_far, env.state.weights.copy())
        state, info = env.step(action)
        total_costs += info.costs
        rows.append(
            {
                "date": info.date,
                "wealth": info.wealth,
                "drawdown": info.drawdown,
                "exposure": float(np.sum(state.weights)),
                "turnover": info.turnover,
                "costs": info.costs,
                "reward": info.reward,
                "ruined": info.ruined,
            }
        )
        decisions.append(
            {
                "step": step,
                "date": info.date,
                "asof_date": str(prices.index[asof_i].date()),
                "effective_date": str(prices.index[effective_t].date()) if effective_t < len(prices) else info.date,
                "asof_i": asof_i,
                "effective_i": effective_t,
                "train_end": str(prices.index[asof_i].date()),
                "arm_id": getattr(policy, "policy_id", "unknown"),
                "weights": info.weights,
                "action": None if action is None else np.asarray(action).tolist(),
                "selected_template": None,
            }
        )
        if state.ruined:
            break
    return pd.DataFrame(rows), total_costs, decisions


def _run_selector_arm(
    prices: pd.DataFrame,
    constrained: bool,
    arm_id: str,
    cfg: ProspectiveConfig,
) -> Tuple[pd.DataFrame, float, List[dict]]:
    """
    Expanding-train offline selection under protocol.
    On decision days: select template using prices through asof only;
    hold those target weights until next decision.
    """
    env = PortfolioEnv(
        prices=prices,
        start_capital=cfg.start_capital,
        cost_bps_one_way=cfg.cost_bps_one_way,
    )
    env.reset()
    n = env.n
    current_target = np.ones(n) / n
    selected_template = None
    rows = []
    decisions = []
    total_costs = 0.0
    select_set = set(
        decision_indices(len(prices), every=cfg.select_every, min_effective=1)
    )
    rebalance_set = set(
        decision_indices(len(prices), every=cfg.decision_every, min_effective=1)
    )

    for step in range(env.n_steps):
        effective_t = env._i + 1
        asof_i = asof_index(effective_t)
        assert_asof_ok(asof_i, effective_t)
        hist = info_slice(prices, effective_t)

        action = None
        do_select = effective_t in select_set or step == 0
        do_rebalance = effective_t in rebalance_set or do_select or step == 0
        if do_select:
            if len(hist) >= cfg.min_train_bars:
                best_i, w, _ = select_template_on_history(
                    hist,
                    constrained=constrained,
                    max_weight=cfg.max_weight_b2,
                    min_names=cfg.min_names_b2,
                    start_capital=cfg.start_capital,
                    cost_bps_one_way=cfg.cost_bps_one_way,
                    every=cfg.decision_every,
                )
                current_target = np.asarray(w, dtype=float)
                selected_template = int(best_i)
            else:
                current_target = np.ones(n) / n
                selected_template = None
        if do_rebalance:
            action = current_target.copy()

        state, info = env.step(action)
        total_costs += info.costs
        rows.append(
            {
                "date": info.date,
                "wealth": info.wealth,
                "drawdown": info.drawdown,
                "exposure": float(np.sum(state.weights)),
                "turnover": info.turnover,
                "costs": info.costs,
                "reward": info.reward,
                "ruined": info.ruined,
            }
        )
        decisions.append(
            {
                "step": step,
                "date": info.date,
                "asof_date": str(prices.index[asof_i].date()),
                "effective_date": str(prices.index[min(effective_t, len(prices) - 1)].date()),
                "asof_i": asof_i,
                "effective_i": effective_t,
                "train_end": str(prices.index[asof_i].date()),
                "arm_id": arm_id,
                "weights": info.weights,
                "action": None if action is None else np.asarray(action).tolist(),
                "selected_template": selected_template,
                "hist_bars": len(hist),
            }
        )
        if state.ruined:
            break
    return pd.DataFrame(rows), total_costs, decisions


def run_all_arms(
    prices: pd.DataFrame,
    cfg: Optional[ProspectiveConfig] = None,
) -> Dict[str, Dict[str, Any]]:
    cfg = cfg or ProspectiveConfig()
    tickers = list(prices.columns)
    results: Dict[str, Dict[str, Any]] = {}

    arms = [
        ("A0", "hold_equal", lambda: HoldPolicy()),
        ("A1", "hold_qqq", lambda: HoldQQQPolicy(tickers)),
        ("A2", "calendar_equal", lambda: CalendarRebalancePolicy(every=21)),
        ("A3", "vol_target", lambda: VolTargetPolicy()),
    ]
    for arm_id, pid, factory in arms:
        pol = factory()
        pol.policy_id = pid  # type: ignore
        equity, costs, dec = _run_static_policy(prices, pol, cfg)
        metrics = compute_metrics(
            equity,
            cfg.start_capital,
            costs,
            pid,
            {"arm_id": arm_id, "seed": cfg.seed},
        )
        metrics["arm_id"] = arm_id
        results[arm_id] = {
            "metrics": metrics,
            "equity": equity,
            "decisions": dec,
            "total_costs": costs,
            "policy_id": pid,
        }

    for arm_id, constrained in (("B1", False), ("B2", True)):
        pid = "select_unconstrained" if not constrained else "select_constrained"
        equity, costs, dec = _run_selector_arm(prices, constrained, arm_id, cfg)
        metrics = compute_metrics(
            equity,
            cfg.start_capital,
            costs,
            pid,
            {"arm_id": arm_id, "seed": cfg.seed, "constrained": constrained},
        )
        metrics["arm_id"] = arm_id
        results[arm_id] = {
            "metrics": metrics,
            "equity": equity,
            "decisions": dec,
            "total_costs": costs,
            "policy_id": pid,
        }

    return results


def pass_b2_rule(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    b2 = results["B2"]["metrics"]
    bases = [results[a]["metrics"] for a in ("A0", "A2", "A3")]
    best_wealth = max(m["ending_wealth"] for m in bases)
    max_dd_bases = max(m["max_drawdown"] for m in bases)
    max_calmar = max(m["calmar"] for m in bases)
    beats_wealth = b2["ending_wealth"] > best_wealth
    dd_ok = b2["max_drawdown"] <= max_dd_bases * 1.20
    calmar_win = b2["calmar"] > max_calmar
    passed = bool(beats_wealth and (dd_ok or calmar_win))
    return {
        "passed_b2": passed,
        "beats_wealth": beats_wealth,
        "dd_ok": dd_ok,
        "calmar_win": calmar_win,
        "b2_ending_wealth": b2["ending_wealth"],
        "best_baseline_ending_wealth": best_wealth,
        "b2_max_drawdown": b2["max_drawdown"],
        "b2_calmar": b2["calmar"],
    }
