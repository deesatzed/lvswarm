from __future__ import annotations

import numpy as np

from dollarpath.governor.rules import ExpertGovernor, GovernorConfig


def test_max_weight_sizes_down():
    gov = ExpertGovernor(GovernorConfig(max_weight=0.4, max_turnover=1.0))
    cur = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    prop = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    dec = gov.govern(prop, cur)
    assert dec.status == "SIZE_DOWN"
    assert "max_weight" in dec.rule_ids
    assert dec.final_weights is not None
    assert dec.final_weights.max() <= 0.4 + 1e-9


def test_noop():
    gov = ExpertGovernor()
    dec = gov.govern(None, np.ones(3) / 3)
    assert dec.status == "NOOP"


def test_disabled_approves():
    gov = ExpertGovernor(GovernorConfig(enabled=False, max_weight=0.1))
    prop = np.array([1.0, 0.0])
    dec = gov.govern(prop, np.array([0.5, 0.5]))
    assert dec.status == "APPROVE"
    assert dec.final_weights is not None
