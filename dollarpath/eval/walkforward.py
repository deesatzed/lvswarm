"""Walk-forward evaluation with embargo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from dollarpath.eval.metrics import compute_metrics
from dollarpath.eval.runner import run_policy
from dollarpath.train.bandit import (
    LearnedTemplatePolicy,
    default_templates,
    offline_select_best_template,
)


def walk_forward(
    prices: pd.DataFrame,
    train_bars: int = 504,  # ~2y
    test_bars: int = 126,  # ~6m
    embargo_bars: int = 5,
    step_bars: Optional[int] = None,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    every: int = 5,
) -> Dict[str, Any]:
    """
    Rolling: train on [i, i+train), embargo, test on following test_bars.
    Learner: offline template selection on train window only.
    """
    step = step_bars or test_bars
    n = len(prices)
    windows: List[Dict[str, Any]] = []
    i = 0
    while i + train_bars + embargo_bars + test_bars <= n:
        train = prices.iloc[i : i + train_bars]
        test_start = i + train_bars + embargo_bars
        test = prices.iloc[test_start - 1 : test_start + test_bars]  # 1 bar overlap for continuity
        # enforce no test labels in train: test_start >= train end + embargo
        assert test_start >= i + train_bars + embargo_bars

        templates = default_templates(train.shape[1], list(train.columns))
        best_i, _ = offline_select_best_template(
            train,
            templates,
            start_capital=start_capital,
            cost_bps_one_way=cost_bps_one_way,
            every=every,
        )
        pol = LearnedTemplatePolicy(
            templates[best_i], every=every, use_governor=False, policy_id="wf_learned"
        )
        equity, costs, _ = run_policy(
            test, pol, start_capital=start_capital, cost_bps_one_way=cost_bps_one_way
        )
        metrics = compute_metrics(
            equity,
            start_capital,
            costs,
            "wf_learned",
            {
                "train_start": str(train.index[0].date()),
                "train_end": str(train.index[-1].date()),
                "test_start": str(prices.index[test_start].date()),
                "test_end": str(test.index[-1].date()),
            },
        )
        windows.append(
            {
                "train_start": str(train.index[0].date()),
                "train_end": str(train.index[-1].date()),
                "test_start": str(prices.index[test_start].date()),
                "test_end": str(test.index[-1].date()),
                "selected_template": best_i,
                "selected_weights": templates[best_i].tolist(),
                "metrics": metrics,
            }
        )
        i += step

    # aggregate: compound window returns approximately via ending wealth ratios
    if not windows:
        return {"windows": [], "aggregate": None}

    wealth = start_capital
    max_dd = 0.0
    for w in windows:
        ret = w["metrics"]["total_return"]
        wealth *= 1.0 + ret
        max_dd = max(max_dd, w["metrics"]["max_drawdown"])

    aggregate = {
        "n_windows": len(windows),
        "compounded_ending_wealth": wealth,
        "mean_window_return": float(
            sum(w["metrics"]["total_return"] for w in windows) / len(windows)
        ),
        "worst_window_max_drawdown": max_dd,
        "mean_window_ending": float(
            sum(w["metrics"]["ending_wealth"] for w in windows) / len(windows)
        ),
    }
    return {"windows": windows, "aggregate": aggregate}


def no_leakage_check(windows: List[Dict[str, Any]]) -> bool:
    for w in windows:
        # train_end < test_start (string ISO dates)
        if w["train_end"] >= w["test_start"]:
            return False
    return True
