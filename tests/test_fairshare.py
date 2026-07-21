"""Fairshare sim tests."""

from __future__ import annotations

import numpy as np

from fairshare.policies import CalendarPolicy, NeverPolicy, ThresholdPolicy
from fairshare.sim import FairShareSim, SimConfig, jain_fairness


def test_jain_perfect():
    assert abs(jain_fairness(np.ones(5)) - 1.0) < 1e-12


def test_jain_unfair():
    x = np.array([100.0, 0.0, 0.0, 0.0, 0.0])
    assert jain_fairness(x) < 0.5


def test_never_runs():
    cfg = SimConfig(steps=100, seed=1)
    sim = FairShareSim(cfg)
    out = sim.run(NeverPolicy())
    assert out["jain_mean"] > 0
    assert "p95_queue" in out


def test_threshold_can_rebalance():
    cfg = SimConfig(steps=500, seed=2, burst_mult=5.0, burst_len=40)
    sim = FairShareSim(cfg)
    out = sim.run(ThresholdPolicy(0.05))
    assert out["n_rebalances"] >= 1


def test_asof_decision_times():
    cfg = SimConfig(steps=50, seed=0)
    sim = FairShareSim(cfg)
    out = sim.run(CalendarPolicy(10))
    for d in out["decisions"]:
        if d["t"] > 0:
            assert d["asof_t"] < d["t"]


def test_f7b_exists_and_runs():
    from fairshare.policies import CostAwareV2Policy

    cfg = SimConfig(steps=300, seed=3, burst_mult=6.0)
    out = FairShareSim(cfg).run(CostAwareV2Policy(cost_per_l1=1.0))
    assert out["jain_mean"] > 0


def test_pareto_nonempty():
    from fairshare.frontier import run_frontier_at_cost

    fr = run_frontier_at_cost(SimConfig(steps=400, seed=1))
    assert len(fr["points"]) >= 8
    assert len(fr["pareto"]) >= 1
