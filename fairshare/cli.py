"""CLI for fairshare lab."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fairshare.battery import cost_grid, run_all
from fairshare.frontier import demand_stress_battery, multi_seed_ci, run_frontier_at_cost
from fairshare.sim import SimConfig


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def cmd_frontier(args: argparse.Namespace) -> int:
    """GOAL_FAIRSHARE_V2 official battery."""
    root = _root()
    run_id = f"fairshare_v2_{'official' if args.official else 'exploratory'}_seed_{args.seed}"
    run_dir = Path(args.artifact_root or root / "fairshare" / "artifacts") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    base = SimConfig(
        n_tenants=args.n,
        capacity=args.capacity,
        steps=args.steps,
        seed=args.seed,
        migration_cost_per_l1=args.mig_cost,
    )
    lock = {
        "run_id": run_id,
        "goal": "GOAL_FAIRSHARE_V2",
        "prereg": "prereg/PREREG_FAIRSHARE_V2.md",
        "official": bool(args.official),
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "n": base.n_tenants,
            "capacity": base.capacity,
            "steps": base.steps,
            "seed": base.seed,
            "mig_cost": base.migration_cost_per_l1,
            "n_seeds_ci": args.n_seeds,
        },
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    print("Baseline ranking + cost grid...")
    ranking = run_all(base)
    slim_rank = [{k: v for k, v in r.items() if k != "decisions"} for r in ranking]
    f0 = next(r for r in slim_rank if r["policy_id"] == "F0_never")
    dyn = [r for r in slim_rank if r["policy_id"] != "F0_never"]
    best = dyn[0]
    f7 = next(r for r in slim_rank if r["policy_id"] == "F7_cost_aware")
    f7b = next(r for r in slim_rank if r["policy_id"] == "F7b_cost_aware_v2")

    for r in ranking:
        ad = run_dir / f"arm_{r['policy_id']}"
        ad.mkdir(exist_ok=True)
        (ad / "metrics.json").write_text(
            json.dumps({k: v for k, v in r.items() if k != "decisions"}, indent=2),
            encoding="utf-8",
        )
        with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for d in r["decisions"]:
                f.write(json.dumps(d) + "\n")

    cg = cost_grid([0.0, 0.5, 1.0, 2.0, 5.0, 10.0], base)
    (run_dir / "cost_grid.json").write_text(json.dumps(cg, indent=2), encoding="utf-8")

    print("Pareto frontier at mig_cost=1...")
    fr = run_frontier_at_cost(base)
    (run_dir / "frontier_pareto.json").write_text(json.dumps(fr, indent=2), encoding="utf-8")

    print("Demand stress battery...")
    stress = demand_stress_battery(base)
    # slim decisions already not in stress
    (run_dir / "demand_stress.json").write_text(json.dumps(stress, indent=2), encoding="utf-8")

    print(f"Multi-seed CI n={args.n_seeds}...")
    seeds = list(range(args.n_seeds))
    mci = multi_seed_ci(base, seeds=seeds)
    (run_dir / "multi_seed_ci.json").write_text(json.dumps(mci, indent=2), encoding="utf-8")

    audit_ok = True
    for r in ranking:
        for d in r["decisions"]:
            if d.get("t", 0) > 0 and d.get("asof_t", -1) >= d.get("t", 0):
                audit_ok = False
    audit = {"L1_asof_lt_t": audit_ok, "all_true": audit_ok}
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    fairness_edge = best["jain_mean"] > f0["jain_mean"] + 1e-4
    f7b_improved = (
        f7b["n_rebalances"] > f7["n_rebalances"]
        or f7b["jain_mean"] > f7["jain_mean"] + 1e-4
    )
    # also count more activity in multi-seed
    f7b_improved = f7b_improved or bool(mci.get("F7b_more_active_than_F7"))

    claim = {
        "status": "SCOPED_FAIRSHARE_V2_COMPLETE" if audit_ok else "SCOPED_FAIRSHARE_V2_VOID",
        "audit_ok": audit_ok,
        "FAIRNESS_EDGE": "PASS" if fairness_edge else "FAIL",
        "COST_REGIME": "PASS" if cg["COST_REGIME_PASS"] else "FAIL",
        "LATENCY_REGRET": {
            "best_fair_id": best["policy_id"],
            "best_p95": best["p95_queue"],
            "F0_p95": f0["p95_queue"],
            "delta_p95": best["p95_queue"] - f0["p95_queue"],
        },
        "F7b_IMPROVED": bool(f7b_improved),
        "F7_vs_F7b": {
            "F7_jain": f7["jain_mean"],
            "F7b_jain": f7b["jain_mean"],
            "F7_n_rebal": f7["n_rebalances"],
            "F7b_n_rebal": f7b["n_rebalances"],
            "F7_mig": f7["migration_cost"],
            "F7b_mig": f7b["migration_cost"],
        },
        "STRESS_STABLE": stress["STRESS_STABLE"],
        "STRESS_STABLE_frac": stress["STRESS_STABLE_frac"],
        "multi_seed_ci": mci,
        "pareto_count": len(fr["pareto"]),
        "pareto_top": fr["pareto"][:10],
        "ranking_default": slim_rank,
        "run_id": run_id,
    }
    (run_dir / "claim_matrix_v2.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")

    lines = [
        f"# GOAL_FAIRSHARE_V2 — {claim['status']}",
        "",
        f"**FAIRNESS_EDGE:** {claim['FAIRNESS_EDGE']} ({best['policy_id']})",
        f"**COST_REGIME:** {claim['COST_REGIME']}",
        f"**LATENCY_REGRET:** Δp95 queue best-fair vs F0 = {claim['LATENCY_REGRET']['delta_p95']:.2f}",
        f"**F7b_IMPROVED:** {claim['F7b_IMPROVED']}",
        f"**STRESS_STABLE:** {claim['STRESS_STABLE']} (frac={claim['STRESS_STABLE_frac']:.2f})",
        "",
        "## Multi-seed (F3 − F0)",
        f"- ΔJain mean={mci['delta_jain_F3_minus_F0']['mean']:.4f} "
        f"CI90=[{mci['delta_jain_F3_minus_F0']['ci90_low']:.4f}, {mci['delta_jain_F3_minus_F0']['ci90_high']:.4f}]",
        f"- Δp95 mean={mci['delta_p95_F3_minus_F0']['mean']:.2f} "
        f"CI90=[{mci['delta_p95_F3_minus_F0']['ci90_low']:.2f}, {mci['delta_p95_F3_minus_F0']['ci90_high']:.2f}]",
        f"- F7b mean rebalances={mci['F7b_mean_n_rebalances']:.1f} vs F7={mci['F7_mean_n_rebalances']:.1f}",
        "",
        "## Ranking @ mig_cost=1",
        "",
        "| Policy | Jain | track | p95q | mig | n_rebal |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in slim_rank:
        lines.append(
            f"| {r['policy_id']} | {r['jain_mean']:.4f} | {r.get('mean_tracking_l1', 0):.4f} | "
            f"{r['p95_queue']:.1f} | {r['migration_cost']:.1f} | {r['n_rebalances']} |"
        )
    lines.extend(["", "## Pareto (top)", ""])
    for p in fr["pareto"][:8]:
        lines.append(
            f"- {p['policy_id']}: Jain={p['jain_mean']:.4f} p95q={p['p95_queue']:.1f} mig={p['migration_cost']:.1f}"
        )
    lines.extend(["", "## Limits", "- Synthetic demand; local sim only.", ""])
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: claim[k] for k in claim if k not in ("ranking_default", "pareto_top", "multi_seed_ci")}, indent=2))
    print(json.dumps(claim["multi_seed_ci"], indent=2))
    print(f"artifacts -> {run_dir}")
    return 0 if claim["status"] == "SCOPED_FAIRSHARE_V2_COMPLETE" else 3


def cmd_run(args: argparse.Namespace) -> int:
    root = _root()
    run_id = f"fairshare_{'official' if args.official else 'exploratory'}_seed_{args.seed}"
    run_dir = Path(args.artifact_root or root / "fairshare" / "artifacts") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    base = SimConfig(
        n_tenants=args.n,
        capacity=args.capacity,
        steps=args.steps,
        seed=args.seed,
        migration_cost_per_l1=args.mig_cost,
    )

    lock = {
        "run_id": run_id,
        "goal": "GOAL_FAIRSHARE",
        "prereg": "prereg/PREREG_FAIRSHARE_V1.md",
        "official": bool(args.official),
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "n_tenants": base.n_tenants,
            "capacity": base.capacity,
            "steps": base.steps,
            "seed": base.seed,
            "migration_cost_per_l1": base.migration_cost_per_l1,
            "protocol": "act at t uses usage/queue asof t-1",
        },
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    print("Running arms at default migration cost...")
    ranking = run_all(base)
    f0 = next(r for r in ranking if r["policy_id"] == "F0_never")
    dyn = [r for r in ranking if r["policy_id"] != "F0_never"]
    best = dyn[0]
    fairness_edge = best["jain_mean"] > f0["jain_mean"] + 1e-4

    # write arms
    for r in ranking:
        ad = run_dir / f"arm_{r['policy_id']}"
        ad.mkdir(exist_ok=True)
        slim = {k: v for k, v in r.items() if k != "decisions"}
        (ad / "metrics.json").write_text(json.dumps(slim, indent=2), encoding="utf-8")
        with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for d in r["decisions"]:
                f.write(json.dumps(d) + "\n")

    print("Cost grid...")
    costs = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    cg = cost_grid(costs, base)
    (run_dir / "cost_grid.json").write_text(json.dumps(cg, indent=2), encoding="utf-8")

    # audit: asof_t < t for all decisions
    audit_ok = True
    bad = 0
    for r in ranking:
        for d in r["decisions"]:
            if d.get("asof_t", -1) >= d.get("t", -1) and d.get("t", 0) > 0:
                audit_ok = False
                bad += 1
    audit = {
        "L1_asof_lt_t": audit_ok,
        "bad": bad,
        "all_true": audit_ok,
        "note": "asof_t = t-1 by construction; t=0 init has asof -1",
    }
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    slim_rank = [{k: v for k, v in r.items() if k != "decisions"} for r in ranking]
    claim = {
        "status": "SCOPED_FAIRSHARE_COMPLETE" if audit_ok else "SCOPED_FAIRSHARE_VOID",
        "audit_ok": audit_ok,
        "FAIRNESS_EDGE": "PASS" if fairness_edge else "FAIL",
        "COST_REGIME": "PASS" if cg["COST_REGIME_PASS"] else "FAIL",
        "F0_jain": f0["jain_mean"],
        "best_id": best["policy_id"],
        "best_jain": best["jain_mean"],
        "F0_p95_queue": f0["p95_queue"],
        "best_p95_queue": best["p95_queue"],
        "ranking": slim_rank,
        "run_id": run_id,
    }
    (run_dir / "claim_matrix.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")

    lines = [
        f"# GOAL_FAIRSHARE — {claim['status']}",
        "",
        f"**FAIRNESS_EDGE:** {claim['FAIRNESS_EDGE']} (best {best['policy_id']} Jain={best['jain_mean']:.4f} vs F0 {f0['jain_mean']:.4f})",
        f"**COST_REGIME:** {claim['COST_REGIME']}",
        f"**Default migration_cost_per_l1:** {base.migration_cost_per_l1}",
        "",
        "| Policy | Jain mean | track L1 | p95 queue | mig cost | n_rebal |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in slim_rank:
        lines.append(
            f"| {r['policy_id']} | {r['jain_mean']:.4f} | {r.get('mean_tracking_l1', 0):.4f} | "
            f"{r['p95_queue']:.2f} | {r['migration_cost']:.2f} | {r['n_rebalances']} |"
        )
    lines.extend(["", "## Cost grid fairness_edge", ""])
    for g in cg["grid"]:
        lines.append(
            f"- cost={g['migration_cost_per_l1']}: edge={g['fairness_edge']} best={g['best_id']} "
            f"Jain {g['best_jain']:.4f} vs F0 {g['F0_jain']:.4f}"
        )
    lines.extend(
        [
            "",
            "## Limits",
            "- Synthetic demand with real queueing mechanics (not finance).",
            "- Local sealed sim; not a production multi-tenant deploy.",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: claim[k] for k in claim if k != "ranking"}, indent=2))
    print(f"artifacts -> {run_dir}")
    return 0 if claim["status"] == "SCOPED_FAIRSHARE_COMPLETE" else 3


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="fairshare")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Official/exploratory fairshare battery")
    r.add_argument("--official", action="store_true")
    r.add_argument("--seed", type=int, default=42)
    r.add_argument("--n", type=int, default=5)
    r.add_argument("--capacity", type=float, default=100.0)
    r.add_argument("--steps", type=int, default=2000)
    r.add_argument("--mig-cost", type=float, default=1.0)
    r.add_argument("--artifact-root", default=None)
    r.set_defaults(func=cmd_run)

    fr = sub.add_parser("frontier", help="GOAL_FAIRSHARE_V2 frontier battery")
    fr.add_argument("--official", action="store_true")
    fr.add_argument("--seed", type=int, default=42)
    fr.add_argument("--n", type=int, default=5)
    fr.add_argument("--capacity", type=float, default=100.0)
    fr.add_argument("--steps", type=int, default=2000)
    fr.add_argument("--mig-cost", type=float, default=1.0)
    fr.add_argument("--n-seeds", type=int, default=20)
    fr.add_argument("--artifact-root", default=None)
    fr.set_defaults(func=cmd_frontier)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
