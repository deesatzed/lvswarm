# GOAL_REBAL_V3 — COMPLETE

**Status:** `SCOPED_REBAL_V3_COMPLETE`  
**Audit:** OK · **pytest:** 31 passed  
**Run:** `rebal_v3_official_seed_42`  
**Command:** `rebalance-frontier --official --seed 42 --n-boot 80`

## F1 — Fee break-even (R0 vs best of R2/R7b)

| | |
|---|---|
| Dynamic wealth edge holds for fees up to | **~1.75 bps** |
| Approx cross to “never wins” | **~1.875 bps** |
| At 2.5 bps (R2/R7b only) | never still edges those two anchors |

## F2 — Band×α frontier @ 2.5 bps

**Best wealth in full (b,α) grid:** `Rba_b0.07_a1` (band 7%, full step)  
- Ending ≈ **$166,720** vs R0 ≈ **$164,805** → **this family can beat never at 2.5 bps**  
- Tracking worse than tight calendar (L1 ≈ 0.093 vs R2 ≈ 0.036)

Pareto set mixes high-wealth loose bands with tighter-tracking calendars/partials (see `frontier_2.5bps.json`).

## F3 — Bootstrap @ 2.5 bps (80 resamples, block 21)

For R7b, R2, and Rba_b0.1_a0.5 vs R0:

- Real Δ mostly slightly negative for anchors  
- **90% CI includes 0** for tested deltas → wealth gaps are **not cleanly significant** under this bootstrap  
- Fraction of boots with dynamic > R0 is low (≈12–20%)

## Interpretation

1. **Fees:** Rebalance wealth edge is real only at **very low** all-in costs (~≤1.75 bps) for simple anchors.  
2. **Policy shape:** A **no-trade band (~7%) + full rebalance when hit** can beat never on this sample even at 2.5 bps—v2 arms under-explored the band family.  
3. **Uncertainty:** Bootstrap says don’t over-claim; many gaps are noise-scale.  
4. **Product:** Offer a **frontier** (tracking vs wealth vs fees), not a single slogan.

Artifacts: `dollarpath/artifacts/rebal_v3_official_seed_42/`
