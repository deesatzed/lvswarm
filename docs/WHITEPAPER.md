# DollarPath — White Paper

**Working title:** Learning Policies That Grow Wealth Over Time  
**Codename:** DollarPath  
**Workspace:** `/Volumes/WS4TB/lvswarm`  
**Status:** Design + autonomous build contract (implementation not complete)  
**Related prior art in-workspace:** `naked_straddle_sim` (prediction + ACE + governor), `clawswarmed` (ledgered eval), `predoc1.md` (LV ecology ideas)

---

## Abstract

DollarPath is a research-grade system whose **only success criterion** is growing **worth (dollars) over time** better than transparent baselines, without catastrophic ruin. The system treats capital allocation as a **reinforcement learning (RL) problem**: observe market and internal state, choose risk and allocation actions (including “do nothing”), receive a **dollar-denominated reward**, and improve the policy.

Prediction models, expert rules, and “autobalance” controllers are **not** the product. They are **optional state and constraint modules**. A module is retained only if ablations show it improves after-cost wealth or reduces ruin risk without destroying net dollars.

This white paper specifies problem formulation, architecture, evaluation protocol, statistical guardrails, local-resource constraints, non-goals, and the path to a falsifiable **SOTA-class claim** within honest scope (historical faux-capital policy learning — not “guaranteed live alpha”).

---

## 1. Motivation

### 1.1 The real objective

Humans and institutions care about:

- more capital later than earlier  
- survival through adverse regimes  
- costs (fees, spread, tax drag, thrash) not eating the edge  

Most multi-agent and “AI trading” systems optimize proxies (accuracy, disagreement quality, aesthetic swarm structure). **Proxies drift.** DollarPath hard-codes the economic objective:

\[
\max_{\pi} \; \mathbb{E}\big[U(W_T)\big]
\quad\text{subject to risk / ruin constraints}
\]

where \(W_t\) is wealth at time \(t\), \(\pi\) is a policy mapping state to actions, and \(U\) is a utility (default: log-wealth growth with drawdown penalties).

### 1.2 Why RL

Rule engines and static optimizers do not automatically improve from **realized dollar outcomes**. RL (broadly: any loop that updates a policy from rewards) does:

1. Act under uncertainty  
2. Observe wealth change  
3. Update what to do next time  

This includes simple bandits and ACE-style codon memory as **weak RL**, and can grow to full policy-gradient or actor-critic methods when justified by data volume.

### 1.3 Why prediction still matters

Calendar rebalancing needs no forecast. **Higher wealth** under realistic costs usually requires:

- estimates of return **distributions** (not point tips)  
- **regime** labels and transition risk  
- **confidence / model disagreement** (when *not* to act)  
- comparison to **market-implied** beliefs when available  

Prediction is the **knowledge base for state**, not a substitute for the reward.

### 1.4 Why expert systems are double-edged

Hard rules (event vetoes, concentration limits, stress tests) often **save dollars** by blocking ruin. They also **cost dollars** by blocking opportunity. Soft experts (ACE, ensembles) help when calibrated; they harm when they thrash on small samples or invent confidence.

DollarPath **measures** both effects with ablations. No expert layer is sacred.

---

## 2. Problem formulation

### 2.1 Environment

- **Assets:** universe \(\mathcal{A}\) (Phase 1: liquid ETFs / equities with free historical data; options optional later).  
- **Time:** discrete evaluation steps (daily or weekly).  
- **Information:** only data available **as of** \(t\) (no peeking).  
- **Execution model:** next-bar or same-bar-with-slippage (declared in prereg; default next open/close with bid-ask model).  

### 2.2 State \(s_t\)

Minimum fields:

| Field | Description |
|---|---|
| `wealth` | Mark-to-market capital |
| `cash`, `positions` | Holdings and weights |
| `prices` / returns history | Windowed features |
| `regime` | From regime detector (if enabled) |
| `forecast` | Distribution summary or features (if enabled) |
| `market_implied` | Optional IV / implied moments |
| `confidence` | Ensemble disagreement / forecast confidence |
| `costs_so_far` | Cumulative friction |
| `drawdown` | Current peak-to-trough |

### 2.3 Action \(a_t\)

Phase 1 discrete / low-dimensional continuous hybrid:

| Action class | Examples |
|---|---|
| **Target risk** | Scale gross exposure \(\in \{0, 0.25, 0.5, 0.75, 1.0\}\) of max |
| **Allocation** | Weights over assets (simplex), or “equal weight among selected” |
| **Rebalance intensity** | Fraction of gap to target closed this step (autobalance throttle) |
| **No-op** | Hold current positions (always legal) |

Phase 2+ may add option geometry actions only after cash/equity policy beats baselines.

### 2.4 Transition and costs

- Prices evolve from **real historical series**.  
- Trades incur: commission (if any) + spread model + optional tax proxy.  
- Wealth update:

\[
W_{t+1} = W_t + \text{PnL}_{t\to t+1} - \text{Costs}_t
\]

### 2.5 Reward

**Primary (default):**

\[
r_t = \log(W_{t+1} + \epsilon) - \log(W_t + \epsilon)
\]

**Optional shaped terms (must be ablated):**

- \(-\lambda_{\text{dd}} \cdot \max(0, \text{drawdown}_t - d^\*)\)  
- \(-\lambda_{\text{turn}} \cdot \text{turnover}_t\)  
- large negative terminal reward on **ruin** (\(W_t < W_{\text{ruin}}\))

Shaping must never replace reporting of **raw ending wealth**.

### 2.6 Policy classes

| Class | Role |
|---|---|
| \(\pi_{\text{hold}}\) | Buy-and-hold baseline |
| \(\pi_{\text{calendar}}\) | Periodic rebalance to fixed targets |
| \(\pi_{\text{vol}}\) | Simple volatility targeting |
| \(\pi_{\text{pred}}\) | Fixed rules on prediction features (no learning) |
| \(\pi_{\text{rl}}\) | Learned policy (ACE bandit → tabular/RL → later deep) |
| \(\pi_{\text{gov}}\) | Any of the above + hard expert governor |

---

## 3. System architecture

### 3.1 Modules

```
┌─────────────────────────────────────────────────────────────┐
│                     DollarPath Runtime                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Data plane  │→│ State builder │→│ Policy π (RL/base)  │  │
│  │ prices/macro│  │ features     │  │ action proposal      │  │
│  └─────────────┘  └──────────────┘  └──────────┬─────────┘  │
│         │                │                      │            │
│         │         ┌──────▼───────┐       ┌──────▼───────┐   │
│         │         │ Prediction KB│       │ Expert       │   │
│         │         │ (optional)   │       │ governor     │   │
│         │         └──────────────┘       └──────┬───────┘   │
│         │                                       │            │
│         │                              APPROVE/SIZE/VETO     │
│         ▼                                       ▼            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Portfolio / execution simulator          │    │
│  │         marks, costs, positions, wealth path          │    │
│  └──────────────────────────┬──────────────────────────┘    │
│                             ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Reward · ledger · metrics · ACE/RL update            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Prediction knowledge base (optional module)

Reuse concepts from `naked_straddle_sim` / `ace_core`:

| Component | Function |
|---|---|
| `UniversalRegimeDetector` | Regime + transition flags |
| `UniversalEnsembleForecaster` / distribution features | Forecast moments / quantiles |
| Market-implied features | When options data available |
| Calibration store | Realized quantile hits → trust weights |

**Hard rule:** prediction never writes trades directly. It only enriches \(s_t\).

### 3.3 Expert governor (optional module)

Hard constraints (non-learned), examples:

- max position / sector concentration  
- max turnover per step  
- veto new risk if regime confidence low or model disagreement high  
- cash floor  
- stress: if 2× vol shock breaches loss cap → size down  

Governor may only **APPROVE / SIZE DOWN / VETO**. It may not invent edge.

### 3.4 Autobalance

Autobalance = control of **how fast and how far** allocations move toward a target under cost:

- target from policy  
- gap closed subject to turnover budget and governor  
- thrash metric: unnecessary round-trips  

Inspired by MoE load balance / portfolio rebalance practice: **utilization of capital without collapse into monoculture or churn**.

### 3.5 Learning (RL stack, staged)

| Stage | Method | When |
|---|---|---|
| L0 | No learning; fixed policies | Baselines |
| L1 | ACE / multi-armed bandit over discrete action templates | First learning win |
| L2 | Contextual bandit (state features → action) | After L1 beats L0 |
| L3 | Full episodic RL (e.g. PPO/A2C on compact state) | Only if L2 plateaus and data supports |
| L4 | Multi-strategy population (LV-style influence over strategy mix) | Research extension |

**Population / LV ecology** is deferred until a single policy clearly beats baselines; then strategies become “species” whose sampling weights autobalance under dollar rewards.

### 3.6 Evidence plane (mandatory)

Every run writes artifacts (pattern from `clawswarmed`):

| Artifact | Content |
|---|---|
| `metrics.json` | Ending wealth, CAGR, max DD, costs, vs baselines |
| `equity_curve.csv` | \(W_t\) path |
| `ledger.jsonl` | Hash-chained decisions (optional but preferred) |
| `result_card.md` | Human summary, claims, limits |
| `config.json` | Seeds, universe, costs, policy id, git hash |
| `ablation_matrix.json` | Module on/off results |

---

## 4. Evaluation protocol

### 4.1 Baselines (always run)

1. **Cash** (optional sanity)  
2. **Buy-and-hold** equal or market proxy  
3. **Calendar rebalance** to fixed weights  
4. **Volatility targeting** (simple)  

### 4.2 Primary SOTA claim (honest scope)

> On preregistered universe, period, cost model, and seeds, DollarPath policy \(\pi_{\text{rl}}\) achieves **higher ending wealth** (or higher CAGR) than all baselines **and** max drawdown not worse than the best baseline by more than a preregistered tolerance **or** superior Calmar (CAGR / |maxDD|) with non-inferior ending wealth — **after costs**.

This is **historical policy SOTA under stated assumptions**, not proof of future live alpha.

### 4.3 Ablations (required before claiming modules help)

| Ablation | Question |
|---|---|
| − prediction features | Does forecast state add dollars? |
| − governor | Does governor save more than it costs? |
| − learning (freeze policy) | Does RL beat fixed pred rules? |
| − autobalance throttle | Does thrash control add dollars? |

A module with no positive ablation is **removed or demoted**.

### 4.4 Statistical rigor (non-negotiable)

Aligned with short-premium / backtest literature cited in `naked_straddle_sim/docs/STATISTICAL_RIGOR.md`:

- Preregister universe, costs, periods, metrics **before** tuning claims.  
- Walk-forward or purged cross-validation; no random shuffle of time.  
- Report **multiple testing** awareness (Harvey–Liu style caution).  
- Separate **dev** seeds from **held-out** evaluation seeds.  
- Stress windows mandatory: e.g. 2008 (if data), 2018 vol spike, 2020 crash, 2022 rates — as available for the universe.  
- Never claim significance from a single lucky path.

### 4.5 Local / limited cloud constraints

| Resource | Policy |
|---|---|
| Compute | Prefer Apple Silicon local (M-series, 64GB-class) |
| Market data | Free first (e.g. yfinance); cache to disk (real data, not mock) |
| LLM / OpenRouter | Optional; hard budget cap; disabled by default for core RL loop |
| Live trading | **Out of scope** until faux SOTA gates pass and human authorizes capital |
| Mocks | **Forbidden** for market outcomes, fills, or rewards without explicit human approval |

---

## 5. Implementation shape (repository)

Proposed package layout under `/Volumes/WS4TB/lvswarm`:

```text
lvswarm/
  docs/
    WHITEPAPER.md          # this document
  GOAL.md                 # autonomous agent contract
  BUILD_TODO.md           # ordered checklist with gates
  README.md
  dollarpath/             # application package
    __init__.py
    data/                 # feeds, cache, validators
    env/                  # portfolio simulator, costs, rewards
    state/                # feature builders
    policies/             # baselines + RL policies
    prediction/           # optional adapters to ace_core concepts
    governor/             # hard rules
    train/                # learning loops
    eval/                 # walk-forward, metrics, ablations
    artifacts/            # run outputs (gitignored bulk)
    cli.py
  tests/
  prereg/                 # preregistration docs per experiment
  scripts/
```

**Reuse (do not rewrite blindly):**

- Regime / ACE patterns from `macwise-clean-test/naked_straddle_sim/ace_core`  
- Artifact / ledger discipline from `clawswarmed/broadcast_alpha`  
- Faux portfolio ideas from `naked_straddle_sim/docs/SIMULATION_AND_MEASUREMENT.md`  

---

## 6. Threats to validity

| Threat | Mitigation |
|---|---|
| Lookahead bias | Strict as-of joins; tests that fail on shifted labels |
| Survivorship | Prefer point-in-time universes when possible; document bias |
| Overfit RL | Held-out years; limited policy capacity early |
| Cost underestimation | Conservative spread model; sensitivity table |
| Regime detector lag | Explicit crisis stress; compare to oracle-free baselines |
| Expert over-veto | Ablation −governor; opportunity cost report |
| Fake “SOTA” wording | Claims always scoped: historical, costs, universe |

---

## 7. Non-goals

- Guaranteed live trading profits  
- Replacing professional asset managers without live validation  
- Multi-agent theater without dollar lift  
- MoE / grid / ads products (analogies only)  
- White-box LLM mechanistic interpretability (clawswarmed J-lens path) as a dependency  
- Mock market data as proof  

---

## 8. Phased capability roadmap

| Phase | Capability | Exit gate |
|---|---|---|
| **P0** | Repo skeleton, data cache, portfolio env, metrics, baselines | Baselines produce equity curves + metrics.json |
| **P1** | Prediction-optional state + governor + autobalance throttle | Pred/gov ablations runnable |
| **P2** | L1 learning (bandit/ACE) on dollar reward | \(\pi_{\text{rl}}\) beats baselines on dev set |
| **P3** | Walk-forward + stress + prereg held-out | Held-out claim pass or honest fail |
| **P4** | Optional options-aware state / actions | Only if P3 equity policy is strong |
| **P5** | Multi-strategy population (LV autobalance of strategies) | Population beats single best strategy |

**SOTA application** in this program means: **passing P3 with a preregistered, reproducible, after-cost outperformance claim** — not a marketing label.

---

## 9. Ethical and practical notes

- Historical backtests can destroy real money if naively deployed.  
- Live capital requires separate human authorization, custody controls, and risk limits.  
- Limited API spend must be ledgered; never unbounded OpenRouter loops.  
- Prefer open, inspectable policies before black-box deep RL.

---

## 10. Conclusion

DollarPath converts the brainstorm around autobalance, prediction experts, and multi-agent ecology into a single falsifiable program:

**Learn and measure capital allocation policies by dollars over time.**

Everything else is optional machinery, retained only under ablation. The autonomous build contract (`GOAL.md`) and checklist (`BUILD_TODO.md`) exist so agents can implement, test, and **honestly fail or pass** this claim without drifting into proxy metrics.

---

## References (in-workspace)

- `END_GOAL_DOLLARS_OVER_TIME.md`  
- `PORTFOLIO_PREDICTION_EXPERT_ANALYSIS.md`  
- `AUTOBALANCE_CONTEXTS_TOP5.md`  
- `macwise-clean-test/naked_straddle_sim/docs/ARCHITECTURE.md`  
- `macwise-clean-test/naked_straddle_sim/docs/STATISTICAL_RIGOR.md`  
- `macwise-clean-test/naked_straddle_sim/docs/SIMULATION_AND_MEASUREMENT.md`  
- `clawswarmed/README.md` (artifact discipline)

## External literature anchors (for statistical design)

- Bailey & López de Prado — track record length / backtest overfitting  
- Harvey & Liu — t-stats and multiple testing in finance  
- López de Prado — advances in financial machine learning (purging, embargo)  
- Standard portfolio rebalancing and transaction-cost theory  

---

*Document version: 1.0 — for autonomous development under GOAL.md*
