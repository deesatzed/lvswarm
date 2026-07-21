"""Fast template scoring for expanding-train selection."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd


def score_template_path(
    prices: pd.DataFrame,
    weights: np.ndarray,
    rebalance_every: int = 5,
    cost_bps_one_way: float = 2.5,
    start_capital: float = 100_000.0,
) -> float:
    """
    Fast approximate ending wealth.

    Primary score: growth from mean daily log-return under fixed target weights
    (constant mix), minus a turnover penalty proportional to rebalance frequency.
    Ranking-stable and O(n_assets * n_bars) vectorized.
    """
    w = np.asarray(weights, dtype=float)
    rets = prices.pct_change().to_numpy(dtype=float)
    rets = np.nan_to_num(rets, nan=0.0, posinf=0.0, neginf=0.0)
    if rets.shape[0] < 2:
        return float(start_capital)
    # portfolio daily returns under constant-mix assumption
    port = rets @ w
    # invested fraction may be < 1
    inv = float(np.clip(w.sum(), 0.0, 1.0))
    # cash earns 0
    # compound
    growth = float(np.prod(1.0 + port))
    # rebalance cost model: each rebalance pays turnover from drifted weights.
    # Approximate average drift turnover between rebalances as small fraction of inv.
    n = rets.shape[0]
    n_reb = max(1, n // max(1, rebalance_every))
    # crude: assume 2% of book turns each rebalance on average for mixed books
    turn_per = 0.02 * inv
    cost_rate = (cost_bps_one_way / 10_000.0) * 2.0
    cost_factor = (1.0 - turn_per * cost_rate) ** n_reb
    return float(start_capital * growth * cost_factor)


def score_template_path_exact_loop(
    prices: pd.DataFrame,
    weights: np.ndarray,
    rebalance_every: int = 5,
    cost_bps_one_way: float = 2.5,
    start_capital: float = 100_000.0,
) -> float:
    """Slower exact-ish loop; available for tests."""
    w_tgt = np.asarray(weights, dtype=float)
    rets = prices.pct_change().to_numpy(dtype=float)
    rets = np.nan_to_num(rets, nan=0.0, posinf=0.0, neginf=0.0)
    n = rets.shape[0]
    if n < 2:
        return start_capital
    wealth = float(start_capital)
    w = w_tgt.copy()
    cost_rate = (cost_bps_one_way / 10_000.0) * 2.0
    for i in range(1, n):
        r = rets[i]
        grown = w * (1.0 + r)
        cash_w = max(0.0, 1.0 - float(w.sum()))
        port_ret = float(grown.sum() + cash_w - 1.0)
        wealth = max(0.0, wealth * (1.0 + port_ret))
        if wealth <= 0:
            return 0.0
        scale = 1.0 + port_ret
        w = grown / scale if abs(scale) > 1e-12 else w
        w = np.clip(w, 0.0, None)
        if i % rebalance_every == 0:
            turnover = 0.5 * float(np.abs(w_tgt - w).sum())
            wealth = max(0.0, wealth - wealth * turnover * cost_rate)
            w = w_tgt.copy()
    return wealth


def fast_select_best_template(
    prices: pd.DataFrame,
    templates: List[np.ndarray],
    rebalance_every: int = 5,
    cost_bps_one_way: float = 2.5,
    start_capital: float = 100_000.0,
) -> Tuple[int, np.ndarray, List[dict]]:
    rows = []
    best_i = 0
    best_w = -1e100
    # Precompute returns once
    rets = prices.pct_change().to_numpy(dtype=float)
    rets = np.nan_to_num(rets, nan=0.0, posinf=0.0, neginf=0.0)
    n = max(1, rets.shape[0])
    n_reb = max(1, n // max(1, rebalance_every))
    cost_rate = (cost_bps_one_way / 10_000.0) * 2.0
    for i, tmpl in enumerate(templates):
        w = np.asarray(tmpl, dtype=float)
        port = rets @ w
        growth = float(np.prod(1.0 + port)) if port.size else 1.0
        inv = float(np.clip(w.sum(), 0.0, 1.0))
        turn_per = 0.02 * inv
        cost_factor = (1.0 - turn_per * cost_rate) ** n_reb
        ending = float(start_capital * growth * cost_factor)
        rows.append({"template": i, "ending_wealth": ending, "weights": w.tolist()})
        if ending > best_w:
            best_w = ending
            best_i = i
    return best_i, np.asarray(templates[best_i], dtype=float), rows
