from __future__ import annotations

import numpy as np
import pandas as pd

from dollarpath.eval.walkforward import no_leakage_check, walk_forward


def test_walkforward_no_leakage_and_windows():
    idx = pd.bdate_range("2018-01-01", periods=900)
    t = np.arange(900)
    prices = pd.DataFrame(
        {
            "A": 100 * (1.001**t),
            "B": 100 * (1.0008**t),
        },
        index=idx,
    )
    wf = walk_forward(
        prices,
        train_bars=200,
        test_bars=50,
        embargo_bars=5,
        step_bars=50,
        start_capital=100_000.0,
        cost_bps_one_way=0.0,
        every=5,
    )
    assert wf["aggregate"] is not None
    assert wf["aggregate"]["n_windows"] >= 1
    assert no_leakage_check(wf["windows"]) is True
