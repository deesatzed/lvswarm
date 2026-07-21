# Outside Finance — Testable Directions (After Rebalance Lab)

**Constraint:** Must be **testable** with local resources / free data / simulators that are **real mechanics** (not mock outcomes).  
**Reuse:** sealed multi-arm eval, prereg, audit-style decision logs, dual scoreboards, Pareto (cost vs quality).  
**Do not:** restart unconstrained “pick the winner” finance; don’t require live capital or paid APIs for the core claim.

---

## 1. What we can take with us (portable methodology)

| Asset from this repo | Portable to non-finance |
|---|---|
| Fixed “target” + control policies | Any setpoint control problem |
| Cost vs quality frontier | Latency/$, thrash vs fairness, tokens vs accuracy |
| No-lookahead / as-of protocol | Streaming, online systems |
| Multi-arm sealed battery | A/B of algorithms |
| Honest FAIL culture | Kill bad controllers early |
| Autobalance vocabulary | Load, roles, queues, experts |

**Alien restatement:** We built a **controller comparison lab**. Controllers don’t have to move capital; they can move jobs, tokens, messages, or attention.

---

## 2. Filter: “can we test it?”

| Test type | Allowed | Examples |
|---|---|---|
| Deterministic sim with real rules | Yes | Queues, schedulers, band policies |
| Real public datasets | Yes | Logs, Wikipedia dumps, open ML sets |
| Tiny local ML (M4 Pro 64GB) | Yes | Small MoE / routing toys |
| Existing in-workspace repos | Yes | clawswarmed, stigmergic, Agent_Pidgeon |
| Needs paid cloud / live markets | No for v1 claim | Frontier LLM training, HFT |
| Pure mock labels as “proof” | No | Fake user happiness scores |

---

## 3. Five non-finance directions (with utility + test plan)

### Option NF1 — **Compute / job autobalance** (local cluster or discrete-event sim)

**Problem:** Match workers to load without thrash (K8s HPA analogue).  
**Target:** utilization near setpoint; minimize queue delay + scale thrash + “$” (node-time).  
**Test:** Synthetic but **rule-real** arrival processes (Poisson/bursty traces from public web logs if available); compare reactive threshold vs calendar vs partial α vs cost-aware scale.  
**Reuse:** band/α, fee break-even → “start cost” break-even.  
**Utility:** Directly useful for anyone running services; same math as rebalance frontier.  
**P(sealed useful result):** **78%**  
**P(real-world utility if true):** **High**

---

### Option NF2 — **MoE / expert load balancing** (tiny local model)

**Problem:** Routers overload a few experts; dead experts waste capacity.  
**Target:** balance expert load **and** task quality (toy multi-domain classification).  
**Test:** Pure PyTorch/MLX micro-MoE on M4 Pro; metrics CV of load, accuracy, tokens/sec.  
**Reuse:** dual scoreboard (balance vs quality); ablations.  
**Utility:** Hottest technical twin of “autobalance”; research-relevant.  
**P(sealed useful result):** **62%** (toy SOTA only; not DeepSeek-scale)  
**P(real-world utility if true):** **Medium–high** (method transferable)

---

### Option NF3 — **Minority-signal / council communication** (clawswarmed)

**Problem:** Correct scarce signal dies under majority pressure.  
**Target:** maximize `GLASSGATE_LIFT`-style metric under sealed prereg.  
**Test:** Already has instrument + synthetic/live-gated paths; expand **control** (how to weight/spawn roles), not only measure.  
**Reuse:** prereg, artifacts, audit culture; LV-lite role weights as controller.  
**Utility:** High for multi-agent AI products; unique in-workspace head start.  
**P(sealed useful result):** **70%**  
**P(real-world utility if true):** **High** for agent systems

---

### Option NF4 — **Stigmergic / predictive ops** (existing stigmergic-swarm-engine)

**Problem:** Detect precursors to failure (critical slowing down) cheaper than centralized AI.  
**Target:** lead time before failure, precision, token/cost.  
**Test:** Public log datasets (e.g. BGL-style) already in that project’s story; ablations of agent types.  
**Reuse:** multi-arm eval; cost vs detection frontier.  
**Utility:** Clear ops buyer story if metrics hold.  
**P(sealed useful result):** **55%** (depends on data access/repro)  
**P(real-world utility if true):** **High** if lead time real

---

### Option NF5 — **Fair scheduling / attention allocation** (stdlib sim)

**Problem:** Multi-tenant fair share (CPU, rate limits, agent tool calls, classroom time analogue).  
**Target:** fairness (Jain index) + throughput + latency.  
**Test:** Fully local discrete-event sim; policies: equal share, DRR, threshold rebalance of quotas, partial α toward fair weights.  
**Reuse:** almost 1:1 mapping from portfolio weights → resource shares.  
**Utility:** Clean paper/demo; medium product until embedded in a real gateway.  
**P(sealed useful result):** **80%**  
**P(real-world utility if true):** **Medium** (rises if wired to Agent_Pidgeon / OpenClaw-class gates)

---

## 4. What we are *not* recommending first

| Idea | Why not first |
|---|---|
| Pure game swarmy warfare | Fun, weaker “must use” utility |
| Full LV multi-species theory paper | High scope, low immediate test payoff |
| Live multi-model OpenRouter swarms as core | Spend + confounds |
| Generic chatbot product | Not a differentiator from our lab strengths |

---

## 5. Ranking (outside finance, testable)

| Rank | Direction | Testability | Usefulness if true | Combined |
|---|---|---|---|---|
| **1** | **NF5 Fair share / quota autobalance** | Excellent | Medium→High if integrated | **Best “same lab, new domain”** |
| **2** | **NF3 Glass Gate / minority control** | Excellent (in-repo) | High for multi-agent | **Best unique asset** |
| **3** | **NF1 Job/load autobalance sim** | Excellent | High ops | **Best industry analogy** |
| **4** | **NF2 Tiny MoE load balance** | Good on M4 | High ML | **Best research brand** |
| **5** | **NF4 Stigmergic predictive ops** | Medium | High if real | Strong but data/repro heavier |

---

## 6. Recommendation (if leaving finance)

### Primary pick: **NF3 or NF5** (choose by taste)

| If you care about… | Pick |
|---|---|
| **Multi-agent AI / truth under majority pressure** | **NF3 clawswarmed control layer** |
| **Cleanest transfer of rebalance math + fastest sealed battery** | **NF5 fair quota autobalance** |
| **Ops / infra story** | **NF1** |
| **ML systems / MoE** | **NF2** |

**Single default recommendation:**  
**NF5 Fair-share autobalance lab** as the *method twin* of rebalancing (weights = resource shares; fees = migration cost; tracking = fairness error),  
**plus a thin hook to NF3** later (fair attention among agent roles so minority signals aren’t starved).

Why NF5 over staying in finance: same controller science, **new domain**, **fully testable offline**, no market narrative baggage, and a direct path to “this is useful” (rate limits, tool quotas, multi-tenant agents).

Why keep NF3 in view: you already own a **metricized** research instrument; turning measure → **control** is a high-leverage non-finance exploit.

---

## 7. What a sealed NF5 v1 would look like (sketch)

```text
Target: equal share of capacity among N tenants (or weighted SLA shares)
Drift: demand shocks change “effective” usage
Policies: never rebalance quotas | calendar | threshold | partial α | cost-aware
Cost: migration / reallocation penalty
Metrics: Jain fairness, p95 latency, thrash count, total penalty
Protocol: decisions use only past arrivals (as-of)
PASS: dual flags — fairness edge vs cost regime (same spirit as REBAL_V3)
```

---

## 8. Bottom line

| | |
|---|---|
| Leave finance? | Yes for *primary* research bet if rebalance-as-alpha is done |
| Quit entirely? | No — **controller + frontier lab** generalizes |
| Best outside-finance default | **Fair-share / quota autobalance (NF5)** |
| Best unique-repo exploit | **Glass Gate control (NF3)** |
| Best ML-systems exploit | **Tiny MoE balance (NF2)** |

*Next concrete step when ready: `GOAL_FAIRSHARE.md` or `GOAL_GLASSGATE_CONTROL.md` — not more ETF rebalance unless cash-flow sequel only.*
