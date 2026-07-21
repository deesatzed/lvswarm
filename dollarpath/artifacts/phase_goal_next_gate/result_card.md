# GOAL_NEXT / DPL-1 — Terminal result

**Status:** `SCOPED_PROSPECTIVE_FAIL_B2`  
**Audit:** all L1–L7 **true** (run is valid; claim is FAIL not VOID)  
**Run id:** `prospective_official_seed_42_2020-01-02_2024-12-31`  
**Window:** 2020-01-02 → 2024-12-31 (burn-in history from 2018; ranking normalized to $100k at T_start)  
**Protocol:** asof=t−1, earn bar t; expanding train; select_every=21; decision_every=5  
**B2 constraints:** max_weight=0.40, min_names=3  

## Official arm results (window-normalized ending wealth)

| Arm | Role | Ending wealth | Max DD | Calmar |
|---|---|---:|---:|---:|
| A0 | hold_equal | **168,443.90** | 26.97% | 0.409 |
| A1 | hold_qqq (honesty) | 245,952.44 | 35.12% | 0.563 |
| A2 | calendar_equal | 160,861.79 | 25.76% | 0.388 |
| A3 | vol_target | 140,850.46 | 17.54% | 0.405 |
| B1 | unconstrained select | 188,934.58 | 35.12% | 0.387 |
| **B2** | **constrained select (primary)** | **165,690.25** | 29.64% | 0.359 |

### B2 rule

- beats_wealth vs max(A0,A2,A3): **False** (165.7k < 168.4k A0)
- dd_ok: True  
- calmar_win: False  
→ **FAIL_B2**

### Honesty: B1 vs A1

- B1 188.9k vs A1 QQQ-hold 246.0k (ratio ≈ 0.77)  
- Unconstrained selector **did not** match buy-and-hold QQQ; re-selection/costs underperformed pure QQQ hold.

## Multi-year appendix (fixed train→test deploy)

| Year | B2 end | A0 end | B2>A0? |
|---|---:|---:|---|
| 2020 | 127,747 | 123,772 | yes |
| 2021 | 119,688 | 111,688 | yes |
| 2022 | 77,543 | 80,808 | no |
| 2023 | 125,828 | 117,635 | yes |
| 2024 | 121,275 | 117,935 | yes |

B2 beat A0 in 4/5 years on nested battery but **lost the sealed full-path primary metric**.

## Cost surface (full path absolute, A0 vs B2)

B2 ending < A0 at every bps in {0, 2.5, 5, 10, 25}; gap widens with costs.

## Interpretation (useful FAIL)

Under risk limits and no-lookahead protocol, **this template menu + offline selection does not beat equal-weight hold** on the primary sealed path.  
v1 unconstrained QQQ held-out win does **not** transfer to diversified prospective B2.

## Artifacts

`dollarpath/artifacts/prospective_official_seed_42_2020-01-02_2024-12-31/`

## Next (not auto under this GOAL)

- Exploratory: train score = mean log growth / Calmar (label `exploratory_*`)  
- Or accept no free diversified edge with current menu  
- Online RL / prediction only after a new prereg (DPL-2)
