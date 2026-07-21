# GOAL_REBALANCE.md — Fixed-Target Rebalancing Lab

Use as Codex / Claude / Grok **`/goal`**.

**Chosen path:** Option 2 from `docs/ALIEN_GOGGLES_STEP_BACK.md`  
**Not this goal:** allocation menu search, QQQ concentration, options truth engine, live trading  

**Companions:** `prereg/PREREG_REBALANCE_V1.md`, `docs/ALIEN_GOGGLES_STEP_BACK.md`, prospective protocol in `dollarpath/prospective/protocol.py`

---

```text
/goal

══════════════════════════════════════════════════════════════════
OUTCOME
══════════════════════════════════════════════════════════════════

Build and seal-evaluate a FIXED-TARGET rebalancing lab:

1. Freeze a single strategic target mix w* (default: equal weight on
   demo universe SPY,QQQ,IWM,TLT,GLD).
2. Compare ONLY rebalance policies that try to keep the portfolio
   near w* under costs — not policies that change what w* is.
3. Use no-lookahead protocol (asof = t-1; action earns bar t).
4. Produce official multi-arm faux-$ results + leakage audit +
   terminal PASS/FAIL/REPORT status.

Primary scientific question:
  "Given a fixed diversified target, which rebalance rule best
   grows after-cost faux wealth (and/or minimizes thrash) vs
   never-rebalance and naive calendar?"

══════════════════════════════════════════════════════════════════
TASK TYPE
══════════════════════════════════════════════════════════════════

Research eng: rebalance policies, runner, CLI, tests, sealed eval.
NO live money. NO mock market prices. NO switching target mid-claim.

══════════════════════════════════════════════════════════════════
STARTING POINT
══════════════════════════════════════════════════════════════════

/Volumes/WS4TB/lvswarm
Reuse: dollarpath/env, prospective/protocol, data/price_feed, eval/metrics
Package: dollarpath/rebalance/

══════════════════════════════════════════════════════════════════
FIXED TARGET (DEFAULT LOCK)
══════════════════════════════════════════════════════════════════

universe:     ["SPY","QQQ","IWM","TLT","GLD"]
w_star:       equal weight 1/5 each (fully invested)
history:      2018-01-01 → enough for burn-in
T_start:      2020-01-02
T_end:        2024-12-31
capital:      100000 faux USD
cost_bps:     2.5 one-way (CostModel as PortfolioEnv)
seed:         42
protocol:     E1 asof=t-1; E2 earn bar t

══════════════════════════════════════════════════════════════════
ARMS (REBALANCE POLICIES ONLY)
══════════════════════════════════════════════════════════════════

R0  never        — buy w* once; never rebalance (pure drift)
R1  calendar_21  — every 21 sessions fully reset to w*
R2  calendar_63  — every 63 sessions fully reset to w*
R3  threshold_5  — rebalance to w* only if max_i |w_i - w*_i| > 0.05
R4  threshold_10 — same with band 0.10
R5  partial_0.25 — every 21 sessions: w ← w + 0.25*(w* - w)
R6  partial_0.50 — every 21 sessions: α=0.50
R7  cost_aware   — every 5 sessions: rebalance fully to w* only if
                   estimated_benefit > estimated_cost
                   (benefit proxy: 0.5 * sum |w-w*| * recent_vol * wealth
                    cost proxy: wealth * turnover * 2 * bps/1e4)
                   else no-op

Do NOT add "pick different w*" arms under this goal.

══════════════════════════════════════════════════════════════════
METRICS
══════════════════════════════════════════════════════════════════

Primary: ending_wealth on [T_start,T_end] with window-normalized
         $100k at T_start (same as DPL-1 fairness)
Co-primary: max_drawdown
Secondary: total_costs, mean_turnover, mean L1 distance to w*
           (tracking error proxy)

══════════════════════════════════════════════════════════════════
PASS RULE (SEALED)
══════════════════════════════════════════════════════════════════

PASS_REBAL if:
  (ending_wealth(best of R1..R7) > ending_wealth(R0)
   AND that winner has total_costs documented)
  AND leakage audit all true

Also REPORT ranking table of all arms (even if PASS).

FAIL_REBAL if no R1..R7 beats R0 on ending_wealth (honest:
  "under these costs, never-rebalance won").

VOID if audit fails.

Note: PASS does not require beating calendar — only beating never
(R0). Ranking among R1..R7 is the main insight deliverable.

══════════════════════════════════════════════════════════════════
GATES
══════════════════════════════════════════════════════════════════

G0  pytest existing green; create dollarpath/rebalance/
G1  TargetSpec + distance_to_target helper + tests
G2  Policies R0–R7 implemented; unit tests on synthetic drift
G3  Runner under protocol (info_slice / asof); decisions log
G4  CLI: rebalance-run --official
G5  Official sealed run T_start..T_end; audit; result_card
G6  Optional cost sweep {0,2.5,5,10,25} for R0 vs winner vs calendar_21
G7  PROGRESS + README handoff

══════════════════════════════════════════════════════════════════
DEFINITION OF DONE
══════════════════════════════════════════════════════════════════

DONE when G0–G5 and G7 complete with status PASS_REBAL or FAIL_REBAL
(not VOID), pytest green, artifacts written.

G6 recommended but not blocking.

══════════════════════════════════════════════════════════════════
NON-GOALS
══════════════════════════════════════════════════════════════════

- Changing w* using performance (that's allocation)
- Options / truth engine (Option 5) — separate goal later
- Live trading
- Claiming production-ready

══════════════════════════════════════════════════════════════════
END /goal
══════════════════════════════════════════════════════════════════
```
