"""Protocol + planted leakage tests (GOAL_NEXT N1–N2)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dollarpath.env.portfolio import PortfolioEnv
from dollarpath.prospective.protocol import (
    asof_index,
    assert_asof_ok,
    decision_indices,
    info_slice,
)


def test_info_slice_asof_is_t_minus_1():
    idx = pd.bdate_range("2020-01-01", periods=20)
    prices = pd.DataFrame({"A": np.arange(20, dtype=float) + 100}, index=idx)
    effective_t = 10
    hist = info_slice(prices, effective_t)
    assert len(hist) == 10
    assert hist.index[-1] == prices.index[9]
    assert asof_index(effective_t) == 9
    assert_asof_ok(9, 10)
    with pytest.raises(AssertionError):
        assert_asof_ok(10, 10)


def test_decision_indices():
    idxs = decision_indices(100, every=5, min_effective=1)
    assert idxs[0] == 1
    assert all(i % 5 == 1 or i == 1 for i in idxs) or idxs[0] == 1
    assert idxs == list(range(1, 100, 5))


def test_planted_jump_not_captured_with_protocol():
    """
    Flat prices then huge jump on day T*.
    Protocol: action for day T* only sees data through T*-1, so equal-hold
    from before jump cannot reweight using the jump print itself on same bar.
    Wealth after jump day equals pre-jump wealth * (1+r) with pre-set weights.
    """
    n = 30
    idx = pd.bdate_range("2020-01-01", periods=n)
    px = np.ones(n) * 100.0
    jump_i = 20
    px[jump_i] = 200.0  # jump realized on bar jump_i (from 100 to 200)
    # after jump stay 200
    px[jump_i:] = 200.0
    prices = pd.DataFrame({"A": px, "B": px.copy()}, index=idx)

    env = PortfolioEnv(prices, start_capital=100_000.0, cost_bps_one_way=0.0)
    env.reset(initial_weights=np.array([0.5, 0.5]))
    # walk until step that earns return into jump_i
    # env: step at _i uses return of _i+1
    while env._i + 1 < jump_i:
        # only use info_slice for any "decision"
        effective_t = env._i + 1
        hist = info_slice(prices, effective_t)
        assert hist.index[-1] < prices.index[jump_i]
        env.step(None)
    # next step earns the jump return
    w_before = env.state.wealth
    effective_t = env._i + 1
    assert effective_t == jump_i
    hist = info_slice(prices, effective_t)
    # hist must NOT include jump bar
    assert prices.index[jump_i] not in hist.index
    env.step(None)
    # doubled prices → wealth roughly doubles with full investment
    assert env.state.wealth == pytest.approx(w_before * 2.0, rel=1e-9)


def test_peek_same_bar_would_see_jump():
    """Document anti-pattern: full series through jump_i includes jump."""
    n = 30
    idx = pd.bdate_range("2020-01-01", periods=n)
    px = np.ones(n) * 100.0
    jump_i = 20
    px[jump_i:] = 200.0
    prices = pd.DataFrame({"A": px}, index=idx)
    illegal = prices.iloc[: jump_i + 1]
    legal = info_slice(prices, jump_i)
    assert illegal.iloc[-1, 0] == 200.0
    assert legal.iloc[-1, 0] == 100.0
