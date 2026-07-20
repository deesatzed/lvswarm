# GOAL.md — DollarPath Autonomous Development Contract

Use this document as the Codex / Claude / Grok **`/goal`** (or equivalent) for building and testing DollarPath until the SOTA gate passes or fails honestly.

**White paper:** `docs/WHITEPAPER.md`  
**Checklist:** `BUILD_TODO.md`  
**North star:** `END_GOAL_DOLLARS_OVER_TIME.md`

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

Build and validate DollarPath: a local-first application that learns
and evaluates capital-allocation policies whose sole success metric is
MORE WORTH / DOLLARS OVER TIME (after costs) versus transparent
baselines, without catastrophic ruin — with reproducible artifacts.

The v1 SOTA application gate (Phase P3) is reached only when a
preregistered held-out evaluation shows the learned policy beats all
required baselines on the primary dollar metric under the preregistered
drawdown/Calmar constraint, after costs, with ablations and replayable
artifacts. If it fails, record FAIL with evidence; do not reword the
metric to force a win.

══════════════════════════════════════════════════════════════════
TASK TYPE
══════════════════════════════════════════════════════════════════

Full-stack research software engineering:
  - portfolio simulation environment (real historical prices)
  - baseline + RL/bandit policies
  - optional prediction state + expert governor
  - walk-forward evaluation, metrics, artifacts
  - tests and CLI
  - NO live capital trading unless a human explicitly authorizes a
    separate goal

══════════════════════════════════════════════════════════════════
STARTING POINT
══════════════════════════════════════════════════════════════════

Workspace root:
  /Volumes/WS4TB/lvswarm

Authoritative specs:
  - docs/WHITEPAPER.md
  - BUILD_TODO.md
  - GOAL.md (this file)
  - END_GOAL_DOLLARS_OVER_TIME.md

Prior art to REUSE (read before reinventing):
  - /Volumes/WS4TB/macwise-clean-test/naked_straddle_sim/
      ace_core/ (regime, ACE memory, ensemble patterns)
      docs/SIMULATION_AND_MEASUREMENT.md
      docs/STATISTICAL_RIGOR.md
      docs/ARCHITECTURE.md
  - /Volumes/WS4TB/lvswarm/clawswarmed/
      artifact patterns: metrics.json, result_card.md, ledger.jsonl
  - /Volumes/WS4TB/lvswarm/PORTFOLIO_PREDICTION_EXPERT_ANALYSIS.md
  - /Volumes/WS4TB/lvswarm/AUTOBALANCE_CONTEXTS_TOP5.md

Application package target:
  /Volumes/WS4TB/lvswarm/dollarpath/

Default compute:
  Local Apple Silicon. Prefer $0 market data (yfinance + disk cache).
  LLM/OpenRouter OFF by default. Any paid API requires hard budget
  and logging; stop if budget would be exceeded.

══════════════════════════════════════════════════════════════════
PRIMARY OBJECTIVE (NON-NEGOTIABLE)
══════════════════════════════════════════════════════════════════

Maximize and PROVE after-cost wealth growth of a learned policy vs
baselines on historical faux capital.

Primary metric (default; change only with human approval + prereg):
  ending_wealth  (and report CAGR alongside)

Risk constraint (default):
  max_drawdown of learned policy must not be worse than the best
  baseline max_drawdown by more than 20% relative
  OR Calmar_ratio (CAGR / |max_drawdown|) strictly better with
  ending_wealth not worse than best baseline
  (prereg must pick ONE rule before P3 held-out)

Baselines that must be beaten at P3:
  1. Buy-and-hold (equal weight or declared market proxy)
  2. Calendar rebalance to fixed targets
  3. Simple volatility targeting

══════════════════════════════════════════════════════════════════
EXPLICIT NON-GOALS
══════════════════════════════════════════════════════════════════

- Live brokerage trading / real money deployment
- Claiming production-ready while BUILD_TODO items remain open
- Mock market prices, mock fills, or mock rewards as evidence
- Multi-agent swarm theater without dollar lift
- J-lens / Glass Gate as a dependency for this goal
- Guaranteeing future live alpha
- Skipping ablations and still claiming modules “add value”
- Time estimates in plans

══════════════════════════════════════════════════════════════════
HARD CONSTRAINTS
══════════════════════════════════════════════════════════════════

1. NO MOCK for market outcomes, fills, or rewards without explicit
   human approval in-session.
2. Real data may be CACHED on disk (cache is not a mock).
3. No lookahead: features at t use only information available at t.
4. Deterministic seeds for reported runs.
5. Every claim needs an artifact path (metrics.json + result_card.md).
6. Do not start P4/P5 until P3 PASS or human override in writing.
7. Do not spend unbounded API money; default spend = 0.
8. If the same error occurs 3+ times: stop, list 5–7 causes, pick
   1–2, add logs, then fix (project error protocol).
9. Validate each BUILD_TODO gate before the next phase.
10. Never mark GOAL complete if tests fail or held-out claim is FAIL
    without documenting FAIL as the terminal honest result.

══════════════════════════════════════════════════════════════════
FIRST REQUIRED STEP (EVERY AGENT SESSION)
══════════════════════════════════════════════════════════════════

Before editing code:

  cd /Volumes/WS4TB/lvswarm
  # inspect state
  ls -la
  test -f docs/WHITEPAPER.md && test -f BUILD_TODO.md && test -f GOAL.md
  # if dollarpath exists:
  #   python -m compileall -q dollarpath tests 2>/dev/null || true
  #   pytest -q 2>/dev/null || true
  # read PROGRESS.md and FAILURE_LEDGER.md if present
  # continue from first incomplete BUILD_TODO gate

If the tree is dirty mid-phase, finish or repair the current gate
before starting a new phase.

══════════════════════════════════════════════════════════════════
AUTONOMOUS EXECUTION LOOP
══════════════════════════════════════════════════════════════════

Loop until P3 terminal state (PASS or FAIL) or hard block:

  1. Read BUILD_TODO.md; select the first incomplete checkbox section.
  2. Implement ONLY that section’s items.
  3. Run that section’s Validation / Gate commands.
  4. If gate fails:
       - append FAILURE_LEDGER.md (symptom, hypothesis, mitigation)
       - fix or narrow scope within the SAME section
       - do not advance phase
  5. If gate passes:
       - mark checkboxes [x] in BUILD_TODO.md
       - append PROGRESS.md with: section id, commands run, artifact
         paths, key metrics, next section
  6. Proceed to next section.
  7. After P0, P1, P2, P3 gates: write/update
       dollarpath/artifacts/phase_<id>_gate/result_card.md

Stop and surface to human if:
  - human approval item is required (see BUILD_TODO)
  - data vendor blocks all free sources
  - P2 cannot beat baselines after reasonable iteration cap
    (define: 5 full train/eval redesigns without dev lift → STOP
     with FAIL-P2 report)
  - disk or environment broken

══════════════════════════════════════════════════════════════════
PHASE EXIT CRITERIA (SUMMARY)
══════════════════════════════════════════════════════════════════

P0 COMPLETE:
  - Baselines run on real cached prices
  - metrics.json + equity_curve per baseline
  - pytest green
  - Claim language: dollars measurable only

P1 COMPLETE:
  - pred/governor/autobalance ablations runnable
  - no module claimed helpful without numbers

P2 COMPLETE:
  - prereg/PREREG_P2_DEV.md exists and matches run config
  - learned policy beats all three baselines on DEV after costs
    OR FAIL-P2 report with evidence

P3 COMPLETE (v1 SOTA application gate):
  - prereg/PREREG_P3_HELDOUT.md written BEFORE held-out run
  - walk-forward + stress artifacts exist
  - held-out: learned beats baselines on primary metric after costs
  - risk constraint satisfied
  - ablations present
  - result_card claims either:
      SCOPED_HISTORICAL_SOTA_PASS
      or SCOPED_HISTORICAL_SOTA_FAIL
  - both are valid terminal outcomes; only PASS means “SOTA app”
    for marketing language; FAIL means science succeeded in falsifying

══════════════════════════════════════════════════════════════════
DEFAULT EXPERIMENT CONFIG (override only via prereg)
══════════════════════════════════════════════════════════════════

universe:     ["SPY", "QQQ", "IWM", "TLT", "GLD"]
start_capital: 100000.0
cost_model:    5 bps round-trip equivalent (document exact formula)
bar:           daily
execution:     next bar (declare open or close in config)
seed:          42 for smoke; prereg list for official runs
prediction:    optional; default off for first baseline purity, then on
governor:      on for learned policy evals
llm:           disabled

══════════════════════════════════════════════════════════════════
ARTIFACT CONTRACT (EVERY OFFICIAL RUN)
══════════════════════════════════════════════════════════════════

dollarpath/artifacts/<run_id>/
  config.json          # full config + git commit if available
  metrics.json         # machine metrics
  equity_curve.csv     # time, wealth, drawdown, exposure
  result_card.md       # human summary + claims + limits
  decisions.jsonl      # optional: actions, vetoes, costs
  comparison.json      # vs baselines when applicable

metrics.json MUST include at least:
  ending_wealth, total_return, cagr, max_drawdown, calmar,
  total_costs, mean_turnover, policy_id, universe, start, end,
  seed, primary_metric_name, beats_baselines (bool or null)

══════════════════════════════════════════════════════════════════
CLAIM LANGUAGE (ENFORCED)
══════════════════════════════════════════════════════════════════

ALLOWED after P3 PASS:
  "On preregistered universe U and period T with cost model C,
   DollarPath policy P achieved higher after-cost ending wealth
   than baselines B1–B3 under risk rule R (historical simulation)."

FORBIDDEN always unless separate live goal passes:
  "guaranteed profits", "production trading ready", "will make money
  live", "SOTA on all markets", "no risk"

FORBIDDEN before P3 PASS:
  "SOTA application complete"

══════════════════════════════════════════════════════════════════
DEFINITION OF DONE (THIS GOAL)
══════════════════════════════════════════════════════════════════

DONE = P3 terminal artifact exists with either PASS or FAIL status
       AND BUILD_TODO phases P0–P3 checkboxes closed or explicitly
       blocked with human-visible reason
       AND pytest green
       AND PROGRESS.md summarizes final metrics and claim status
       AND no live trading was enabled

DONE does NOT require P4/P5.

══════════════════════════════════════════════════════════════════
SUGGESTED AGENT COMMANDS (IMPLEMENT WHEN CODE EXISTS)
══════════════════════════════════════════════════════════════════

python -m dollarpath.cli fetch --universe demo --start 2015-01-01 --end 2024-12-31
python -m dollarpath.cli run-baselines --universe demo --seed 42
python -m dollarpath.cli train --prereg prereg/PREREG_P2_DEV.md
python -m dollarpath.cli eval --policy learned --prereg prereg/PREREG_P3_HELDOUT.md
python -m dollarpath.cli ablate --prereg prereg/PREREG_P3_HELDOUT.md
python -m dollarpath.cli summarize dollarpath/artifacts/<run_id>
pytest -q

══════════════════════════════════════════════════════════════════
SESSION HANDOFF TEMPLATE (WRITE TO PROGRESS.md)
══════════════════════════════════════════════════════════════════

## Session <date>
- Phase / section:
- Gates passed:
- Gates failed:
- Artifacts:
- Key metrics:
- Next action:
- Blockers:

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```

---

## Quick reference for humans

| Question | Answer |
|---|---|
| What are we building? | DollarPath — RL/policies for **more dollars over time** |
| What is SOTA here? | Preregistered **held-out historical** beat of baselines after costs + risk rule |
| Where is the design? | `docs/WHITEPAPER.md` |
| What do I implement next? | First open item in `BUILD_TODO.md` |
| Can agents trade live? | **No** under this GOAL |
| Can agents use mocks? | **No** for market/rewards without human OK |

---

## Document control

| Version | Note |
|---|---|
| 1.0 | Initial autonomous contract for DollarPath v1 (P0–P3) |
