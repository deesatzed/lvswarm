# Phase P1 gate — PASS

**Date:** 2026-07-20  
**Claim:** P1 complete — modules measurable; no SOTA claim.

## Evidence

| Check | Result |
|---|---|
| pytest | 12 passed |
| State features | `dollarpath/state/features.py` (as-of only) |
| Regime detector | `dollarpath/prediction/regime.py` (AR1, local) |
| Governor | `dollarpath/governor/rules.py` + unit tests |
| Autobalance throttle | `rebalance_speed` on PredRulePolicy |
| Ablation CLI | `python -m dollarpath.cli ablate` |

## Ablation matrix (seed 42, 2018–2024 demo universe)

| Variant | Ending wealth | CAGR | Max DD | Mean turnover |
|---|---:|---:|---:|---:|
| pred_on_gov_on_speed1 | 134,006.86 | 4.28% | 10.86% | 0.00099 |
| pred_off_gov_on_speed1 | 196,169.59 | 10.13% | 25.61% | 0.00201 |
| pred_on_gov_off_speed1 | 134,477.00 | 4.34% | 10.86% | 0.00113 |
| pred_on_gov_on_speed025 | 132,645.81 | 4.13% | 10.96% | 0.00048 |
| hold_equal_ref | 202,748.31 | 10.66% | 26.97% | 0.00028 |

## Honest reading (no false “helpful” claims)

- Fixed `pred_rule` **reduces max DD** vs hold when prediction exposure scaling is on, but **lowers ending wealth** on this period.
- Therefore prediction-informed **defensive** rules are **not** claimed dollar-helpful yet; they are measurable for risk tradeoffs.
- Governor on vs off (pred on): nearly identical wealth/DD here — weak lift on this policy.
- Lower rebalance speed reduces turnover as designed.

Artifacts: `dollarpath/artifacts/p1_ablation_matrix_seed_42/`

## Next

P2 — learn discrete action templates on dollar reward (bandit/ACE).
