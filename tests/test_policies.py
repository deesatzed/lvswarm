"""Policy determinism tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dollarpath.eval.runner import run_policy
from dollarpath.policies.baselines import CalendarRebalancePolicy, HoldPolicy


def _prices(n=60):
    idx = pd.bdate_range("2020-01-01", periods=n)
    t = np.arange(n)
    return pd.DataFrame(
        {
            "X": 100 * (1.001**t),
            "Y": 100 * (1.0005**t),
        },
        index=idx,
    )


def test_hold_lower_turnover_than_calendar():
    prices = _prices()
    eq_h, _, _ = run_policy(prices, HoldPolicy(), cost_bps_one_way=2.5)
    eq_c, _, _ = run_policy(prices, CalendarRebalancePolicy(every=5), cost_bps_one_way=2.5)
    assert eq_h["turnover"].sum() < eq_c["turnover"].sum()


def test_hold_deterministic():
    prices = _prices()
    e1, c1, _ = run_policy(prices, HoldPolicy(), start_capital=50_000.0)
    e2, c2, _ = run_policy(prices, HoldPolicy(), start_capital=50_000.0)
    assert e1["wealth"].tolist() == e2["wealth"].tolist()
    assert c1 == c2
