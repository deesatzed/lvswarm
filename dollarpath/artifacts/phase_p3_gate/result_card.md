# Phase P3 gate — SCOPED_HISTORICAL_SOTA_PASS

**Date:** 2026-07-20  
**Prereg:** `prereg/PREREG_P3_HELDOUT.md` (written before held-out run)  
**Command:** `python -m dollarpath.cli eval-heldout --universe demo --seed 42`

## Claim (allowed language)

On preregistered universe [SPY, QQQ, IWM, TLT, GLD], train **2018-01-01 → 2022-12-31**, held-out **2023-01-01 → 2024-12-31**, cost **2.5 bps one-way**, DollarPath **offline template selection** achieved higher after-cost **ending wealth** than hold/calendar/vol-target under risk rule R (historical simulation). Risk rule satisfied via **calmar_win** (drawdown was higher than 1.2× min baseline DD).

## Held-out results ($100k start)

| Policy | Ending wealth | CAGR | Max DD | Calmar |
|---|---:|---:|---:|---:|
| **learned (QQQ 100%)** | **196,480.49** | 40.55% | 13.56% | **2.991** |
| hold_equal | 142,869.80 | 19.70% | 10.57% | 1.865 |
| calendar_equal | 140,326.02 | 18.62% | 10.66% | 1.747 |
| vol_target | 131,229.55 | 14.68% | 9.70% | 1.513 |

- beats_wealth: **True**
- dd_ok: False (concentration)
- calmar_win: **True** → **PASS**
- walkforward: 9 windows, no leakage: **True**

## Artifacts

- `dollarpath/artifacts/p3_heldout_seed_42/claim_matrix.json`
- `dollarpath/artifacts/p3_heldout_seed_42/heldout/`
- `dollarpath/artifacts/p3_heldout_seed_42/walkforward.json`
- `dollarpath/artifacts/p3_heldout_seed_42/stress.json`
- `dollarpath/artifacts/p3_heldout_seed_42/result_card.md`

## Tests

`pytest`: 15 passed

## Limits (mandatory)

- **Not** live trading; **not** a guarantee of future alpha  
- Method can select **single-name concentration** (here QQQ)  
- SOTA is **scoped historical** under stated costs/universe/periods only  
- P4/P5 not required for GOAL done  

## GOAL.md definition of done

**DONE** with `SCOPED_HISTORICAL_SOTA_PASS`.
