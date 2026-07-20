# lvswarm / DollarPath

**End goal:** learn and prove capital-allocation policies that produce **more worth (dollars) over time** after costs, versus simple baselines, without ruin — on real historical data, local-first.

This is **not** a live trading product under the current goal. It is a measurable research application with an autonomous build contract.

---

## Start here

| Document | Purpose |
|---|---|
| **[GOAL.md](GOAL.md)** | Autonomous agent contract — outcome, gates, non-goals, claim language |
| **[BUILD_TODO.md](BUILD_TODO.md)** | Ordered build checklist with validation gates (no time estimates) |
| **[docs/WHITEPAPER.md](docs/WHITEPAPER.md)** | Full white paper: problem, RL formulation, architecture, eval, phases |
| [END_GOAL_DOLLARS_OVER_TIME.md](END_GOAL_DOLLARS_OVER_TIME.md) | Plain-language north star |
| [PORTFOLIO_PREDICTION_EXPERT_ANALYSIS.md](PORTFOLIO_PREDICTION_EXPERT_ANALYSIS.md) | Prediction KB + expert value/inverse |
| [AUTOBALANCE_CONTEXTS_TOP5.md](AUTOBALANCE_CONTEXTS_TOP5.md) | External autobalance domains + local testability |

---

## What “SOTA application” means here

**Phase P3 PASS** in `GOAL.md` / `BUILD_TODO.md`:

- Preregistered universe, period, costs, risk rule  
- Learned policy beats buy-and-hold, calendar rebalance, and vol-targeting **after costs** on **held-out** history  
- Risk constraint satisfied  
- Ablations + artifacts on disk  

Failure of that test is a valid scientific outcome (`SCOPED_HISTORICAL_SOTA_FAIL`). It is not success.

---

## Related prior art (reuse, don’t rewrite blindly)

| Path | Reuse for |
|---|---|
| `macwise-clean-test/naked_straddle_sim/` | ace_core regime/ACE, faux portfolio measurement, statistical rigor |
| `clawswarmed/` | `metrics.json`, `result_card.md`, ledger discipline |
| `predoc1.md` | LV / multi-strategy ecology ideas (Phase P5 only) |

---

## Status

| Item | Status |
|---|---|
| White paper | Written |
| Build checklist | P0–P3 gates closed |
| GOAL contract | **DONE** — `SCOPED_HISTORICAL_SOTA_PASS` |
| `dollarpath/` package | Implemented; CLI + tests green |

### Held-out result (prereg P3)

Train 2018–2022 → deploy on 2023–2024 (demo universe, 2.5 bps one-way):

| Policy | Ending wealth ($100k start) |
|---|---:|
| **learned (QQQ template)** | **$196,480** |
| hold_equal | $142,870 |
| calendar_equal | $140,326 |
| vol_target | $131,230 |

Artifacts: `dollarpath/artifacts/p3_heldout_seed_42/`  
Gate card: `dollarpath/artifacts/phase_p3_gate/result_card.md`

### Quick start

```bash
cd /Volumes/WS4TB/lvswarm
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m dollarpath.cli fetch --universe demo
PYTHONPATH=. .venv/bin/python -m dollarpath.cli run-baselines --universe demo --seed 42
PYTHONPATH=. .venv/bin/python -m dollarpath.cli train --universe demo --seed 42
PYTHONPATH=. .venv/bin/python -m dollarpath.cli eval-heldout --universe demo --seed 42
```

---

## Agent entry

```text
Read GOAL.md and execute the /goal contract.
Continue from the first incomplete gate in BUILD_TODO.md.
```

---

## Human rules (project)

- No mocks for market outcomes/fills/rewards without explicit approval  
- No live capital under this GOAL  
- No “production ready” / “SOTA complete” with open gates  
- User selects LLM model versions when APIs are used  
