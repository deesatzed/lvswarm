# GOAL_GLASSGATE_CONTROL.md

Use as **`/goal`**. Turn Glass Gate from **measure-only** into **control** of agent attention weights so correct minority signals survive majority/authority bias — sealed, synthetic, no live spend.

```text
/goal

OUTCOME:
1. Implement broadcast_alpha/glassgate_control.py (+ tests + CLI).
2. Controllers assign attention weights over panel agents; selection =
   weighted policy under bias pressure (synthetic judges).
3. Arms: equal, majority_force, authority_boost, scarce_protect,
   dissent_boost, threshold_rebalance, fairshare_pull.
4. Metrics: accuracy on one_correct_two_wrong + wrong_bias cases;
   discrimination D; control_lift vs equal baseline; cost = total
   weight-mass / thrash proxy.
5. Sealed official run → claim_matrix + result_card.
6. Terminal SCOPED_GLASSGATE_CONTROL_COMPLETE (FAIL flags OK if audit OK).

LOCK:
  seed=42, use generate_ab_cases from ab_bias_suite
  focus filter: panel_composition one_correct_two_wrong
  bias conditions: neutral + wrong_bias (report both)
  no live LLM

PASS FLAGS (report):
  CONTROL_LIFT: scarce_protect or dissent_boost accuracy > equal on wrong_bias minority cases
  HARM_LIMIT: control does not tank neutral accuracy below equal - 0.05
  COST_OK: report thrash; no hard fail

NON-GOALS: JLENS, live OpenRouter, product UI

END /goal
```
