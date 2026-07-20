"""Fixed prediction-informed policy (no learning) — P1."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from dollarpath.governor.rules import ExpertGovernor, GovernorConfig
from dollarpath.policies.baselines import Policy
from dollarpath.prediction.regime import SimpleRegimeDetector


class PredRulePolicy(Policy):
    """
    Equal-weight core; reduce exposure in volatile/transitioning regimes;
    optional governor + rebalance cadence.
    """

    policy_id = "pred_rule"

    def __init__(
        self,
        every: int = 5,
        use_prediction: bool = True,
        use_governor: bool = True,
        rebalance_speed: float = 1.0,
        stable_exposure: float = 1.0,
        transition_exposure: float = 0.6,
        volatile_exposure: float = 0.4,
        governor_config: Optional[GovernorConfig] = None,
        policy_id: Optional[str] = None,
    ):
        self.every = max(1, every)
        self.use_prediction = use_prediction
        self.use_governor = use_governor
        self.rebalance_speed = rebalance_speed
        self.stable_exposure = stable_exposure
        self.transition_exposure = transition_exposure
        self.volatile_exposure = volatile_exposure
        self.detector = SimpleRegimeDetector()
        self.governor = ExpertGovernor(governor_config or GovernorConfig(enabled=use_governor))
        self._n = 0
        self._drawdown = 0.0
        self.last_decision = None
        if policy_id is not None:
            self.policy_id = policy_id

    def reset(self, n_assets: int) -> None:
        self._n = n_assets
        self.detector = SimpleRegimeDetector()
        self._drawdown = 0.0
        self.last_decision = None

    def set_drawdown(self, dd: float) -> None:
        self._drawdown = float(dd)

    def act(self, step_index, prices_so_far, current_weights):
        if step_index % self.every != 0:
            return None

        exp = self.stable_exposure
        conf = 1.0
        if self.use_prediction:
            reg = self.detector.detect(prices_so_far)
            conf = reg.confidence
            if reg.regime_type == "volatile":
                exp = self.volatile_exposure
            elif reg.regime_type == "transitioning":
                exp = self.transition_exposure
            else:
                exp = self.stable_exposure

        target = np.ones(self._n) / self._n * exp
        # apply rebalance speed toward target from current
        blended = current_weights + self.rebalance_speed * (target - current_weights)
        blended = np.clip(blended, 0.0, None)

        if self.use_governor:
            dec = self.governor.govern(
                blended,
                current_weights,
                drawdown=self._drawdown,
                regime_confidence=conf,
            )
            self.last_decision = dec.as_dict()
            return dec.final_weights

        self.last_decision = {"status": "APPROVE", "rule_ids": []}
        return blended
