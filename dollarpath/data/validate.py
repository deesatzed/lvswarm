"""Validate real price panels."""

from __future__ import annotations

import pandas as pd


class PriceValidationError(ValueError):
    pass


def validate_price_panel(df: pd.DataFrame, tickers: list[str]) -> None:
    if df is None or df.empty:
        raise PriceValidationError("empty price panel")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise PriceValidationError("index must be DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        raise PriceValidationError("dates not monotonic increasing")
    if df.index.has_duplicates:
        raise PriceValidationError("duplicate dates")
    missing = [t for t in tickers if t not in df.columns]
    if missing:
        raise PriceValidationError(f"missing tickers: {missing}")
    if df[tickers].isna().all().any():
        bad = [t for t in tickers if df[t].isna().all()]
        raise PriceValidationError(f"all-NaN columns: {bad}")
    if (df[tickers] <= 0).any().any():
        raise PriceValidationError("non-positive prices present")
