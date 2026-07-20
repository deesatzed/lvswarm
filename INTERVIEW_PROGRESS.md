# planning --mode=interview — Progress (in progress)

**Session:** `/build` Stage 1 · role=SWE · checkpoints=stage defaults · goal=Clarify the idea  
**Source:** `predoc1.md` + prior repos under `/Volumes/WS4TB` (esp. `lvswarm/clawswarmed`, `lvswarm/Agent_Pidgeon`, stigmergic/swarmy/ASI-Evolve)

## Confirmed so far

| Item | Answer | Evidence |
|---|---|---|
| Primary product family | LV multi-agent swarm system | User selection |
| Pre-doc menu pick | Declined fixed DLV-MC / ACE / etc. | User: breakthrough methodology; examine prior work |
| Novelty arena | Training / co-evolution algorithm (user "number 2") | User notes |
| Design stance | Not pure brainstorm; ground in prior repos + pragmatic usefulness | User notes |

## Prior-repo facts (grounding)

1. **clawswarmed** — research instrument; `GLASSGATE_LIFT` measures correct-minority influence under majority pressure; no population dynamics.
2. **Agent_Pidgeon** — semantic contracts, receipts, flight recorder; no role-population control.
3. **stigmergic-swarm-engine** — pheromone substrate + decay / critical slowing down; single-substrate dynamics, not multi-species equilibrium learning.
4. **swarmy** — tactical swarm sim + sim-console; not a learning algorithm.
5. **ASI-Evolve / evolver** — single-lineage experiment evolution loops; not multi-swarm co-evolution under equilibrium control.
6. **predoc1.md** — LV→MARL mapping + creative methodologies (DLV-MC, LV-ACE, MS-LV-HSI, SLV-EM); **no code in this workspace yet**.
7. **swarm2.md** (`/Volumes/WS4TB/macwise-clean-test/swarm2.md`) — **examined this session**. Tutorial/architecture for multi-angle LLM decision swarm:
   - Orchestrator assigns *conflicting* roles (not complementary)
   - Experts run independent/parallel (no mutual visibility = anti-conformity)
   - Optional debate round (structured rebuttal after independence)
   - Devil’s advocate attacks fake consensus
   - Merge preserves disagreement as signal (not averaging)
   - Static role set per task; no population dynamics, no learning of role mix, no equilibrium, no LV

## Working thesis (NOT YET CONFIRMED — user declined MC confirm)

**Name (provisional):** Equilibrium Swarm Learning (ESL)

**Claim:** Multi-agent learning should treat role/influence counts as a dynamical system driven toward a stable multi-species equilibrium, not as static team sizes or pure competitive extinction.

**Method core:**
- Each epoch: update species influences with generalized Lotka–Volterra (competitive/mutualistic) step.
- Use influences as sampling weights / spawn rates / learning-rate gates for co-evolution.
- Optimize local policies for task reward **and** a global equilibrium utility (productivity + diversity + minority-signal survival).

**Pragmatic “why want this”:**
1. Stops agent-team monoculture (all agents copy the loudest role).
2. Gives clawswarmed-style minority truth a population-dynamics defense, not just a metric.
3. Gives orchestrators a principled auto-scaler for explorer vs executor vs critic.
4. Differs from stigmergy-only and single-lineage evolve loops.

**First falsifiable test:** On a controlled multi-role task, ESL maintains higher long-horizon utility and higher correct-minority influence than fixed-mix and winner-take-all baselines.

## Open (interview incomplete)

- Confirm / reject / narrow ESL thesis
- In-scope vs out-of-scope (LLM orchestrator vs pure MARL sim vs both)
- Stack constraints (stdlib-only like clawswarmed? PettingZoo? torchdiffeq?)
- Hardware / live-API spend rules
- Edge cases (extinction, oscillation, non-stationarity)
- Acceptance criteria / “done”
- Explicit user confirmation of requirements summary

## User Confirmation

**pending**
