from __future__ import annotations

import numpy as np

from dollarpath.prospective.templates import (
    assert_constrained,
    constrained_templates,
    templates_sha256,
    unconstrained_templates,
)


def test_constrained_respects_caps():
    ts = constrained_templates(5, max_weight=0.40, min_names=3)
    assert len(ts) >= 1
    assert_constrained(ts, max_weight=0.40, min_names=3)


def test_hash_stable():
    ts = constrained_templates(5)
    h1 = templates_sha256(ts)
    h2 = templates_sha256(ts)
    assert h1 == h2
    assert len(h1) == 64


def test_unconstrained_has_single_name():
    ts = unconstrained_templates(5)
    has_single = any(int(np.sum(np.asarray(w) > 1e-12)) == 1 for w in ts)
    assert has_single
