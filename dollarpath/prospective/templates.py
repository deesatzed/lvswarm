"""Template libraries + stable hashes for DPL-1."""

from __future__ import annotations

import hashlib
import json
from typing import List, Optional, Sequence

import numpy as np

from dollarpath.train.bandit import default_templates


def unconstrained_templates(n_assets: int, tickers: Optional[Sequence[str]] = None) -> List[np.ndarray]:
    return default_templates(n_assets, list(tickers) if tickers is not None else None)


def constrained_templates(
    n_assets: int,
    max_weight: float = 0.40,
    min_names: int = 3,
    tickers: Optional[Sequence[str]] = None,
) -> List[np.ndarray]:
    """Filter / build templates that satisfy max_weight and min_names."""
    raw = unconstrained_templates(n_assets, tickers)
    out: List[np.ndarray] = []
    for w in raw:
        w = np.asarray(w, dtype=float)
        if w.size != n_assets:
            continue
        if np.any(w < -1e-12):
            continue
        # soft project if slightly over due to float
        if w.max(initial=0.0) > max_weight + 1e-12:
            continue
        n_pos = int(np.sum(w > 1e-12))
        if n_pos < min_names:
            continue
        if w.sum() > 1.0 + 1e-9:
            continue
        out.append(w)

    # Ensure a non-empty diversified library: equal weight and equal*scale variants
    ew = np.ones(n_assets) / n_assets
    if ew.max() <= max_weight + 1e-12 and n_assets >= min_names:
        for scale in (1.0, 0.75, 0.5):
            cand = ew * scale
            if cand.max() <= max_weight + 1e-12:
                out.append(cand)

    # Simple diversified patterns for n=5
    if n_assets >= 5 and min_names <= 5:
        candidates = [
            np.array([0.2, 0.2, 0.2, 0.2, 0.2]),
            np.array([0.25, 0.25, 0.2, 0.15, 0.15]),
            np.array([0.3, 0.25, 0.2, 0.15, 0.1]),
            np.array([0.2, 0.3, 0.2, 0.15, 0.15]),
            np.array([0.15, 0.15, 0.2, 0.25, 0.25]),
            np.array([0.2, 0.2, 0.2, 0.25, 0.15]),
            np.array([0.25, 0.15, 0.15, 0.2, 0.25]),
            np.array([0.2, 0.2, 0.15, 0.2, 0.25]),
        ]
        for c in candidates:
            if c.size != n_assets:
                continue
            if c.max() <= max_weight + 1e-12 and int(np.sum(c > 1e-12)) >= min_names:
                out.append(c[:n_assets])

    # Deduplicate
    uniq: List[np.ndarray] = []
    seen = set()
    for w in out:
        key = tuple(np.round(w, 8).tolist())
        if key not in seen:
            seen.add(key)
            uniq.append(np.asarray(w, dtype=float))

    if not uniq:
        # fallback equal if n allows
        if n_assets >= min_names:
            uniq = [np.ones(n_assets) / n_assets]
        else:
            raise ValueError("cannot build constrained templates for this n_assets/min_names")
    return uniq


def templates_sha256(templates: List[np.ndarray]) -> str:
    payload = [np.round(np.asarray(t, dtype=float), 10).tolist() for t in templates]
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assert_constrained(templates: List[np.ndarray], max_weight: float = 0.40, min_names: int = 3) -> None:
    for w in templates:
        w = np.asarray(w, dtype=float)
        assert w.max(initial=0.0) <= max_weight + 1e-9, w
        assert int(np.sum(w > 1e-12)) >= min_names or float(w.sum()) < 1e-12, w
