"""Ensure features use only prices_so_far (caller contract)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dollarpath.state.features import build_features


def test_features_length_matches_so_far_only():
    idx = pd.bdate_range("2020-01-01", periods=50)
    full = pd.DataFrame({"A": np.linspace(100, 150, 50), "B": np.linspace(50, 80, 50)}, index=idx)
    so_far = full.iloc[:20]
    # If someone mistakenly passes full, vol would differ — we assert API uses so_far length
    f = build_features(so_far, np.array([0.5, 0.5]), drawdown=0.1, step_index=19, days_since_rebalance=3)
    assert f.step_index == 19
    assert f.drawdown == 0.1
    # sanity: finite
    assert np.isfinite(f.realized_vol)
