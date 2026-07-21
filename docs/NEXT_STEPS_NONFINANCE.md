# Next Steps — Outside Finance (After Fairshare V2 + Glass Gate Control)

**Date:** 2026-07-21  
**Ground truth (non-finance):**

| Lab | Status | Core finding |
|---|---|---|
| **Fairshare V2** | COMPLETE | Threshold control **raises Jain fairness** (Δ≈+0.043, multi-seed CI excludes 0) but **raises p95 queue** (~+60); F7b better than inert F7; stress-stable 6/6 |
| **Glass Gate Control** | COMPLETE | Under synthetic wrong_bias + minority panels, **scarce_protect (oracle)** acc=1.0 vs equal=0.0; **dissent_boost (label-free)** acc=0.5; majority/authority fail |
| Finance rebalance/alloc | Characterized / FAIL on free alpha | Not primary path |

**Constraint:** Experiments must run on **local / free / synthetic-but-mechanistic** data. No live capital. Live LLM only if separately gated.

---

## 1. What we actually own now (portable assets)

| Asset | Reusable for |
|---|---|
| Fixed-target + drift + rebalance policies | Any quota/share/attention controller |
| Dual/triple scoreboard (quality · pain · cost) | Fairness/latency/mig; accuracy/harm/tokens |
| Sealed multi-arm batteries + prereg flags | Cross-domain science culture |
| Fairshare sim | Multi-tenant / rate-limit sandbox |
| Glass Gate panel bank + controllers | Multi-agent judgment control |
| clawswarmed ledger / A/B suite | Provenance + behavioral screening |
| Agent_Pidgeon (sibling) | Semantic gates on tool use (integrate later) |

**Alien one-liner:** We built a **controller comparison OS** for “return to target under pressure.” Finance was one substrate; fairshare and Glass Gate proved transfer.

---

## 2. Strategic posture

**Do not:** chase finance wealth alpha or expand LV swarm theory without a metric.  
**Do:** either (A) **harden non-finance labs into playbooks**, or (B) **close the gap between oracle control and deployable signals**, or (C) **port controllers to a third substrate** with a sharp external metric.

Highest leverage is **(B) then (A)** — Glass Gate’s C3 is an upper bound; without label-free lift, the story is incomplete.

---

## 3. Real experiments (faux / synthetic OK if mechanics real)

### Tier A — Highest priority

#### A1. Label-free minority detection (Glass Gate V2)

**Problem:** C3 uses `is_correct` (oracle). Deployable systems don’t have that.  
**Experiment:** Controllers using only:

- claim clustering / embedding distance (stdlib: bag-of-words Jaccard first; optional local embed later)  
- disagreement graph centrality  
- evidence-overlap scores (token overlap with evidence field)  
- length/confidence **as negative features** under wrong_bias  

**Metrics:** accuracy on wrong_bias minority cases; harm on neutral; compare to C3 ceiling and C0 floor.  
**Success:** label-free arm > equal by ≥0.15 absolute accuracy with HARM_LIMIT PASS.  
**P(useful sealed result):** **72%**

#### A2. Fairshare utility frontier (productize V2)

**Problem:** Jain PASS alone misleads (latency tax).  
**Experiment:** Utility \(U=\mathrm{Jain}-\lambda \hat{Q}-\mu \hat{C}\); map winners over \((\lambda,\mu)\); multi-seed.  
**Success:** Region map: when threshold / calendar / never each win.  
**P(useful sealed result):** **85%**

#### A3. Coupled experiment: **attention quotas on panels**

**Problem:** Fairshare and Glass Gate are still separate.  
**Experiment:** Treat agent attention mass as fairshare quotas; drift under bias cues; rebalance with F3/F7b-style rules; score Glass Gate accuracy + thrash.  
**Success:** Quota-rebalance controller beats equal under wrong_bias without oracle labels (or beats equal with dissent features only).  
**P(useful sealed result):** **55%** (integration risk) but **highest thesis payoff**

#### A4. Demand/bias process stress for Glass Gate

**Problem:** Small cell counts (4 wrong_bias minority cases in default bank).  
**Experiment:** Expand synthetic generator: more seeds, more compositions, adversarial majority sizes (1v4), stronger cue magnitudes; multi-seed.  
**Success:** C4/C5 lift CI excludes 0 or cleanly fails → kill weak controllers.  
**P(useful sealed result):** **80%**

---

### Tier B — Strong ports (third substrate)

#### B1. Job/autoscaler sim (HPA twin)

Arrival process + scale-up/down cost + p95 latency + thrash. Same policy family.  
**P(useful):** **75%** · Ops-facing.

#### B2. Tiny MoE load balance (M4 local)

Router balance CV + task accuracy; threshold rebalance of capacity/temperature.  
**P(useful):** **60%** · Research brand; not frontier MoE SOTA.

#### B3. Tool-call / rate-limit gateway (stdlib + optional Pidgin hook)

N agent tools, budgets, bursty tools; fairshare quotas; log decisions.  
**P(useful):** **65%** · Direct path to agent stacks.

#### B4. Trace-driven fairshare (public cluster traces)

Replace synthetic bursts with published stats/traces.  
**P(useful):** **50%** · Depends on trace access/format.

---

### Tier C — Methodology-only (high ROI, low drama)

#### C1. Autobalance Controller Kit extraction

Shared interface: `Target, State, Policy.act, Scoreboard, Battery, ClaimFlags`.  
Fairshare + Glass Gate + rebalance as adapters.  
**P(useful):** **90%** as engineering artifact.

#### C2. Unified decision ledger schema

`asof, old_alloc, new_alloc, l1, scores…` across labs.

#### C3. Adversarial red-team of controllers

Policies that *attack* fairness/minority (already have majority_force) as mandatory baselines in every battery.

---

## 4. Methodology enhancements (how to get better, not just “more goals”)

| Enhancement | Why |
|---|---|
| **Always dual/triple metrics** | Fairshare taught Jain≠latency; Glass Gate needs accuracy≠harm |
| **Oracle vs deployable split** | Report C3 as ceiling; primary claim on label-free arms |
| **Larger synthetic banks** | 4 cases/cell is fragile; target ≥50–100 per condition |
| **Multi-seed default** | Fairshare V2 standard; apply to Glass Gate |
| **Process stress battery** | Demand/bias generators as first-class prereg axes |
| **Utility surfaces** | Stakeholder λ,μ instead of single winner |
| **Partial observability** | Controllers without full cue flags (harder, more real) |
| **Cost in the same units as quality** | Tokens/rounds for GG; migration for fairshare |
| **No silent oracle leakage** | Static checks: controllers can’t read `is_correct` except in `oracle_*` namespace |

---

## 5. What not to do next

| Trap | Why |
|---|---|
| Restart finance wealth alpha as primary | Already characterized |
| Full LV multi-agent theory | No new metric yet |
| Live multi-model spend as first GG proof | Confounds + cost |
| Celebrate C3 oracle as deployable | Label leak |
| Merge fairshare+GG into one PASS criterion | Muddy science |

---

## 6. Recommended sequence

```text
Wave 1 (default) — GOAL_GLASSGATE_CONTROL_V2
  Expand case bank
  Label-free controllers (evidence-overlap, claim cluster, dissent graph)
  Multi-seed CIs
  Explicit oracle_* namespace for C3
  Primary claim on label-free lift only

Wave 2 — GOAL_FAIRSHARE_V3 (utility surfaces)
  (λ,μ) maps + SLA-weighted w*
  Optional: only if V2 kit extraction needs another adapter

Wave 3 — Coupling or port
  A3 attention-quotas on panels  OR  B3 tool-rate gateway
  Pick one external exploit

Wave 4 — Kit freeze
  C1 shared controller kit + methodology note
```

**If only one next goal:** **Glass Gate Control V2 (label-free)** — largest remaining gap between “interesting oracle” and “something you could ship.”

**If two (as before):** V2 Glass Gate first (harder science), Fairshare utility map second (fast productization)—or reverse if you want a quick playbook doc.

---

## 7. Probability-tinted shortlist

| Next package | P(useful sealed result) | Benefit if true |
|---|---:|---|
| **GG Control V2 label-free** | **72%** | High multi-agent utility |
| Fairshare utility/Pareto playbook polish | **85%** | High clarity, lower novelty |
| Panel×quota coupling (A3) | **55%** | Thesis glue |
| Tool-rate gateway (B3) | **65%** | Agent-ops product |
| HPA/job sim (B1) | **75%** | Ops story |
| Tiny MoE (B2) | **60%** | ML systems story |
| Controller kit extraction (C1) | **90%** | Engineering durability |

---

## 8. One-sentence north star (non-finance)

> **Build sealed controllers that defend a target allocation of scarce attention or capacity under adversarial pressure—prove them on dual metrics without oracle leakage, then port the kit.**

---

## 9. Immediate “do this” recommendation

**Primary:** `GOAL_GLASSGATE_CONTROL_V2`  
- Label-free minority protection  
- Larger synthetic bank + multi-seed  
- Oracle ceiling reported separately  
- Claim only on deployable arms  

**Secondary (parallel docs only or short follow-on):** Fairshare \((\lambda,\mu)\) utility map so F3 isn’t “always best.”

**Beneficial exploit still open:**  
Yes — **label-free minority control** and **fairness–latency operating points** are both real, testable, and not finance.
