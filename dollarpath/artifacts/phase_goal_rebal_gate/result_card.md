# GOAL_REBAL execute — terminal gate

**Date:** 2026-07-20  
**Command:** `python -m dollarpath.cli rebalance-battery --official --seed 42`  
**Status:** `SCOPED_REBAL_V2_COMPLETE`  
**pytest:** 30 passed  
**Audit:** all_true  

## Three flags (GOAL_REBAL)

| Flag | Result |
|---|---|
| WEALTH_EDGE @ 2.5 bps T-EQ | **FAIL_WEALTH** (never-rebalance still highest $) |
| COST_REGIME (any fee in grid) | **PASS** (dynamic beats never at 0–1 bps) |
| TRACKING_VALUE | **R2_calendar_63** (best track among near-wealth) |

## Artifacts

`dollarpath/artifacts/rebal_v2_official_seed_42/`

- LOCK.json, claim_matrix_v2.json, leakage_audit.json, result_card.md  
- cost_grid_T-EQ.json, target_T-EQ_2.5bps.json, target_T-64_2.5bps.json  
- multi_year_T-EQ.json, b4_r7b_ablation.json, arm_*  

## Definition of done

Met: batteries B1–B4, three flags written, audit OK, no live trading.  
WEALTH_EDGE FAIL is allowed under GOAL_REBAL.
