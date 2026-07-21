# GOAL_FAIRSHARE_V2 — Fairshare Frontier Characterization

Use as **`/goal`**. Prior: v1 `SCOPED_FAIRSHARE_COMPLETE` (FAIRNESS PASS, latency tradeoff, F7 shy).

```text
/goal

OUTCOME:
1. Pareto: Jain vs p95_queue vs migration_cost for F0–F7 + F7b + band×α grid
2. Demand-stress battery (vary burst params)
3. F7b cost-aware v2 (band + k*cost + slower check)
4. Multi-seed CIs for ΔJain and Δp95 (F3 vs F0)
5. claim_matrix_v2 + result_card; SCOPED_FAIRSHARE_V2_COMPLETE

LOCK:
  N=5, C=100, steps=2000, default seed=42, drift_alpha=0.08
  w*=equal, protocol asof t-1
  mig costs grid: [0, 0.5, 1, 2, 5, 10]
  seeds for CI: 0..19 (20 seeds)
  demand stress: at least 6 configs (baseline + extremes)

FLAGS (report all):
  FAIRNESS_EDGE @ mig=1 (best dynamic Jain > F0)
  LATENCY_REGRET (best fairness arm p95 vs F0)
  F7b_IMPROVED (F7b n_rebalances > F7 and costs structure sane)
  STRESS_STABLE (fraction of stress configs where F3 Jain > F0)

DONE: artifacts + tests + COMPLETE status (FAIL flags OK)

NON-GOALS: finance, Glass Gate implement, live deploy

END /goal
```
