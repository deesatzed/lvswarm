# GOAL_GLASSGATE_CONTROL_V2 — Label-Free Minority Control

Use as **`/goal`**. Prior v1: oracle C3 lift PASS; deployable path incomplete.

```text
/goal

OUTCOME:
1. Expand synthetic minority+wrong_bias case bank (multi-seed generator).
2. Controllers split into:
   - oracle_*  (may use is_correct) — CEILING only, not primary claim
   - deployable_* (NO is_correct access) — PRIMARY claim
3. Deployable features: claim-text dissent, evidence token overlap,
   majority-claim opposition, length penalty under pressure.
4. Multi-seed evaluation (seeds 0..19) with mean/CI for accuracy lift.
5. Flags: DEPLOYABLE_LIFT, ORACLE_CEILING, HARM_LIMIT, MULTI_SEED_ROBUST
6. SCOPED_GLASSGATE_CONTROL_V2_COMPLETE

LOCK:
  composition focus: one_correct_two_wrong
  bias: wrong_bias primary; neutral for harm
  n_seeds: 20
  no live LLM

PASS (primary):
  DEPLOYABLE_LIFT: best deployable mean acc > equal mean acc by >= 0.10
    on wrong_bias minority, multi-seed mean
  MULTI_SEED_ROBUST: frac seeds with deployable > equal >= 0.75
  HARM_LIMIT: deployable neutral acc >= equal neutral - 0.05 (mean)

ORACLE_CEILING: report only

END /goal
```
