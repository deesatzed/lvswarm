# GOAL_GLASSGATE_CONTROL — COMPLETE

**Status:** `SCOPED_GLASSGATE_CONTROL_COMPLETE`  
**Command:** `python3 -m broadcast_alpha run-glassgate-control --seed 42`  
**Tests:** 4 unittest OK  
**Live LLM:** none  

## Flags

| Flag | Result |
|---|---|
| CONTROL_LIFT | **PASS** (Δacc = +1.0 for C3 vs equal on wrong_bias minority panels) |
| HARM_LIMIT | **PASS** (protect controllers do not tank neutral below equal − 0.05) |

## Wrong-bias + one-correct-two-wrong (accuracy)

| Controller | Acc | Notes |
|---|---:|---|
| **C3 scarce_protect** | **1.00** | Boosts numerical minority using **correctness labels** (oracle upper bound) |
| **C4 dissent_boost** | **0.50** | Boosts non-modal **claim text** (no label leak) |
| C0 equal | 0.00 | Bias pressure captures selection |
| C1 majority_force | 0.00 | Amplifies wrong majority |
| C2 authority_boost | 0.00 | Amplifies wrong authority cues |
| C5 threshold_rebalance | 0.00 | Did not overcome bias in this scoring model |
| C6 fairshare_pull | 0.00 | Pull-to-equal too weak under cue boosts |

## Interpretation

1. **Control can preserve minority signal** when the controller knows/protects the scarce side (oracle C3).  
2. **Label-free dissent boost helps somewhat** (0.5) but is not perfect.  
3. Equal / majority / authority controllers **fail** under wrong_bias — matches the Glass Gate thesis.  
4. Synthetic sealed screening only — not live model proof, not JLENS.

## Artifacts

`clawswarmed/artifacts/glassgate_control_seed_42/`
