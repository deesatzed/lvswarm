# PREREG_P2_DEV — Template bandit dollar learning (dev)

**Status:** Preregistered before P2 official comparison  
**Date:** 2026-07-20  
**Seed list:** 42 (primary)

## Hypothesis

**Offline template selection** (evaluate each discrete allocation template on the **train** window by ending wealth; deploy the winner) achieves higher **ending_wealth** on the **dev full period** than:

1. hold_equal  
2. calendar_equal  
3. vol_target  

after costs (2.5 bps one-way).

Rationale: pure online UCB exploration is structurally disadvantaged vs the best fixed baseline when exploration continues; offline selection is a valid L1 learning algorithm (policy class search on dollar reward).

## Config (locked)

| Field | Value |
|---|---|
| Universe | SPY, QQQ, IWM, TLT, GLD |
| Period | 2018-01-01 → 2024-12-31 |
| Start capital | 100_000 |
| Cost | 2.5 bps one-way |
| Train frac | 0.7 of bars for template scoring |
| Deploy | best train template, rebalance every 5 days |
| Method | offline_template_selection |
| Governor | OFF for learned deploy (fair vs unconstrained hold) |
| Primary metric | ending_wealth |

## Pass rule (dev only — not P3 SOTA)

`ending_wealth(learned_offline_template) > max(ending_wealth of three baselines)` on same full period/costs/seed.

## Failure rule

If not met after this run, record FAIL-P2 in FAILURE_LEDGER and PROGRESS; iterate design (templates/reward) up to 5 redesigns per GOAL.md before hard stop.

## Non-claims

- Not held-out SOTA  
- Not live trading  
