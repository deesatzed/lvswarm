# Next Steps, Real Faux-Dollar Tests, and Methodology Enhancements

**Context:** DollarPath v1 achieved `SCOPED_HISTORICAL_SOTA_PASS` (train 2018–2022 → held-out 2023–2024; offline template selection → QQQ 100%).  
**Purpose:** Separate **what is actually proven** from **what would make the methodology serious**, still using **faux dollars** and local/real historical data (no live capital required).

---

## 1. Hard truth about the current win

### What we proved (real, but narrow)

| Proven | Detail |
|---|---|
| Pipeline works | Data → env → costs → metrics → prereg → held-out gate |
| A **learned selector** beat three baselines on one held-out window | Offline max ending-wealth over a **finite template set** |
| Walk-forward plumbing exists | 9 windows, no train/test date leakage by construction |
| Unit tests | Env math, governor, offline selection on formula paths |

### What we did **not** prove

| Not proven | Why it matters |
|---|---|
| **True RL** that improves while acting | Online UCB **lost** to hold (F001/F002); winner is offline argmax, not adaptive control |
| Robustness across regimes | Held-out 2023–24 is a strong equity bull for QQQ; selection may not generalize to 2008/2022-style pain |
| Skill vs lucky template | One name (QQQ) in a growth-friendly OOS window is a classic concentration “win” |
| Cost realism | 2.5 bps one-way is gentle; no market impact, no tax, no borrow, no overnight gap model stress |
| Prediction/governor add value | P1 ablations: defensive pred **hurt** dollars; governor barely moved results |
| Statistical significance | One prereg window, one seed, no multiple-testing correction, short track record |
| Production readiness | Explicit non-goal; still true |

**Bottom line:** v1 is a **valid historical policy-selection instrument** with a scoped win. It is **not** yet a durable “grows dollars under uncertainty” learning system. Next work should **try to falsify** the QQQ-style win, not celebrate it.

---

## 2. Principles for the next phase

1. **Faux dollars only** until a separate human-gated live goal exists.  
2. **Every enhancement must move ending wealth, risk, or reliability of the claim** — not architecture aesthetics.  
3. **Real market history** (cached yfinance/FRED); no mock prices as evidence.  
4. **Prereg before hard tests**; failures go to `FAILURE_LEDGER.md`.  
5. Prefer tests that would make a skeptical quant say “ok, that’s interesting.”

---

## 3. Real tests (faux $) — ranked by diagnostic power

### Tier A — Must-run (kill or strengthen the claim)

#### A1. Multi-window held-out battery (not one OOS period)

**Design:** For each end year \(Y \in \{2020,2021,2022,2023,2024\}\):

- Train: start → \(Y-1\)-12-31  
- Test: \(Y\)-01-01 → \(Y\)-12-31 (or next 12–24 months)  
- Same templates, costs, baselines  

**Pass signal (methodology health, not marketing):**  
Learned beats best baseline on **ending wealth** in ≥ K of N windows **and** mean log-wealth edge > 0.  
**Fail signal:** Only wins in QQQ bull years.

**Faux $:** $100k each window; report distribution of outcomes.

#### A2. Concentration-constrained template set

**Design:** Rerun A1 / P3 with hard constraints in the template library:

- `max_weight ≤ 0.40` (or 0.25)  
- minimum # of names ≥ 3  
- optional sector/asset-class diversity (e.g. force ≥1 of {TLT, GLD} sleeve options only as templates, not unconstrained 100% QQQ)

**Question:** Does “learning” still beat hold **without** single-name lottery tickets?

If **no**, the v1 win was mostly **template class freedom**, not a smart dynamic policy.

#### A3. Cost stress surface

**Design:** Sweep one-way bps ∈ {0, 2.5, 5, 10, 25, 50}.  
Plot ending wealth / turnover for learned vs hold.

**Question:** Does edge survive realistic friction? High turnover methods die first; QQQ-hold-like should be stable.

#### A4. Crisis-first evaluation (selection before pain)

Already partially in `stress.json` — **formalize as a gate:**

| Episode | Train cutoff | Eval window |
|---|---|---|
| COVID crash | ≤ 2020-02-01 | 2020-02-15 → 2020-04-15 |
| 2022 bear | ≤ 2021-12-31 | 2022 calendar year |
| Rate shock (if data) | pre-2022 hike | 2022 H1 |

**Metrics:** ending wealth **and** max DD vs hold and vs 60/40.  
**Success:** not “make money in crash,” but **lose less / recover better** without look-ahead.

#### A5. Walk-forward compound path (primary metric candidate)

Today walk-forward is “supporting.” Elevate it:

- Compound window returns into one faux equity curve  
- Compare to hold run on the same calendar  
- Report: compounded wealth, worst window, % windows beat hold  

This is closer to “money over time under re-learning” than one frozen OOS.

---

### Tier B — Scientific / statistical rigor (still faux $)

#### B1. Bootstrap / block-bootstrap of daily returns

Resample held-out path in blocks (e.g. 21-day) under the **fixed** deployed weights; get CI on ending wealth difference vs hold.  
Does not create new alpha; tests **path luck** for a fixed policy.

#### B2. Deflated / multiple-testing awareness

You search many templates + windows. Report:

- Number of templates tried  
- Number of windows / configs  
- Simple Bonferroni-style caution or deflated Sharpe-style note (Harvey–Liu / Bailey–López de Prado spirit)

Even if not formal paper-grade, **state the search multiplicity** on every result card.

#### B3. Longer history if available

Extend fetch to 2007+ (or max free history) for SPY/QQQ/TLT/GLD; drop assets that lack history.  
Re-run A1 on a cycle that includes GFC if data allows.

#### B4. Execution model variants

- Next-open vs next-close  
- Conservative: always pay worse side of a wider spread when turnover high  
- Optional: delay rebalance 1 day after signal  

If ranking of policies flips, document sensitivity.

#### B5. Baseline expansion (fairer scoreboard)

Add:

- 60/40 SPY/TLT  
- Risk parity (simple inverse-vol weights)  
- Momentum (12–1) equal-weight top-2  
- Buy-and-hold **QQQ** (critical: if learned is “pick QQQ,” this baseline must exist)

**If learned ≈ buy-and-hold QQQ, the algorithm’s value is “selected QQQ from a menu,” not continuous skill.** That is still useful automation — but claim language must say so.

---

### Tier C — Live-loop faux dollars (continuous paper)

#### C1. Paper clock / as-of ledger

Daily (or weekly) job:

1. Fetch latest bars (real)  
2. Update train window (expanding or rolling)  
3. Re-select template (or update bandit)  
4. Log proposed weights + faux mark-to-market  
5. Hash-chained `decisions.jsonl` (clawswarmed style)

No real orders. After 90–180 days, compare cumulative faux $ to hold.

**This is the most “real” test without capital** — non-stationary, messy, psychological.

#### C2. Shadow competition of methods

Run in parallel faux accounts:

| Account | Method |
|---|---|
| A | Hold equal |
| B | Offline template (v1) |
| C | Constrained templates (A2) |
| D | Contextual online bandit (improved) |
| E | Prediction-gated exposure |

Same capital, same costs, same calendar. Winner by dollars + DD.

---

## 4. Methodology enhancements (ideas ranked)

### M1. Constrained policy class (highest priority)

**Problem:** Unconstrained argmax over templates discovers “be QQQ.”  
**Enhancement:** Optimize only inside a **risk budget**:

\[
\max_{\pi \in \Pi_{\text{safe}}} \text{ending wealth (train)}
\quad
\Pi_{\text{safe}} = \{ w : w_i \le c,\ \sum w = e,\ H(w) \ge h \}
\]

Then learning is forced to find **diversified** dollar improvement.  
If nothing beats hold inside \(\Pi_{\text{safe}}\), **report that honestly** — better than fake SOTA.

### M2. True online learning that can beat hold

**Problem:** UCB exploration burns dollars (F001).  
**Enhancements:**

| Idea | Mechanism |
|---|---|
| **Burn-in then exploit** | Pure explore N steps or ε→0 schedule |
| **Hold as default action** | Only deviate when posterior P(better) > threshold |
| **Relative reward** | \(r = \Delta\log W_{\pi} - \Delta\log W_{\text{hold}}\) so learning targets **excess** dollars |
| **Conservative bandits / risk-aware UCB** | Penalize variance / CVaR of segment rewards |
| **Frozen retrain cadence** | Retrain weekly offline; act greedy between retrains (hybrid of v1 + adaptivity) |

**Test:** Online method must beat hold **and** beat frozen offline selection on walk-forward compound wealth — or lose cleanly.

### M3. Prediction as state, not as a defensive religion

P1 showed naive “de-risk when volatile” **destroyed** dollars in 2018–24.  
Better uses of prediction:

| Use | Reward link |
|---|---|
| **When to rebalance** (skip if forecast noise high) | Cut costs / thrash |
| **Confidence-weighted blend** toward hold | Autobalance toward safety without binary panic |
| **Regime-conditional template libraries** | Different \(\Pi\) per regime, selected offline per regime |
| **Distributional forecasts** (from naked_straddle_sim spirit) | Size exposure by estimated tail, not AR1 alone |

**Gate:** Ablation must show **higher after-cost wealth or better Calmar** vs same policy without prediction.

### M4. Expert governor as measured insurance

Turn Layer-5-style rules into **priced insurance**:

- Run with governor ON vs OFF on identical paths  
- Report: dollars saved in stress windows minus dollars lost in bulls (**net insurance premium**)

Keep rules that have positive net premium; delete the rest.

### M5. Autobalance = turnover-aware control (not just speed knob)

Cast rebalancing as:

\[
w_{t+1} = w_t + \alpha_t (w^\* - w_t),\quad \alpha_t = f(\text{edge estimate},\ \text{cost},\ \text{vol})
\]

Learn or schedule \(\alpha_t\) to maximize after-cost wealth (classic no-trade-band / Rebalancing premium literature).

**Test:** vs always \(\alpha=1\) and vs calendar.

### M6. Multi-objective / utility that matches “worth over time”

Primary metric ending wealth favors lottery tickets. Alternatives (report **all**):

| Utility | Effect |
|---|---|
| Mean log-wealth (Kelly-ish) | Penalizes blow-up paths |
| CVaR-constrained wealth | Hard left-tail control |
| Calmar / MAR | Growth per unit pain |
| Ulcer index / time-under-water | Path quality |

**Enhancement:** Select template by **train Calmar** or **train mean log growth**, not raw ending wealth — then re-run P3-style held-out.

### M7. Population / LV ecology (P5, only after M1–M2)

Treat templates or strategies as species; influence \(N_i\) updates from dollar rewards with competitive terms so **no monoculture** (anti-QQQ-forever).  

**Only valuable if** multi-strategy compound wealth > best single template on walk-forward **with** diversification constraints.

### M8. Options / mispricing (P4, later)

Naked_straddle_sim’s dual distribution stack is a **state provider** for sizing equity/vol sleeves — not a jump to live options.  
Faux $ first: use IV/regime features to choose among **equity templates** only.

---

## 5. Recommended sequence (practical)

```text
Wave 1 — Falsify / bound the v1 win (faux $, local)
  1. Add buy-and-hold QQQ baseline
  2. A2 constrained templates + re-run held-out + multi-year battery (A1)
  3. A3 cost sweep
  4. Elevate walk-forward compound (A5) as co-primary report

Wave 2 — Make learning real
  5. M6 select by log-wealth / Calmar on train
  6. M2 hybrid: offline retrain weekly + greedy act; relative reward
  7. M3 prediction only if ablation wins dollars or Calmar

Wave 3 — Continuous faux reality
  8. C1 paper clock + C2 multi-account shadow
  9. M4 governor insurance accounting

Wave 4 — Research extensions (optional)
  10. M7 LV population under constraints
  11. M8 options features for sizing (still faux equity book)
```

**Do not** raise claim language until Wave 1 passes without unconstrained 100% single-name templates — or explicitly claim “menu selector that may concentrate.”

---

## 6. Concrete new prereg sketches (ready to implement later)

### PREREG_P3B_MULTIYEAR.md (sketch)

- Windows: annual OOS 2020…2024  
- Method: offline template selection  
- Variants: unconstrained vs max_weight 0.4  
- Primary: mean excess log-wealth vs hold; secondary: % windows beat hold  
- PASS: mean excess > 0 and ≥ 3/5 windows beat hold under **constrained** variant  

### PREREG_P2B_ONLINE.md (sketch)

- Method: weekly offline retrain + greedy; relative reward to hold  
- Eval: walk-forward compound 2018–2024  
- PASS: compound wealth > hold and > frozen single train/test split selector  

### PREREG_PAPER_90D.md (sketch)

- Start date T0; 90 calendar days  
- Daily update faux ledger  
- Compare accounts A/B/C  
- No PASS claim until day 90; only dashboard  

---

## 7. Implementation checklist candidates (for BUILD_TODO append)

- [ ] Baseline: `HoldQQQPolicy` / per-asset buy-and-hold  
- [ ] `cli multi-heldout --years 2020-2024`  
- [ ] Template factory: `max_weight`, `min_names`  
- [ ] Cost sweep CLI + JSON surface  
- [ ] Train objective switch: `ending_wealth | calmar | mean_log_growth`  
- [ ] Walk-forward compound equity writer  
- [ ] Paper ledger command + daily cron-friendly entrypoint  
- [ ] Result cards always list **template count** and **search multiplicity**  
- [ ] Unit tests: constrained templates never violate max_weight; multi-heldout no leakage  

---

## 8. What “enhanced methodology” should mean in one sentence

> **Search only over risk-admissible policies, score them by after-cost multi-window faux dollars (and path risk), adapt without free exploration burn, and never claim skill that is indistinguishable from “picked the asset that won the bull.”**

---

## 9. Decision prompts for the human

1. **Is concentration allowed in the product claim?**  
   - Yes → keep v1, add QQQ hold baseline and multiplicity notes.  
   - No → Wave 1 constrained templates is mandatory before any new “SOTA” language.

2. **Is the goal better automation (selector) or true adaptive RL?**  
   - Selector → deepen offline + multi-year + paper clock.  
   - Adaptive RL → prioritize M2 relative-reward hybrid.

3. **Primary utility?** Ending wealth vs log-growth vs Calmar — pick one for the next prereg.

---

*Document status: planning only — not an executed build phase.*
