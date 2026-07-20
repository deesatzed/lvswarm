"""Unit tests for portfolio math (no network)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dollarpath.env.portfolio import CostModel, PortfolioEnv


def _linear_prices(n: int = 10, n_assets: int = 2) -> pd.DataFrame:
    """Deterministic formula path — not market data, for unit math only."""
    idx = pd.bdate_range("2020-01-01", periods=n)
    data = {}
    for j in range(n_assets):
        # asset j grows 1% per day from 100
        data[f"A{j}"] = 100.0 * (1.01 ** np.arange(n)) * (1.0 + 0.001 * j)
    return pd.DataFrame(data, index=idx)


def test_cost_model_zero_turnover():
    c = CostModel(bps_one_way=2.5)
    assert c.cost_for_turnover(100_000, 0.0) == 0.0


def test_cost_model_positive():
    c = CostModel(bps_one_way=10.0)  # 10 bps one way
    cost = c.cost_for_turnover(100_000, 0.5)
    assert cost > 0


def test_no_trade_zero_costs_after_init_hold():
    prices = _linear_prices(30, 2)
    env = PortfolioEnv(prices, start_capital=100_000.0, cost_bps_one_way=2.5)
    env.reset(initial_weights=np.array([0.5, 0.5]))
    total_cost = 0.0
    for _ in range(5):
        _, info = env.step(None)
        total_cost += info.costs
    assert total_cost == 0.0
    assert env.state.wealth > 100_000.0  # grew with prices


def test_rebalance_incurs_cost():
    prices = _linear_prices(20, 2)
    env = PortfolioEnv(prices, start_capital=100_000.0, cost_bps_one_way=50.0)
    env.reset(initial_weights=np.array([1.0, 0.0]))
    _, info = env.step(np.array([0.0, 1.0]))
    assert info.costs > 0
    assert info.turnover > 0


def test_wealth_identity_full_invest_one_asset():
    """Single asset 1% daily; full weight; no costs → wealth = 100k * 1.01^steps."""
    n = 6
    prices = _linear_prices(n, 1)
    env = PortfolioEnv(prices, start_capital=100_000.0, cost_bps_one_way=0.0)
    env.reset(initial_weights=np.array([1.0]))
    for _ in range(n - 1):
        env.step(None)
    expected = 100_000.0 * (1.01 ** (n - 1))
    assert env.state.wealth == pytest.approx(expected, rel=1e-9)
