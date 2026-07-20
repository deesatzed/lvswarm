"""L1 learning: offline template selection + contextual UCB helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dollarpath.env.portfolio import PortfolioEnv
from dollarpath.eval.runner import run_policy
from dollarpath.governor.rules import ExpertGovernor, GovernorConfig
from dollarpath.policies.baselines import Policy
from dollarpath.prediction.regime import SimpleRegimeDetector


def default_templates(n_assets: int, tickers: Optional[List[str]] = None) -> List[np.ndarray]:
    """Discrete target weight templates."""
    ew = np.ones(n_assets) / n_assets
    templates: List[np.ndarray] = [
        ew * 1.0,
        ew * 0.75,
        ew * 0.5,
        ew * 0.25,
        # no pure cash — exploration of cash is known to destroy dollars vs hold in bull regimes
    ]
    for i in range(n_assets):
        w = np.zeros(n_assets)
        w[i] = 1.0
        templates.append(w)
        templates.append(w * 0.7)
    k = min(3, n_assets)
    ro = np.zeros(n_assets)
    ro[:k] = 1.0 / k
    templates.append(ro)
    if n_assets >= 2:
        rf = np.zeros(n_assets)
        rf[-2:] = 0.5
        templates.append(rf)
        # 60/40 style: first 3 vs last 2
        if n_assets >= 5:
            bal = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
            templates.append(bal)
            templates.append(np.array([0.3, 0.3, 0.2, 0.1, 0.1]))
            templates.append(np.array([0.35, 0.35, 0.15, 0.1, 0.05]))
    return templates


class FixedTemplatePolicy(Policy):
    policy_id = "fixed_template"

    def __init__(self, weights: np.ndarray, every: int = 5, policy_id: str = "fixed_template"):
        self.weights = np.asarray(weights, dtype=float)
        self.every = every
        self.policy_id = policy_id
        self._n = 0

    def reset(self, n_assets: int) -> None:
        self._n = n_assets

    def act(self, step_index, prices_so_far, current_weights):
        if step_index % self.every == 0 or step_index == 0:
            return self.weights.copy()
        return None


def offline_select_best_template(
    prices: pd.DataFrame,
    templates: List[np.ndarray],
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    every: int = 5,
) -> Tuple[int, List[Dict]]:
    """Pick template maximizing ending wealth on the provided (train) prices."""
    rows = []
    best_i = 0
    best_w = -1e100
    for i, w in enumerate(templates):
        pol = FixedTemplatePolicy(w, every=every, policy_id=f"tmpl_{i}")
        equity, costs, _ = run_policy(
            prices, pol, start_capital=start_capital, cost_bps_one_way=cost_bps_one_way
        )
        ending = float(equity["wealth"].iloc[-1]) if len(equity) else start_capital
        rows.append({"template": i, "ending_wealth": ending, "total_costs": costs, "weights": w.tolist()})
        if ending > best_w:
            best_w = ending
            best_i = i
    return best_i, rows


@dataclass
class BanditState:
    counts: Dict[str, List[int]]
    values: Dict[str, List[float]]
    total_steps: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BanditState":
        return cls(
            counts={k: list(v) for k, v in d["counts"].items()},
            values={k: list(v) for k, v in d["values"].items()},
            total_steps=int(d.get("total_steps", 0)),
        )


class ContextualTemplateBandit:
    CONTEXTS = ("stable", "volatile", "transitioning", "unknown")

    def __init__(self, n_actions: int, c: float = 1.0, seed: int = 42):
        self.n_actions = n_actions
        self.c = c
        self.rng = np.random.default_rng(seed)
        self.state = BanditState(
            counts={ctx: [0] * n_actions for ctx in self.CONTEXTS},
            values={ctx: [0.0] * n_actions for ctx in self.CONTEXTS},
            total_steps=0,
        )

    def _ctx(self, context: str) -> str:
        return context if context in self.state.counts else "unknown"

    def select(self, context: str = "unknown") -> int:
        ctx = self._ctx(context)
        self.state.total_steps += 1
        counts = self.state.counts[ctx]
        values = self.state.values[ctx]
        for i, cnt in enumerate(counts):
            if cnt == 0:
                return i
        t = max(1, sum(counts))
        scores = [values[i] + self.c * np.sqrt(np.log(t + 1) / counts[i]) for i in range(self.n_actions)]
        return int(np.argmax(scores))

    def update(self, action: int, reward: float, context: str = "unknown") -> None:
        ctx = self._ctx(context)
        n = self.state.counts[ctx][action] + 1
        v = self.state.values[ctx][action]
        self.state.values[ctx][action] = v + (reward - v) / n
        self.state.counts[ctx][action] = n

    def best_action(self, context: str = "unknown") -> int:
        ctx = self._ctx(context)
        counts = self.state.counts[ctx]
        values = self.state.values[ctx]
        tried = [(values[i], i) for i in range(self.n_actions) if counts[i] > 0]
        if not tried:
            return 0
        return max(tried)[1]

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.state.to_dict(), indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        self.state = BanditState.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


TemplateBandit = ContextualTemplateBandit


def train_bandit_on_prices(
    prices: pd.DataFrame,
    start_capital: float = 100_000.0,
    cost_bps_one_way: float = 2.5,
    every: int = 5,
    seed: int = 42,
    use_governor: bool = True,
    mode: str = "ucb",
) -> Tuple[ContextualTemplateBandit, List[np.ndarray], Dict]:
    """Auxiliary: online contextual UCB path for diagnostics (not primary P2 selector)."""
    del mode
    templates = default_templates(prices.shape[1], list(prices.columns))
    bandit = ContextualTemplateBandit(n_actions=len(templates), seed=seed)
    gov = ExpertGovernor(GovernorConfig(enabled=use_governor, max_weight=1.0))
    det = SimpleRegimeDetector()
    env = PortfolioEnv(prices, start_capital=start_capital, cost_bps_one_way=cost_bps_one_way)
    env.reset()
    pending_action: Optional[int] = None
    pending_ctx = "unknown"
    wealth_at = env.state.wealth
    n_updates = 0
    for step in range(env.n_steps):
        prices_so_far = prices.iloc[: env._i + 1]
        action_w = None
        if step % every == 0:
            if pending_action is not None:
                r = float(np.log(env.state.wealth + 1e-12) - np.log(wealth_at + 1e-12))
                bandit.update(pending_action, r, pending_ctx)
                n_updates += 1
            reg = det.detect(prices_so_far)
            a = bandit.select(reg.regime_type)
            pending_action, pending_ctx, wealth_at = a, reg.regime_type, env.state.wealth
            dec = gov.govern(templates[a], env.state.weights, drawdown=env.state.drawdown)
            action_w = dec.final_weights
        state, _ = env.step(action_w)
        if state.ruined:
            break
    if pending_action is not None:
        r = float(np.log(env.state.wealth + 1e-12) - np.log(wealth_at + 1e-12))
        bandit.update(pending_action, r, pending_ctx)
    return bandit, templates, {
        "ending_wealth_train": env.state.wealth,
        "n_updates": n_updates,
        "counts": bandit.state.counts,
        "values": bandit.state.values,
    }


class LearnedTemplatePolicy(Policy):
    """Deploy fixed offline-selected template (primary P2 learned policy)."""

    policy_id = "learned_bandit"

    def __init__(
        self,
        template: np.ndarray,
        every: int = 5,
        use_governor: bool = False,
        policy_id: str = "learned_offline_template",
    ):
        self.template = np.asarray(template, dtype=float)
        self.every = every
        self.governor = ExpertGovernor(GovernorConfig(enabled=use_governor, max_weight=1.0))
        self.use_governor = use_governor
        self.policy_id = policy_id
        self._n = 0
        self._drawdown = 0.0
        self.last_decision = None

    def reset(self, n_assets: int) -> None:
        self._n = n_assets
        self._drawdown = 0.0

    def set_drawdown(self, dd: float) -> None:
        self._drawdown = float(dd)

    def act(self, step_index, prices_so_far, current_weights):
        if step_index % self.every != 0 and step_index != 0:
            return None
        w = self.template.copy()
        if self.use_governor:
            dec = self.governor.govern(w, current_weights, drawdown=self._drawdown)
            self.last_decision = dec.as_dict()
            return dec.final_weights
        self.last_decision = {"status": "APPROVE", "rule_ids": [], "template": "offline_best"}
        return w
