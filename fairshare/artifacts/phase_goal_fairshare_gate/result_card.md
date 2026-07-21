# GOAL_FAIRSHARE — COMPLETE

**Status:** `SCOPED_FAIRSHARE_COMPLETE`  
**FAIRNESS_EDGE:** PASS · **COST_REGIME:** PASS · **Audit:** OK  

## Setup

- 5 tenants, capacity 100/step, 2000 steps, seed 42  
- Target: equal shares  
- Quotas **drift toward recent usage** (sticky pressure); policies pull back to fair shares  
- Migration cost for changing quotas  

## Ranking (default mig cost = 1)

| Policy | Jain (quota fairness) | Track L1 | p95 queue | mig cost |
|---|---:|---:|---:|---:|
| **F3 threshold 5%** | **~0.999** | low | higher | pays |
| F0 never | ~0.956 | higher drift | lower | ~0 |
| calendars / partials | high | … | … | … |

## Insight

1. **Rebalancing quotas toward a fair target improves fairness** vs letting shares drift with demand pressure.  
2. **Tradeoff:** fair shares under burst load → **hot tenant queues more** (p95 queue up).  
3. Same dual story as finance rebalance: **control quality vs cost/latency**, not free lunch on every metric.

Artifacts: `fairshare/artifacts/fairshare_official_seed_42/`
