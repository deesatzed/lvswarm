"""DollarPath CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

import pandas as pd

from dollarpath.config import DEFAULT_UNIVERSE, RunConfig
from dollarpath.data.price_feed import fetch_prices
from dollarpath.eval.metrics import compute_metrics, write_run_artifacts
from dollarpath.eval.runner import run_policy
from dollarpath.policies.baselines import (
    CalendarRebalancePolicy,
    HoldPolicy,
    VolTargetPolicy,
)
from dollarpath.policies.pred_rule import PredRulePolicy
from dollarpath.governor.rules import GovernorConfig


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def cmd_fetch(args: argparse.Namespace) -> int:
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(_project_root() / "data_cache")
    df = fetch_prices(
        tickers=universe,
        start=args.start,
        end=args.end,
        cache_dir=cache_dir,
        force_refresh=args.force,
    )
    print(f"OK rows={len(df)} cols={list(df.columns)}")
    print(f"range={df.index[0].date()} -> {df.index[-1].date()}")
    print(f"cache_dir={cache_dir}")
    return 0


def cmd_run_baselines(args: argparse.Namespace) -> int:
    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cfg = RunConfig(
        universe=universe,
        start=args.start,
        end=args.end,
        seed=args.seed,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        cache_dir=args.cache_dir or str(root / "data_cache"),
        rebalance_every=args.rebalance_every,
    )
    prices = fetch_prices(cfg.universe, cfg.start, cfg.end, cache_dir=cfg.cache_dir)
    policies = [
        HoldPolicy(),
        CalendarRebalancePolicy(every=cfg.rebalance_every),
        VolTargetPolicy(
            lookback=cfg.vol_lookback,
            target_annual=cfg.vol_target_annual,
        ),
    ]
    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    summary = []
    for pol in policies:
        cfg.policy_id = pol.policy_id
        equity, total_costs, decisions = run_policy(
            prices,
            pol,
            start_capital=cfg.start_capital,
            cost_bps_one_way=cfg.cost_bps_one_way,
        )
        metrics = compute_metrics(equity, cfg.start_capital, total_costs, pol.policy_id, cfg.to_dict())
        run_id = f"p0_{pol.policy_id}_seed_{cfg.seed}"
        run_dir = art_root / run_id
        write_run_artifacts(
            run_dir,
            cfg.to_dict(),
            metrics,
            equity,
            decisions=decisions,
            claim="P0 complete — dollars measurable; no RL claim",
        )
        summary.append(metrics)
        print(
            f"{pol.policy_id:16s} ending={metrics['ending_wealth']:,.2f} "
            f"cagr={metrics['cagr']:.2%} maxDD={metrics['max_drawdown']:.2%} "
            f"costs={metrics['total_costs']:,.2f} -> {run_dir}"
        )

    # comparison table
    comp = {
        "seed": cfg.seed,
        "universe": cfg.universe,
        "start": cfg.start,
        "end": cfg.end,
        "policies": {m["policy_id"]: m for m in summary},
        "best_ending_wealth": max(summary, key=lambda m: m["ending_wealth"])["policy_id"],
    }
    comp_dir = art_root / f"p0_baselines_compare_seed_{cfg.seed}"
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "comparison.json").write_text(json.dumps(comp, indent=2), encoding="utf-8")
    lines = [
        "# P0 baselines comparison",
        "",
        f"Period: {cfg.start} → {cfg.end}",
        f"Universe: {cfg.universe}",
        "",
        "| Policy | Ending wealth | CAGR | Max DD | Costs |",
        "|---|---:|---:|---:|---:|",
    ]
    for m in summary:
        lines.append(
            f"| {m['policy_id']} | {m['ending_wealth']:,.2f} | {m['cagr']:.2%} | "
            f"{m['max_drawdown']:.2%} | {m['total_costs']:,.2f} |"
        )
    lines.append("")
    lines.append(f"Best ending wealth: **{comp['best_ending_wealth']}**")
    lines.append("")
    lines.append("Claim: P0 complete — dollars measurable; no RL claim.")
    (comp_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"comparison -> {comp_dir}")
    return 0


def cmd_ablate(args: argparse.Namespace) -> int:
    """P1 ablation matrix: pred on/off, governor on/off, rebalance speed high/low."""
    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cfg = RunConfig(
        universe=universe,
        start=args.start,
        end=args.end,
        seed=args.seed,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        cache_dir=args.cache_dir or str(root / "data_cache"),
    )
    prices = fetch_prices(cfg.universe, cfg.start, cfg.end, cache_dir=cfg.cache_dir)
    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")

    variants = [
        ("pred_on_gov_on_speed1", True, True, 1.0),
        ("pred_off_gov_on_speed1", False, True, 1.0),
        ("pred_on_gov_off_speed1", True, False, 1.0),
        ("pred_on_gov_on_speed025", True, True, 0.25),
        ("hold_equal_ref", None, None, None),
    ]

    results = {}
    for name, use_pred, use_gov, speed in variants:
        if name == "hold_equal_ref":
            pol = HoldPolicy()
            env_speed = 1.0
        else:
            pol = PredRulePolicy(
                every=5,
                use_prediction=bool(use_pred),
                use_governor=bool(use_gov),
                rebalance_speed=float(speed),
                governor_config=GovernorConfig(enabled=bool(use_gov)),
                policy_id=name,
            )
            # policy blends speed; env also has speed — keep env at 1, policy owns throttle
            env_speed = 1.0
        cfg.policy_id = name
        equity, total_costs, decisions = run_policy(
            prices,
            pol,
            start_capital=cfg.start_capital,
            cost_bps_one_way=cfg.cost_bps_one_way,
            rebalance_speed=env_speed,
        )
        metrics = compute_metrics(equity, cfg.start_capital, total_costs, name, cfg.to_dict())
        run_dir = art_root / f"p1_ablate_{name}_seed_{cfg.seed}"
        write_run_artifacts(
            run_dir,
            {**cfg.to_dict(), "ablation": name, "use_prediction": use_pred, "use_governor": use_gov, "speed": speed},
            metrics,
            equity,
            decisions=decisions,
            claim="P1 ablation cell — module helpfulness not claimed without comparison",
        )
        results[name] = metrics
        print(
            f"{name:28s} ending={metrics['ending_wealth']:,.2f} "
            f"cagr={metrics['cagr']:.2%} maxDD={metrics['max_drawdown']:.2%} "
            f"turn={metrics['mean_turnover']:.5f}"
        )

    # No automatic "helpful" claims — only matrix dump
    matrix = {
        "seed": cfg.seed,
        "universe": cfg.universe,
        "start": cfg.start,
        "end": cfg.end,
        "cells": {k: {
            "ending_wealth": v["ending_wealth"],
            "cagr": v["cagr"],
            "max_drawdown": v["max_drawdown"],
            "mean_turnover": v["mean_turnover"],
            "total_costs": v["total_costs"],
        } for k, v in results.items()},
        "note": "Compare cells manually; do not claim module value without lift vs controls",
    }
    out = art_root / f"p1_ablation_matrix_seed_{cfg.seed}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ablation_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")

    lines = [
        "# P1 ablation matrix",
        "",
        f"Period: {cfg.start} → {cfg.end}",
        f"Universe: {cfg.universe}",
        "",
        "| Variant | Ending wealth | CAGR | Max DD | Mean turnover | Costs |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for k, v in results.items():
        lines.append(
            f"| {k} | {v['ending_wealth']:,.2f} | {v['cagr']:.2%} | {v['max_drawdown']:.2%} | "
            f"{v['mean_turnover']:.5f} | {v['total_costs']:,.2f} |"
        )
    lines.extend([
        "",
        "Claim: **P1 complete — modules measurable; no SOTA claim.**",
        "No module is marked helpful without explicit lift vs hold_equal_ref / matched controls.",
    ])
    (out / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"matrix -> {out}")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    """P2: offline template selection on train dollars; deploy on full dev period."""
    from dollarpath.train.bandit import (
        LearnedTemplatePolicy,
        default_templates,
        offline_select_best_template,
        train_bandit_on_prices,
    )

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cfg = RunConfig(
        universe=universe,
        start=args.start,
        end=args.end,
        seed=args.seed,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        cache_dir=args.cache_dir or str(root / "data_cache"),
        policy_id="learned_offline_template",
    )
    prices = fetch_prices(cfg.universe, cfg.start, cfg.end, cache_dir=cfg.cache_dir)
    split = int(len(prices) * args.train_frac)
    split = max(split, 50)
    train_prices = prices.iloc[:split]
    eval_prices = prices.iloc[split - 1 :]

    templates = default_templates(prices.shape[1], list(prices.columns))
    best_i, train_rows = offline_select_best_template(
        train_prices,
        templates,
        start_capital=cfg.start_capital,
        cost_bps_one_way=cfg.cost_bps_one_way,
        every=args.every,
    )
    # diagnostic bandit still trained for artifacts
    bandit, _, bandit_summary = train_bandit_on_prices(
        train_prices,
        start_capital=cfg.start_capital,
        cost_bps_one_way=cfg.cost_bps_one_way,
        every=args.every,
        seed=cfg.seed,
        use_governor=False,
        mode=args.mode,
    )

    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    run_dir = art_root / f"p2_train_bandit_seed_{cfg.seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    bandit.save(run_dir / "bandit_state.json")
    (run_dir / "templates.json").write_text(
        json.dumps([t.tolist() for t in templates], indent=2), encoding="utf-8"
    )
    (run_dir / "offline_selection.json").write_text(
        json.dumps({"best_template": best_i, "train_rows": train_rows}, indent=2),
        encoding="utf-8",
    )
    (run_dir / "train_summary.json").write_text(
        json.dumps(
            {
                "method": "offline_template_selection",
                "best_template": best_i,
                "best_train_ending": train_rows[best_i]["ending_wealth"],
                "bandit_diag": {
                    "ending_wealth_train": bandit_summary.get("ending_wealth_train"),
                    "n_updates": bandit_summary.get("n_updates"),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "config.json").write_text(
        json.dumps(
            {
                **cfg.to_dict(),
                "train_frac": args.train_frac,
                "every": args.every,
                "mode": "offline_template_selection",
                "prereg": "prereg/PREREG_P2_DEV.md",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    pol = LearnedTemplatePolicy(
        templates[best_i],
        every=args.every,
        use_governor=False,
        policy_id="learned_offline_template",
    )

    # smoke on post-split
    equity, costs, decisions = run_policy(
        eval_prices if len(eval_prices) > 10 else prices,
        pol,
        start_capital=cfg.start_capital,
        cost_bps_one_way=cfg.cost_bps_one_way,
    )
    metrics = compute_metrics(
        equity, cfg.start_capital, costs, "learned_offline_smoke", cfg.to_dict()
    )
    write_run_artifacts(
        run_dir / "eval_smoke",
        cfg.to_dict(),
        metrics,
        equity,
        decisions=decisions,
        claim="P2 smoke on post-train split — not held-out SOTA",
    )

    # official full-period deploy of train-selected template
    equity_f, costs_f, dec_f = run_policy(
        prices, pol, start_capital=cfg.start_capital, cost_bps_one_way=cfg.cost_bps_one_way
    )
    metrics_f = compute_metrics(
        equity_f, cfg.start_capital, costs_f, "learned_offline_template", cfg.to_dict()
    )

    base_metrics = {}
    for base in (HoldPolicy(), CalendarRebalancePolicy(every=21), VolTargetPolicy()):
        eq_b, c_b, _ = run_policy(
            prices, base, start_capital=cfg.start_capital, cost_bps_one_way=cfg.cost_bps_one_way
        )
        base_metrics[base.policy_id] = compute_metrics(
            eq_b, cfg.start_capital, c_b, base.policy_id, cfg.to_dict()
        )

    best_base = max(base_metrics.values(), key=lambda m: m["ending_wealth"])
    beats = metrics_f["ending_wealth"] > best_base["ending_wealth"]
    metrics_f["beats_baselines"] = beats
    metrics_f["best_baseline_id"] = best_base["policy_id"]
    metrics_f["best_baseline_ending_wealth"] = best_base["ending_wealth"]
    metrics_f["selected_template"] = best_i
    metrics_f["selected_weights"] = templates[best_i].tolist()

    write_run_artifacts(
        run_dir / "eval_full_dev",
        cfg.to_dict(),
        metrics_f,
        equity_f,
        decisions=dec_f,
        claim=(
            "P2 DEV PASS — offline-selected template beats baselines on ending_wealth"
            if beats
            else "P2 DEV FAIL — offline-selected template does not beat best baseline"
        ),
    )
    comparison = {
        "learned": metrics_f,
        "baselines": base_metrics,
        "beats_all_baselines": beats,
        "primary_metric": "ending_wealth",
        "method": "offline_template_selection",
        "prereg": "prereg/PREREG_P2_DEV.md",
    }
    (run_dir / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    print(f"selected_template={best_i} weights={templates[best_i].tolist()}")
    print(f"train_best_ending={train_rows[best_i]['ending_wealth']:,.2f}")
    print(f"eval_smoke ending={metrics['ending_wealth']:,.2f}")
    print(
        f"eval_full_dev ending={metrics_f['ending_wealth']:,.2f} "
        f"best_base={best_base['policy_id']}:{best_base['ending_wealth']:,.2f} BEATS={beats}"
    )
    for k, m in base_metrics.items():
        print(f"  baseline {k:16s} {m['ending_wealth']:,.2f}")
    print(f"artifacts -> {run_dir}")
    return 0 if beats else 2


def cmd_eval_heldout(args: argparse.Namespace) -> int:
    """P3 held-out SOTA gate per prereg/PREREG_P3_HELDOUT.md."""
    from dollarpath.eval.walkforward import no_leakage_check, walk_forward
    from dollarpath.train.bandit import (
        LearnedTemplatePolicy,
        default_templates,
        offline_select_best_template,
    )

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    # full fetch then slice
    prices = fetch_prices(universe, args.start, args.end, cache_dir=cache_dir)
    train = prices.loc[args.train_start : args.train_end]
    held = prices.loc[args.held_start : args.held_end]
    if len(train) < 50 or len(held) < 20:
        print(f"insufficient bars train={len(train)} held={len(held)}", file=sys.stderr)
        return 1

    templates = default_templates(train.shape[1], list(train.columns))
    best_i, train_rows = offline_select_best_template(
        train,
        templates,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        every=args.every,
    )
    pol = LearnedTemplatePolicy(
        templates[best_i],
        every=args.every,
        use_governor=False,
        policy_id="learned_heldout",
    )

    cfg = RunConfig(
        universe=universe,
        start=args.held_start,
        end=args.held_end,
        seed=args.seed,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        policy_id="learned_heldout",
    )

    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    run_dir = art_root / f"p3_heldout_seed_{args.seed}"
    run_dir.mkdir(parents=True, exist_ok=True)

    equity, costs, decisions = run_policy(
        held, pol, start_capital=args.capital, cost_bps_one_way=args.cost_bps
    )
    learned = compute_metrics(equity, args.capital, costs, "learned_heldout", cfg.to_dict())

    base_metrics = {}
    for base in (HoldPolicy(), CalendarRebalancePolicy(every=21), VolTargetPolicy()):
        eq_b, c_b, _ = run_policy(
            held, base, start_capital=args.capital, cost_bps_one_way=args.cost_bps
        )
        base_metrics[base.policy_id] = compute_metrics(
            eq_b, args.capital, c_b, base.policy_id, cfg.to_dict()
        )

    best_wealth = max(m["ending_wealth"] for m in base_metrics.values())
    min_dd = min(m["max_drawdown"] for m in base_metrics.values())
    max_calmar = max(m["calmar"] for m in base_metrics.values())
    beats_wealth = learned["ending_wealth"] > best_wealth
    dd_ok = learned["max_drawdown"] <= min_dd * 1.20
    calmar_win = learned["calmar"] > max_calmar
    passed = bool(beats_wealth and (dd_ok or calmar_win))

    learned["beats_baselines"] = passed
    learned["beats_wealth"] = beats_wealth
    learned["dd_ok"] = dd_ok
    learned["calmar_win"] = calmar_win
    learned["selected_template"] = best_i
    learned["selected_weights"] = templates[best_i].tolist()
    learned["train_start"] = args.train_start
    learned["train_end"] = args.train_end

    claim = (
        "SCOPED_HISTORICAL_SOTA_PASS — "
        "prereg PREREG_P3_HELDOUT held-out after-cost wealth beat with risk rule"
        if passed
        else "SCOPED_HISTORICAL_SOTA_FAIL — held-out gate not met"
    )
    write_run_artifacts(
        run_dir / "heldout",
        {
            **cfg.to_dict(),
            "train_start": args.train_start,
            "train_end": args.train_end,
            "prereg": "prereg/PREREG_P3_HELDOUT.md",
        },
        learned,
        equity,
        decisions=decisions,
        claim=claim,
    )

    # walk-forward supporting
    wf = walk_forward(
        prices,
        train_bars=args.wf_train,
        test_bars=args.wf_test,
        embargo_bars=args.wf_embargo,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        every=args.every,
    )
    leak_ok = no_leakage_check(wf["windows"])
    (run_dir / "walkforward.json").write_text(json.dumps(wf, indent=2), encoding="utf-8")

    # stress: select before stress, eval during
    stress_reports = {}
    for name, s0, s1 in (
        ("covid_2020", "2020-02-15", "2020-04-15"),
        ("bear_2022", "2022-01-01", "2022-12-31"),
    ):
        pre = prices.loc[:s0]
        seg = prices.loc[s0:s1]
        if len(pre) < 50 or len(seg) < 5:
            stress_reports[name] = {"status": "skipped", "reason": "insufficient bars"}
            continue
        bi, _ = offline_select_best_template(
            pre.iloc[:-1],
            default_templates(pre.shape[1]),
            start_capital=args.capital,
            cost_bps_one_way=args.cost_bps,
            every=args.every,
        )
        spol = LearnedTemplatePolicy(
            default_templates(pre.shape[1])[bi], every=args.every, use_governor=False
        )
        eq_s, c_s, _ = run_policy(
            seg, spol, start_capital=args.capital, cost_bps_one_way=args.cost_bps
        )
        stress_reports[name] = compute_metrics(
            eq_s, args.capital, c_s, f"stress_{name}", {"start": s0, "end": s1}
        )
    (run_dir / "stress.json").write_text(json.dumps(stress_reports, indent=2), encoding="utf-8")

    summary = {
        "status": "SCOPED_HISTORICAL_SOTA_PASS" if passed else "SCOPED_HISTORICAL_SOTA_FAIL",
        "passed": passed,
        "learned": learned,
        "baselines": base_metrics,
        "walkforward_aggregate": wf.get("aggregate"),
        "walkforward_no_leakage": leak_ok,
        "stress": stress_reports,
        "prereg": "prereg/PREREG_P3_HELDOUT.md",
    }
    (run_dir / "claim_matrix.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        f"# P3 Held-out gate — {'PASS' if passed else 'FAIL'}",
        "",
        f"**Status:** `{summary['status']}`",
        f"**Prereg:** prereg/PREREG_P3_HELDOUT.md",
        f"**Train:** {args.train_start} → {args.train_end}",
        f"**Held-out:** {args.held_start} → {args.held_end}",
        f"**Selected template:** {best_i} weights={templates[best_i].tolist()}",
        "",
        "## Held-out metrics",
        "",
        "| Policy | Ending wealth | CAGR | Max DD | Calmar |",
        "|---|---:|---:|---:|---:|",
        f"| learned | {learned['ending_wealth']:,.2f} | {learned['cagr']:.2%} | {learned['max_drawdown']:.2%} | {learned['calmar']:.3f} |",
    ]
    for k, m in base_metrics.items():
        lines.append(
            f"| {k} | {m['ending_wealth']:,.2f} | {m['cagr']:.2%} | {m['max_drawdown']:.2%} | {m['calmar']:.3f} |"
        )
    lines.extend(
        [
            "",
            f"- beats_wealth: {beats_wealth}",
            f"- dd_ok (≤1.2× min baseline DD): {dd_ok}",
            f"- calmar_win: {calmar_win}",
            f"- walkforward windows: {wf['aggregate']['n_windows'] if wf.get('aggregate') else 0}",
            f"- walkforward no leakage: {leak_ok}",
            "",
            "## Limits",
            "- Historical simulation only; not live trading.",
            "- Offline template selection can concentrate (single asset).",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": summary["status"], "learned_ending": learned["ending_wealth"], "best_base": best_wealth, "passed": passed}, indent=2))
    print(f"artifacts -> {run_dir}")
    return 0 if passed else 3


def cmd_summarize(args: argparse.Namespace) -> int:
    path = Path(args.run_dir)
    metrics_path = path / "metrics.json"
    if not metrics_path.exists():
        # allow phase result cards without metrics.json
        card = path / "result_card.md"
        if card.exists():
            print(card.read_text(encoding="utf-8"))
            return 0
        print(f"missing {metrics_path}", file=sys.stderr)
        return 1
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    print(json.dumps(metrics, indent=2))
    card = path / "result_card.md"
    if card.exists():
        print("---")
        print(card.read_text(encoding="utf-8"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dollarpath", description="DollarPath CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="Fetch and cache real prices")
    f.add_argument("--universe", default="demo")
    f.add_argument("--start", default="2018-01-01")
    f.add_argument("--end", default="2024-12-31")
    f.add_argument("--cache-dir", default=None)
    f.add_argument("--force", action="store_true")
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("run-baselines", help="Run P0 baseline policies")
    b.add_argument("--universe", default="demo")
    b.add_argument("--start", default="2018-01-01")
    b.add_argument("--end", default="2024-12-31")
    b.add_argument("--seed", type=int, default=42)
    b.add_argument("--capital", type=float, default=100_000.0)
    b.add_argument("--cost-bps", type=float, default=2.5)
    b.add_argument("--rebalance-every", type=int, default=21)
    b.add_argument("--cache-dir", default=None)
    b.add_argument("--artifact-root", default=None)
    b.set_defaults(func=cmd_run_baselines)

    s = sub.add_parser("summarize", help="Print metrics for a run dir")
    s.add_argument("run_dir")
    s.set_defaults(func=cmd_summarize)

    a = sub.add_parser("ablate", help="P1 ablation matrix (pred/gov/speed)")
    a.add_argument("--universe", default="demo")
    a.add_argument("--start", default="2018-01-01")
    a.add_argument("--end", default="2024-12-31")
    a.add_argument("--seed", type=int, default=42)
    a.add_argument("--capital", type=float, default=100_000.0)
    a.add_argument("--cost-bps", type=float, default=2.5)
    a.add_argument("--cache-dir", default=None)
    a.add_argument("--artifact-root", default=None)
    a.set_defaults(func=cmd_ablate)

    t = sub.add_parser("train", help="P2 train template bandit on dollar rewards")
    t.add_argument("--universe", default="demo")
    t.add_argument("--start", default="2018-01-01")
    t.add_argument("--end", default="2024-12-31")
    t.add_argument("--seed", type=int, default=42)
    t.add_argument("--capital", type=float, default=100_000.0)
    t.add_argument("--cost-bps", type=float, default=2.5)
    t.add_argument("--train-frac", type=float, default=0.7)
    t.add_argument("--every", type=int, default=5)
    t.add_argument("--mode", choices=["ucb", "epsilon"], default="ucb")
    t.add_argument("--no-governor", action="store_true")
    t.add_argument("--cache-dir", default=None)
    t.add_argument("--artifact-root", default=None)
    t.set_defaults(func=cmd_train)

    e = sub.add_parser("eval-heldout", help="P3 held-out SOTA gate")
    e.add_argument("--universe", default="demo")
    e.add_argument("--start", default="2018-01-01", help="data fetch start")
    e.add_argument("--end", default="2024-12-31", help="data fetch end")
    e.add_argument("--train-start", default="2018-01-01")
    e.add_argument("--train-end", default="2022-12-31")
    e.add_argument("--held-start", default="2023-01-01")
    e.add_argument("--held-end", default="2024-12-31")
    e.add_argument("--seed", type=int, default=42)
    e.add_argument("--capital", type=float, default=100_000.0)
    e.add_argument("--cost-bps", type=float, default=2.5)
    e.add_argument("--every", type=int, default=5)
    e.add_argument("--wf-train", type=int, default=504)
    e.add_argument("--wf-test", type=int, default=126)
    e.add_argument("--wf-embargo", type=int, default=5)
    e.add_argument("--cache-dir", default=None)
    e.add_argument("--artifact-root", default=None)
    e.set_defaults(func=cmd_eval_heldout)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
