# Next Steps — Fixed-Target Rebalancing (After GOAL_REBAL v2)

**Ground truth (sealed):** `rebal_v2_official_seed_42`  
- WEALTH_EDGE @ 2.5 bps: **FAIL** (R0 never slightly beats best dynamic)  
- COST_REGIME: **PASS** (R7b beats R0 at 0–1 bps)  
- TRACKING: rebalance helps; R2 calendar_63 strong near-wealth track pick  
- R7b much better than R7 (costs ~47 vs ~135)  
- Multi-year: dynamic beats R0 in **40%** of years only  

**Identity lock:** fixed \(w^\*\) only. No allocation menu. No options P&L as primary.

---

## 1. What we actually know now

| Claim | Status |
|---|---|
| Rebalancing is implementable under no-lookahead | Proven |
| Rebalancing reduces drift from \(w^\*\) | Proven |
| Rebalancing raises ending $ at ~2.5 bps on U5 equal-weight 2020–24 | **Falsified** |
| At near-zero fees, careful rebalance can edge never | Supported (thin edge) |
| “Smarter” rules always beat calendar | Not supported (R7 over-traded; R7b ≈ never on $) |
| One fee level tells the whole story | Falsified (grid matters) |

**Methodological implication:** Stop trying to “make rebalancing win on wealth” by silent retuning. Either (a) characterize the **wealth–tracking–cost frontier**, or (b) change the **economic setting** (taxes, cash flows, different assets) where rebalancing is *supposed* to matter more.

---

## 2. Principles for next work

1. **Fixed \(w^\*\) forever** in a prereg (or explicit multi-target table—not learned).  
2. **Dual (or triple) scoreboard always:** wealth, tracking, costs/turnover.  
3. **Fee is a first-class axis**, not a footnote.  
4. **Faux $ + real prices + E1/E2** remain mandatory.  
5. Prefer tests a skeptical quant would run after reading our FAIL.  
6. Do not re-open QQQ/allocation as “rebalancing.”

---

## 3. Real tests (still faux $) — ranked

### Tier A — Highest value (do next)

#### A1. Break-even fee curve (make COST_REGIME quantitative)

**Design:** Fine grid bps ∈ {0, 0.25, 0.5, 1, 1.5, 2, 2.5, 3, 5, …}.  
For each arm, plot ending_wealth(bps). Find **break-even bps\*** where best dynamic = R0.

**Why:** We only know “wins below ~1–2.5.” A break-even number is the product insight  
(“rebalance only if your all-in costs are under X bps”).

**Pass/report:** Publish bps\* for R2, R3, R7b; CI later optional.

#### A2. Cash-flow rebalancing (where theory says rebalance helps)

**Design:** Monthly **external cash addition** (e.g. +$500 faux) and/or quarterly withdrawal.  
Policies:  
- invest new cash to restore \(w^\*\) (contribution rebalance)  
- vs dump into one asset  
- vs full portfolio rebalance on calendar  

**Why:** Classic household/401(k) setting; pure price-drift rebalance is the *hardest* place to show wealth gains. Cash flows change the problem.

**Metric:** ending wealth + tracking after same contributions.

#### A3. Volatility / crisis path metrics (not just end wealth)

**Design:** Same policies; report:  
- max DD  
- time under water  
- wealth **at** 2020-03-23 and 2022-10 troughs  
- recovery time to prior peak  

**Why:** Investors rebalance for **risk control and discipline**, not only terminal wealth. Our FAIL on terminal $ may coexist with better path risk.

#### A4. No-trade band theory (optimal threshold scan)

**Design:** Threshold policies with band \(b \in \{0.01, 0.02, …, 0.20\}\) and optional partial α.  
Fixed cost 2.5 bps. Plot wealth vs band and tracking vs band.

**Why:** Literature: no-trade regions. We only tried 5% and 10%. Maybe optimal band is 15%+ (closer to never) or 3%.

#### A5. Longer history / more regimes

**Design:** Extend U5 (or subset with long history) back toward 2007–2010 if free data allows; same E1/E2.  
Or second universe: 3-asset SPY/TLT/GLD only.

**Why:** 2020–24 is one macro story (COVID, rates, tech). Rebalance value may flip in mean-reverting cross-section decades.

---

### Tier B — Methodology rigor

#### B1. Statistical significance of wealth gaps

Bootstrap block paths (e.g. 21-day blocks) for Δwealth = W_dynamic − W_R0 at 2.5 bps.  
Report 90% interval. If interval covers 0, “FAIL” is noisy tie—not a strong anti-rebalance law.

#### B2. Turnover-matched controls

Compare calendar_63 to “random rebalance with same turnover.”  
If calendar ≈ random, skill is just “trade less”; if calendar > random at same turnover, timing of rebalance matters.

#### B3. Execution realism

- Next-open vs next-close  
- Asymmetric buy/sell costs  
- Minimum trade size / lot effects (approx)  

#### B4. Tax-aware faux ledger (US-style)

Simple long-term vs short-term lot accounting on rebalance sells.  
**Hypothesis:** tax drag can dominate bps spreads—may strengthen “rebalance less.”

#### B5. Prereg multi-seed / multi-start

Shift T_start by months; require stable ranking of top-3 policies.

---

### Tier C — “Live-ish” faux continuous

#### C1. Paper rebalance clock

Frozen \(w^\*\), frozen policy set (R0, R2, R3, R7b). Each week: append decisions with as-of data only; no code changes for 90 days. Dashboard: wealth, tracking, turnover.

#### C2. Shadow accounts with real contribution schedule

User-defined monthly deposit; compare contribution-rebalance vs never.

---

## 4. Methodology enhancements

### M1. Explicit multi-objective / Pareto front (highest leverage)

Stop single “winner.” Every result card plots:

- x = mean tracking L1 (or max drift)  
- y = ending wealth  
- size = total costs  

Arms are points; R0 is anchor. **Product claim:** “pick your point on the frontier,” not “we print free alpha.”

### M2. No-trade-band + partial α as the core policy class

Replace ad-hoc R7 magic with a **two-parameter family**:

\[
\text{if } \|w - w^\*\|_\infty > b: \quad w \leftarrow w + \alpha (w^\* - w)
\]

Grid \((b,\alpha)\). This is standard, interpretable, tunable, research-comparable.

### M3. Cost model as calibrated input

Map “2.5 bps one-way” to retail ETF round-trip estimates; optional spread that rises with turnover. Document assumption file `COST_ASSUMPTIONS.md`.

### M4. Utility beyond terminal wealth

Primary utilities to support (prereg one):

| Utility | Why |
|---|---|
| Mean log growth | Path-sensitive |
| Wealth − λ × tracking | Explicit tradeoff |
| Max DD constraint | Risk budgets |
| Calmar | Growth per pain |

### M5. Learn **only** \((b,\alpha)\) or check frequency on train years

Unlike allocation learning, parameters stay inside **rebalance class** with fixed \(w^\*\).  
Train 2018–2019 / 2018–2021, test 2022–2024 under E1/E2.  
If learned (b,α) beats frozen grid winner OOS → real methodology upgrade; if not, stick to simple calendar_63.

### M6. Contribution / withdrawal as first-class environment

Env extension: `cash_flow_t` exogenous. Rebalance policies must specify how flows are allocated. This is where “rebalancing” becomes household-real.

### M7. Do **not** (yet)

| Idea | Why wait |
|---|---|
| Options truth engine | Different object; separate GOAL |
| Allocation selector revival | Already FAIL under caps |
| Online RL over weights freely | Collapses to allocation |
| Claiming “rebalancing is useless” | Only true for terminal $ @ 2.5 bps on this sample |

---

## 5. Recommended sequence

```text
Wave 1 — Characterize (no new claim inflation)
  A1 break-even fee curve
  A4 threshold/α grid (no-trade family)
  M1 Pareto plot in result_card
  B1 bootstrap Δwealth at 2.5 bps (tie vs real loss?)

Wave 2 — Change the economic setting
  A2 cash-flow rebalancing
  A3 crisis path metrics
  M6 env cash flows

Wave 3 — Careful learning inside rebalance class
  M5 learn (b,α) with prereg train/test
  Only if Wave 1–2 show structure worth fitting

Wave 4 — Continuous faux
  C1 paper clock 90d
```

---

## 6. Probability-tinted priorities (subjective)

| Next package | P(useful sealed result)* | Notes |
|---|---:|---|
| Break-even fee + Pareto (A1+M1) | **80%** | Low risk, high clarity |
| Threshold/α grid (A4+M2) | **75%** | Core methodology |
| Bootstrap gap (B1) | **70%** | May reframe FAIL as “tie” |
| Cash-flow env (A2+M6) | **65%** | More “real life,” more eng |
| Crisis path metrics (A3) | **70%** | Cheap if paths stored |
| Learn (b,α) OOS (M5) | **45%** | Easy to overfit |
| Tax ledger (B4) | **50%** | Assumptions heavy |
| Options detour | n/a | Wrong goal object |

\*Useful = clear prereg result that changes decisions or beliefs, PASS or FAIL.

---

## 7. Single best next move

**Ship Wave 1 as GOAL_REBAL_V3 (characterize):**

> For fixed equal-weight U5, map the **fee break-even** and the **(band, α) Pareto frontier** of wealth vs tracking under E1/E2. Report bootstrap CI on W_R7b − W_R0 at 2.5 bps. No new “we beat the market” language.

That makes the methodology **real** without denying the wealth FAIL—and turns the fee finding into something operators can use.

---

## 8. One-sentence north star (revised)

> **Rebalancing is a cost-controlled controller that trades tracking error against fees; measure the frontier, don’t pretend terminal wealth always improves.**
