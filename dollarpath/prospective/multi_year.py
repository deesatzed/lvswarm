"""Multi-year nested battery (report-only, Mode C)."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from dollarpath.eval.metrics import compute_metrics
from dollarpath.eval.runner import run_policy
from dollarpath.policies.baselines import HoldPolicy
from dollarpath.prospective.arms import select_template_on_history
from dollarpath.train.bandit import FixedTemplatePolicy


def multi_year_battery(
    prices: pd.DataFrame,
    years: List[int],
    history_start: str = "2018-01-01",
    embargo_bars: int = 5,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    every: int = 5,
    max_weight: float = 0.40,
    min_names: int = 3,
) -> List[Dict[str, Any]]:
    records = []
    for y in years:
        train = prices.loc[history_start : f"{y - 1}-12-31"]
        year_prices = prices.loc[f"{y}-01-01" : f"{y}-12-31"]
        if len(train) < 50 or len(year_prices) < embargo_bars + 10:
            records.append({"year": y, "skipped": True, "reason": "insufficient bars"})
            continue
        # embargo: skip first embargo_bars of year
        test = year_prices.iloc[embargo_bars:]
        if len(test) < 5:
            records.append({"year": y, "skipped": True, "reason": "test too short after embargo"})
            continue
        train_end = str(train.index[-1].date())
        test_start = str(test.index[0].date())
        row: Dict[str, Any] = {
            "year": y,
            "skipped": False,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": str(test.index[-1].date()),
            "embargo_bars": embargo_bars,
        }
        for name, constrained in (("B1", False), ("B2", True)):
            best_i, w, _ = select_template_on_history(
                train,
                constrained=constrained,
                max_weight=max_weight,
                min_names=min_names,
                start_capital=start_capital,
                cost_bps_one_way=cost_bps_one_way,
                every=every,
            )
            pol = FixedTemplatePolicy(w, every=every, policy_id=f"{name}_y{y}")
            equity, costs, _ = run_policy(
                test, pol, start_capital=start_capital, cost_bps_one_way=cost_bps_one_way
            )
            m = compute_metrics(equity, start_capital, costs, pol.policy_id, {"year": y})
            row[name] = {
                "selected_template": best_i,
                "weights": w.tolist(),
                "metrics": m,
            }
        # hold baseline on test
        eq_h, c_h, _ = run_policy(
            test, HoldPolicy(), start_capital=start_capital, cost_bps_one_way=cost_bps_one_way
        )
        row["A0"] = compute_metrics(eq_h, start_capital, c_h, "hold_equal", {"year": y})
        records.append(row)
    return records
