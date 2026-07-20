"""Default experiment configuration (override via CLI / prereg later)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


DEFAULT_UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
DEFAULT_START_CAPITAL = 100_000.0
# Half-spread equivalent per side; round-trip ≈ 2 * bps/10000 of traded notional.
DEFAULT_COST_BPS_ONE_WAY = 2.5
DEFAULT_SEED = 42


@dataclass
class RunConfig:
    universe: List[str] = field(default_factory=lambda: list(DEFAULT_UNIVERSE))
    start: str = "2018-01-01"
    end: str = "2024-12-31"
    start_capital: float = DEFAULT_START_CAPITAL
    cost_bps_one_way: float = DEFAULT_COST_BPS_ONE_WAY
    execution: str = "next_close"  # apply new weights at next bar close
    seed: int = DEFAULT_SEED
    rebalance_every: int = 21  # calendar rebalance period (trading days)
    vol_lookback: int = 21
    vol_target_annual: float = 0.10
    policy_id: str = "unspecified"
    cache_dir: str = "data_cache"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
