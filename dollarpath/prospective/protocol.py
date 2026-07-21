"""
E1–E3 anti-leakage protocol.

E1: decision at bar t uses only prices with index <= t-1 (asof = t-1).
E2: action earns the return of bar t (next bar after asof).
E3: batch train slices respect embargo_bars before first eval bar.
"""

from __future__ import annotations

from typing import List

import pandas as pd


def info_slice(prices: pd.DataFrame, effective_t: int) -> pd.DataFrame:
    """
    Prices available when acting for effective bar `effective_t`.

    asof exclusive end index = effective_t  → rows [0, effective_t)
    i.e. last included bar index = effective_t - 1.
    """
    if effective_t < 1:
        raise ValueError("effective_t must be >= 1 to have nonempty asof history")
    if effective_t > len(prices):
        raise ValueError("effective_t exceeds price length")
    return prices.iloc[:effective_t]


def asof_index(effective_t: int) -> int:
    """Last fully observed bar index for effective bar t."""
    return effective_t - 1


def assert_asof_ok(asof_i: int, effective_i: int) -> None:
    if asof_i >= effective_i:
        raise AssertionError(f"leakage: asof_i={asof_i} >= effective_i={effective_i}")


def decision_indices(
    n_bars: int,
    every: int = 5,
    min_effective: int = 1,
) -> List[int]:
    """
    Effective bar indices at which we may re-decide weights.
    First possible effective bar is max(min_effective, 1).
    """
    every = max(1, int(every))
    start = max(1, int(min_effective))
    return list(range(start, n_bars, every))


def train_end_ok(train_end_i: int, asof_i: int) -> bool:
    return train_end_i <= asof_i


def embargo_first_eval_ok(train_end_i: int, first_eval_i: int, embargo_bars: int) -> bool:
    return first_eval_i >= train_end_i + 1 + max(0, int(embargo_bars))
