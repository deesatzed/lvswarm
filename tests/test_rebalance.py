"""Fixed-target rebalance policy tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dollarpath.rebalance.policies import (
    CalendarRebalanceToTarget,
    NeverRebalancePolicy,
    PartialRebalancePolicy,
    ThresholdRebalancePolicy,
)
from dollarpath.rebalance.target import distance_to_target, equal_weight_target


def test_distance_to_target():
    t = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    c = np.array([0.4, 0.1, 0.2, 0.2, 0.1])
    d = distance_to_target(c, t)
    assert d["max_abs"] == pytest_approx(0.2)
    assert d["l1"] > 0


def pytest_approx(x):
    return x  # use numpy below


def test_distance_max_abs():
    t = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    c = np.array([0.4, 0.1, 0.2, 0.2, 0.1])
    d = distance_to_target(c, t)
    assert abs(d["max_abs"] - 0.2) < 1e-12


def test_threshold_fires_when_drifted():
    target = equal_weight_target(["A", "B"])
    pol = ThresholdRebalancePolicy(target, band=0.05)
    pol.reset(2)
    # init
    a0 = pol.act(0, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.0, 0.0]))
    assert a0 is not None
    # drifted beyond band
    a1 = pol.act(1, pd.DataFrame({"A": [1.0, 1.1], "B": [1.0, 0.9]}), np.array([0.8, 0.2]))
    assert a1 is not None
    assert abs(a1[0] - 0.5) < 1e-12
    # inside band
    a2 = pol.act(2, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.52, 0.48]))
    assert a2 is None


def test_partial_moves_partway():
    target = equal_weight_target(["A", "B"])
    pol = PartialRebalancePolicy(target, alpha=0.5, every=1)
    pol.reset(2)
    pol.act(0, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.zeros(2))
    out = pol.act(1, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([1.0, 0.0]))
    assert out is not None
    # halfway from [1,0] to [0.5,0.5] => [0.75, 0.25]
    assert abs(out[0] - 0.75) < 1e-12
    assert abs(out[1] - 0.25) < 1e-12


def test_never_only_once():
    target = equal_weight_target(["A", "B"])
    pol = NeverRebalancePolicy(target)
    pol.reset(2)
    assert pol.act(0, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.zeros(2)) is not None
    assert pol.act(1, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.5, 0.5])) is None


def test_calendar_on_schedule():
    target = equal_weight_target(["A", "B"])
    pol = CalendarRebalanceToTarget(target, every=5)
    pol.reset(2)
    pol.act(0, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.zeros(2))
    assert pol.act(3, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.6, 0.4])) is None
    assert pol.act(5, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.6, 0.4])) is not None


def test_r7b_skips_tiny_drift():
    from dollarpath.rebalance.policies import CostAwareRebalanceV2Policy

    target = equal_weight_target(["A", "B"])
    pol = CostAwareRebalanceV2Policy(target, check_every=1, band=0.05, k=2.0)
    pol.reset(2)
    pol.act(0, pd.DataFrame({"A": [100.0], "B": [100.0]}), np.zeros(2))
    # tiny drift inside band
    out = pol.act(
        1,
        pd.DataFrame({"A": [100.0, 101.0], "B": [100.0, 100.5]}),
        np.array([0.51, 0.49]),
    )
    assert out is None


def test_sixty_forty_sums_to_one():
    from dollarpath.rebalance.target import sixty_forty_target

    t = sixty_forty_target(["SPY", "QQQ", "IWM", "TLT", "GLD"])
    assert abs(sum(t.weights) - 1.0) < 1e-12
    assert t.weights[0] == 0.30


def test_band_alpha_triggers():
    from dollarpath.rebalance.band_alpha import BandAlphaRebalancePolicy

    target = equal_weight_target(["A", "B"])
    pol = BandAlphaRebalancePolicy(target, band=0.05, alpha=0.5, check_every=1)
    pol.reset(2)
    pol.act(0, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.zeros(2))
    out = pol.act(1, pd.DataFrame({"A": [1.0], "B": [1.0]}), np.array([0.9, 0.1]))
    assert out is not None
    # halfway from 0.9/0.1 to 0.5/0.5
    assert abs(out[0] - 0.7) < 1e-9
