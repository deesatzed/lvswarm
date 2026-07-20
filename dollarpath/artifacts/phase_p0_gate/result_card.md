# Phase P0 gate — PASS

**Date:** 2026-07-20  
**Claim:** P0 complete — dollars measurable; no RL claim.

## Evidence

| Check | Result |
|---|---|
| `pytest` | 8 passed |
| Real prices cached | SPY,QQQ,IWM,TLT,GLD · 2018-01-02 → 2024-12-30 · 1760 rows |
| Baselines runnable | hold_equal, calendar_equal, vol_target |
| Artifacts | `metrics.json` + `equity_curve.csv` + `result_card.md` per policy |

## Baseline results (seed 42, $100k start, 2.5 bps one-way)

| Policy | Ending wealth | CAGR | Max DD | Costs |
|---|---:|---:|---:|---:|
| hold_equal | 202,748.31 | 10.66% | 26.97% | 25.00 |
| calendar_equal | 195,056.17 | 10.04% | 25.76% | 109.22 |
| vol_target | 169,602.43 | 7.86% | 17.54% | 629.56 |

Best ending wealth: **hold_equal**

Comparison: `dollarpath/artifacts/p0_baselines_compare_seed_42/`

## Limits

- No learning / RL yet  
- No SOTA claim  
- Historical simulation only  

## Next

BUILD_TODO **P1.1** — state builder / prediction-optional / governor / autobalance
