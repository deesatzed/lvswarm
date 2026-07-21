# PROGRESS.md — DollarPath

## Session 2026-07-21 GOAL_GLASSGATE_CONTROL_V2

- Label-free deployable controllers + oracle ceiling + multi-seed (20) + expanded bank
- **Status:** `SCOPED_GLASSGATE_CONTROL_V2_COMPLETE`
- DEPLOYABLE_LIFT **PASS** (Δ≈0.94, best=`deployable_anti_cue`)
- MULTI_SEED_ROBUST **PASS** · HARM_LIMIT **PASS**
- Oracle ceiling reported separately (~1.0 mean)
- Artifacts: `clawswarmed/artifacts/glassgate_control_v2_seed_42/`
- unittest v2: 5 passed

## Session 2026-07-21 GOAL_GLASSGATE_CONTROL

- Created GOAL_GLASSGATE_CONTROL.md + glassgate_control.py + CLI + tests
- **Status:** `SCOPED_GLASSGATE_CONTROL_COMPLETE`
- CONTROL_LIFT **PASS** (C3 scarce_protect oracle upper bound acc=1.0 vs equal 0.0 under wrong_bias)
- Label-free C4 dissent_boost acc=0.5 on wrong_bias minority
- HARM_LIMIT **PASS**
- Artifacts: `clawswarmed/artifacts/glassgate_control_seed_42/`
- unittest: 4 passed

## Session 2026-07-21 GOAL_FAIRSHARE_V2

- Created GOAL_FAIRSHARE_V2.md; frontier CLI; F7b; stress; multi-seed
- **Status:** `SCOPED_FAIRSHARE_V2_COMPLETE`
- FAIRNESS_EDGE PASS · COST_REGIME PASS · STRESS_STABLE 6/6 · F7b_IMPROVED true
- Multi-seed ΔJain F3-F0 ≈ +0.043 CI excludes 0; Δp95 ≈ +60 always
- Artifacts: `fairshare/artifacts/fairshare_v2_official_seed_42/`

## Session 2026-07-20 GOAL_FAIRSHARE

- Created GOAL_FAIRSHARE.md, fairshare/ sim+policies+CLI
- Fixed model: quota **drift toward usage** so rebalance is meaningful
- **Status:** `SCOPED_FAIRSHARE_COMPLETE` FAIRNESS_EDGE=**PASS** COST_REGIME=**PASS**
- Best fairness: **F3_threshold_0.05** (Jain ~0.999 vs F0 ~0.956)
- Tradeoff: stricter fairness → higher p95 queue under bursts
- Artifacts: `fairshare/artifacts/fairshare_official_seed_42/`
- pytest fairshare: 5 passed

## Session 2026-07-20 execute GOAL_REBAL_V3

- Created GOAL_REBAL_V3.md + PREREG + frontier module + CLI `rebalance-frontier`
- **Status:** `SCOPED_REBAL_V3_COMPLETE` (audit OK, 31 tests)
- Break-even: dynamic edge up to **~1.75 bps**; cross ~1.875 bps
- Best (b,α) @ 2.5 bps: **Rba_b0.07_a1** ends **above** R0 (~$166.7k vs $164.8k)
- Bootstrap 90% CIs for tested Δ vs R0 **include 0**
- Artifacts: `dollarpath/artifacts/rebal_v3_official_seed_42/`
- Gate: `dollarpath/artifacts/phase_goal_rebal_v3_gate/result_card.md`

## Session 2026-07-20 execute GOAL_REBAL

- Re-ran full battery: `rebalance-battery --official --seed 42`
- **Status:** `SCOPED_REBAL_V2_COMPLETE` (audit OK, 30 tests)
- Flags: WEALTH_EDGE=FAIL_WEALTH · COST_REGIME=PASS · TRACKING=R2_calendar_63
- Gate card: `dollarpath/artifacts/phase_goal_rebal_gate/result_card.md`
- **GOAL_REBAL definition of done: MET**

## Session 2026-07-20 GOAL_REBAL v2

- **Status:** `SCOPED_REBAL_V2_COMPLETE` (audit OK)
- **WEALTH_EDGE:** FAIL at 2.5 bps (never still wins on $)
- **COST_REGIME:** PASS (dynamic beats never at some lower fee levels)
- **TRACKING_VALUE:** R2 calendar_63 near-wealth best track among near-R0
- **R7b vs R7:** costs 47 vs 135; ending 164.8k vs 159.2k
- **Artifacts:** `dollarpath/artifacts/rebal_v2_official_seed_42/`
- **pytest:** 30 passed
- **CLI:** `rebalance-battery --official`

## Session 2026-07-20 GOAL_REBALANCE (Option 2)

- **Status:** `SCOPED_REBALANCE_FAIL` (audit OK) — never-rebalance beat all dynamic rules on $  
- **Insight:** rebalancing improves tracking, costs reduce wealth at 2.5 bps on 2020–24 equal-weight target  
- **Best dynamic:** R2 calendar_63  
- **Artifacts:** `dollarpath/artifacts/rebalance_official_seed_42_2020-01-02_2024-12-31/`  
- **pytest:** 28 passed  
- **Docs:** GOAL_REBALANCE.md, prereg/PREREG_REBALANCE_V1.md  

## Session 2026-07-20 GOAL_NEXT execute

- **Gates completed:** N0–N10  
- **Official status:** `SCOPED_PROSPECTIVE_FAIL_B2` (audit_ok=true)  
- **Artifacts:** `dollarpath/artifacts/prospective_official_seed_42_2020-01-02_2024-12-31/`  
  Gate card: `dollarpath/artifacts/phase_goal_next_gate/result_card.md`  
- **Key metrics B2 vs A0:** 165,690 vs 168,444 (window-normalized $) — FAIL  
- **B1 vs A1:** 188,935 vs 245,952 — unconstrained ≠ QQQ hold  
- **Audit:** L1–L7 all true; 10554 decisions checked  
- **pytest:** 22 passed  
- **Next:** Human decides exploratory train-score variant or accept FAIL; do not claim PASS  
- **Blockers:** None  

### Implementation notes

- Added `dollarpath/prospective/` (protocol, templates, arms, runner, audit, multi_year, fast_select)  
- CLI: `prospective-run`, `prospective-audit`, `multi-year-battery`  
- Fast constant-mix score for selection (vectorized) so expanding reselect is tractable  

## Session 2026-07-20 (execute GOAL v1)

- P0–P3 complete; `SCOPED_HISTORICAL_SOTA_PASS` (unconstrained QQQ held-out)

## Session 2026-07-19 (design)

- Spec-only white paper / BUILD / GOAL
