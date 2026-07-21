# GOAL_REBAL.md — Make Fixed-Target Rebalancing Real (v2)

Use as Codex / Claude / Grok **`/goal`**.

**Supersedes for next work:** `GOAL_REBALANCE.md` v1 (completed with `SCOPED_REBALANCE_FAIL` at 2.5 bps).  
**This goal:** deepen, multi-cost, multi-target, dual scoreboard, improved cost-aware rule, sealed multi-test battery.

**Prior result (do not erase):** At equal-weight, 2020–2024, 2.5 bps: **never-rebalance beat all dynamic rules on ending $**; more rebalance → better tracking, higher costs.

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

Make the rebalancing lab REAL and fully tested:

1. Keep FIXED target w* (no allocation search / no QQQ-picking).
2. Dual scoreboard (both always reported):
   S_wealth  = window ending_wealth (after costs)
   S_track   = mean L1 distance to w*  (lower better)
3. Required battery (all sealed, no-lookahead E1/E2):
   B1  Cost grid on equal-weight target
   B2  Second target: 60/40 risk (see TARGETS)
   B3  Multi-year nested (calendar years 2020–2024)
   B4  Improved cost-aware policy R7b (fix over-trading R7)
4. Produce one consolidated claim_matrix + result_card with
   Pareto notes (who wins $ vs who wins tracking).
5. Terminal status (see PASS rules) — FAIL is allowed.

Primary question:
  "For fixed diversified targets, when does rebalancing help
   after-cost wealth, when does it only buy tracking, and how
   do fees change that tradeoff?"

══════════════════════════════════════════════════════════════════
TASK TYPE
══════════════════════════════════════════════════════════════════

Research eng + sealed evaluation. Faux $ only. Real prices only.
NO live trading. NO mock market data. NO changing w* via performance.

══════════════════════════════════════════════════════════════════
STARTING POINT
══════════════════════════════════════════════════════════════════

/Volumes/WS4TB/lvswarm
Existing:
  dollarpath/rebalance/  (R0–R7, runner)
  dollarpath/cli.py rebalance-run
  artifacts/rebalance_official_seed_42_2020-01-02_2024-12-31/
  tests/test_rebalance.py
  prereg/PREREG_REBALANCE_V1.md

Extend package as needed:
  dollarpath/rebalance/policies.py   # add R7b
  dollarpath/rebalance/targets.py    # equal + sixty_forty
  dollarpath/rebalance/battery.py    # cost grid, multi-year, multi-target
  CLI: rebalance-battery --official

══════════════════════════════════════════════════════════════════
TARGETS (FIXED — not learned)
══════════════════════════════════════════════════════════════════

T-EQ  equal_weight:
  universe U5 = SPY,QQQ,IWM,TLT,GLD
  w* = 0.2 each

T-64  sixty_forty (stocks/defensive):
  same U5
  w* = SPY 0.30, QQQ 0.20, IWM 0.10, TLT 0.25, GLD 0.15
  (sum=1.0; frozen strategic mix — NOT optimized on test)

══════════════════════════════════════════════════════════════════
PROTOCOL (LOCKED)
══════════════════════════════════════════════════════════════════

E1: decision at bar t uses prices index <= t-1 only
E2: action earns return of bar t
capital: 100000 faux per arm
default cost_bps_one_way: 2.5 (grid varies)
T_start: 2020-01-02
T_end:   2024-12-31
history_start: 2018-01-01 (data fetch only)
seed: 42
window metrics: path starts at T_start with $100k (slice prices to window)

══════════════════════════════════════════════════════════════════
ARMS
══════════════════════════════════════════════════════════════════

R0   never
R1   calendar_21
R2   calendar_63
R3   threshold_5
R4   threshold_10
R5   partial_0.25 every 21
R6   partial_0.50 every 21
R7   cost_aware v1 (legacy; keep for comparison)
R7b  cost_aware v2 IMPROVED:
     - check_every = 21 (not 5)
     - rebalance only if max_abs drift > 0.05 AND benefit > k * cost
     - benefit = 0.5 * l1_drift * vol * sqrt(21)
     - cost = turnover * 2 * bps/1e4
     - k = 2.0 (require clear edge before trading)
     - optional: skip if turnover < 0.02

Do NOT add performance-based w* changers.

══════════════════════════════════════════════════════════════════
BATTERY B1 — COST GRID (required)
══════════════════════════════════════════════════════════════════

Target: T-EQ
For cost_bps in [0, 1, 2.5, 5, 10, 25]:
  run all arms
  record ending_wealth, max_dd, total_costs, mean_turnover, mean_tracking_l1
  flag: does any R1–R7b beat R0 on wealth?

Write: cost_grid_T-EQ.json

══════════════════════════════════════════════════════════════════
BATTERY B2 — SECOND TARGET (required)
══════════════════════════════════════════════════════════════════

Target: T-64
cost_bps = 2.5
run all arms
Write: target_T-64.json
Compare narrative to T-EQ at 2.5 bps

══════════════════════════════════════════════════════════════════
BATTERY B3 — MULTI-YEAR (required)
══════════════════════════════════════════════════════════════════

Target: T-EQ, cost 2.5 bps
For year Y in 2020..2024:
  prices = that calendar year only (or year with 5-day burn-in from prior
  if needed for vol); start $100k at first bar of year
  run R0, R2, R3, R7b at minimum (all arms preferred if fast)
Write: multi_year_T-EQ.json
Report: fraction of years best-dynamic beats R0 on wealth

══════════════════════════════════════════════════════════════════
BATTERY B4 — R7b UNIT + ABLATION (required)
══════════════════════════════════════════════════════════════════

Unit tests: R7b does not rebalance every 5 days on tiny drift
Synthetic: large drift + high vol → may rebalance; tiny drift → no
On T-EQ 2.5 bps: R7b total_costs must be < R7 total_costs
  (if not, document and tune k only once under exploratory_ then
   freeze for official)

══════════════════════════════════════════════════════════════════
PASS / FAIL / REPORT RULES
══════════════════════════════════════════════════════════════════

This goal uses THREE terminal flags (all written):

1) WEALTH_EDGE (at 2.5 bps, T-EQ, full window):
   PASS if max(S_wealth of R1..R7b) > S_wealth(R0)
   else FAIL_WEALTH
   (v1 already FAIL — expect FAIL unless R7b or re-run changes)

2) COST_REGIME (B1):
   PASS if exists some cost_bps in grid where a dynamic arm beats R0
        on wealth
   else FAIL_COST_REGIME ("rebalance never helps on wealth at any fee")

3) TRACKING_VALUE (always REPORT, not wealth-PASS):
   Identify arm that minimizes mean_tracking_l1 among those with
   ending_wealth >= 0.98 * R0 ending_wealth (near-wealth, best track)
   If none, pick best track and note wealth gap

OVERALL:
  SCOPED_REBAL_V2_COMPLETE when B1–B4 artifacts exist, audit OK,
  and all three flags are written (PASS or FAIL each).

  Do NOT claim "rebalancing works" unless WEALTH_EDGE or COST_REGIME
  is PASS. Tracking-only value is still a valid product insight.

══════════════════════════════════════════════════════════════════
GATES (ORDERED)
══════════════════════════════════════════════════════════════════

G0  Read this file + v1 result card; pytest green baseline
G1  TargetSpec for T-EQ and T-64; tests
G2  Implement R7b; tests prove calmer than R7 on synthetic
G3  battery runner: cost grid + multi-target + multi-year
G4  CLI rebalance-battery --official
G5  Official battery run; leakage audit on decision logs
G6  claim_matrix_v2.json + result_card with three flags
G7  PROGRESS.md + README status update

══════════════════════════════════════════════════════════════════
DEFINITION OF DONE
══════════════════════════════════════════════════════════════════

DONE iff:
  - G0–G7 complete
  - B1, B2, B3, B4 artifacts present
  - pytest green
  - audit all_true on official decision logs
  - three flags WEALTH_EDGE, COST_REGIME, TRACKING_VALUE written
  - no live trading

DONE does not require WEALTH_EDGE=PASS.

══════════════════════════════════════════════════════════════════
NON-GOALS
══════════════════════════════════════════════════════════════════

- Options truth engine
- Allocation menu / unconstrained single-name
- Live capital
- Silent re-tuning until wealth PASS

══════════════════════════════════════════════════════════════════
ARTIFACT LAYOUT
══════════════════════════════════════════════════════════════════

dollarpath/artifacts/rebal_v2_<run_id>/
  LOCK.json
  claim_matrix_v2.json
  leakage_audit.json
  result_card.md
  cost_grid_T-EQ.json
  target_T-EQ_2.5bps.json
  target_T-64_2.5bps.json
  multi_year_T-EQ.json
  arm_* / (optional full dumps for 2.5 bps T-EQ)

══════════════════════════════════════════════════════════════════
COMMANDS (IMPLEMENT THEN RUN)
══════════════════════════════════════════════════════════════════

PYTHONPATH=. .venv/bin/python -m pytest -q tests
PYTHONPATH=. .venv/bin/python -m dollarpath.cli rebalance-battery --official --seed 42

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```
