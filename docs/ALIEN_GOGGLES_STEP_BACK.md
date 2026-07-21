# Alien Goggles Step-Back — Finance Stack After DollarPath

**Date:** 2026-07-20  
**Mode:** Alien goggles + first/second principles + net-new tech scan + revised recommendations  
**Context:** User leans toward **B = options truth engine**, but wants a full step-back first.

---

## 0. Alien goggles activation (assumption purge)

Strip names we like (“DollarPath,” “SOTA,” “straddle,” “autobalance,” “RL,” “ACE”). Keep only what an outsider would keep after reading the evidence.

### What exists as physics of the problem

| Fact | Evidence |
|---|---|
| Capital changes when prices move and when you trade | Trivial; implemented in `dollarpath` env |
| Trading has friction | Cost model; cost surface widened selector losses |
| Using future information is cheating | Protocol E1–E2; audit passed |
| Markets price risk in options as well as stocks | Options IV → risk-neutral distributions (standard theory) |
| Fat tails and rare blows dominate short-premium economics | `naked_straddle_sim` STATISTICAL_RIGOR; literature |
| “Pick best past recipe” ≠ durable edge under risk caps | GOAL_NEXT **FAIL_B2** |
| “Pick best past recipe” can look great if 100% one winner allowed | v1 **PASS** with QQQ |
| Naive regime de-risk can destroy dollars | P1 ablation |
| Online explore-while-earn is expensive | UCB **lost** to hold |

### Assumptions to throw out (unless re-earned)

| Drop | Why |
|---|---|
| “We are building rebalancing” | Code/claims optimized allocation selection |
| “Learning ⇒ more money” | Constrained learning failed primary test |
| “AI factor graphs are truth” | Design already warns of hallucination |
| “Options = print premium” | Purpose was distribution skill, not tip-finding |
| “SOTA” without scope | Only scoped historical claims valid |
| “Expert rules always help” | Unmeasured opportunity cost |

### Alien re-description (no branding)

> There is a machine that, given a time series of prices, outputs portfolio weights and a ledger of fake wealth. Another design exists for a machine that, given prices and option quotes, outputs a full probability distribution and compares it to the market’s implied distribution, and may later choose option payoffs only when those disagree and risk rules allow. The first machine was built and stress-tested; under diversification it does not beat equal-weight holding. The second machine is largely specified, partially scaffolded elsewhere, and not yet forced through a falsifiable calibration exam.

---

## 1. First principles (base theories)

### 1.1 Information and forecasting

**FP1 — Predictive content is about distributions, not point tips.**  
A single “expected return” is almost useless under heavy tails. Calibration of quantiles / full CDFs is the right object.

**FP2 — The market is a competing forecaster.**  
In options, the risk-neutral distribution extracted from prices is a high-powered baseline. Beating *something weak* is not beating the market.

**FP3 — No free lunch without risk or cost.**  
Any method that raises expected wealth without extra risk or cost is either (a) rare genuine edge, (b) luck, or (c) leakage/mis-specification.

### 1.2 Portfolio theory

**FP4 — Allocation vs rebalancing are different operators.**  
- Allocation: choose target \(w^\*\).  
- Rebalancing: map drifted \(w_t\) toward \(w^\*\) under costs.  
Conflating them confuses claims.

**FP5 — Diversification is a constraint on admissible policies, not decoration.**  
Unconstrained max wealth search collapses to concentrated bets in many samples.

**FP6 — Friction turns dynamic strategies into cost centers.**  
Higher turnover must buy enough edge to pay the bid-ask.

### 1.3 Derivatives / pricing

**FP7 — Option prices encode a risk-neutral measure \(Q\), not the real-world measure \(P\).**  
Edge claims must specify: better \(P\), better risk premia harvest, better hedging, or better *execution*—not vague “model smarter.”

**FP8 — Breeden–Litzenberger / IV surface → density is classical.**  
Extracting market-implied PDFs is not net-new science; **how you build \(P\) and prove calibration** might be.

**FP9 — Short volatility has high hit rate, left-tail death.**  
Track-record length requirements explode (Bailey–López de Prado-style).

### 1.4 Learning / control

**FP10 — Exploration has an opportunity cost in dollars.**  
UCB-style explore-while-you-bleed is hostile to wealth objectives unless exploration is off-policy or synthetic.

**FP11 — Offline selection on a finite menu is combinatorial search, not deep RL.**  
Calling it “RL” without online improvement is branding drift.

**FP12 — Leakage is an information-set error, not a vibe.**  
One-bar lag + as-of features is the minimum credible protocol.

---

## 2. Second principles (derived practice)

These are not axioms; they follow from first principles + our evidence.

| ID | Second principle | Source |
|---|---|---|
| SP1 | **Separate scoreboard objects:** calibration of \(P\) vs wealth of a trading rule | Options architecture; DollarPath muddle |
| SP2 | **Prereg + audit before claim** | GOAL / GOAL_NEXT worked |
| SP3 | **Primary arm must match product ethics** (caps if “balanced,” concentration if “satellite beta”) | FAIL_B2 vs PASS QQQ |
| SP4 | **Prediction modules need ablation on the real objective** | P1 de-risk hurt $ |
| SP5 | **Phase-gate truth engine before payoff optimization** | naked_straddle Phase 1 design |
| SP6 | **Reuse DollarPath’s discipline (artifacts, faux capital, no mock fills) for options later** | Process learning |
| SP7 | **Do not expand to multi-agent/LV until a single objective is falsifiable and green** | Swarm predoc drift risk |
| SP8 | **Net-new is rare; composition + rigorous eval is the usual win** | MoE/portfolio analogies |

---

## 3. Methods inventory (what tools we actually have)

| Method | Maturity here | Natural objective |
|---|---|---|
| Historical price cache + portfolio env | **Shipped** | Wealth under weights |
| Offline template selection | **Shipped** | Pick \(w^\*\) from menu |
| Prospective protocol + audit | **Shipped** | No-lookahead claims |
| Calendar / threshold / partial rebalance | **Partial** (calendar yes; threshold/α weak) | Keep fixed \(w^\*\) |
| Simple AR1 regime | **Shipped (lite)** | State feature |
| ACE / ensemble (ace_core) | **External scaffold** | Adaptive forecast weights |
| AI factor graph + MC | **Designed, not validated** | Real-world \(P\) |
| Market-implied PDF from options | **Designed** | Baseline \(Q\)-density |
| Payoff optimizer + straddle book | **Designed** | Exploit \(P\) vs \(Q\) |
| Risk governor rules | **Designed / lite in DollarPath** | Ruin control |
| Online bandit / RL | **Tried, weak** | Adaptive policy |
| LV multi-agent ecology | **Idea only** | Population of strategies |

---

## 4. Net-new technology? (alien view)

### What is **not** net-new

- Equal-weight hold, calendar rebalance, vol target  
- Offline “pick best backtested weights”  
- IV → risk-neutral density  
- Short straddle as a product shape  
- AR1 regime on returns  
- Kelly / fractional Kelly sizing talk  

### Where **net-new or net-differentiated** *could* appear

| Candidate | Novelty type | Catch |
|---|---|---|
| **Falsifiable dual-track: \(P\)-calibration exam before any option P&L claim** | Process / product integrity (rare in retail “AI options”) | Discipline, not a model patent |
| **AI factor graph with hard data injection + confidence flags + calibration loop** | Composition of LLM structure + classical MC | Hallucination; must prove calibration |
| **ACE codon memory across regimes for distribution models** | Adaptive ensemble for densitites | Needs many resolved horizons |
| **Governor as priced insurance (net premium in $)** | Eval innovation | Must instrument stress vs bull |
| **Rebalance α as learned cost-aware control under fixed \(w^\*\)** | Classical + light learning | Small edges, careful stats |
| **LV population over strategies with dollar reward** | Speculative net-new | High complexity; failed simpler learning first |
| **Uzumaki/spiral embeddings for finance** | Speculative | No evidence path from this repo |

**Alien judgment:** The highest *plausible* differentiation is not “a new straddle.” It is **a ruthless exam system**: prove distribution skill against the market’s options-implied baseline, refuse to trade when you can’t, ledger everything. That is **methodological product**, not a new PDE.

---

## 5. Utility: why or why not

### Why a **truth engine (B)** may have utility

| Why | Why not / hard part |
|---|---|
| Matches a real need: *know when you don’t know* | Calibration is hard; markets are efficient-ish |
| Clear scientific scoreboard (PIT, CRPS, quantile hit rates) vs mushy “alpha” | Options data quality and horizon alignment |
| De-risks later trading (no trade without edge exam) | Long wait before any $ story |
| Differentiates from “AI said buy calls” junk | Easy to overfit graphs with LLMs |
| Reuses ace_core + existing design | Implementation still multi-month if done properly |
| Feeds later rebalance/allocation as *state* | Utility of \(P\) for equities alone may be modest |

### Why **pure rebalancing** may have utility

| Why | Why not |
|---|---|
| Clear question; institutional demand | Edges often small after costs |
| We already have env + costs + protocol | Less “wow,” harder marketing |
| Fixes the drift problem | May conclude calendar ≈ optimal |
| Honest product: “keep mix without thrash” | Not options/straddle path |

### Why **allocation selector** may have utility

| Why | Why not |
|---|---|
| People want “auto portfolio” | We **failed** constrained test |
| Easy demos | Collapses to concentration without caps |
| | Competes with free Bogle advice |

### Why **full straddle trading system** may have utility

| Why | Why not |
|---|---|
| If \(P\) truly beats \(Q\) after costs, EV exists | Statistical sample sizes brutal |
| | Left tail can erase years |
| | Regulatory/ops if ever live |
| | Skipping truth engine = theater |

### Why **swarm / LV / multi-agent finance** may have utility

| Why | Why not |
|---|---|
| Novel research story | No falsifiable $ win yet |
| | Massive scope; prior swarm repos already exist |
| | Violates SP7 |

---

## 6. What we learned → how we revise beliefs

| Prior belief | Evidence | Revised belief |
|---|---|---|
| Learning menus raises wealth | FAIL_B2 under caps | Learning **menus** needs better features/objectives or is weak |
| Unconstrained SOTA is encouraging | QQQ concentration | Treat as **beta lottery**, not method proof |
| Dollars-over-time is enough north star | Drifted off rebalancing | North star needs **problem class** (rebalance / \(P\)-skill / trade) |
| Prediction helps | P1 hurt $ | Only keep prediction if **calibration or $ ablation** wins |
| Explore online = learning | UCB lost | Prefer offline / batch retrain + greedy, or off-policy |
| Process discipline works | Prereg, audit, FAIL accepted | **Keep process**; change problem object |
| Options were abandoned | Never coded in lvswarm | **Parked**, not falsified — good candidate for next *object* |
| B (truth engine) “sounds best” | Aligns FP1–2, SP1, SP5 | Still must **earn** with a calibration exam design |

**Revision of the program identity:**

> Stop claiming we are primarily an “RL wealth OS.”  
> We are a **falsification lab for financial decision objects**.  
> Next object should be one of: (1) distribution skill vs market, (2) rebalance control under fixed mix, (3) allocation under hard constraints with better state—not all three.

---

## 7. Five options — description, utility, P(success)

**Success** = within a serious research cycle (local/faux data, sealed eval), produce a **credible, non-leaky result** that either (a) shows useful skill on a pre-registered metric, or (b) cleanly falsifies the approach and saves future waste.  
**Not** = “get rich” or “live trading works.”

Probabilities are **subjective**, conditioned on focused execution and no live-capital distraction. Scale: 0–100%.

---

### Option 1 — Options **truth engine** (path B): \(P\) vs market-implied \(Q\), no trading P&L claim

**What:** Regime + data-backed factors + distribution; extract IV density; mispricing/calibration metrics; “I don’t know” gate.  
**Net-new?** Process + possible LLM-structured factors with validation—not a new pricing theory.  
**Utility if works:** High for integrity and later trading; medium standalone product (research/tooling).  
**Main failure modes:** Uncalibrated LLM graphs; data gaps; no beat vs simple historical vol baselines.

| | |
|---|---|
| **P(success)** | **58%** |
| **P(useful FAIL)** | **25%** |
| **P(waste / muddle)** | **17%** |

---

### Option 2 — **Rebalancing lab**: fixed target, only rebalance policies compete

**What:** Freeze equal-weight (or fixed strategic mix). Compare never / calendar / threshold / partial-α / cost-aware. Optional learn α.  
**Net-new?** Unlikely; solid engineering + clear science.  
**Utility if works:** High clarity for “autobalance”; product = rebalance engine.  
**Main failure modes:** All policies ≈ same after costs; boring true answer.

| | |
|---|---|
| **P(success)** | **72%** |
| **P(useful FAIL)** | **18%** |
| **P(waste / muddle)** | **10%** |

*(Success includes “we measured cleanly and ranked policies,” even if winner is calendar.)*

---

### Option 3 — **Constrained allocation 2.0**: better state + train score, still caps, same prospective protocol

**What:** Keep DPL-1 protocol; improve templates/features/objective (log-growth, Calmar); no 100% single names.  
**Net-new?** Low–medium.  
**Utility if works:** Auto-allocator people want; we already failed once.  
**Main failure modes:** Second FAIL; complexity creep; still loses to hold.

| | |
|---|---|
| **P(success)** | **35%** |
| **P(useful FAIL)** | **40%** |
| **P(waste / muddle)** | **25%** |

---

### Option 4 — **Full faux options book** (straddle/condor) without finishing truth-engine exam

**What:** Simulate short premium etc. on historical chains ASAP for dollar curves.  
**Net-new?** No.  
**Utility if works:** Exciting demos; dangerous science.  
**Main failure modes:** Overfit, hidden leakage, tail undersampling, fake confidence.

| | |
|---|---|
| **P(success)** | **22%** |
| **P(useful FAIL)** | **28%** |
| **P(waste / muddle)** | **50%** |

---

### Option 5 — **Hybrid bridge**: truth-engine MVP on **one** liquid name + DollarPath protocol discipline; still no option trading P&L as primary claim

**What:** Smallest B that ships: one ticker (e.g. SPY or LOW), real IV/history as available, historical-vol / simple ensemble \(P_0\) baseline vs market \(Q\), calibration report, confidence gate. Optional later: use calibration state to **throttle equity exposure** in DollarPath (secondary).  
**Net-new?** Low science, high **integration** of our process strengths with options theory.  
**Utility if works:** Unblocks B without boiling ocean; keeps equity lab alive as consumer of scores.  
**Main failure modes:** Data pain; weak \(P_0\) never beats naive baselines—still useful FAIL.

| | |
|---|---|
| **P(success)** | **64%** |
| **P(useful FAIL)** | **22%** |
| **P(waste / muddle)** | **14%** |

---

## 8. Comparison table

| # | Option | P(success) | Aligns “B”? | Aligns rebalance? | Drift risk | Alien utility |
|---|---|---:|---|---|---|---|
| 1 | Full truth engine | 58% | Strong | Indirect | Medium | High if exam is real |
| 2 | Rebalancing lab | **72%** | Weak | **Strong** | Low | High clarity |
| 3 | Constrained alloc 2.0 | 35% | Weak | Weak | Medium | Low after FAIL_B2 |
| 4 | Jump to straddle P&L | 22% | Fake-B | None | **High** | Low integrity |
| 5 | Hybrid truth MVP | **64%** | **Yes (B-lite)** | Optional later | Low–med | **Best balance** |

---

## 9. Best recommendations (after the step-back)

### Primary recommendation: **Option 5 — Hybrid truth-engine MVP** (B, but small)

**Why this over pure full B (Option 1):**  
Same theory object (\(P\) vs \(Q\), calibration, humility), lower muddle risk, faster falsification, reuses DollarPath’s prereg/audit culture without pretending we already have a straddle money machine.

**Why this over pure rebalancing (Option 2):**  
You said B sounds best; Option 5 **is** B’s first principles path. Rebalancing scores higher on “will we complete a clean study,” but lower on your stated pull. Option 5 still leaves rebalancing as a **downstream consumer** of a confidence score (“don’t rebalance / don’t increase risk when \(P\) is uncalibrated”).

**Why not 3 or 4:**  
3 fights a battle we already mostly lost without new state. 4 is how retail AI-options projects die—P&L theater without a distribution exam.

### Secondary recommendation (if B loses appeal): **Option 2 — Rebalancing lab**

Highest P(success), fixes identity drift, true “autobalance,” smaller ego story.

### Explicit do-not

- Do not run Option 4 as next primary.  
- Do not re-open unconstrained QQQ as “method SOTA.”  
- Do not start LV/swarm finance until one of {5, 2} has a sealed result card.

---

## 10. If we adopt Option 5 — success definition (preview)

**In (truth):**

- For ticker T and horizons H: produce \(P\) and market \(Q\) (or IV-based summary).  
- Metrics: calibration (e.g. PIT histogram, quantile coverage), log score / CRPS vs baselines (historical vol, naive lognormal).  
- Output includes **abstain** when confidence low.  
- Prereg + as-of protocol + artifacts like DollarPath.

**Out:**

- Straddle PnL as primary claim  
- Multi-ticker empire  
- Live trading  

**Pass:** \(P\) beats naive baselines on prereg calibration score on held-out windows **or** clean FAIL that historical/simple models win (still valuable).  
**Only later:** payoff layer / faux short-vol under governor.

---

## 11. One-page alien summary

| | |
|---|---|
| **What the universe is** | Prices, option quotes, costs, uncertainty |
| **What we proved** | Menu-picking under caps doesn’t beat equal hold here; process discipline works |
| **What we didn’t prove** | Distribution skill; rebalance optimality; option edge |
| **What would be new enough** | A forced **exam** of \(P\) against market \(Q\) before any trade story |
| **Best next bet** | **Option 5 (64%)** — truth-engine MVP, one name, calibration first |
| **Runner-up** | **Option 2 (72%)** — if you re-prioritize rebalancing purity over B |
| **Avoid** | Straddle P&L first (**22%** success / **50%** waste) |

---

*End of step-back. No code commitment implied until a GOAL is chosen for Option 5 or 2.*
