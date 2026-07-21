# GOAL_REBAL_V3 — Characterize the Rebalance Frontier

Use as Codex / Claude / Grok **`/goal`**.

**Prior:** GOAL_REBAL v2 → `SCOPED_REBAL_V2_COMPLETE`  
- WEALTH_EDGE FAIL @ 2.5 bps · COST_REGIME PASS @ 0–1 bps · tracking helps  

**This goal:** Map **fee break-even** and **(band, α) wealth–tracking frontier**; bootstrap Δwealth at 2.5 bps. No allocation search. No “force a wealth win.”

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

1. Fixed target w* = equal weight on U5 = SPY,QQQ,IWM,TLT,GLD.
2. Protocol E1/E2 (asof=t-1, earn bar t). Faux $100k. Real prices.
3. Battery F1: fine cost grid → break-even bps* where best dynamic
   ties or exceeds R0 never on ending_wealth.
4. Battery F2: no-trade family (band b, partial α) grid at 2.5 bps
   and at 0 bps; Pareto wealth vs mean_tracking_l1.
5. Battery F3: block-bootstrap CI for W_R7b - W_R0 and
   W_best_grid - W_R0 at 2.5 bps (block length 21).
6. claim_matrix_v3 + result_card + Pareto CSV/JSON.
7. Terminal: SCOPED_REBAL_V3_COMPLETE if all batteries written
   and audit OK. Wealth PASS not required.

══════════════════════════════════════════════════════════════════
LOCK DEFAULTS
══════════════════════════════════════════════════════════════════

universe: U5
w*: equal 1/5
T_start: 2020-01-02
T_end: 2024-12-31
history_start: 2018-01-01
capital: 100000
seed: 42
cost_grid_fine: [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0, 15.0, 25.0]
bands: [0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.12, 0.15, 0.20]
alphas: [0.25, 0.5, 0.75, 1.0]
check_every for band/α: 5 (evaluate rule each 5 sessions; act only if band hit)
bootstrap: n_boot=200, block=21, seed=42
arms always include: R0_never, R2_calendar_63, R7b_cost_aware_v2
plus full band×α grid labeled Rba_b{b}_a{a}

══════════════════════════════════════════════════════════════════
PASS / FLAGS (REPORT ALL)
══════════════════════════════════════════════════════════════════

BREAK_EVEN: smallest bps in grid where max_dynamic_ending >= R0_ending
  (if none, BREAK_EVEN = none / only_below_grid_min)
BOOTSTRAP_2.5: report 90% CI for deltas; flag if CI excludes 0
PARETO: list non-dominated (wealth, -tracking) points at 2.5 bps

OVERALL COMPLETE when artifacts + audit OK.

══════════════════════════════════════════════════════════════════
GATES
══════════════════════════════════════════════════════════════════

G0 pytest green
G1 frontier module: cost fine grid, band-alpha policies, bootstrap
G2 CLI rebalance-frontier --official
G3 official run
G4 claim_matrix_v3 + result_card + PROGRESS

══════════════════════════════════════════════════════════════════
DONE
══════════════════════════════════════════════════════════════════

Artifacts under dollarpath/artifacts/rebal_v3_<run_id>/
pytest green, audit OK, three batteries present.

══════════════════════════════════════════════════════════════════
NON-GOALS
══════════════════════════════════════════════════════════════════

Allocation search, options, live money, silent retune for wealth PASS.

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```
