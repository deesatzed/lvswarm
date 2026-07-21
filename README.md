# lvswarm / DollarPath

**End goal:** learn and prove capital-allocation policies that produce **more worth (dollars) over time** after costs, versus simple baselines, without ruin — on real historical data, local-first.

This is **not** a live trading product under the current goal. It is a measurable research application with an autonomous build contract.

---

## Start here

| Document | Purpose |
|---|---|
| **[GOAL_GLASSGATE_CONTROL_V2.md](GOAL_GLASSGATE_CONTROL_V2.md)** | Label-free Glass Gate control (primary deployable claim) |
| [GOAL_GLASSGATE_CONTROL.md](GOAL_GLASSGATE_CONTROL.md) | Glass Gate control v1 (oracle ceiling) |
| [GOAL_FAIRSHARE_V2.md](GOAL_FAIRSHARE_V2.md) | Fairshare frontier |
| [GOAL_FAIRSHARE.md](GOAL_FAIRSHARE.md) | Fairshare v1 |
| [GOAL_REBAL_V3.md](GOAL_REBAL_V3.md) | Finance rebalance frontier (characterized) |
| [GOAL_REBAL.md](GOAL_REBAL.md) | Rebal v2 multi-battery |
| [GOAL_REBALANCE.md](GOAL_REBALANCE.md) | v1 rebalance goal (single-cost FAIL) |
| [prereg/PREREG_REBAL_V2.md](prereg/PREREG_REBAL_V2.md) | Sealed rebal v2 experiment |
| [GOAL_NEXT.md](GOAL_NEXT.md) | Prior path DPL-1 (constrained allocation; FAIL_B2) |
| [prereg/PREREG_PROSPECTIVE_V1.md](prereg/PREREG_PROSPECTIVE_V1.md) | Leakage-resistant prospective experiment design |
| [docs/NEXT_STEPS_METHODOLOGY.md](docs/NEXT_STEPS_METHODOLOGY.md) | Rationale, real faux-$ tests, methodology upgrades |
| [GOAL.md](GOAL.md) | v1 contract (P0–P3) — completed with scoped historical pass |
| [BUILD_TODO.md](BUILD_TODO.md) | Ordered build checklist with validation gates |
| [docs/WHITEPAPER.md](docs/WHITEPAPER.md) | Full white paper |
| [END_GOAL_DOLLARS_OVER_TIME.md](END_GOAL_DOLLARS_OVER_TIME.md) | Plain-language north star |

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
| GOAL v1 (P0–P3) | **DONE** — `SCOPED_HISTORICAL_SOTA_PASS` (unconstrained held-out) |
| GOAL_REBAL_V3 | **DONE** — `SCOPED_REBAL_V3_COMPLETE`: break-even ~**1.75 bps**; band **7%+full** can beat never @2.5bps; bootstrap CIs wide (include 0) |
| GOAL_REBAL v2 | **DONE** — dual flags; COST_REGIME PASS; WEALTH_EDGE FAIL @2.5bps |
| GOAL_REBALANCE v1 | **DONE** — `SCOPED_REBALANCE_FAIL` at 2.5 bps equal-weight |
| GOAL_NEXT (DPL-1) | **DONE** — `SCOPED_PROSPECTIVE_FAIL_B2` (constrained allocation) |
| `dollarpath/` package | Prospective protocol + CLI; tests green |

### DPL-1 official (GOAL_NEXT)

Sealed prospective path 2020-01-02 → 2024-12-31, max weight 40% / ≥3 names (B2):

| Arm | Ending wealth (norm. $100k at T_start) |
|---|---:|
| A0 hold_equal | **$168,444** |
| B2 constrained select | $165,690 (FAIL vs A0) |
| A1 hold_qqq | $245,952 |
| B1 unconstrained | $188,935 |

Artifacts: `dollarpath/artifacts/prospective_official_seed_42_2020-01-02_2024-12-31/`

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
