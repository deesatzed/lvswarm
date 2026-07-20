"""Hard expert governor — APPROVE / SIZE DOWN / VETO only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class GovernorConfig:
    max_weight: float = 0.40
    max_turnover: float = 0.50  # half L1
    cash_floor: float = 0.0  # min cash weight
    max_drawdown_brake: float = 0.25  # if DD above, scale exposure
    drawdown_scale: float = 0.5
    low_confidence_threshold: float = 0.3
    low_confidence_scale: float = 0.75
    enabled: bool = True


@dataclass
class GovernorDecision:
    final_weights: Optional[np.ndarray]
    status: str  # APPROVE | SIZE_DOWN | VETO | NOOP
    rule_ids: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "rule_ids": self.rule_ids,
            "final_weights": None
            if self.final_weights is None
            else self.final_weights.tolist(),
        }


class ExpertGovernor:
    def __init__(self, config: Optional[GovernorConfig] = None):
        self.config = config or GovernorConfig()

    def govern(
        self,
        proposed: Optional[np.ndarray],
        current_weights: np.ndarray,
        drawdown: float = 0.0,
        regime_confidence: float = 1.0,
    ) -> GovernorDecision:
        if not self.config.enabled:
            return GovernorDecision(proposed, "APPROVE" if proposed is not None else "NOOP", [])

        if proposed is None:
            return GovernorDecision(None, "NOOP", [])

        w = np.asarray(proposed, dtype=float).copy()
        rules: List[str] = []
        status = "APPROVE"

        # non-negative
        w = np.clip(w, 0.0, None)

        # max weight
        if w.max(initial=0.0) > self.config.max_weight + 1e-12:
            w = np.minimum(w, self.config.max_weight)
            rules.append("max_weight")
            status = "SIZE_DOWN"

        # cash floor: ensure sum(w) <= 1 - cash_floor
        max_invest = 1.0 - self.config.cash_floor
        if w.sum() > max_invest + 1e-12:
            w = w * (max_invest / w.sum())
            rules.append("cash_floor")
            status = "SIZE_DOWN"

        # drawdown brake
        if drawdown >= self.config.max_drawdown_brake:
            w = w * self.config.drawdown_scale
            rules.append("drawdown_brake")
            status = "SIZE_DOWN"

        # low confidence
        if regime_confidence < self.config.low_confidence_threshold:
            w = w * self.config.low_confidence_scale
            rules.append("low_confidence")
            status = "SIZE_DOWN"

        # max turnover vs current
        turnover = 0.5 * float(np.abs(w - current_weights).sum())
        if turnover > self.config.max_turnover + 1e-12:
            # scale step toward target
            gap = w - current_weights
            # find alpha such that 0.5*||alpha*gap||_1 = max_turnover
            l1 = float(np.abs(gap).sum())
            if l1 < 1e-12:
                w = current_weights.copy()
            else:
                alpha = (2.0 * self.config.max_turnover) / l1
                alpha = min(1.0, alpha)
                w = current_weights + alpha * gap
            rules.append("max_turnover")
            status = "SIZE_DOWN"

        # veto empty nonsense
        if np.any(~np.isfinite(w)):
            return GovernorDecision(None, "VETO", ["non_finite"])

        return GovernorDecision(w, status, rules)
