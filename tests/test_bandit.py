"""Learning tests on formula paths."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dollarpath.train.bandit import (
    ContextualTemplateBandit,
    default_templates,
    offline_select_best_template,
)


def test_bandit_ucb_prefers_high_reward_action():
    b = ContextualTemplateBandit(n_actions=3, seed=0)
    for _ in range(20):
        b.update(0, 0.01, "stable")
        b.update(1, 0.05, "stable")
        b.update(2, -0.02, "stable")
    picks = [b.select("stable") for _ in range(50)]
    assert picks.count(1) > picks.count(0)


def test_offline_selects_faster_asset():
    idx = pd.bdate_range("2020-01-01", periods=120)
    t = np.arange(120)
    prices = pd.DataFrame(
        {
            "SLOW": 100 * (1.0005**t),
            "FAST": 100 * (1.003**t),
        },
        index=idx,
    )
    templates = default_templates(2)
    best_i, rows = offline_select_best_template(
        prices, templates, start_capital=100_000.0, cost_bps_one_way=0.0, every=5
    )
    # FAST-only templates should dominate
    w = np.asarray(templates[best_i])
    assert w[1] >= w[0] - 1e-9
    assert rows[best_i]["ending_wealth"] >= 100_000.0
