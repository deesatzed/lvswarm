# PROGRESS.md — DollarPath

## Session 2026-07-20 (execute GOAL)

- **Phase / section:** P0 → P1 → P2 → P3 complete
- **Gates passed:** P0, P1, P2 DEV, **P3 SCOPED_HISTORICAL_SOTA_PASS**
- **Gates failed (recovered):** Online UCB full-period lost to hold (2 redesigns) → offline template selection
- **Artifacts:**
  - `dollarpath/artifacts/phase_p0_gate/`
  - `dollarpath/artifacts/phase_p1_gate/`
  - `dollarpath/artifacts/phase_p2_gate/`
  - `dollarpath/artifacts/phase_p3_gate/`
  - `dollarpath/artifacts/p3_heldout_seed_42/`
- **Key metrics (held-out 2023–2024):**
  - learned ending_wealth **$196,480** vs best baseline hold **$142,870**
  - Calmar 2.99 vs 1.87 → risk rule PASS
- **pytest:** 15 passed
- **Next action:** Optional P4/P5; or harden concentration risk; human may authorize live only under new goal
- **Blockers:** None

## Session 2026-07-19 (design)

- Spec-only: WHITEPAPER, BUILD_TODO, GOAL, README
