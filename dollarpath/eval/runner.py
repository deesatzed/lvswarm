"""Run a policy through PortfolioEnv and collect equity curve."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dollarpath.env.portfolio import PortfolioEnv
from dollarpath.policies.baselines import Policy


def run_policy(
    prices: pd.DataFrame,
    policy: Policy,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    rebalance_speed: float = 1.0,
) -> Tuple[pd.DataFrame, float, List[dict]]:
    env = PortfolioEnv(
        prices=prices,
        start_capital=start_capital,
        cost_bps_one_way=cost_bps_one_way,
        rebalance_speed=rebalance_speed,
    )
    policy.reset(env.n)
    env.reset()

    rows: List[dict] = []
    decisions: List[dict] = []
    total_costs = 0.0

    for step in range(env.n_steps):
        # prices available as-of current index env._i (before step uses i+1 return)
        prices_so_far = prices.iloc[: env._i + 1]
        if hasattr(policy, "set_drawdown"):
            policy.set_drawdown(env.state.drawdown)
        if hasattr(policy, "note_wealth"):
            policy.note_wealth(env.state.wealth)
        action = policy.act(step, prices_so_far, env.state.weights.copy())
        state, info = env.step(action)
        total_costs += info.costs
        exposure = float(np.sum(state.weights))
        rows.append(
            {
                "date": info.date,
                "wealth": info.wealth,
                "drawdown": info.drawdown,
                "exposure": exposure,
                "turnover": info.turnover,
                "costs": info.costs,
                "reward": info.reward,
                "ruined": info.ruined,
            }
        )
        dec = getattr(policy, "last_decision", None)
        decisions.append(
            {
                "step": step,
                "date": info.date,
                "action": None if action is None else np.asarray(action).tolist(),
                "weights": info.weights,
                "costs": info.costs,
                "wealth": info.wealth,
                "governor": dec,
            }
        )
        if state.ruined:
            break

    equity = pd.DataFrame(rows)
    return equity, total_costs, decisions
