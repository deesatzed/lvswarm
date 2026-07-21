# FAILURE_LEDGER.md — DollarPath

Append-only. Do not erase prior entries; amend with new rows if status changes.

| ID | Date | Phase | Symptom | Likely cause | Mitigation / status |
|---|---|---|---|---|---|
| F001 | 2026-07-20 | P2 | Online UCB full-period ending_wealth < hold | Exploration allocates to cash/defensive templates; bull market punishes explore | Switch to offline template selection on train dollars; **resolved** |
| F002 | 2026-07-20 | P2 | Frozen contextual greedy after UCB still < hold | Segment mean rewards ≠ full-path optimal; still exploration bias in values | Same as F001; **resolved** via offline selection |
| F003 | 2026-07-20 | P3 | dd_ok false (learned DD 13.6% > 1.2× min baseline ~9.7%) | Single-name QQQ concentration | Risk rule still PASS via calmar_win; document concentration limit as future work |
| F004 | 2026-07-20 | GOAL_NEXT N7 | SCOPED_PROSPECTIVE_FAIL_B2: B2 ending 165.7k < A0 168.4k | Constrained menu cannot beat equal hold on 2020–24 sealed path; selection/turnover drag | Valid scientific FAIL; audit clean; optional exploratory train score later |
| F005 | 2026-07-20 | GOAL_NEXT | Official run too slow with env-based offline select | O(templates × bars × reselections) | Mitigated with vectorized fast_select constant-mix score |

## Protocol

If the same class of error occurs **3+ times** in a row:

1. List 5–7 possible sources  
2. Distill to 1–2 most likely  
3. Add logs/assertions to validate  
4. Only then implement the fix  
