# GOAL_REBALANCE — Official result

**Status:** `SCOPED_REBALANCE_FAIL`  
**Meaning:** No dynamic rebalance arm beat **R0 never-rebalance** on after-cost ending wealth (valid scientific outcome).  
**Audit:** OK  

**Target:** equal weight SPY/QQQ/IWM/TLT/GLD (fixed)  
**Window:** 2020-01-02 → 2024-12-31 · **Cost:** 2.5 bps one-way · **Protocol:** asof=t−1  

## Ranking (ending faux $)

| Rank | Policy | Ending $ | Max DD | Costs | Mean track L1 |
|---:|---|---:|---:|---:|---:|
| 1 | **R0 never** | **164,805** | 26.8% | 25 | 0.162 |
| 2 | R2 calendar_63 | 162,544 | 26.1% | 57 | 0.036 |
| 3 | R4 threshold_10 | 161,871 | 26.8% | 34 | 0.126 |
| 4 | R3 threshold_5 | 160,680 | 26.5% | 41 | 0.070 |
| 5 | R5 partial_0.25 | 160,537 | 26.1% | 49 | 0.041 |
| 6 | R1 calendar_21 | 160,499 | 26.0% | 81 | 0.021 |
| 7 | R6 partial_0.50 | 160,419 | 26.0% | 58 | 0.027 |
| 8 | R7 cost_aware | 159,181 | 25.9% | 135 | 0.008 |

## Insight

Under these costs and this window:

- **Not rebalancing** after buying equal weight made the most money.  
- **More rebalancing** → better tracking (lower L1 to target) but **more fees** and slightly lower wealth.  
- Best dynamic: infrequent calendar (63 days).  
- Cost-aware rule rebalanced too often (highest costs, best tracking, worst wealth).

Artifacts: `dollarpath/artifacts/rebalance_official_seed_42_2020-01-02_2024-12-31/`
