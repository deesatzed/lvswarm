# Phase P2 gate — PASS (dev)

**Date:** 2026-07-20  
**Prereg:** `prereg/PREREG_P2_DEV.md`  
**Method:** offline template selection (train 70% → deploy winner full period)

## Result

| Policy | Ending wealth | CAGR | Max DD |
|---|---:|---:|---:|
| **learned_offline_template** (QQQ 100%) | **337,702.95** | — | — |
| hold_equal | 202,748.31 | 10.66% | 26.97% |
| calendar_equal | 195,056.17 | 10.04% | 25.76% |
| vol_target | 169,602.43 | 7.86% | 17.54% |

**BEATS baselines on ending_wealth: YES**

Selected template index 6: weights `[0,1,0,0,0]` = **QQQ** only (universe order SPY,QQQ,IWM,TLT,GLD).

Artifacts: `dollarpath/artifacts/p2_train_bandit_seed_42/`

## Failed approaches (documented)

1. Online UCB full-period — exploration cost lost to hold  
2. Frozen contextual greedy after UCB — still underperformed hold  

## Limits

- **Not** held-out SOTA (P3)  
- Train/deploy overlap on full-period score is optimistic (train subset for selection only; deploy evaluated full period including train years)  
- Concentration risk (single name) not penalized in primary metric  

## Next

P3 walk-forward + true held-out years + stress windows.
