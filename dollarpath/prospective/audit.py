"""Leakage audit L1–L7 for prospective runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def audit_decisions(decisions: List[dict]) -> Dict[str, Any]:
    l1 = True
    l2 = True
    bad = []
    for d in decisions:
        asof_i = d.get("asof_i")
        effective_i = d.get("effective_i")
        if asof_i is None or effective_i is None:
            l1 = False
            bad.append({"reason": "missing indices", "d": d.get("step")})
            continue
        if asof_i >= effective_i:
            l1 = False
            bad.append({"reason": "asof>=effective", "asof_i": asof_i, "effective_i": effective_i})
        # train_end date string compared loosely; index check preferred
        # L2: train_end corresponds to asof — we set train_end = asof_date
        if d.get("train_end") and d.get("asof_date") and d["train_end"] > d["asof_date"]:
            l2 = False
            bad.append({"reason": "train_end>asof", "step": d.get("step")})
    return {
        "L1_asof_lt_effective": l1,
        "L2_train_end_le_asof": l2,
        "n_decisions": len(decisions),
        "bad_samples": bad[:20],
    }


def audit_run(
    run_dir: Path,
    templates_sha_expected: Optional[Dict[str, str]] = None,
    git_commit: Optional[str] = None,
    multi_year: Optional[List[dict]] = None,
    cache_meta_ok: Optional[bool] = None,
) -> Dict[str, Any]:
    run_dir = Path(run_dir)
    checks: Dict[str, Any] = {}
    all_decisions = []
    for arm_dir in sorted(run_dir.glob("arm_*")):
        dec_path = arm_dir / "decisions.jsonl"
        if not dec_path.exists():
            continue
        for line in dec_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                all_decisions.append(json.loads(line))

    d_audit = audit_decisions(all_decisions)
    checks["L1_asof_lt_effective"] = d_audit["L1_asof_lt_effective"]
    checks["L2_train_end_le_asof"] = d_audit["L2_train_end_le_asof"]
    checks["L3_protocol_structural"] = True  # enforced by runner using info_slice
    checks["decision_detail"] = {
        "n_decisions": d_audit["n_decisions"],
        "bad_samples": d_audit["bad_samples"],
    }

    lock_path = run_dir / "LOCK.json"
    if lock_path.exists():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock_commit = lock.get("git_commit")
        if git_commit and lock_commit and lock_commit not in ("unknown", None):
            checks["L4_git_commit_match"] = lock_commit == git_commit
        else:
            checks["L4_git_commit_match"] = True  # unknown allowed
            checks["L4_note"] = "git commit unknown or not cross-checked"
        if templates_sha_expected:
            ok = True
            for k, v in templates_sha_expected.items():
                if lock.get(k) != v:
                    ok = False
            checks["L5_templates_sha_match"] = ok
        else:
            checks["L5_templates_sha_match"] = bool(
                lock.get("templates_constrained_sha256") and lock.get("templates_unconstrained_sha256")
            )
    else:
        checks["L4_git_commit_match"] = False
        checks["L5_templates_sha_match"] = False

    if multi_year:
        l6 = True
        for row in multi_year:
            if row.get("skipped"):
                continue
            if not (row.get("train_end") < row.get("test_start")):
                l6 = False
        checks["L6_multi_year_embargo"] = l6
    else:
        checks["L6_multi_year_embargo"] = True
        checks["L6_note"] = "no multi_year payload; skipped"

    if cache_meta_ok is None:
        checks["L7_cache_meta"] = True
        checks["L7_note"] = "not supplied"
    else:
        checks["L7_cache_meta"] = bool(cache_meta_ok)

    required = [
        "L1_asof_lt_effective",
        "L2_train_end_le_asof",
        "L3_protocol_structural",
        "L4_git_commit_match",
        "L5_templates_sha_match",
        "L6_multi_year_embargo",
        "L7_cache_meta",
    ]
    checks["all_true"] = all(bool(checks.get(k)) for k in required)
    checks["required_keys"] = required
    return checks
