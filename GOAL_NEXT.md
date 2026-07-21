# GOAL_NEXT.md — DollarPath DPL-1 Autonomous Contract

Use this as the Codex / Claude / Grok **`/goal`** (or equivalent) to **algorithmically execute** the recommended path after v1:

> **S2 (constrained template selector) + E3 (sealed prospective protocol)**  
> Primary claim arm: **B2**. Honesty arms: **A1 hold QQQ**, **B1 unconstrained**.  
> Faux dollars only. Leakage audit must pass or the run is void.

**Supersedes for next work:** do **not** re-open v1 P3 unconstrained QQQ claim as the main goal.  
**Prior GOAL.md:** historical; v1 `SCOPED_HISTORICAL_SOTA_PASS` is archived context only.

**Authoritative companions:**

| Doc | Role |
|---|---|
| `prereg/PREREG_PROSPECTIVE_V1.md` | Protocol E1–E3, arms, PASS rules, audit L1–L7 |
| `docs/NEXT_STEPS_METHODOLOGY.md` | Rationale, waves, falsification agenda |
| `docs/WHITEPAPER.md` | North-star dollars over time |
| `BUILD_TODO.md` | Append new N* checkboxes as gates complete |
| `FAILURE_LEDGER.md` | Append failures; do not erase |
| `PROGRESS.md` | Session handoff after each gate |

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

Implement and run DollarPath Prospective Ledger (DPL-1):

1. Anti-leakage decision protocol (one-bar information lag; next-bar
   fill; retrain embargo; automated audit L1–L7).
2. Parallel faux-$ arms including hold_equal, hold_qqq, calendar,
   vol_target, unconstrained selector (B1), constrained selector (B2).
3. One sealed official prospective historical replay under locked
   prereg (or auto-lock defaults in §DEFAULT LOCK if human has not
   set LOCKED — see HARD CONSTRAINTS).
4. Multi-year nested battery as APPENDIX (report-only).
5. Terminal status:
     SCOPED_PROSPECTIVE_PASS_B2
  or SCOPED_PROSPECTIVE_FAIL_B2
  or SCOPED_PROSPECTIVE_VOID (audit fail)
  or BLOCKED (needs human)

Do not reword metrics to force PASS. FAIL is a valid scientific outcome.

══════════════════════════════════════════════════════════════════
TASK TYPE
══════════════════════════════════════════════════════════════════

Research software engineering + sealed evaluation:
  - prospective protocol module + unit tests (planted leakage)
  - constrained/unconstrained template libraries + hash
  - multi-arm runner + CLI
  - leakage_audit.json
  - official artifact pack + result_card
  - multi-year appendix
  - NO live brokerage / real money
  - NO mock market prices as evidence (real yfinance + disk cache OK)

══════════════════════════════════════════════════════════════════
STARTING POINT
══════════════════════════════════════════════════════════════════

Workspace:
  /Volumes/WS4TB/lvswarm

Existing (reuse, do not rewrite blindly):
  - dollarpath/env/portfolio.py
  - dollarpath/eval/runner.py, metrics.py, walkforward.py
  - dollarpath/train/bandit.py (offline_select_best_template, templates)
  - dollarpath/cli.py
  - dollarpath/artifacts/phase_p3_gate/ (v1 context only)
  - tests/ (extend; keep green)

Package target additions:
  dollarpath/prospective/
    __init__.py
    protocol.py      # E1–E3
    templates.py     # libraries + sha256
    arms.py          # A0–A3, B1–B2
    audit.py         # L1–L7
    runner.py        # prospective multi-arm run
  tests/test_leakage_protocol.py
  tests/test_constrained_templates.py
  prereg/PREREG_PROSPECTIVE_V1.md  (update Status when locking)

Default compute:
  Local. $0 market data. LLM APIs OFF.

══════════════════════════════════════════════════════════════════
RECOMMENDED PATH (DO NOT DRIFT)
══════════════════════════════════════════════════════════════════

Strategy:  S2 constrained selector = PRIMARY (arm B2)
Honesty:   B1 unconstrained + A1 hold_qqq = REPORT ONLY
Experiment: E3 sealed prospective protocol
Appendix:  E2 multi-year nested battery (report only)
DEFER:     heavy online RL (S3), prediction-first (S4), live-only (S5)
           until B2 terminal status is written

Branch after official B2 result:
  IF PASS_B2:
      optional N8 hybrid weekly reselect (light adaptivity) as
      EXPLORATORY only unless new prereg DPL-2 locked
  IF FAIL_B2:
      write FAIL card; may run one exploratory mean_log_growth
      train score variant labeled exploratory_*; do NOT claim PASS
  IF VOID:
      fix audit/protocol; re-run only after fix; new run_id

══════════════════════════════════════════════════════════════════
DEFAULT LOCK (algorithmic — use if prereg still DRAFT)
══════════════════════════════════════════════════════════════════

If prereg/PREREG_PROSPECTIVE_V1.md Status is not LOCKED, the agent
SHALL apply these defaults, write them into:
  dollarpath/artifacts/prospective_<run_id>/LOCK.json
and set prereg Status line to:
  LOCKED_BY_GOAL_NEXT (auto) at <UTC ISO timestamp>
unless human previously set LOCKED with different values (then obey human).

Defaults:
  universe:           ["SPY","QQQ","IWM","TLT","GLD"]
  history_start:      2018-01-01
  T_start:            2020-01-02
  T_end:              2024-12-31
  start_capital:      100000.0
  cost_bps_one_way:   2.5
  decision_every:     5
  embargo_bars:       5
  min_train_bars:     504
  max_weight_B2:      0.40
  min_names_B2:       3
  train_score_B2:     ending_wealth
  arms:               [A0, A1, A2, A3, B1, B2]
  primary_claim_arm:  B2
  execution:          asof = t-1; action earns return of bar t
  seed:               42
  data:               yfinance cache under data_cache/

══════════════════════════════════════════════════════════════════
PRIMARY OBJECTIVE
══════════════════════════════════════════════════════════════════

Prove or falsify, under no-lookahead rules:

  After-cost ending_wealth(B2) beats A0, A2, A3 on [T_start, T_end]
  AND risk rule:
      max_drawdown(B2) <= 1.20 * max(max_drawdown of A0,A2,A3)
      OR calmar(B2) > max(calmar of A0,A2,A3)

Report B1 vs A1 for honesty (not required for PASS_B2).

══════════════════════════════════════════════════════════════════
EXPLICIT NON-GOALS
══════════════════════════════════════════════════════════════════

- Live capital / brokerage orders
- Claiming PASS if leakage_audit any check is false
- Silent hyperparameter search until B2 wins
- Replacing primary arm with unconstrained B1 to force a win
- Mock prices/fills/rewards as evidence
- Marking production-ready
- P4 options / P5 LV ecology (unless B2 PASS and human asks)
- Time estimates

══════════════════════════════════════════════════════════════════
HARD CONSTRAINTS
══════════════════════════════════════════════════════════════════

1. NO MOCK market outcomes.
2. E1: decision at bar t uses only prices with index <= t-1.
3. E2: action effective for return of bar t (next bar after asof).
4. E3: train_end + embargo_bars before first credited eval bar
   when using batch train slices; expanding asof train must still
   satisfy asof <= t-1.
5. B2 templates: every weight vector max(w)<=0.40 and count(w>1e-12)>=3
   (or cash-only exception: all zero invested — only if explicitly
   in library; default library should not use pure cash as sole winner path).
6. Official run: single run_id; code changes after LOCK require new run_id
   and Status note — do not overwrite official artifacts.
7. pytest must be green before official prospective-run.
8. If same error 3+ times: 5–7 causes → 1–2 likely → logs → then fix.
9. Validate each numbered gate before the next.
10. Do not spend unbounded API money.

══════════════════════════════════════════════════════════════════
FIRST REQUIRED STEP (EVERY SESSION)
══════════════════════════════════════════════════════════════════

cd /Volumes/WS4TB/lvswarm
test -f GOAL_NEXT.md && test -f prereg/PREREG_PROSPECTIVE_V1.md
# read PROGRESS.md, FAILURE_LEDGER.md
# if .venv exists: use it; else create and pip install -r requirements.txt
PYTHONPATH=/Volumes/WS4TB/lvswarm .venv/bin/python -m pytest -q tests || true
# Continue from first incomplete gate N0..N9 below

══════════════════════════════════════════════════════════════════
AUTONOMOUS EXECUTION LOOP
══════════════════════════════════════════════════════════════════

Loop:

  1. Find lowest incomplete gate Nk in §GATES.
  2. Implement only that gate.
  3. Run Validation commands for Nk.
  4. On fail: FAILURE_LEDGER entry; fix within Nk; do not skip.
  5. On pass: mark Nk done in PROGRESS.md; checkboxes in this file
     or BUILD_TODO appendix; proceed.
  6. Stop at terminal status or BLOCKED.

Exploratory runs (optional after FAIL_B2) MUST use artifact prefix
  exploratory_
and MUST NOT write SCOPED_PROSPECTIVE_PASS_*.

══════════════════════════════════════════════════════════════════
GATES (ORDERED — ALGORITHM)
══════════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────────
N0 — Bootstrap & inventory
──────────────────────────────────────────────────────────────────
Actions:
  - Ensure venv + deps
  - Confirm dollarpath imports
  - Record git status / commit if repo clean enough to commit later
Validation:
  PYTHONPATH=. python -c "import dollarpath; print(dollarpath.__version__)"
  PYTHONPATH=. python -m pytest -q tests
Gate pass: pytest green (existing suite).

──────────────────────────────────────────────────────────────────
N1 — Prospective protocol module (E1–E3)
──────────────────────────────────────────────────────────────────
Actions:
  - Create dollarpath/prospective/protocol.py
  - Functions (names flexible, behavior fixed):
      info_slice(prices, t) -> prices.iloc[:t]   # asof = t-1 ⇒ pass t as exclusive end
      decision_indices(n_bars, every, min_asof) 
      assert_asof_ok(asof_i, effective_i)
  - Document: effective bar t uses asof t-1
Validation:
  Unit tests: for t=10, info end index == 9; effective > asof
Gate pass: tests/test_leakage_protocol.py includes protocol unit tests green.

──────────────────────────────────────────────────────────────────
N2 — Planted leakage test (must catch peeks)
──────────────────────────────────────────────────────────────────
Actions:
  - Synthetic flat series + huge jump at T*
  - Correct protocol policy cannot earn jump on illegal same-bar peek
  - Optional: deliberately broken peek helper fails an assert in a
    separate test that documents the anti-pattern
Validation:
  pytest tests/test_leakage_protocol.py -q
Gate pass: planted test green.

──────────────────────────────────────────────────────────────────
N3 — Template libraries + hash
──────────────────────────────────────────────────────────────────
Actions:
  - dollarpath/prospective/templates.py
  - unconstrained_templates(n)  # may include 100% single names
  - constrained_templates(n, max_weight=0.40, min_names=3)
  - sha256 of canonical JSON of weight lists
Validation:
  tests/test_constrained_templates.py:
    - all constrained templates satisfy max_weight and min_names
    - hash stable for fixed inputs
Gate pass: those tests green.

──────────────────────────────────────────────────────────────────
N4 — Arms A0, A1, A2, A3, B1, B2 under protocol
──────────────────────────────────────────────────────────────────
Actions:
  - dollarpath/prospective/arms.py + runner.py
  - A0 hold_equal, A1 hold_qqq (column QQQ required), A2 calendar_equal,
    A3 vol_target, B1 offline select unconstrained on expanding train
    asof, B2 offline select constrained
  - Before min_train_bars: B1/B2 behave as hold_equal
  - Every decision_every bars: re-select using only info through asof
  - Log decisions.jsonl fields:
      step, date, asof_date, train_end, arm_id, weights, selected_template
Validation:
  Short dry-run on cached demo data (or fetch if needed) for 1 year slice
  labeled exploratory_dry_run — produces equity curves for all arms
Gate pass: dry-run completes; 6 arms write metrics.json

──────────────────────────────────────────────────────────────────
N5 — Leakage audit L1–L7
──────────────────────────────────────────────────────────────────
Actions:
  - dollarpath/prospective/audit.py
  - L1 asof < effective for every decision
  - L2 train_end <= asof
  - L3 (structural) protocol used for features
  - L4 git commit recorded in LOCK.json (allow "unknown" if not a git repo)
  - L5 templates_sha256 match
  - L6 multi-year train_end < test_start with embargo (when battery run)
  - L7 cache meta present for fetch key or explicit skip reason
Validation:
  audit on exploratory_dry_run returns all required true (or documented skip)
Gate pass: audit module + test that fails if asof >= effective planted

──────────────────────────────────────────────────────────────────
N6 — CLI wiring
──────────────────────────────────────────────────────────────────
Actions:
  - python -m dollarpath.cli prospective-run ...
  - python -m dollarpath.cli multi-year-battery ...
  - python -m dollarpath.cli prospective-audit <run_dir>
  - Flags: --official / default exploratory; --start --end --seed
Validation:
  --help shows new commands; exploratory dry-run via CLI works
Gate pass: CLI dry-run exit 0

──────────────────────────────────────────────────────────────────
N7 — LOCK + OFFICIAL prospective run (PRIMARY GATE)
──────────────────────────────────────────────────────────────────
Actions:
  1. Apply §DEFAULT LOCK or human LOCK from prereg
  2. Write LOCK.json + prereg_hash + git sha + templates_sha256
  3. Fetch real prices for universe covering history_start..T_end
  4. Run all arms T_start..T_end under protocol
  5. Run leakage audit — if any fail → status VOID; stop claim
  6. Evaluate PASS_B2 rule vs A0,A2,A3
  7. Compare B1 vs A1 (report only)
  8. Write:
       dollarpath/artifacts/prospective_<run_id>/
         LOCK.json, claim_matrix.json, comparison.json,
         leakage_audit.json, result_card.md, arm_*/...
  9. Update PROGRESS.md + FAILURE_LEDGER if FAIL/VOID
Validation:
  claim_matrix.json status in
    {SCOPED_PROSPECTIVE_PASS_B2, SCOPED_PROSPECTIVE_FAIL_B2,
     SCOPED_PROSPECTIVE_VOID}
  audit all true unless VOID
Gate pass: official artifacts exist with terminal status (PASS or FAIL
  both count as gate complete; VOID is gate incomplete until fixed)

Algorithm for status:
  if audit_failed: VOID
  elif B2 beats A0 and A2 and A3 on ending_wealth and risk_rule: PASS_B2
  else: FAIL_B2

──────────────────────────────────────────────────────────────────
N8 — Multi-year appendix (report-only)
──────────────────────────────────────────────────────────────────
Actions:
  For Y in 2020,2021,2022,2023,2024:
    train: history_start → (Y-1)-12-31
    embargo: 5 sessions
    test: after embargo → Y-12-31
    B1/B2 select on train only; FIXED deploy on test
    baselines on test
  Write multi_year_battery.json + short section in result_card appendix
Validation:
  each year train_end < test_start; L6 true
Gate pass: 5 year records written (skip year only if insufficient bars,
  with reason)

──────────────────────────────────────────────────────────────────
N9 — Cost surface (report-only, lightweight)
──────────────────────────────────────────────────────────────────
Actions:
  Re-run B2 vs A0 only (or all arms if cheap) for cost_bps in
  [0, 2.5, 5, 10, 25] on same T_start..T_end protocol
  Write cost_surface.json
Validation:
  file exists; monotonic expectation not required
Gate pass: cost_surface.json written

──────────────────────────────────────────────────────────────────
N10 — Handoff & claim freeze
──────────────────────────────────────────────────────────────────
Actions:
  - PROGRESS.md final summary
  - result_card top-line status
  - README.md short "DPL-1 status" section
  - Do NOT claim live alpha
  - If PASS_B2: note optional next = DPL-2 hybrid (new GOAL), not auto
  - If FAIL_B2: note next = change train score exploratory OR accept no edge
Validation:
  human-readable result_card states status + limits
Gate pass: GOAL_NEXT terminal definition of done met

══════════════════════════════════════════════════════════════════
DEFINITION OF DONE (THIS GOAL)
══════════════════════════════════════════════════════════════════

DONE when ALL of:
  [ ] Gates N0–N7 complete
  [ ] N7 status is PASS_B2 or FAIL_B2 (not VOID)
  [ ] N8 complete (appendix)
  [ ] N10 handoff written
  [ ] pytest green
  [ ] leakage_audit all true on official run
  [ ] no live trading enabled

N9 cost surface: required for DONE (report-only).

DONE does not require PASS — FAIL_B2 with clean audit is DONE.

══════════════════════════════════════════════════════════════════
ARTIFACT CONTRACT (OFFICIAL)
══════════════════════════════════════════════════════════════════

dollarpath/artifacts/prospective_<run_id>/
  LOCK.json
  prereg_hash.txt
  templates_unconstrained_sha256.txt
  templates_constrained_sha256.txt
  leakage_audit.json
  comparison.json
  claim_matrix.json
  result_card.md
  multi_year_battery.json
  cost_surface.json
  arm_A0/ metrics.json equity_curve.csv decisions.jsonl
  arm_A1/ ...
  arm_A2/ ...
  arm_A3/ ...
  arm_B1/ ...
  arm_B2/ ...

metrics.json MUST include:
  ending_wealth, total_return, cagr, max_drawdown, calmar,
  total_costs, mean_turnover, arm_id, primary_metric_name

claim_matrix.json MUST include:
  status, passed_b2, audit_ok, b2_vs_baselines, b1_vs_a1, run_id, git_commit

══════════════════════════════════════════════════════════════════
CLAIM LANGUAGE
══════════════════════════════════════════════════════════════════

ALLOWED if PASS_B2:
  "After sealed lock under GOAL_NEXT / PREREG_PROSPECTIVE_V1, with
   one-bar information lag and constrained templates (max weight 40%,
   >=3 names), arm B2 achieved higher after-cost faux ending wealth
   than equal-hold, calendar equal, and vol-target from T_start to
   T_end on the demo universe; leakage audit passed. Not live trading."

FORBIDDEN:
  "guaranteed profits", "production ready", "beats buy-and-hold QQQ"
  without numbers, "no leakage" without audit file, "SOTA" without
  scoped historical/prospective qualifier

IF B1 ≈ A1:
  MUST note: unconstrained arm behaved like QQQ buy-and-hold menu pick.

══════════════════════════════════════════════════════════════════
SUGGESTED COMMANDS (IMPLEMENT THEN USE)
══════════════════════════════════════════════════════════════════

PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m dollarpath.cli fetch --universe demo --start 2018-01-01 --end 2024-12-31
PYTHONPATH=. .venv/bin/python -m dollarpath.cli prospective-run --official --start 2020-01-02 --end 2024-12-31 --seed 42
PYTHONPATH=. .venv/bin/python -m dollarpath.cli prospective-audit dollarpath/artifacts/prospective_<run_id>
PYTHONPATH=. .venv/bin/python -m dollarpath.cli multi-year-battery --start-year 2020 --end-year 2024 --seed 42

══════════════════════════════════════════════════════════════════
SESSION HANDOFF (APPEND TO PROGRESS.md)
══════════════════════════════════════════════════════════════════

## Session <date> GOAL_NEXT
- Gate completed:
- Official status (if any):
- Artifacts:
- Key metrics B2 vs A0:
- B1 vs A1:
- Audit:
- Next gate:
- Blockers:

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```

---

## Quick reference (human)

| Question | Answer |
|---|---|
| What path? | **S2 + E3** — constrained B2 under sealed prospective protocol |
| What is success? | Clean **PASS_B2 or FAIL_B2** with audit true |
| What is cheating? | Using B1/QQQ unconstrained as the primary win |
| When to stop? | N10 after N7 terminal + N8 + N9 |
| Live money? | **Never** under this goal |

## Document control

| Version | Note |
|---|---|
| 1.0 | Initial GOAL_NEXT for DPL-1 algorithmic execution |
