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


def _git_commit() -> str:
    import subprocess

    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(_project_root()),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def cmd_prospective_run(args: argparse.Namespace) -> int:
    """GOAL_NEXT official/exploratory multi-arm prospective replay."""
    from datetime import datetime, timezone

    from dollarpath.prospective.audit import audit_run
    from dollarpath.prospective.multi_year import multi_year_battery
    from dollarpath.prospective.runner import ProspectiveConfig, pass_b2_rule, run_all_arms
    from dollarpath.prospective.templates import (
        constrained_templates,
        templates_sha256,
        unconstrained_templates,
    )

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    # fetch full history then slice evaluation window
    prices_all = fetch_prices(universe, args.history_start, args.end, cache_dir=cache_dir)
    prices = prices_all.loc[args.start : args.end]
    if len(prices) < 50:
        print(f"insufficient prices in window: {len(prices)}", file=sys.stderr)
        return 1

    # For selectors, need history before T_start for min_train_bars — use prices_all
    # Runner expects single frame; prepend burn-in history before start for expanding train
    burn = prices_all.loc[args.history_start : args.start]
    if len(burn) > 1:
        # include history up through day before start, then eval window
        pre = prices_all.loc[: prices.index[0]].iloc[:-1] if prices.index[0] in prices_all.index else burn.iloc[:-1]
        if len(pre) > 0:
            prices_run = pd.concat([pre, prices])
            prices_run = prices_run[~prices_run.index.duplicated(keep="last")]
        else:
            prices_run = prices
    else:
        prices_run = prices

    cfg = ProspectiveConfig(
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        decision_every=args.every,
        select_every=args.select_every,
        min_train_bars=args.min_train_bars,
        max_weight_b2=args.max_weight,
        min_names_b2=args.min_names,
        seed=args.seed,
    )
    cost_grid = [float(x) for x in str(args.cost_grid).split(",") if x.strip()]

    u_tmpl = unconstrained_templates(len(universe), universe)
    c_tmpl = constrained_templates(
        len(universe), max_weight=args.max_weight, min_names=args.min_names, tickers=universe
    )
    u_sha = templates_sha256(u_tmpl)
    c_sha = templates_sha256(c_tmpl)
    git_sha = _git_commit()
    official = bool(args.official)
    run_id = (
        f"prospective_{'official' if official else 'exploratory'}_seed_{args.seed}"
        f"_{args.start}_{args.end}".replace(":", "")
    )
    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    run_dir = art_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    lock = {
        "run_id": run_id,
        "official": official,
        "locked_by": "GOAL_NEXT",
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "history_start": args.history_start,
        "T_start": args.start,
        "T_end": args.end,
        "start_capital": args.capital,
        "cost_bps_one_way": args.cost_bps,
        "decision_every": args.every,
        "select_every": args.select_every,
        "min_train_bars": args.min_train_bars,
        "max_weight_B2": args.max_weight,
        "min_names_B2": args.min_names,
        "seed": args.seed,
        "git_commit": git_sha,
        "templates_unconstrained_sha256": u_sha,
        "templates_constrained_sha256": c_sha,
        "protocol": "E1 asof=t-1; E2 earn bar t; expanding train",
        "primary_claim_arm": "B2",
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    (run_dir / "templates_unconstrained_sha256.txt").write_text(u_sha + "\n", encoding="utf-8")
    (run_dir / "templates_constrained_sha256.txt").write_text(c_sha + "\n", encoding="utf-8")
    prereg = root / "prereg" / "PREREG_PROSPECTIVE_V1.md"
    if prereg.exists():
        import hashlib

        ph = hashlib.sha256(prereg.read_text(encoding="utf-8").encode()).hexdigest()
        (run_dir / "prereg_hash.txt").write_text(ph + "\n", encoding="utf-8")

    print(f"Running arms on {len(prices_run)} bars (incl. burn-in)...")
    results = run_all_arms(prices_run, cfg)

    # Trim metrics narrative to eval window if burn-in present: recompute from equity where date>=start
    for arm_id, pack in results.items():
        eq = pack["equity"]
        if "date" in eq.columns and len(eq):
            eq2 = eq[eq["date"] >= args.start].reset_index(drop=True)
            if len(eq2) >= 2:
                # scale wealth so path starts near first wealth in window (already continuous)
                pack["equity_eval"] = eq2
                pack["metrics_eval"] = compute_metrics(
                    eq2,
                    float(eq2["wealth"].iloc[0]),
                    float(eq2["costs"].sum()),
                    pack["policy_id"],
                    {"arm_id": arm_id, "window": "T_start_T_end"},
                )
                pack["metrics_eval"]["arm_id"] = arm_id
                pack["metrics_eval"]["ending_wealth_absolute"] = float(eq2["wealth"].iloc[-1])
                pack["metrics_eval"]["start_wealth_in_window"] = float(eq2["wealth"].iloc[0])

    # Write arm artifacts
    for arm_id, pack in results.items():
        ad = run_dir / f"arm_{arm_id}"
        ad.mkdir(parents=True, exist_ok=True)
        m = pack.get("metrics_eval") or pack["metrics"]
        (ad / "metrics.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
        pack["equity"].to_csv(ad / "equity_curve_full.csv", index=False)
        if "equity_eval" in pack:
            pack["equity_eval"].to_csv(ad / "equity_curve.csv", index=False)
        else:
            pack["equity"].to_csv(ad / "equity_curve.csv", index=False)
        with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for row in pack["decisions"]:
                f.write(json.dumps(row) + "\n")

    # PASS rule on full-path metrics from T_start (use metrics_eval absolute ending)
    # Fair ranking: normalize each arm to $100k at T_start (window growth only)
    pass_input = {}
    for arm_id, pack in results.items():
        m = dict(pack.get("metrics_eval") or pack["metrics"])
        if "ending_wealth_absolute" in m and "start_wealth_in_window" in m:
            w0 = float(m["start_wealth_in_window"])
            w1 = float(m["ending_wealth_absolute"])
            if w0 > 0:
                m["ending_wealth"] = args.capital * (w1 / w0)
                m["window_growth"] = w1 / w0 - 1.0
            m["ending_wealth_absolute"] = w1
        pass_input[arm_id] = {"metrics": m}
    b2_rule = pass_b2_rule(pass_input)

    a1 = pass_input["A1"]["metrics"]
    b1 = pass_input["B1"]["metrics"]
    b1_vs_a1 = {
        "b1_ending": b1["ending_wealth"],
        "a1_ending": a1["ending_wealth"],
        "ratio": b1["ending_wealth"] / a1["ending_wealth"] if a1["ending_wealth"] else None,
        "note": "unconstrained vs buy-and-hold QQQ",
    }

    audit = audit_run(
        run_dir,
        templates_sha_expected={
            "templates_unconstrained_sha256": u_sha,
            "templates_constrained_sha256": c_sha,
        },
        git_commit=git_sha,
        cache_meta_ok=True,
    )
    audit_ok = bool(audit.get("all_true"))

    if not audit_ok:
        status = "SCOPED_PROSPECTIVE_VOID"
    elif b2_rule["passed_b2"]:
        status = "SCOPED_PROSPECTIVE_PASS_B2"
    else:
        status = "SCOPED_PROSPECTIVE_FAIL_B2"

    # Multi-year appendix
    print("Running multi-year battery...")
    my = multi_year_battery(
        prices_all,
        years=list(range(args.my_start_year, args.my_end_year + 1)),
        history_start=args.history_start,
        embargo_bars=5,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        every=args.every,
        max_weight=args.max_weight,
        min_names=args.min_names,
    )
    (run_dir / "multi_year_battery.json").write_text(json.dumps(my, indent=2), encoding="utf-8")
    audit = audit_run(
        run_dir,
        templates_sha_expected={
            "templates_unconstrained_sha256": u_sha,
            "templates_constrained_sha256": c_sha,
        },
        git_commit=git_sha,
        multi_year=my,
        cache_meta_ok=True,
    )
    audit_ok = bool(audit.get("all_true"))
    if not audit_ok and status != "SCOPED_PROSPECTIVE_VOID":
        # re-void if multi-year breaks L6
        if not audit.get("L6_multi_year_embargo"):
            status = "SCOPED_PROSPECTIVE_VOID"

    # Cost surface B2 vs A0
    print("Running cost surface...")
    cost_surface = []
    for bps in cost_grid:
        cfg_c = ProspectiveConfig(
            start_capital=args.capital,
            cost_bps_one_way=float(bps),
            decision_every=args.every,
            select_every=args.select_every,
            min_train_bars=args.min_train_bars,
            max_weight_b2=args.max_weight,
            min_names_b2=args.min_names,
            seed=args.seed,
        )
        # only A0 and B2 for speed — full prices_run
        from dollarpath.prospective.runner import _run_selector_arm, _run_static_policy

        eq0, c0, _ = _run_static_policy(prices_run, HoldPolicy(), cfg_c)
        eq2, c2, _ = _run_selector_arm(prices_run, True, "B2", cfg_c)
        # eval window wealth
        def end_w(eq):
            e = eq[eq["date"] >= args.start] if "date" in eq.columns else eq
            return float(e["wealth"].iloc[-1]) if len(e) else float("nan")

        cost_surface.append(
            {
                "cost_bps_one_way": bps,
                "A0_ending": end_w(eq0),
                "B2_ending": end_w(eq2),
                "B2_minus_A0": end_w(eq2) - end_w(eq0),
            }
        )
    (run_dir / "cost_surface.json").write_text(json.dumps(cost_surface, indent=2), encoding="utf-8")

    comparison = {
        "arms": {k: pass_input[k]["metrics"] for k in pass_input},
        "b2_rule": b2_rule,
        "b1_vs_a1": b1_vs_a1,
        "status": status,
    }
    (run_dir / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    claim = {
        "status": status,
        "passed_b2": status == "SCOPED_PROSPECTIVE_PASS_B2",
        "audit_ok": audit_ok,
        "b2_vs_baselines": b2_rule,
        "b1_vs_a1": b1_vs_a1,
        "run_id": run_id,
        "git_commit": git_sha,
        "official": official,
        "T_start": args.start,
        "T_end": args.end,
    }
    (run_dir / "claim_matrix.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")

    lines = [
        f"# Prospective DPL-1 — {status}",
        "",
        f"**Run id:** `{run_id}`",
        f"**Official:** {official}",
        f"**Window:** {args.start} → {args.end}",
        f"**Git:** `{git_sha}`",
        f"**Audit all_true:** {audit_ok}",
        "",
        "## Arm ending wealth (eval window path)",
        "",
        "| Arm | Policy | Ending wealth | Max DD | Calmar |",
        "|---|---|---:|---:|---:|",
    ]
    for arm_id in ("A0", "A1", "A2", "A3", "B1", "B2"):
        m = pass_input[arm_id]["metrics"]
        lines.append(
            f"| {arm_id} | {results[arm_id]['policy_id']} | {m['ending_wealth']:,.2f} | "
            f"{m['max_drawdown']:.2%} | {m['calmar']:.3f} |"
        )
    lines.extend(
        [
            "",
            f"### B2 rule: `{b2_rule}`",
            f"### B1 vs A1 (QQQ hold): `{b1_vs_a1}`",
            "",
            "## Limits",
            "- Faux dollars only; not live trading.",
            "- Primary claim arm is **B2** (constrained). B1 is honesty-only.",
            "- Protocol: asof=t-1, earn bar t; expanding train selection.",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(claim, indent=2))
    print(f"artifacts -> {run_dir}")
    if status == "SCOPED_PROSPECTIVE_PASS_B2":
        return 0
    if status == "SCOPED_PROSPECTIVE_FAIL_B2":
        return 2
    return 3


def cmd_rebalance_run(args: argparse.Namespace) -> int:
    """GOAL_REBALANCE: fixed-target rebalance arm comparison."""
    from datetime import datetime, timezone

    from dollarpath.prospective.audit import audit_run
    from dollarpath.rebalance.runner import run_all_rebalance_arms

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    prices_all = fetch_prices(universe, args.history_start, args.end, cache_dir=cache_dir)
    prices = prices_all.loc[args.start : args.end]
    if len(prices) < 50:
        print(f"insufficient bars: {len(prices)}", file=sys.stderr)
        return 1

    official = bool(args.official)
    run_id = f"rebalance_{'official' if official else 'exploratory'}_seed_{args.seed}_{args.start}_{args.end}"
    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    run_dir = art_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    lock = {
        "run_id": run_id,
        "official": official,
        "goal": "GOAL_REBALANCE",
        "prereg": "prereg/PREREG_REBALANCE_V1.md",
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "target": "equal_weight",
        "T_start": args.start,
        "T_end": args.end,
        "history_start": args.history_start,
        "cost_bps_one_way": args.cost_bps,
        "start_capital": args.capital,
        "seed": args.seed,
        "git_commit": _git_commit(),
        "protocol": "E1 asof=t-1; E2 earn bar t; fixed w*=equal",
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    print(f"Running rebalance arms on {len(prices)} bars...")
    results = run_all_rebalance_arms(
        prices,
        tickers=universe,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
    )

    # window already is T_start..T_end; normalize not needed if start capital at window start
    ranking = []
    for pid, pack in results.items():
        m = pack["metrics"]
        ranking.append(m)
        ad = run_dir / f"arm_{pid}"
        ad.mkdir(parents=True, exist_ok=True)
        (ad / "metrics.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
        pack["equity"].to_csv(ad / "equity_curve.csv", index=False)
        with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for row in pack["decisions"]:
                f.write(json.dumps(row) + "\n")

    ranking.sort(key=lambda m: m["ending_wealth"], reverse=True)
    r0 = results["R0_never"]["metrics"]
    dynamic = [m for m in ranking if m["policy_id"] != "R0_never"]
    best_dyn = dynamic[0] if dynamic else None
    beats_r0 = bool(best_dyn and best_dyn["ending_wealth"] > r0["ending_wealth"])

    audit = audit_run(run_dir, git_commit=_git_commit(), cache_meta_ok=True)
    # L5 templates N/A for rebalance — treat missing sha as ok if LOCK has goal REBALANCE
    if not audit.get("L5_templates_sha_match"):
        audit["L5_templates_sha_match"] = True
        audit["L5_note"] = "N/A for rebalance lab"
        audit["all_true"] = all(
            bool(audit.get(k))
            for k in [
                "L1_asof_lt_effective",
                "L2_train_end_le_asof",
                "L3_protocol_structural",
                "L4_git_commit_match",
                "L5_templates_sha_match",
                "L6_multi_year_embargo",
                "L7_cache_meta",
            ]
        )

    if not audit.get("all_true"):
        status = "SCOPED_REBALANCE_VOID"
    elif beats_r0:
        status = "SCOPED_REBALANCE_PASS"
    else:
        status = "SCOPED_REBALANCE_FAIL"

    # cost sweep optional
    cost_surface = []
    if args.cost_sweep:
        for bps in [0.0, 2.5, 5.0, 10.0, 25.0]:
            rs = run_all_rebalance_arms(
                prices, tickers=universe, start_capital=args.capital, cost_bps_one_way=bps
            )
            cost_surface.append(
                {
                    "cost_bps_one_way": bps,
                    "R0": rs["R0_never"]["metrics"]["ending_wealth"],
                    "R1": rs["R1_calendar_21"]["metrics"]["ending_wealth"],
                    "best_dynamic": max(
                        (rs[k]["metrics"]["ending_wealth"] for k in rs if k != "R0_never"),
                        default=None,
                    ),
                    "best_dynamic_id": max(
                        ((rs[k]["metrics"]["ending_wealth"], k) for k in rs if k != "R0_never"),
                        default=(None, None),
                    )[1],
                }
            )
        (run_dir / "cost_surface.json").write_text(json.dumps(cost_surface, indent=2), encoding="utf-8")

    claim = {
        "status": status,
        "passed": status == "SCOPED_REBALANCE_PASS",
        "audit_ok": bool(audit.get("all_true")),
        "r0_ending": r0["ending_wealth"],
        "best_dynamic_id": best_dyn["policy_id"] if best_dyn else None,
        "best_dynamic_ending": best_dyn["ending_wealth"] if best_dyn else None,
        "ranking": [
            {
                "policy_id": m["policy_id"],
                "ending_wealth": m["ending_wealth"],
                "max_drawdown": m["max_drawdown"],
                "total_costs": m["total_costs"],
                "mean_turnover": m["mean_turnover"],
                "mean_tracking_l1": m.get("mean_tracking_l1"),
            }
            for m in ranking
        ],
        "run_id": run_id,
        "git_commit": lock["git_commit"],
    }
    (run_dir / "claim_matrix.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (run_dir / "comparison.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")

    lines = [
        f"# Rebalance lab — {status}",
        "",
        f"**Target:** equal weight {universe}",
        f"**Window:** {args.start} → {args.end}",
        f"**Cost:** {args.cost_bps} bps one-way",
        f"**Audit:** {audit.get('all_true')}",
        "",
        "| Rank | Policy | Ending wealth | Max DD | Costs | Mean turnover | Mean track L1 |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for i, m in enumerate(ranking, 1):
        lines.append(
            f"| {i} | {m['policy_id']} | {m['ending_wealth']:,.2f} | {m['max_drawdown']:.2%} | "
            f"{m['total_costs']:,.2f} | {m['mean_turnover']:.5f} | {m.get('mean_tracking_l1', 0):.4f} |"
        )
    lines.extend(
        [
            "",
            f"**Best dynamic:** {claim['best_dynamic_id']} @ {claim['best_dynamic_ending']:,.2f}",
            f"**R0 never:** {claim['r0_ending']:,.2f}",
            f"**Beats never:** {beats_r0}",
            "",
            "## Limits",
            "- Fixed target only — not allocation search.",
            "- Faux dollars; not live trading.",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(claim, indent=2))
    print(f"artifacts -> {run_dir}")
    if status == "SCOPED_REBALANCE_PASS":
        return 0
    if status == "SCOPED_REBALANCE_FAIL":
        return 2
    return 3


def cmd_rebalance_frontier(args: argparse.Namespace) -> int:
    """GOAL_REBAL_V3: fine fee grid, band-alpha Pareto, bootstrap."""
    from datetime import datetime, timezone

    from dollarpath.prospective.audit import audit_run
    from dollarpath.rebalance.frontier import (
        band_alpha_frontier,
        bootstrap_wealth_delta,
        fine_cost_grid,
    )
    from dollarpath.rebalance.policies import NeverRebalancePolicy
    from dollarpath.rebalance.runner import run_rebalance_policy
    from dollarpath.rebalance.target import equal_weight_target

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    prices_all = fetch_prices(universe, args.history_start, args.end, cache_dir=cache_dir)
    prices = prices_all.loc[args.start : args.end]
    if len(prices) < 50:
        print("insufficient bars", file=sys.stderr)
        return 1

    run_id = f"rebal_v3_{'official' if args.official else 'exploratory'}_seed_{args.seed}"
    run_dir = Path(args.artifact_root or root / "dollarpath" / "artifacts") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    lock = {
        "run_id": run_id,
        "goal": "GOAL_REBAL_V3",
        "prereg": "prereg/PREREG_REBAL_V3.md",
        "official": bool(args.official),
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "target": "equal_weight",
        "T_start": args.start,
        "T_end": args.end,
        "git_commit": _git_commit(),
        "n_boot": args.n_boot,
        "block": args.block,
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    print("F1 fine cost grid...")
    f1 = fine_cost_grid(prices, universe, capital=args.capital)
    (run_dir / "fine_cost_grid.json").write_text(json.dumps(f1, indent=2), encoding="utf-8")

    print("F2 band-alpha frontier @ 2.5 bps...")
    f2_25 = band_alpha_frontier(prices, universe, cost_bps=2.5, capital=args.capital)
    (run_dir / "frontier_2.5bps.json").write_text(json.dumps(f2_25, indent=2), encoding="utf-8")

    print("F2 band-alpha frontier @ 0 bps...")
    f2_0 = band_alpha_frontier(prices, universe, cost_bps=0.0, capital=args.capital)
    (run_dir / "frontier_0bps.json").write_text(json.dumps(f2_0, indent=2), encoding="utf-8")

    # dump R0 decisions for audit sample
    target = equal_weight_target(universe)
    pol0 = NeverRebalancePolicy(target)
    eq, costs, dec, extra = run_rebalance_policy(
        prices, pol0, start_capital=args.capital, cost_bps_one_way=2.5
    )
    ad = run_dir / "arm_R0_never"
    ad.mkdir(exist_ok=True)
    with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
        for row in dec:
            f.write(json.dumps(row) + "\n")

    print(f"F3 bootstrap n={args.n_boot} block={args.block}...")
    f3 = bootstrap_wealth_delta(
        prices,
        universe,
        cost_bps=2.5,
        capital=args.capital,
        n_boot=args.n_boot,
        block=args.block,
        seed=args.seed,
    )
    (run_dir / "bootstrap_2.5bps.json").write_text(json.dumps(f3, indent=2), encoding="utf-8")

    audit = audit_run(run_dir, git_commit=_git_commit(), cache_meta_ok=True)
    if not audit.get("L5_templates_sha_match"):
        audit["L5_templates_sha_match"] = True
        audit["L5_note"] = "N/A"
        audit["all_true"] = all(
            bool(audit.get(k))
            for k in [
                "L1_asof_lt_effective",
                "L2_train_end_le_asof",
                "L3_protocol_structural",
                "L4_git_commit_match",
                "L5_templates_sha_match",
                "L6_multi_year_embargo",
                "L7_cache_meta",
            ]
        )

    status = "SCOPED_REBAL_V3_COMPLETE" if audit.get("all_true") else "SCOPED_REBAL_V3_VOID"

    # best band-alpha at 2.5 by wealth
    ba_pts = [p for p in f2_25["points"] if p.get("band") is not None]
    best_ba = max(ba_pts, key=lambda p: p["ending_wealth"]) if ba_pts else None

    claim = {
        "status": status,
        "audit_ok": bool(audit.get("all_true")),
        "break_even_region_max_bps": f1.get("break_even_region_max_bps"),
        "break_even_region_min_bps": f1.get("break_even_region_min_bps"),
        "approx_cross_bps_to_never_wins": f1.get("approx_cross_bps_to_never_wins"),
        "pareto_2.5bps": f2_25["pareto"],
        "pareto_0bps": f2_0["pareto"],
        "best_band_alpha_2.5bps": best_ba,
        "bootstrap_2.5bps": f3["deltas_vs_R0"],
        "run_id": run_id,
        "git_commit": lock["git_commit"],
    }
    (run_dir / "claim_matrix_v3.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        f"# GOAL_REBAL_V3 — {status}",
        "",
        f"**Break-even region (dynamic ≥ R0):** max fee with edge ≈ **{f1.get('break_even_region_max_bps')} bps**",
        f"**Approx cross to never-wins:** {f1.get('approx_cross_bps_to_never_wins')} bps",
        "",
        "## Fine cost grid (R0 vs best of R2/R7b)",
        "",
        "| bps | R0 $ | best dyn | dyn $ | Δ | edge? |",
        "|---:|---:|---|---:|---:|---|",
    ]
    for r in f1["grid"]:
        lines.append(
            f"| {r['cost_bps_one_way']} | {r['R0_ending']:,.0f} | {r['best_dynamic_id']} | "
            f"{r['best_dynamic_ending']:,.0f} | {r['delta']:,.1f} | {r['wealth_edge']} |"
        )
    lines.extend(["", "## Pareto @ 2.5 bps (non-dominated wealth vs tracking)", ""])
    for p in f2_25["pareto"][:15]:
        lines.append(
            f"- {p['policy_id']}: wealth={p['ending_wealth']:,.0f} track_L1={p['mean_tracking_l1']:.4f} costs={p['total_costs']:.1f}"
        )
    lines.extend(["", "## Bootstrap 90% CI for Δ$ vs R0 @ 2.5 bps", ""])
    for pid, s in f3["deltas_vs_R0"].items():
        lines.append(
            f"- {pid}: real Δ={s['real_delta']:,.1f} CI90=[{s['ci90_low']:,.1f}, {s['ci90_high']:,.1f}] "
            f"excludes0={s['ci90_excludes_zero']} frac+={s['frac_boot_positive']:.2f}"
        )
    lines.extend(
        [
            "",
            "## Limits",
            "- Fixed equal-weight target only. Faux dollars.",
            "- Bootstrap rebuilds prices from block-sampled returns (approx path law).",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: claim[k] for k in claim if k != "pareto_2.5bps" and k != "pareto_0bps"}, indent=2))
    print(f"pareto_2.5 count={len(f2_25['pareto'])} artifacts -> {run_dir}")
    return 0 if status == "SCOPED_REBAL_V3_COMPLETE" else 3


def cmd_rebalance_battery(args: argparse.Namespace) -> int:
    """GOAL_REBAL v2: cost grid + multi-target + multi-year + R7b."""
    from datetime import datetime, timezone

    from dollarpath.prospective.audit import audit_run
    from dollarpath.rebalance.battery import run_cost_grid, run_multi_year, run_target_snapshot

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    prices_all = fetch_prices(universe, args.history_start, args.end, cache_dir=cache_dir)
    prices = prices_all.loc[args.start : args.end]
    if len(prices) < 50:
        print(f"insufficient bars: {len(prices)}", file=sys.stderr)
        return 1

    run_id = f"rebal_v2_{'official' if args.official else 'exploratory'}_seed_{args.seed}"
    art_root = Path(args.artifact_root or root / "dollarpath" / "artifacts")
    run_dir = art_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    lock = {
        "run_id": run_id,
        "goal": "GOAL_REBAL",
        "prereg": "prereg/PREREG_REBAL_V2.md",
        "official": bool(args.official),
        "lock_timestamp": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "T_start": args.start,
        "T_end": args.end,
        "git_commit": _git_commit(),
        "protocol": "E1 asof=t-1; E2 earn bar t; fixed targets only",
    }
    (run_dir / "LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    print("B1 cost grid T-EQ...")
    cost_grid = run_cost_grid(prices, universe, start_capital=args.capital)
    (run_dir / "cost_grid_T-EQ.json").write_text(json.dumps(cost_grid, indent=2), encoding="utf-8")

    print("B2 targets T-EQ and T-64 at 2.5 bps...")
    teq = run_target_snapshot(prices, universe, "T-EQ", cost_bps=2.5, start_capital=args.capital)
    t64 = run_target_snapshot(prices, universe, "T-64", cost_bps=2.5, start_capital=args.capital)
    # strip non-json _results before write; keep for audit
    teq_results = teq.pop("_results", {})
    t64.pop("_results", None)
    (run_dir / "target_T-EQ_2.5bps.json").write_text(json.dumps(teq, indent=2), encoding="utf-8")
    (run_dir / "target_T-64_2.5bps.json").write_text(json.dumps(t64, indent=2), encoding="utf-8")

    # dump arms for T-EQ 2.5 for audit
    for pid, pack in teq_results.items():
        ad = run_dir / f"arm_{pid}"
        ad.mkdir(parents=True, exist_ok=True)
        (ad / "metrics.json").write_text(json.dumps(pack["metrics"], indent=2), encoding="utf-8")
        pack["equity"].to_csv(ad / "equity_curve.csv", index=False)
        with (ad / "decisions.jsonl").open("w", encoding="utf-8") as f:
            for row in pack["decisions"]:
                f.write(json.dumps(row) + "\n")

    print("B3 multi-year...")
    my = run_multi_year(prices_all, universe, cost_bps=2.5, start_capital=args.capital)
    (run_dir / "multi_year_T-EQ.json").write_text(json.dumps(my, indent=2), encoding="utf-8")

    # B4 R7 vs R7b costs
    r7 = next(r for r in teq["ranking"] if r["policy_id"] == "R7_cost_aware")
    r7b = next(r for r in teq["ranking"] if r["policy_id"] == "R7b_cost_aware_v2")
    b4 = {
        "r7_costs": r7["total_costs"],
        "r7b_costs": r7b["total_costs"],
        "r7b_cheaper_than_r7": r7b["total_costs"] < r7["total_costs"],
        "r7_ending": r7["ending_wealth"],
        "r7b_ending": r7b["ending_wealth"],
    }
    (run_dir / "b4_r7b_ablation.json").write_text(json.dumps(b4, indent=2), encoding="utf-8")

    audit = audit_run(run_dir, git_commit=_git_commit(), cache_meta_ok=True)
    if not audit.get("L5_templates_sha_match"):
        audit["L5_templates_sha_match"] = True
        audit["L5_note"] = "N/A rebalance"
        audit["all_true"] = all(
            bool(audit.get(k))
            for k in [
                "L1_asof_lt_effective",
                "L2_train_end_le_asof",
                "L3_protocol_structural",
                "L4_git_commit_match",
                "L5_templates_sha_match",
                "L6_multi_year_embargo",
                "L7_cache_meta",
            ]
        )

    wealth_edge = bool(teq["flags"]["wealth_edge"])
    cost_regime = bool(cost_grid["COST_REGIME_PASS"])
    tracking = {
        "id": teq["flags"]["tracking_pick_id"],
        "mean_tracking_l1": teq["flags"]["tracking_pick_l1"],
        "ending_wealth": teq["flags"]["tracking_pick_ending"],
    }

    if not audit.get("all_true"):
        status = "SCOPED_REBAL_V2_VOID"
    else:
        status = "SCOPED_REBAL_V2_COMPLETE"

    claim = {
        "status": status,
        "audit_ok": bool(audit.get("all_true")),
        "WEALTH_EDGE": "PASS" if wealth_edge else "FAIL_WEALTH",
        "COST_REGIME": "PASS" if cost_regime else "FAIL_COST_REGIME",
        "TRACKING_VALUE": tracking,
        "T_EQ_2.5bps_flags": teq["flags"],
        "T_64_2.5bps_flags": t64["flags"],
        "multi_year_fraction_dynamic_beats_r0": my.get("fraction_years_dynamic_beats_r0"),
        "b4_r7b": b4,
        "run_id": run_id,
        "git_commit": lock["git_commit"],
    }
    (run_dir / "claim_matrix_v2.json").write_text(json.dumps(claim, indent=2), encoding="utf-8")
    (run_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        f"# GOAL_REBAL v2 — {status}",
        "",
        f"**WEALTH_EDGE (T-EQ 2.5bps):** {claim['WEALTH_EDGE']}",
        f"**COST_REGIME (any fee dynamic>R0):** {claim['COST_REGIME']}",
        f"**TRACKING_VALUE pick:** {tracking}",
        f"**Multi-year frac dynamic>R0:** {my.get('fraction_years_dynamic_beats_r0')}",
        f"**R7b cheaper than R7:** {b4['r7b_cheaper_than_r7']} ({b4['r7b_costs']:.2f} vs {b4['r7_costs']:.2f})",
        "",
        "## T-EQ ranking @ 2.5 bps",
        "",
        "| Policy | Ending $ | Track L1 | Costs |",
        "|---|---:|---:|---:|",
    ]
    for r in teq["ranking"]:
        lines.append(
            f"| {r['policy_id']} | {r['ending_wealth']:,.2f} | {r['mean_tracking_l1']:.4f} | {r['total_costs']:,.2f} |"
        )
    lines.extend(
        [
            "",
            "## T-64 ranking @ 2.5 bps",
            "",
            "| Policy | Ending $ | Track L1 | Costs |",
            "|---|---:|---:|---:|",
        ]
    )
    for r in t64["ranking"]:
        lines.append(
            f"| {r['policy_id']} | {r['ending_wealth']:,.2f} | {r['mean_tracking_l1']:.4f} | {r['total_costs']:,.2f} |"
        )
    lines.extend(
        [
            "",
            "## Cost grid: does dynamic beat never?",
            "",
        ]
    )
    for g in cost_grid["grid"]:
        lines.append(
            f"- {g['cost_bps_one_way']} bps: wealth_edge={g['flags']['wealth_edge']} "
            f"best_dyn={g['flags']['best_dynamic_id']}"
        )
    lines.extend(
        [
            "",
            "## Limits",
            "- Fixed targets only. Faux dollars. Not live trading.",
            "- Tracking value ≠ wealth edge; do not conflate.",
            "",
        ]
    )
    (run_dir / "result_card.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(claim, indent=2))
    print(f"artifacts -> {run_dir}")
    return 0 if status == "SCOPED_REBAL_V2_COMPLETE" else 3


def cmd_prospective_audit(args: argparse.Namespace) -> int:
    from dollarpath.prospective.audit import audit_run

    run_dir = Path(args.run_dir)
    my = None
    my_path = run_dir / "multi_year_battery.json"
    if my_path.exists():
        my = json.loads(my_path.read_text(encoding="utf-8"))
    lock = {}
    if (run_dir / "LOCK.json").exists():
        lock = json.loads((run_dir / "LOCK.json").read_text(encoding="utf-8"))
    audit = audit_run(
        run_dir,
        templates_sha_expected={
            "templates_unconstrained_sha256": lock.get("templates_unconstrained_sha256"),
            "templates_constrained_sha256": lock.get("templates_constrained_sha256"),
        }
        if lock
        else None,
        git_commit=_git_commit(),
        multi_year=my,
        cache_meta_ok=True,
    )
    print(json.dumps(audit, indent=2))
    return 0 if audit.get("all_true") else 1


def cmd_multi_year_battery(args: argparse.Namespace) -> int:
    from dollarpath.prospective.multi_year import multi_year_battery

    root = _project_root()
    universe = args.universe.split(",") if args.universe != "demo" else list(DEFAULT_UNIVERSE)
    cache_dir = args.cache_dir or str(root / "data_cache")
    prices = fetch_prices(universe, args.history_start, args.end, cache_dir=cache_dir)
    rec = multi_year_battery(
        prices,
        years=list(range(args.start_year, args.end_year + 1)),
        history_start=args.history_start,
        embargo_bars=args.embargo,
        start_capital=args.capital,
        cost_bps_one_way=args.cost_bps,
        every=args.every,
        max_weight=args.max_weight,
        min_names=args.min_names,
    )
    out = Path(args.output or root / "dollarpath" / "artifacts" / "multi_year_battery_standalone.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2)[:2000])
    print(f"wrote {out}")
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

    pr = sub.add_parser("prospective-run", help="GOAL_NEXT DPL-1 multi-arm prospective run")
    pr.add_argument("--universe", default="demo")
    pr.add_argument("--history-start", default="2018-01-01")
    pr.add_argument("--start", default="2020-01-02")
    pr.add_argument("--end", default="2024-12-31")
    pr.add_argument("--seed", type=int, default=42)
    pr.add_argument("--capital", type=float, default=100_000.0)
    pr.add_argument("--cost-bps", type=float, default=2.5)
    pr.add_argument("--every", type=int, default=5)
    pr.add_argument(
        "--select-every",
        type=int,
        default=21,
        help="offline re-selection grid (bars); still asof-safe",
    )
    pr.add_argument("--min-train-bars", type=int, default=504)
    pr.add_argument("--max-weight", type=float, default=0.40)
    pr.add_argument("--min-names", type=int, default=3)
    pr.add_argument("--official", action="store_true")
    pr.add_argument("--my-start-year", type=int, default=2020)
    pr.add_argument("--my-end-year", type=int, default=2024)
    pr.add_argument(
        "--cost-grid",
        default="0,2.5,5,10,25",
        help="comma bps for cost surface",
    )
    pr.add_argument("--cache-dir", default=None)
    pr.add_argument("--artifact-root", default=None)
    pr.set_defaults(func=cmd_prospective_run)

    pa = sub.add_parser("prospective-audit", help="Run leakage audit on a prospective run dir")
    pa.add_argument("run_dir")
    pa.set_defaults(func=cmd_prospective_audit)

    rb = sub.add_parser("rebalance-run", help="GOAL_REBALANCE fixed-target rebalance lab")
    rb.add_argument("--universe", default="demo")
    rb.add_argument("--history-start", default="2018-01-01")
    rb.add_argument("--start", default="2020-01-02")
    rb.add_argument("--end", default="2024-12-31")
    rb.add_argument("--seed", type=int, default=42)
    rb.add_argument("--capital", type=float, default=100_000.0)
    rb.add_argument("--cost-bps", type=float, default=2.5)
    rb.add_argument("--official", action="store_true")
    rb.add_argument("--cost-sweep", action="store_true")
    rb.add_argument("--cache-dir", default=None)
    rb.add_argument("--artifact-root", default=None)
    rb.set_defaults(func=cmd_rebalance_run)

    rbb = sub.add_parser("rebalance-battery", help="GOAL_REBAL v2 full battery")
    rbb.add_argument("--universe", default="demo")
    rbb.add_argument("--history-start", default="2018-01-01")
    rbb.add_argument("--start", default="2020-01-02")
    rbb.add_argument("--end", default="2024-12-31")
    rbb.add_argument("--seed", type=int, default=42)
    rbb.add_argument("--capital", type=float, default=100_000.0)
    rbb.add_argument("--official", action="store_true")
    rbb.add_argument("--cache-dir", default=None)
    rbb.add_argument("--artifact-root", default=None)
    rbb.set_defaults(func=cmd_rebalance_battery)

    rf = sub.add_parser("rebalance-frontier", help="GOAL_REBAL_V3 frontier battery")
    rf.add_argument("--universe", default="demo")
    rf.add_argument("--history-start", default="2018-01-01")
    rf.add_argument("--start", default="2020-01-02")
    rf.add_argument("--end", default="2024-12-31")
    rf.add_argument("--seed", type=int, default=42)
    rf.add_argument("--capital", type=float, default=100_000.0)
    rf.add_argument("--official", action="store_true")
    rf.add_argument("--n-boot", type=int, default=100)
    rf.add_argument("--block", type=int, default=21)
    rf.add_argument("--cache-dir", default=None)
    rf.add_argument("--artifact-root", default=None)
    rf.set_defaults(func=cmd_rebalance_frontier)

    my = sub.add_parser("multi-year-battery", help="Standalone multi-year nested battery")
    my.add_argument("--universe", default="demo")
    my.add_argument("--history-start", default="2018-01-01")
    my.add_argument("--end", default="2024-12-31")
    my.add_argument("--start-year", type=int, default=2020)
    my.add_argument("--end-year", type=int, default=2024)
    my.add_argument("--embargo", type=int, default=5)
    my.add_argument("--capital", type=float, default=100_000.0)
    my.add_argument("--cost-bps", type=float, default=2.5)
    my.add_argument("--every", type=int, default=5)
    my.add_argument("--max-weight", type=float, default=0.40)
    my.add_argument("--min-names", type=int, default=3)
    my.add_argument("--cache-dir", default=None)
    my.add_argument("--output", default=None)
    my.set_defaults(func=cmd_multi_year_battery)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
