# GOAL_FAIRSHARE.md — Fair-Share / Quota Autobalance Lab

Use as Codex / Claude / Grok **`/goal`**.

**Path:** NF5 from `docs/OUTSIDE_FINANCE_DIRECTIONS.md`  
**Not this goal:** finance/ETF rebalance as primary, options, live multi-tenant production deploy  

**Portable idea:** same controller science as rebalancing — fixed target shares, drift, reallocation cost, dual scoreboard (fairness vs thrash/$).

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

1. Build a local discrete-time fair-share simulator:
   N tenants, total capacity C, target shares w*, demand shocks.
2. Policies that ONLY rebalance quotas toward w* (or hold):
   F0 never | F1 calendar | F2 threshold | F3 partial α | F4 cost-aware
3. Metrics: Jain fairness, mean/p95 queue-latency proxy, migration cost,
   thrash (quota L1 change), optional utility = fairness - λ*cost.
4. Sealed battery: baseline window + cost grid + (band,α) style threshold
   grid + bootstrap optional if fast.
5. Terminal SCOPED_FAIRSHARE_COMPLETE with honest flags:
   FAIRNESS_EDGE, COST_REGIME, PARETO note.

══════════════════════════════════════════════════════════════════
SIM LOCK DEFAULTS
══════════════════════════════════════════════════════════════════

N: 5 tenants
C: 100.0 service units / step
w*: equal 1/N
T: 2000 steps
seed: 42
demand: baseline rates + intermittent bursts (deterministic given seed)
migration_cost_per_L1: grid including 0, 0.5, 1, 2, 5
protocol: decisions at t use state at t-1 only (asof)

══════════════════════════════════════════════════════════════════
ARMS
══════════════════════════════════════════════════════════════════

F0  never          — set q=w* once; never change
F1  calendar_25    — every 25 steps fully reset q=w*
F2  calendar_100
F3  threshold_0.05 — if max |usage_share - w*| > 0.05, reset q=w*
F4  threshold_0.10
F5  partial_0.25 every 25
F6  partial_0.50 every 25
F7  cost_aware     — rebalance if estimated unfairness benefit > k * migration cost

══════════════════════════════════════════════════════════════════
FLAGS
══════════════════════════════════════════════════════════════════

FAIRNESS_EDGE @ default migration cost:
  PASS if best F1..F7 Jain > F0 Jain by > 1e-4 (or mean fairness)
COST_REGIME:
  PASS if some cost in grid has dynamic fairness>F0 with acceptable
  latency not worse than 1.1x F0 p95 (or report both)
COMPLETE when artifacts + tests green (FAIL flags OK)

══════════════════════════════════════════════════════════════════
GATES
══════════════════════════════════════════════════════════════════

G0 package fairshare/ + tests
G1 sim core + policies
G2 battery + CLI fairshare-run --official
G3 official sealed run
G4 result_card + PROGRESS + README link

══════════════════════════════════════════════════════════════════
DONE
══════════════════════════════════════════════════════════════════

fairshare artifacts under fairshare/artifacts/ or dollarpath/artifacts/fairshare_*
pytest includes fairshare tests
claim_matrix written

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```
