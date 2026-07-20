"""Metrics hand-check."""

from __future__ import annotations

import pandas as pd

from dollarpath.eval.metrics import compute_metrics


def test_metrics_ending_and_return():
    equity = pd.DataFrame(
        {
            "date": ["2020-01-02", "2020-01-03", "2020-01-04"],
            "wealth": [100_000.0, 110_000.0, 121_000.0],
            "drawdown": [0.0, 0.0, 0.0],
            "exposure": [1.0, 1.0, 1.0],
            "turnover": [0.0, 0.0, 0.0],
            "costs": [0.0, 0.0, 0.0],
            "reward": [0.0, 0.0, 0.0],
        }
    )
    m = compute_metrics(equity, 100_000.0, 0.0, "test", {"universe": ["X"], "seed": 1})
    assert m["ending_wealth"] == 121_000.0
    assert abs(m["total_return"] - 0.21) < 1e-12
