# Portfolio Autobalance × Prediction KB × Expert System (naked_straddle_sim)

**Repo examined:** `/Volumes/WS4TB/macwise-clean-test/naked_straddle_sim`  
**Claim under scrutiny:** In portfolio autobalance, **prediction is the key knowledge base**. Does the existing expert/ACE stack **add value** or the **inverse**?

---

## 1. What the repo actually is

Not “find good option trades.” Per `docs/ARCHITECTURE.md`:

> Estimate the true probability distribution of a stock's future price, compare it to what option prices imply, choose payoff geometry that exploits the mismatch, and **avoid ruin from model error**.

### Five layers (as designed)

| Layer | Role | “Prediction” content |
|---|---|---|
| **1 Regime** (`UniversalRegimeDetector`) | World-state / which playbook | AR(1) ρ → stable / volatile / transitioning (+ planned VIX, RV/IV) |
| **2 Distribution** (factor graph + MC + ensemble pattern) | **P(price path)** | AI factor graph → Monte Carlo; ensemble weighted by ACE |
| **3 Market-implied** | Market’s **P** from options | IV surface → risk-neutral PDF (Breeden–Litzenberger) |
| **4 Payoff optimizer** | Act on mispricing | EV / CVaR under *our* P at *market* prices; ACE codons learn geometries |
| **5 Risk-of-ruin governor** | **Hard expert rules** | Veto / size down / force defined risk — overrides everything |

**Phase 1 intent:** “truth engine” only (distributions + mispricing). No live trading required for first scientific claim.

**Local / limited $:** yfinance + FRED free; Tradier sandbox; OpenRouter for factor graphs (small, bounded $). Faux $100k portfolio for simulation (`SIMULATION_AND_MEASUREMENT.md`). Fits the earlier “portfolio = $0 testable” lane.

---

## 2. Why prediction is the KB for portfolio autobalance

Classic rebalancing (“drift back to 60/40”) is **non-predictive**. It only uses:

- current weights  
- target weights  
- transaction costs  

**Predictive autobalance** (what would be “wow”) needs a knowledge base of:

| KB object | Why rebalance needs it |
|---|---|
| **Forecast distribution** (not point estimate) | Size and direction of drift *expected*, not just past drift |
| **Regime label + transition risk** | When to rebalance early vs sit still |
| **Confidence / model disagreement** | When *not* to rebalance (prediction is noise) |
| **Tail / stress scenarios** | Cap risk when rebalancing into blow-up regimes |
| **Cost of action** | Spread, tax, margin — same as naked straddle slippage model |
| **Calibration history** | Did past predictive quantiles match reality? |

NakedStraddle already aims at exactly those objects for **one-asset options risk**. Portfolio autobalance is the same objects, **vectorized across holdings** and used to move weights—not only to pick option geometry.

```
prediction KB (regime, P(return), confidence, tails)
        ↓
autobalance policy (target risk, turnover budget, veto rules)
        ↓
portfolio weights / position sizes / no-trade
```

So: **yes — prediction is the key KB**, not a side feature. Without calibrated P and confidence, “smart rebalance” collapses to either (a) dumb calendar rebalance or (b) overtrading on noise.

---

## 3. What “expert system software” means here

Two different expert layers in this stack:

### A. Soft / learned expert — ACE (`StrategyMemory`, ensemble weights)

- Codons: strategies helpful vs harmful by context  
- Claims in code: regime-adaptive ensemble, no full retrain; prior +57% MAI note in comments  
- **Value mode:** reweights *which predictors* to trust in which regime  

### B. Hard / classical expert — Layer 5 governor (10 non-negotiable rules)

Examples from architecture:

- Event veto (earnings/FOMC inside horizon → no naked)  
- Model disagreement veto  
- Tail / black-swan force defined risk  
- Regime transition → half size + defined risk  
- Liquidity, concentration, correlation filters  
- Stress “2× vol” size check  
- Max loss caps  

### C. AI “expert” — factor graph generator (OpenRouter)

- Nodes, edges, black swans, ranges  
- Design already fears hallucination → hybrid with FRED/yfinance baselines  

These three must be judged **separately**. Bundling them as one “expert system” hides where value and inverse live.

---

## 4. Value vs inverse (honest matrix)

### Where the stack **adds value** (for portfolio autobalance)

| Component | Value | Evidence in design |
|---|---|---|
| **Distribution vs market compare** | Edge = difference of two P’s, not “AI tip” | Layers 2–3 mispricing score |
| **Regime-gated predictors** | Different rebalance policies per regime | Layer 1 + strategy_config in `OptionsAdapter` |
| **Hard vetoes as risk governor** | Prevents “prediction confident → blow up” | Layer 5 overrides optimizer |
| **No-trade as first-class** | Autobalance must know *when not to act* | Payoff optimizer + governor |
| **Faux portfolio + path marks** | Local, measurable C/T/R without live capital | `SIMULATION_AND_MEASUREMENT.md` |
| **Calibration metrics** | Turns prediction into auditable KB | Quantile of realized return vs model/market |
| **ACE codon memory** | Autobalance of *which models/geometries* over time | StrategyMemory helpful/harmful |

**Portfolio translation of that value:**

- Use Layer 1–2 as **risk/forecast KB** for multi-asset weights  
- Use Layer 5-style rules as **rebalance governor** (don’t rebalance into earnings week; don’t increase equity when model disagreement high)  
- Use ACE to **autobalance predictor mix**, not only asset mix  

That is a coherent story: **autobalance of capital + autobalance of prediction strategies**.

---

### Where the stack is **inverse / value-destroying** (if misused)

| Failure mode | Why inverse | Portfolio rebalance impact |
|---|---|---|
| **Point forecast as truth** | Options need full P; point targets overtrade | Whipsaw rebalance, high turnover |
| **Uncalibrated factor-graph AI** | Hallucinated means/sensitivities | Confident wrong KB → systematic misallocation |
| **Over-veto Layer 5** | Always “no trade / no rebalance” | Opportunity cost; looks safe, earns nothing |
| **Under-veto / override governor** | Optimizer EV without ruin constraints | Fat left tail; classic short-premium death |
| **ACE on small samples** | Helpful/harmful counts unstable early | Chases noise; thrash of strategy weights |
| **Regime detector lag** | AR(1) slow on abrupt crisis | Rebalances *into* the crash |
| **Ignoring market-implied P** | Only “our model” | Fights liquid market with no edge check |
| **Open-ended OpenRouter spend** | Cost without calibration | Burns limited cloud budget; no better KB |
| **Backfill optimism** | IV frozen / sparse marks | Simulated autobalance looks better than live |

**Inverse law for this project:**

> Expert systems add value when they **constrain action under uncertainty**.  
> They destroy value when they **pretend uncertainty is resolved**.

Hard rules → good as **constraints**.  
Hard rules → bad as **substitutes for calibration**.  
AI factor graphs → good as **hypothesis generators**.  
AI factor graphs → bad as **unvalidated probability mass**.

---

## 5. Prediction KB: what must be stored (portfolio-ready)

Minimum objects (local SQLite is enough):

| Record | Fields (sketch) | Used by autobalance |
|---|---|---|
| `regime_snapshot` | t, asset/universe, regime, ρ, conf, transition_flag | gate rebalance frequency |
| `model_distribution` | quantiles, mean, skew, kurt, tails, graph_id | target risk / tilt |
| `market_distribution` | implied quantiles, IV, skew | edge and “don’t fight market” |
| `mispricing` | score vector, confidence | whether to act |
| `ensemble_weights` | strategy → weight (ACE) | which models drive tilt |
| `governor_decision` | approve/size/veto + rule id | audit trail |
| `outcome` | realized return, quantile hit, PnL | **updates KB + ACE** |

Without `outcome` feedback, the expert system **cannot** autobalance predictors—it only freezes priors.

---

## 6. Value / inverse scorecard (for *this* repo as portfolio engine)

Scored for **using naked_straddle_sim stack as the prediction KB behind portfolio autobalance**, local / limited $.

| Piece | Adds value? | Inverse risk | Local testability | Net for first proof |
|---|---|---|---|---|
| Regime detector | High | Lag / mislabel | Excellent $0 | **Keep, measure hit rate on known crises** |
| Ensemble + ACE memory | Medium–High | Small-n thrash | Excellent $0 | **Keep with strict holdout** |
| Market-implied layer | Critical | Data/API gaps | Good (free IV sources limited) | **Required; market is baseline** |
| AI factor graph | Medium | Hallucination cost | Limited $ OpenRouter | **Optional for v1; data baselines first** |
| Hard Layer 5 rules | High for survival | Over-veto | Free logic tests | **Keep as governor, log every veto** |
| Payoff optimizer | Options-specific | Overfit geometries | Needs chains | **Defer if portfolio ≠ options book** |
| Faux $ portfolio sim | High measurement | Backfill bias | $0 | **Primary test harness** |

### Net judgment

| Statement | Verdict |
|---|---|
| Prediction is the key KB for portfolio autobalance | **Yes** |
| This expert stack *can* add much value | **Yes — if** regime + calibrated distributions + market compare + hard governor + outcome feedback |
| This expert stack *can* be the inverse | **Yes — if** AI graph / ACE / EV optimizer dominate without calibration and veto logging |
| Best first use of the repo | **Truth engine + faux portfolio autobalance policy**, not live naked straddles |
| Best “wow” metric (self-evident) | Same capital, lower max drawdown / CVaR **or** same risk, higher net after costs vs calendar rebalance — with **calibration error** reported, not hidden |

---

## 7. How expert system should plug into autobalance (recommended architecture)

```
                 ┌─────────────────────────────┐
                 │  Prediction KB (updated)    │
                 │  regime · model P · market P│
                 │  conf · ACE weights         │
                 └─────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Autobalance policy           │
               │  propose Δw (or option size)  │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Expert governor (Layer 5)    │
               │  APPROVE / SIZE / VETO        │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Execute (sim or live)        │
               │  → outcomes → ACE + KB        │
               └───────────────────────────────┘
```

**Critical separation:**

1. **Prediction** proposes beliefs.  
2. **Autobalance** proposes actions from beliefs + costs.  
3. **Expert governor** may only **shrink or stop** actions (never invent false confidence).  
4. **Outcomes** update ACE and calibration — the only path where the system “gets smarter.”

If the expert layer *increases* conviction without new data → **inverse**.

---

## 8. Three experimental forks (all local / limited $)

| Fork | Question | $ | Expert role |
|---|---|---|---|
| **A. Calendar vs predictive rebalance** | Does P-based rebalance beat 60/40 drift on faux multi-asset? | $0 | Governor only |
| **B. ACE on vs off** | Does codon memory improve calibration / net PnL? | $0 | Soft expert ablated |
| **C. Governor on vs off** | Does Layer 5 reduce ruin more than it costs opportunity? | $0 | Hard expert ablated |

**Success = A wins on risk-adjusted after-cost; B improves calibration without thrash; C reduces left-tail more than it kills EV.**  
If B or C fail, that *is* the inverse finding — publish/kill that layer, don’t paper over it.

---

## 9. Bottom line

1. **Portfolio autobalance without prediction** is commodity. **With a calibrated prediction KB** it can be wow.  
2. **naked_straddle_sim** is already structured as that KB (regime + dual distributions + mispricing + governor + faux portfolio).  
3. **Expert system value is asymmetric:**  
   - **Hard governor + “I don’t know”** → usually +EV for survival.  
   - **Uncalibrated AI expertise + unconstrained optimizer** → usually −EV (inverse).  
4. **ACE** is valuable as **autobalance of predictors**, parallel to **autobalance of capital** — only after enough outcome samples.  
5. Under local resources: build **truth engine + faux rebalance A/B/C** first; treat live options and heavy OpenRouter as optional limited-$ smokes, not the proof.

---

## 10. Open product question (for next brainstorm turn)

Should the first “wow chart” be:

1. **Multi-asset portfolio rebalance** driven by ace_core prediction KB (options optional), or  
2. **Single-name options truth engine** (LOW Phase 1 as designed), with portfolio language deferred, or  
3. **Unified:** same KB feeds both weight rebalance *and* option geometry when edge exists?

That choice decides whether Layer 4 (payoff optimizer) is on the critical path or not.
