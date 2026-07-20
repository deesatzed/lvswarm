# PREREG_P3_HELDOUT — DollarPath v1 SOTA gate

**Status:** LOCKED before held-out execution  
**Date:** 2026-07-20  
**Code method:** offline template selection (`default_templates` + train-window ending wealth)

## Frozen before run

| Field | Value |
|---|---|
| Universe | SPY, QQQ, IWM, TLT, GLD |
| Full data span available | 2018-01-01 → 2024-12-31 |
| **Held-out test period** | **2023-01-01 → 2024-12-31** |
| **Train period for selection** | **2018-01-01 → 2022-12-31** |
| Embargo | none beyond calendar year boundary (train ends 2022-12-31, test starts 2023-01-01) |
| Start capital | 100_000 |
| Cost | 2.5 bps one-way |
| Rebalance every | 5 trading days |
| Seed | 42 (deterministic offline ranking) |
| Governor on learned | OFF |
| Primary metric | ending_wealth on **held-out only** (policy run on held-out prices after selection on train only) |

## Baselines (same held-out period, same costs)

1. hold_equal  
2. calendar_equal (every 21)  
3. vol_target  

## Risk rule (pick ONE — locked)

**Rule R:** Calmar on held-out must be **strictly greater** than best baseline Calmar  
**OR** if learned max_drawdown ≤ best_baseline max_drawdown * 1.20, ending_wealth must be strictly greater than all baselines.

Implemented check in code as:

```
beats_wealth = learned.ending_wealth > max(baseline ending_wealth)
dd_ok = learned.max_drawdown <= max(baseline max_drawdown among those) * 1.20
  OR learned.calmar > max(baseline calmar)
PASS = beats_wealth AND (dd_ok OR calmar_win)
```

Actually simplify per GOAL default:

**PASS if:**
1. `ending_wealth(learned) > max(ending_wealth baselines)` on held-out  
2. AND `max_drawdown(learned) <= 1.20 * min_dd_among_baselines_with_best_wealth_or_best_dd`  

Locked precise rule:

```
PASS = (learned.ending_wealth > best_baseline_ending_wealth)
       AND (learned.max_drawdown <= best_baseline_max_drawdown * 1.20
            OR learned.calmar > best_baseline_calmar)
```

where `best_baseline_*` are each taken as the max ending_wealth baseline's corresponding metric for wealth comparison; for drawdown cap use the **minimum** max_drawdown among baselines (strictest). For calmar use **maximum** calmar among baselines.

## Walk-forward (supporting, not primary)

- train_bars=504, test_bars=126, embargo_bars=5  
- Report aggregate; does not override held-out PASS/FAIL  

## Stress segments (report only)

- 2020-02-15 → 2020-04-15  
- 2022-01-01 → 2022-12-31  
Learned policy: select on data **before** stress start; evaluate **during** stress only.

## Claim language if PASS

"On preregistered universe [SPY,QQQ,IWM,TLT,GLD], train 2018–2022, held-out 2023–2024, cost 2.5 bps one-way, DollarPath offline template selection achieved higher after-cost ending wealth than hold/calendar/vol-target under risk rule R (historical simulation)."

## Claim if FAIL

`SCOPED_HISTORICAL_SOTA_FAIL` with metrics table — valid terminal science outcome.

## Non-claims

- Not live trading  
- Not all markets  
- Not guarantee of future alpha  
