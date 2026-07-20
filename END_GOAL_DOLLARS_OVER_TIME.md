# End Goal: More Worth / Dollars Over Time

**Ignore product forks.** One objective only:

> **Maximize wealth (or risk-adjusted wealth) over time.**

Everything else (prediction, expert rules, autobalance, LV, multi-agent, RL) is only useful if it moves that number.

---

## 1. Plain English

| Word | Meaning here |
|---|---|
| **Worth / dollars over time** | Starting capital → later capital, after costs. Higher path is better. |
| **RL (reinforcement learning)** | A loop that tries actions, sees dollar outcomes, and improves the policy that chooses actions. |
| **Policy** | The rule: “given what we know now, what do we do?” (hold, rebalance, size up/down, no trade, change strategy mix). |
| **State** | What we know now: prices, regime, our forecast, market forecast, positions, cash, confidence. |
| **Action** | Change weights, open/close size, veto, wait. |
| **Reward** | Change in wealth (and optional penalties for drawdown / ruin risk). |

**Success is not** “clever architecture.”  
**Success is** a policy that, over many periods, leaves **more money** than simple baselines — without blowing up.

---

## 2. The only comparison that matters

Always compare:

| Policy | What it does |
|---|---|
| **Baseline A** | Do nothing / buy-and-hold (or fixed 60/40) |
| **Baseline B** | Simple rules (calendar rebalance, fixed short-vol, etc.) |
| **Our policy** | Uses prediction + autobalance / RL |

**Win condition:**

```
Final wealth_our  >  Final wealth_baselines
  AND  max drawdown / ruin risk  not catastrophically worse
  (or: same drawdown, higher wealth)
```

If a fancy expert system loses money vs baseline, it is **inverse** — kill or fix it.

---

## 3. How the pieces serve dollars (or don’t)

```
                    ┌──────────────────────┐
                    │  Goal: more $ over t │
                    └──────────▲───────────┘
                               │
                    rewards = Δ wealth (− costs)
                               │
              ┌────────────────┴────────────────┐
              │     RL / learning policy        │
              │  (improve what we do next time) │
              └────────────────▲────────────────┘
                               │
         actions: size, rebalance, trade, wait, veto
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
 prediction KB            autobalance              expert governor
 (what might happen)   (how to allocate $)     (don’t die / don’t thrash)
```

| Piece | Serves dollars when… | Hurts dollars when… |
|---|---|---|
| **Prediction** | Better estimate of risks/returns → better sizes | Wrong confidence → overtrade / wrong bets |
| **Autobalance** | Moves money toward better risk/return mix over time | Thrash / fees / tax destroy edge |
| **Expert rules** | Block ruin trades that erase months of gains | Block almost everything → earn less than baseline |
| **RL** | Learns which actions actually grew wealth | Optimizes fake metrics or short windows → looks good, then ruins |

**Rule:** Prediction and experts are **inputs**. RL’s job is to learn a **policy** that turns them into **more dollars**, not more theory.

---

## 4. What “RL” means for this project (practical)

Not “train a giant game AI first.”

**Minimal RL loop (local, faux dollars):**

1. **State** each day/week: capital, positions, regime, forecasts, costs.  
2. **Action:** how much to hold/risk/rebalance (including “do nothing”).  
3. **Environment:** real historical prices (and options marks if used) — not invented outcomes.  
4. **Reward:** e.g.  
   - primary: `Δ log(wealth)` or simple `Δ wealth`  
   - optional: penalty if drawdown > threshold or veto-worthy risk  
5. **Update:** improve policy (even simple: bandit / ACE codon weights / policy gradient later).  
6. **Repeat** over years of history and many seeds.

**ACE StrategyMemory is already a weak form of this:**  
record which strategies helped/harmed → reweight.  
Full RL is the same idea with a clearer **dollar reward** and explicit **action space**.

---

## 5. Dollar metrics (self-evident)

Report these every experiment — no vague “smarter swarm”:

| Metric | Why |
|---|---|
| **Ending wealth** | Raw dollars |
| **Total return %** | Scale-free |
| **CAGR** | Speed of growth |
| **Max drawdown** | Pain / ruin proximity |
| **Calmar or return/DD** | Growth per unit pain |
| **Turnover / costs paid** | Whether thrash ate the edge |
| **% time in market / exposure** | Did we earn by being bold or by sitting out? |
| **Ruin / breach count** | Times we hit hard risk limits |

**“Wow” for a money goal:**  
Same starting $100k faux capital → **higher ending wealth** than buy-and-hold and calendar rebalance, **with** max drawdown not much worse (or clearly better risk-adjusted dollars).

---

## 6. What we build toward (no menu of apps)

**One system concept:**

> A **money policy** that uses market data + prediction to choose **how much risk to take and where**, learns from **realized dollar outcomes**, and is **blocked from ruin** by hard rules — measured only by **wealth over time vs baselines**.

| Stage | What gets built | Success = dollars? |
|---|---|---|
| **1. Measure** | Faux portfolio + historical replay | Can we compute ending $ for any policy? |
| **2. Baselines** | Hold / calendar rebalance / simple vol rule | Fixed scoreboard |
| **3. Prediction-informed policy** | Size/rebalance using regime + forecasts | Beats baselines or not |
| **4. Learn (RL / ACE)** | Update policy from rewards | Beats fixed prediction policy |
| **5. Stress** | Crisis periods, costs, veto on/off | Still more $ without blow-ups |

Live trading and multi-agent theater are **optional later**. They only matter if they improve the dollar curve.

---

## 7. Link to prior ideas (only if they make money)

| Prior idea | Only keep if… |
|---|---|
| Autobalance | Reallocating risk/roles **increases after-cost wealth** |
| LV / ecology | Population of strategies **raises long-run $** without monoculture ruin |
| Minority-signal / Glass Gate | Better decisions under disagreement → **more $ / less blowup** |
| swarm2 roles | Only if multi-view decisions improve trade/rebalance quality → $ |
| naked_straddle_sim | Prediction KB + governor **feed the money policy** |
| Expert system | Net **+dollars** after you measure opportunity cost of vetoes |

If it doesn’t show up in ending wealth or drawdown, it’s a distraction.

---

## 8. Single sentence north star

**Learn a policy that turns information into more dollars over time, without going broke — proven on historical faux capital against dumb baselines.**

That’s the end goal. Architecture is subordinate to that chart.
