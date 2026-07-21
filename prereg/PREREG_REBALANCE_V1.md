# PREREG_REBALANCE_V1 — Fixed-Target Rebalancing Lab

**Status:** LOCKED_BY_GOAL_REBALANCE (auto)  
**Codename:** Rebal-1  
**Capital:** Faux USD only  

## Question

Given fixed equal-weight target on {SPY,QQQ,IWM,TLT,GLD}, which rebalance policy maximizes after-cost ending faux wealth on 2020-01-02 → 2024-12-31 under one-bar information lag?

## Frozen

| Param | Value |
|---|---|
| w* | equal 0.2 × 5 |
| T_start / T_end | 2020-01-02 / 2024-12-31 |
| history_start | 2018-01-01 |
| cost | 2.5 bps one-way |
| protocol | asof=t-1, earn bar t |
| arms | R0–R7 per GOAL_REBALANCE.md |

## PASS

Best of R1–R7 beats R0 (never rebalance) on window-normalized ending_wealth; audit OK.

## FAIL

No dynamic rebalance arm beats R0.

## Non-claims

Not live alpha; not allocation skill; not options.
