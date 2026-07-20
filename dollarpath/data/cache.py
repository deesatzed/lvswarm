"""Disk cache for real market data (cache ≠ mock)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd


class PriceCache:
    def __init__(self, cache_dir: str | Path = "data_cache"):
        self.root = Path(cache_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: str) -> tuple[Path, Path]:
        safe = key.replace("/", "_")
        return self.root / f"{safe}.parquet", self.root / f"{safe}.meta.json"

    def get(self, key: str) -> Optional[pd.DataFrame]:
        data_path, meta_path = self._paths(key)
        if not data_path.exists() or not meta_path.exists():
            return None
        return pd.read_parquet(data_path)

    def put(self, key: str, df: pd.DataFrame, meta: dict) -> None:
        data_path, meta_path = self._paths(key)
        df.to_parquet(data_path)
        meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    def meta(self, key: str) -> Optional[dict]:
        _, meta_path = self._paths(key)
        if not meta_path.exists():
            return None
        return json.loads(meta_path.read_text(encoding="utf-8"))
