# DollarPath — Build To-Do List

**Companion docs:** `docs/WHITEPAPER.md`, `GOAL.md`  
**Rules:**  
- No time estimates.  
- No mocks for market data, fills, or rewards without explicit human approval.  
- Each step has a **Validation gate**. Do not proceed if the gate fails.  
- Prefer local resources; cloud/API only with hard budget and ledger.  
- Any change to success criteria requires human approval and GOAL.md update.

---

## Legend

| Mark | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done + gate passed |
| `[!]` | Blocked (record reason in FAILURE_LEDGER.md) |

---

## Phase P0 — Foundations (measure dollars for any policy)

### P0.1 Project skeleton

- [x] Create package `dollarpath/` with modules: `data`, `env`, `state`, `policies`, `prediction`, `governor`, `train`, `eval`, `cli`
- [x] Add `pyproject.toml` or `requirements.txt` (numpy, pandas, yfinance, scipy, pytest)
- [x] Add `.gitignore` (`.env`, `venv`, `__pycache__`, `dollarpath/artifacts/**` bulk, caches)
- [x] Add `FAILURE_LEDGER.md` and `PROGRESS.md` at repo root
- [x] Copy or submodule-safe import path notes for reusing `ace_core` from `naked_straddle_sim` (document path; do not break that repo)

**Validation:** `python -c "import dollarpath"` works from project root; `pytest` collects zero or placeholder tests without error. **PASS 2026-07-20**

---

### P0.2 Real data plane + disk cache

- [x] Implement `dollarpath/data/price_feed.py` — fetch OHLCV via yfinance for a ticker list + date range
- [x] Implement `dollarpath/data/cache.py` — SQLite or parquet cache of **real** responses with TTL/metadata (source, retrieved_at)
- [x] Implement `dollarpath/data/validate.py` — reject empty, non-monotonic dates, absurd prices
- [x] CLI: `python -m dollarpath.cli fetch --universe demo --start YYYY-MM-DD --end YYYY-MM-DD`
- [x] Tests with **real network** fetch for a short recent window OR offline test using previously cached real data committed as a small fixture of real history (label as real-cache, not mock)

**Validation:** Fetch SPY + at least 3 liquid ETFs/stocks; cache hit returns identical bars; validator catches corrupted series. **PASS 2026-07-20** (demo universe 5 assets, 1760 rows)

---

### P0.3 Portfolio environment (faux capital)

- [x] `PortfolioState`: cash, positions, weights, wealth, peak_wealth, drawdown
- [x] `CostModel`: spread bps + optional commission; document defaults in config
- [x] `PortfolioEnv.step(action)` → next state, reward, info (turnover, costs, trades)
- [x] Action schema v1: target weights (simplex) + optional gross exposure scale + no-op
- [x] Execution: **next-bar** open/close (declare in config); apply costs on weight changes
- [x] Ruin flag: wealth < configured floor

**Validation:** Unit tests: no-trade ⇒ zero costs; full rotate ⇒ positive costs; wealth equals mark-to-market identity within float tol. **PASS 2026-07-20**

---

### P0.4 Reward and metrics

- [x] Log-wealth reward \(r_t = \log W_{t+1} - \log W_t\)
- [x] Metrics: ending_wealth, total_return, CAGR, max_drawdown, Calmar, total_costs, turnover, exposure_mean
- [x] Writer: `artifacts/<run_id>/metrics.json`, `equity_curve.csv`, `config.json`, `result_card.md`

**Validation:** Synthetic price path (deterministic arithmetic series from **formula**, not fake market API) produces hand-computed wealth within tol; metrics match spreadsheet check. **PASS 2026-07-20**

---

### P0.5 Baseline policies

- [x] `HoldPolicy` — buy equal weight once, hold
- [x] `CalendarRebalancePolicy` — rebalance to targets every N days
- [x] `VolTargetPolicy` — scale exposure by inverse realized vol (simple)
- [x] Runner: walk price history, log equity for each baseline

**Validation:** On same universe/period/seed, three baselines write three artifact dirs; hold has lower turnover than calendar; all metrics.json present. **PASS 2026-07-20**

---

### P0.6 CLI + regression harness

- [x] `python -m dollarpath.cli run-baselines --universe demo --start ... --end ... --seed 42`
- [x] `python -m dollarpath.cli summarize artifacts/<run_id>`
- [x] Pytest covering env math + policy determinism under seed

**Gate P0 complete when:**

```text
[x] Baselines runnable end-to-end on real cached prices
[x] metrics.json + equity_curve for each baseline
[x] pytest green
[x] result_card states: "P0 complete — dollars measurable; no RL claim"
```

**P0 GATE: PASS 2026-07-20** — see `dollarpath/artifacts/phase_p0_gate/result_card.md`

---

## Phase P1 — State enrichment (prediction optional) + governor + autobalance

### P1.1 State builder

- [x] Features: returns windows, realized vol, drawdown, current weights, days since rebalance
- [x] Config flag: `use_prediction: true|false`

**Validation:** Feature matrix aligned as-of \(t\) (shift tests fail if lookahead introduced). **PASS**

---

### P1.2 Prediction adapter (optional)

- [x] Thin adapter wrapping regime detector pattern (port/import from ace_core)
- [x] Emit: regime label, rho, confidence, optional forecast moments
- [x] If ace_core import fails, prediction module disables cleanly with explicit metric `prediction_enabled=false`

**Validation:** With prediction on, state includes regime fields; offline test uses real price series through detector. **PASS** (local AR1)

---

### P1.3 Expert governor

- [x] Rules v1: max weight per asset, max turnover per step, cash floor, max drawdown brake (reduce exposure), optional “low confidence → size down”
- [x] API: `govern(proposed_action, state) -> (final_action, decision, rule_ids)`
- [x] Log every veto/size-down to ledger or decisions.jsonl

**Validation:** Unit tests force each rule; proposed 100% one name → sized or vetoed per config. **PASS**

---

### P1.4 Autobalance throttle

- [x] Parameter `rebalance_speed ∈ (0,1]`: fraction of weight gap closed per step
- [x] Metric: thrash_score (reversals within K days)

**Validation:** speed=1 matches full rebalance; speed=0.25 reduces turnover vs 1 on same targets. **PASS** (ablation matrix)

---

### P1.5 Fixed prediction-informed policy (no learning)

- [x] `PredRulePolicy`: e.g. reduce exposure in high-vol / transition regime; else calendar targets
- [x] Compare to baselines on same period

**Gate P1 complete when:**

```text
[x] Ablation matrix runnable: pred on/off, governor on/off, speed high/low
[x] No module claimed "helpful" without metrics comparison
[x] result_card: "P1 complete — modules measurable; no SOTA claim"
```

**P1 GATE: PASS 2026-07-20**

---

## Phase P2 — Learning on dollar reward (L1)

### P2.1 Action templates

- [x] Discrete action set (e.g. 8–32 templates): exposure levels × allocation modes (equal, momentum tilt, defensive)
- [x] Document mapping template_id → target weights

**Validation:** All templates produce valid simplex weights under governor. **PASS**

---

### P2.2 ACE / bandit learner

- [x] Port or reimplement StrategyMemory-style helpful/harmful **or** epsilon-greedy / UCB bandit on template_id
- [x] Reward = episode or rolling log-wealth increment (declare in prereg)
- [x] Persist learned scores to disk

**Validation:** On a constructed environment where one template is clearly best (deterministic price rule from formula), learner selects it with high frequency after enough steps. **PASS** (offline selection + UCB diagnostic)

---

### P2.3 Train + eval split (dev)

- [x] Dev period for learning; separate smoke eval period
- [x] `cli train` and `cli eval --policy learned`

**Validation:** Learned policy artifact loads; eval is deterministic given seed + frozen scores. **PASS** (`cli train`)

---

### P2.4 Beat baselines on dev (honest)

- [x] Prereg `prereg/PREREG_P2_DEV.md`: universe, costs, periods, metrics, seeds
- [x] Run baselines + learned; write comparison table
- [x] If learned loses: record in FAILURE_LEDGER, iterate **without** claiming win

**Gate P2 complete when:**

```text
[x] prereg exists and matches config hashes
[x] learned policy beats all P0 baselines on dev primary metric after costs
  OR documented failure with next hypothesis
[x] No held-out SOTA language yet
```

**P2 GATE: PASS 2026-07-20** — offline template selection (QQQ); see `phase_p2_gate/result_card.md`

---

## Phase P3 — Walk-forward, stress, held-out SOTA gate

### P3.1 Walk-forward engine

- [x] Rolling train → test windows
- [x] Purge/embargo gap between train and test (config days)
- [x] Aggregate metrics with per-window table

**Validation:** No test day appears in train features for same window (automated check). **PASS**

---

### P3.2 Stress segments

- [x] Configurable stress date ranges (include 2020-02–2020-04, 2022 bear, etc. as data allows)
- [x] Per-segment metrics in artifacts

**Validation:** Stress report generated even if policy loses (honest). **PASS** (`stress.json`)

---

### P3.3 Held-out evaluation

- [x] Prereg `prereg/PREREG_P3_HELDOUT.md` **before** final eval
- [x] Freeze code + config; run once (or fixed seed list)
- [x] Claim matrix: PASS / FAIL / INCOMPLETE per criterion in GOAL.md

**Gate P3 complete when:**

```text
[x] Held-out primary metric beats baselines after costs
[x] Drawdown / Calmar constraint satisfied per prereg
[x] Ablations recorded
[x] result_card may state scoped historical SOTA claim OR explicit FAIL
[x] audit-goal style summary written
```

**P3 GATE: SCOPED_HISTORICAL_SOTA_PASS 2026-07-20** — `dollarpath/artifacts/p3_heldout_seed_42/`

**This is the definition of “SOTA application” for DollarPath v1.**

---

## Phase P4 — Optional options-aware extension

*Do not start until P3 PASS or human override.*

- [ ] Options chain data path (real vendor/sandbox)
- [ ] State: IV, skew features
- [ ] Actions: optional limited option overlays **or** keep equity-only if no dollar lift
- [ ] Reuse naked_straddle governor ideas for event veto

**Gate P4:** Options-aware policy beats equity-only on held-out after costs, or rejected.

---

## Phase P5 — Multi-strategy population (LV-style)

*Do not start until P3 PASS.*

- [ ] Multiple strategy species; influence weights
- [ ] Update influences from dollar rewards (competitive / mutualistic)
- [ ] Compare to single best strategy

**Gate P5:** Population improves dollars or stability vs single best; else reject.

---

## Continuous obligations (every phase)

- [ ] Update `PROGRESS.md` after each gate
- [ ] Append failures to `FAILURE_LEDGER.md` with mitigation
- [ ] Keep tests green before next phase
- [ ] Never claim production-ready with open checklist items
- [ ] Live capital trading remains human-gated (not on this checklist as autonomous work)

---

## Demo universe (default)

```text
Name: demo
Assets: SPY, QQQ, IWM, TLT, GLD   # liquid, free history; adjust only via prereg
Start capital: 100_000 faux USD
Default costs: 5 bps round-trip equivalent (document)
```

Change only with prereg amendment.

---

## Human approval required

| Item | Why |
|---|---|
| Live trading / real money | Capital risk |
| Mocks of market outcomes | Validity |
| Raising OpenRouter / data spend caps | Budget |
| Changing primary metric or SOTA definition | Claim integrity |
| Skipping P3 for P4/P5 | Scope control |
