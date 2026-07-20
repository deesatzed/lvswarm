"""Faux-capital portfolio simulator with costs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class CostModel:
    """One-way cost in basis points applied to traded notional each side."""

    bps_one_way: float = 2.5

    def cost_for_turnover(self, wealth: float, turnover: float) -> float:
        # turnover = 0.5 * sum(|w_new - w_old|) in [0, 1]
        # round-trip notionally ~ 2 * one-way on half-sum abs; we charge one-way on full L1/2 * 2
        traded_fraction = turnover  # already half L1
        return wealth * traded_fraction * (self.bps_one_way / 10_000.0) * 2.0


@dataclass
class PortfolioState:
    date: Optional[pd.Timestamp]
    cash: float
    weights: np.ndarray  # length n_assets, sum ~ 1 if fully invested (cash residual allowed)
    wealth: float
    peak_wealth: float
    drawdown: float
    positions_value: float
    step_index: int = 0
    ruined: bool = False

    def as_dict(self) -> dict:
        return {
            "date": None if self.date is None else str(self.date.date()),
            "cash": self.cash,
            "wealth": self.wealth,
            "peak_wealth": self.peak_wealth,
            "drawdown": self.drawdown,
            "positions_value": self.positions_value,
            "step_index": self.step_index,
            "ruined": self.ruined,
            "weights": self.weights.tolist(),
        }


@dataclass
class StepInfo:
    turnover: float
    costs: float
    reward: float
    wealth: float
    drawdown: float
    ruined: bool
    date: str
    weights: List[float]


class PortfolioEnv:
    """
    Daily simulation:
    - Hold weights through bar return (price_t / price_{t-1} - 1)
    - At end of bar, apply action as target weights for NEXT bar (next_close execution)
    - Costs charged when weights change
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        start_capital: float = 100_000.0,
        cost_bps_one_way: float = 2.5,
        ruin_fraction: float = 0.2,
        rebalance_speed: float = 1.0,
    ):
        if prices.empty:
            raise ValueError("prices empty")
        self.prices = prices.astype(float)
        self.tickers = list(prices.columns)
        self.n = len(self.tickers)
        self.start_capital = float(start_capital)
        self.cost_model = CostModel(bps_one_way=cost_bps_one_way)
        self.ruin_floor = self.start_capital * float(ruin_fraction)
        self.rebalance_speed = float(np.clip(rebalance_speed, 0.0, 1.0))
        self.returns = self.prices.pct_change()
        self._reset_state()

    def _reset_state(self) -> None:
        self._i = 0  # index into prices
        w = np.zeros(self.n)
        self.state = PortfolioState(
            date=self.prices.index[0],
            cash=self.start_capital,
            weights=w,
            wealth=self.start_capital,
            peak_wealth=self.start_capital,
            drawdown=0.0,
            positions_value=0.0,
            step_index=0,
            ruined=False,
        )
        self._pending_weights: Optional[np.ndarray] = None

    def reset(self, initial_weights: Optional[np.ndarray] = None) -> PortfolioState:
        self._reset_state()
        if initial_weights is not None:
            w = self._normalize_weights(np.asarray(initial_weights, dtype=float))
            self.state.weights = w
            self.state.positions_value = self.state.wealth * float(w.sum())
            self.state.cash = self.state.wealth - self.state.positions_value
        return self.state

    @property
    def n_steps(self) -> int:
        # number of return steps available (from day 1..)
        return max(0, len(self.prices) - 1)

    def _normalize_weights(self, w: np.ndarray) -> np.ndarray:
        w = np.asarray(w, dtype=float).reshape(-1)
        if w.shape[0] != self.n:
            raise ValueError(f"weights length {w.shape[0]} != {self.n}")
        w = np.clip(w, 0.0, None)
        s = w.sum()
        if s > 1.0 + 1e-9:
            w = w / s
        return w

    def _apply_pending(self) -> float:
        """Apply pending target weights; return cost charged."""
        if self._pending_weights is None:
            return 0.0
        target = self._pending_weights
        speed = self.rebalance_speed
        new_w = self.state.weights + speed * (target - self.state.weights)
        new_w = self._normalize_weights(new_w)
        # invested fraction may be < 1 (cash)
        turnover = 0.5 * float(np.abs(new_w - self.state.weights).sum())
        # also account for cash sleeve change in turnover of invested book
        cost = self.cost_model.cost_for_turnover(self.state.wealth, turnover)
        self.state.wealth = max(0.0, self.state.wealth - cost)
        self.state.weights = new_w
        invested = float(new_w.sum())
        self.state.positions_value = self.state.wealth * invested
        self.state.cash = self.state.wealth - self.state.positions_value
        self._pending_weights = None
        return cost

    def step(self, target_weights: Optional[np.ndarray]) -> Tuple[PortfolioState, StepInfo]:
        """
        Advance one trading day.
        target_weights: desired weights for the *next* period (or None = no-op / hold).
        """
        if self.state.ruined:
            info = StepInfo(
                turnover=0.0,
                costs=0.0,
                reward=0.0,
                wealth=self.state.wealth,
                drawdown=self.state.drawdown,
                ruined=True,
                date=str(self.state.date.date()) if self.state.date is not None else "",
                weights=self.state.weights.tolist(),
            )
            return self.state, info

        if self._i >= self.n_steps:
            raise StopIteration("episode finished")

        # 1) mark portfolio through today's return (using weights set previously)
        # Weights drift with relative asset returns (share quantities held fixed).
        prev_wealth = self.state.wealth
        ret_row = self.returns.iloc[self._i + 1]
        r = ret_row.to_numpy(dtype=float)
        r = np.nan_to_num(r, nan=0.0, posinf=0.0, neginf=0.0)
        invested = float(self.state.weights.sum())
        cash_w = max(0.0, 1.0 - invested)
        if invested > 1e-12:
            # gross growth factors for invested sleeves
            grown = self.state.weights * (1.0 + r)
            port_ret = float(grown.sum() + cash_w - 1.0)
            self.state.wealth = max(0.0, prev_wealth * (1.0 + port_ret))
            # renormalize weights so sum(weights)+cash_w = 1 in wealth terms
            if self.state.wealth > 0:
                self.state.weights = grown * (prev_wealth / self.state.wealth)
                # numerical cleanup
                self.state.weights = np.clip(self.state.weights, 0.0, None)
        else:
            port_ret = 0.0
            self.state.wealth = prev_wealth
        invested = float(self.state.weights.sum())
        self.state.date = self.prices.index[self._i + 1]
        self.state.positions_value = self.state.wealth * invested
        self.state.cash = self.state.wealth - self.state.positions_value

        # 2) apply rebalance for next period at this close
        if target_weights is None:
            self._pending_weights = None
            cost = 0.0
            turnover = 0.0
        else:
            self._pending_weights = self._normalize_weights(np.asarray(target_weights, dtype=float))
            old_w = self.state.weights.copy()
            cost = self._apply_pending()
            turnover = 0.5 * float(np.abs(self.state.weights - old_w).sum())

        self.state.peak_wealth = max(self.state.peak_wealth, self.state.wealth)
        self.state.drawdown = 0.0 if self.state.peak_wealth <= 0 else 1.0 - (
            self.state.wealth / self.state.peak_wealth
        )
        self.state.ruined = self.state.wealth < self.ruin_floor
        self._i += 1
        self.state.step_index = self._i

        # log-wealth reward
        eps = 1e-12
        reward = float(np.log(self.state.wealth + eps) - np.log(prev_wealth + eps))

        info = StepInfo(
            turnover=turnover,
            costs=cost,
            reward=reward,
            wealth=self.state.wealth,
            drawdown=self.state.drawdown,
            ruined=self.state.ruined,
            date=str(self.state.date.date()),
            weights=self.state.weights.tolist(),
        )
        return self.state, info
