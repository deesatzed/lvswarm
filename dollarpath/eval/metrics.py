"""Wealth metrics and artifact writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def compute_metrics(
    equity: pd.DataFrame,
    start_capital: float,
    total_costs: float,
    policy_id: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    equity columns: date, wealth, drawdown, exposure, turnover, costs, reward
    """
    if equity.empty:
        raise ValueError("empty equity curve")
    w = equity["wealth"].to_numpy(dtype=float)
    ending = float(w[-1])
    total_return = ending / start_capital - 1.0
    n = len(w)
    years = max(n / 252.0, 1e-9)
    cagr = (ending / start_capital) ** (1.0 / years) - 1.0 if ending > 0 else -1.0
    max_dd = float(equity["drawdown"].max()) if "drawdown" in equity else 0.0
    calmar = (cagr / max_dd) if max_dd > 1e-12 else (cagr if cagr > 0 else 0.0)
    mean_turnover = float(equity["turnover"].mean()) if "turnover" in equity else 0.0
    mean_exposure = float(equity["exposure"].mean()) if "exposure" in equity else 0.0

    return {
        "ending_wealth": ending,
        "start_capital": start_capital,
        "total_return": total_return,
        "cagr": cagr,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "total_costs": float(total_costs),
        "mean_turnover": mean_turnover,
        "mean_exposure": mean_exposure,
        "n_steps": int(n),
        "years": years,
        "policy_id": policy_id,
        "primary_metric_name": "ending_wealth",
        "universe": config.get("universe"),
        "start": config.get("start"),
        "end": config.get("end"),
        "seed": config.get("seed"),
        "beats_baselines": None,
    }


def write_run_artifacts(
    run_dir: Path,
    config: Dict[str, Any],
    metrics: Dict[str, Any],
    equity: pd.DataFrame,
    decisions: Optional[List[dict]] = None,
    claim: str = "P0 complete — dollars measurable; no RL claim",
) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    equity.to_csv(run_dir / "equity_curve.csv", index=False)
    if decisions is not None:
        with (run_dir / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for row in decisions:
                f.write(json.dumps(row) + "\n")

    card = f"""# Result card — `{metrics.get('policy_id')}`

## Claim
{claim}

## Metrics
| Metric | Value |
|---|---|
| Ending wealth | {metrics.get('ending_wealth'):,.2f} |
| Total return | {metrics.get('total_return'):.4%} |
| CAGR | {metrics.get('cagr'):.4%} |
| Max drawdown | {metrics.get('max_drawdown'):.4%} |
| Calmar | {metrics.get('calmar'):.4f} |
| Total costs | {metrics.get('total_costs'):,.2f} |
| Mean turnover | {metrics.get('mean_turnover'):.6f} |
| Steps | {metrics.get('n_steps')} |

## Config
- Universe: {config.get('universe')}
- Period: {config.get('start')} → {config.get('end')}
- Seed: {config.get('seed')}
- Cost bps one-way: {config.get('cost_bps_one_way')}

## Limits
- Historical simulation only; not live trading.
- No SOTA claim at P0.
"""
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    return run_dir
