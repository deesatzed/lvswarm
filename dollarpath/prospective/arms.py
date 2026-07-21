"""Arm definitions for DPL-1 multi-account run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np
import pandas as pd

from dollarpath.policies.baselines import CalendarRebalancePolicy, HoldPolicy, VolTargetPolicy
from dollarpath.prospective.fast_select import fast_select_best_template
from dollarpath.prospective.templates import constrained_templates, unconstrained_templates


@dataclass
class ArmConfig:
    arm_id: str
    kind: str  # hold_equal | hold_qqq | calendar | vol_target | select_uncon | select_con


def qqq_column_index(tickers: List[str]) -> int:
    for i, t in enumerate(tickers):
        if t.upper() == "QQQ":
            return i
    raise ValueError(f"QQQ not in universe: {tickers}")


class HoldQQQPolicy:
    policy_id = "hold_qqq"

    def __init__(self, tickers: List[str]):
        self.tickers = tickers
        self._n = len(tickers)
        self._i = qqq_column_index(tickers)
        self._done = False

    def reset(self, n_assets: int) -> None:
        self._n = n_assets
        self._done = False

    def act(self, step_index, prices_so_far, current_weights):
        if not self._done:
            self._done = True
            w = np.zeros(self._n)
            w[self._i] = 1.0
            return w
        return None


def select_template_on_history(
    prices_hist: pd.DataFrame,
    constrained: bool,
    max_weight: float = 0.40,
    min_names: int = 3,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    every: int = 5,
) -> tuple[int, np.ndarray, list]:
    n = prices_hist.shape[1]
    tickers = list(prices_hist.columns)
    if constrained:
        templates = constrained_templates(n, max_weight=max_weight, min_names=min_names, tickers=tickers)
    else:
        templates = unconstrained_templates(n, tickers=tickers)
    best_i, w, rows = fast_select_best_template(
        prices_hist,
        templates,
        rebalance_every=every,
        cost_bps_one_way=cost_bps_one_way,
        start_capital=start_capital,
    )
    return best_i, w, templates
