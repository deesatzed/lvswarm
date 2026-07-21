# PREREG_PROSPECTIVE_V1 — Leakage-Resistant Prospective Experiment

**Status:** LOCKED_BY_GOAL_NEXT (auto) at 2026-07-20 — official run `prospective_official_seed_42_2020-01-02_2024-12-31`  
**Codename:** DollarPath Prospective Ledger (DPL-1)  
**Capital:** Faux USD only (default $100,000 per arm)  
**Purpose:** Evaluate allocation methods going **forward in calendar time** so “lookahead / leakage” is not a credible criticism.

---

## 0. One-sentence protocol

> **Freeze the code and rules first; then only make decisions using data whose timestamps are ≤ decision time; score wealth only on returns that occur strictly after those decisions.**

---

## 1. What “prospective” means here

| Mode | Definition | Leakage risk if sloppy |
|---|---|---|
| **A. Frozen-method forward test** | Method (code + hyperparams + template class) locked at `T_lock`. From `T_start ≥ T_lock`, walk **forward only** through history (or live calendar), re-fitting **only on past data**. | Medium if retrain uses future bars |
| **B. Live paper clock** | Same as A, but wall-clock time is real “now”; data pulled as-of today | Low if as-of joins enforced |
| **C. Nested walk-forward (retrospective but clean)** | Simulate A on past years with hard embargo | Low if implemented correctly; critics may still say “researcher degrees of freedom” unless prereg locked |

**DPL-1 primary track = Mode A on historical tape after lock** (reproducible, free)  
**DPL-1 secondary track = Mode B** (optional continuous paper after Mode A code is frozen)

Mode C is a **supporting battery** (multi-year), also preregistered below, never mixed into the same claim as “live prospective” without labeling.

---

## 2. Leakage threat model (what we explicitly block)

| Attack / mistake | Block |
|---|---|
| Using close of day *t* to trade at *t* | **Decision at t uses bars with `date ≤ t−1` only** (or decision at close *t* applies from **next open/close** — pick one and freeze) |
| Train window includes test days | `train_end < decision_time` and `train_end + embargo < first_eval_bar` |
| Optimizing templates on full sample then “testing” | Template **library** frozen at lock; **selection** only on data ≤ train_end |
| Snooping costs / universe after seeing OOS | Universe, costs, baselines frozen in this file |
| Multiple silent retries until PASS | One official run id per lock; extra runs labeled `exploratory` |
| Survivorship / revised history | Document data vendor; cache snapshot **at first fetch** with `retrieved_at`; never silently replace cache for official run without new run_id |
| Label leakage (regime using future vol) | Regime/features computed on `prices.loc[:asof]` only; unit test forbids full-series stats |
| Embargo zero with overlapping features | Default **embargo_bars ≥ 1** trading day between last train bar and first return credited to a decision |

---

## 3. Frozen configuration (lock these before any official run)

### 3.1 Calendar

| Parameter | Value |
|---|---|
| `T_lock` | *(set when human sets Status=LOCKED — ISO datetime UTC)* |
| `T_start` | First decision date ≥ max(T_lock calendar date, 2018-01-01) for historical replay; for live paper = next session after lock |
| `T_end` | Historical replay end (e.g. 2024-12-31) **or** “open-ended” for live paper |
| Bar frequency | Daily |
| Timezone | America/New_York session dates as provided by vendor index |

### 3.2 Execution & information set (anti-leakage core)

**LOCKED RULE E1 — Information set**

At decision index `t` (integer bar index):

```text
asof_bar = t - 1                    # last fully observed bar
info_t   = all prices with index ≤ asof_bar
train_window = prices[asof_bar - L + 1 : asof_bar]   # length L
```

**LOCKED RULE E2 — Action effective time**

```text
action chosen using info_t
fills / weight change effective at bar t   # next bar after asof (next_close semantics)
reward credited from return of bar t only after action applied
```

Equivalent statement for humans:

> We never use today’s close to choose today’s close trade. We use **yesterday’s** history to set weights that earn **today’s** return.

**LOCKED RULE E3 — Embargo for retrain batches**

When doing offline selection on a train slice ending at `train_end`:

```text
first_eval_bar_date > train_end_date + embargo_bars
embargo_bars = 5   # trading days
```

### 3.3 Universe, capital, costs

| Parameter | Value |
|---|---|
| Universe | SPY, QQQ, IWM, TLT, GLD |
| Start capital per arm | 100_000 faux USD |
| Cost | 2.5 bps one-way (same CostModel as v1) |
| Rebalance decision every | 5 trading days (on decision grid) |
| Data source | yfinance auto_adjust close; cache with retrieved_at |

### 3.4 Method arms (parallel faux accounts)

All arms share E1–E3, universe, costs.

| Arm ID | Name | Description |
|---|---|---|
| **A0** | hold_equal | Buy equal weight once; hold |
| **A1** | hold_qqq | Buy QQQ 100%; hold *(critical honesty baseline)* |
| **A2** | calendar_equal | Rebalance equal every 21 days |
| **A3** | vol_target | Existing vol target policy |
| **B1** | select_unconstrained | Offline template selection on rolling/expanding train; full template set including 100% single names |
| **B2** | select_constrained | Same algorithm; **max_weight ≤ 0.40**, templates with fewer than 3 positive names removed |
| **B3** | select_calmar | Like B2 but train score = Calmar (or mean log growth — freeze one: **mean_log_growth**) |
| **C1** | hybrid_weekly | Once per 5 decision days: re-run B2 selection on train ending asof; act greedy until next retrain |

*(Implement B3/C1 in code before lock if included; otherwise drop from locked arm list.)*

**Minimum lock set if engineering time is tight:** A0, A1, A2, A3, B1, B2.

### 3.5 Template libraries (frozen)

**Unconstrained library:** current `default_templates` (may include 100% single asset).

**Constrained library:**

```text
max_weight = 0.40
min_positive_names = 3
sum(weights) ≤ 1.0
weights ≥ 0
```

Generate once in code; hash the list of weight vectors into `templates_sha256` at lock.

### 3.6 Train window mode (frozen)

| Parameter | Value |
|---|---|
| Mode | **Expanding** from `history_start` to `asof_bar` |
| `history_start` | 2018-01-01 (or first available) |
| Min train bars before first selection | 504 (~2 years) |
| Before min train | Hold equal (A0 behavior) for B-arms |

### 3.7 Primary / secondary metrics (frozen)

| Role | Metric |
|---|---|
| **Primary** | Ending faux wealth at `T_end` |
| **Co-primary (path)** | Max drawdown |
| **Secondary** | CAGR, Calmar, total costs, mean turnover |
| **Honesty** | Excess wealth vs A1 (hold_qqq): `W_arm - W_A1` |

### 3.8 Official PASS rules (prospective historical replay)

Run once after lock on `[T_start, T_end]` with sealed code.

**PASS-B2 (main scientific claim we want):**

```text
W(B2) > W(A0) and W(B2) > W(A2) and W(B2) > W(A3)
AND maxDD(B2) ≤ 1.20 * max( maxDD(A0), maxDD(A2), maxDD(A3) )
   OR Calmar(B2) > max(Calmar(A0), Calmar(A2), Calmar(A3))
```

**REPORT-ONLY (not PASS):** B1 vs A1 — if B1 ≈ A1, document “selector found QQQ.”

**FAIL** is a valid outcome.

### 3.9 Multi-year nested battery (Mode C — supporting)

Also frozen, run after same code lock:

For each year Y in {2020,2021,2022,2023,2024}:

```text
train: history_start → (Y-1)-12-31
embargo: 5 trading days into Y
test: first bar after embargo → Y-12-31
selection: offline on train only (B1 and B2)
evaluate: deploy fixed selected weights on test (or re-select only inside test with E1 expanding — pick FIXED deploy for simplicity)
```

**LOCKED for supporting battery:** **fixed deploy** of train-selected template through test year (no mid-year reselect) — simplest leakage story.

Supporting summary stats (not override of §3.8 unless human amends):

- Mean excess log-wealth vs A0 across years  
- Fraction of years B2 beats A0  

---

## 4. Artifact contract (every official run)

```text
dollarpath/artifacts/prospective_<run_id>/
  LOCK.json                 # copy of frozen params + git commit + templates_sha256
  prereg_hash.txt           # sha256 of this prereg file at lock
  arm_<id>/
    metrics.json
    equity_curve.csv
    decisions.jsonl         # each line: decision_time, asof_bar, train_end, action, rules
  comparison.json
  leakage_audit.json        # automated checks (below)
  result_card.md
```

### 4.1 Automated leakage audit (must all be true)

| Check ID | Assertion |
|---|---|
| L1 | For every decision row: `asof_bar < effective_bar` |
| L2 | For every decision: `max(train dates) ≤ asof_bar` |
| L3 | No price from `date > asof_bar` appears in feature/regime inputs (code path test) |
| L4 | Official run git commit == LOCK.json commit |
| L5 | templates_sha256 matches locked library |
| L6 | For nested yearly tests: `train_end < test_start` and embargo gap ≥ 5 sessions |
| L7 | Cache meta `retrieved_at` recorded; official run uses that snapshot only |

Any false → run void for claims.

---

## 5. How this answers “leakage” criticism

| Critic says | Response |
|---|---|
| “You fit on the whole sample” | Selection uses only `≤ asof`; audit L2 |
| “You traded on the same close you measured” | E1/E2: info lag one bar; audit L1 |
| “You tried many specs until it worked” | Single locked prereg; exploratory runs separate namespace |
| “QQQ was obvious in hindsight” | Arm A1 is the QQQ hold baseline; B2 is constrained |
| “Walk-forward still peeked at design” | Design locked before official run; supporting multi-year uses fixed deploy |
| “Vendor revised history” | Cached snapshot + retrieved_at; re-fetch = new run_id |

---

## 6. Implementation map (what to build)

| Module | Responsibility |
|---|---|
| `dollarpath/prospective/protocol.py` | E1–E3 helpers: `info_slice`, `decision_grid`, embargo |
| `dollarpath/prospective/templates.py` | unconstrained vs constrained libraries + hash |
| `dollarpath/prospective/arms.py` | A0–A3, B1–B2 runners under protocol |
| `dollarpath/prospective/audit.py` | L1–L7 checks → leakage_audit.json |
| `dollarpath/cli.py` | `prospective-run`, `prospective-audit`, `multi-year-battery` |
| `tests/test_leakage_protocol.py` | Synthetic prices with planted future spike: policy must not capture spike if only future-visible |

### 6.1 Canonical planted-leakage unit test

```text
Prices flat, then huge jump on day T*.
Policy that peeks at T* close to set weights for T* return would capture jump.
Protocol-correct policy using asof=T*-1 must NOT earn the jump on the decision that only sees T*-1.
Assert wealth path difference.
```

---

## 7. Execution steps (human + agent)

### Phase 0 — Lock

1. Human reviews this prereg; sets **Status = LOCKED**, fills `T_lock`, `T_start`, `T_end`, final arm list.  
2. `git commit` of code + prereg; record commit SHA in LOCK.json.  
3. Compute `templates_sha256`, `prereg_hash`.  
4. **No further hyperparameter changes** for official run.

### Phase 1 — Implement protocol + arms + audit + tests

5. Implement §6; `pytest` green including planted leakage test.  
6. Dry-run on short window labeled `exploratory_dry_run` (not claimable).

### Phase 2 — Official historical prospective replay

7. `prospective-run --official` from T_start→T_end.  
8. Auto-audit must pass.  
9. Write result_card: PASS-B2 / FAIL / incomplete.  
10. Run multi-year battery; attach as appendix (report-only unless prereg amended).

### Phase 3 — Optional live paper (Mode B)

11. Same LOCK.json; each session day append decisions with wall-clock timestamp.  
12. No code change without new prereg version (DPL-2).

---

## 8. Relationship to prior P3 PASS

| Item | Status under DPL-1 |
|---|---|
| P3 QQQ unconstrained held-out | **Historical scoped claim only**; not re-used as prospective PASS |
| DPL-1 B1 | May rediscover QQQ; honesty via A1 |
| DPL-1 B2 | Intended main prospective claim (diversified selector) |

Do **not** market “SOTA” on DPL-1 until §3.8 PASS-B2 under sealed lock.

---

## 9. Lock checklist (sign-off)

- [ ] Status set to LOCKED  
- [ ] T_lock / T_start / T_end filled  
- [ ] Arm list frozen  
- [ ] B3/C1 included or struck  
- [ ] Train score for B2 = ending_wealth (default) or mean_log_growth (if B3 merged)  
- [ ] git commit SHA recorded  
- [ ] templates_sha256 recorded  
- [ ] Human approval: no live capital  

**Lock signature (human):** _________________ **Date:** ________  

---

## 10. Claim language templates

**If PASS-B2:**

> After preregistered lock at T_lock, under one-bar information lag and 5-day retrain embargo, constrained offline template selection (max weight 40%, ≥3 names) achieved higher after-cost faux ending wealth than equal hold, calendar equal, and vol-target from T_start to T_end on universe U with cost C. Leakage audit L1–L7 passed. Not live trading.

**If B1 ≈ A1:**

> Unconstrained selection matched buy-and-hold QQQ within X%; method behaved as a single-name menu selector on this path.

**If FAIL:**

> SCOPED_PROSPECTIVE_FAIL — constrained selector did not beat baselines under sealed protocol (valid scientific outcome).
