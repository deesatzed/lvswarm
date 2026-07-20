"""Fetch real OHLCV closes via yfinance; cache on disk."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
import yfinance as yf

from dollarpath.data.cache import PriceCache
from dollarpath.data.validate import validate_price_panel


def _cache_key(tickers: List[str], start: str, end: str) -> str:
    uni = "_".join(sorted(tickers))
    return f"prices_{uni}_{start}_{end}"


def fetch_prices(
    tickers: List[str],
    start: str,
    end: str,
    cache_dir: str = "data_cache",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Return wide DataFrame of adjusted closes: index=date, columns=tickers.
    Uses real yfinance data; results cached as parquet + metadata.
    """
    tickers = list(tickers)
    cache = PriceCache(cache_dir)
    key = _cache_key(tickers, start, end)

    if not force_refresh:
        cached = cache.get(key)
        if cached is not None:
            # Ensure columns order
            cached = cached[tickers]
            validate_price_panel(cached, tickers)
            return cached

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )
    if raw is None or raw.empty:
        raise RuntimeError(f"yfinance returned empty data for {tickers} {start}->{end}")

    if isinstance(raw.columns, pd.MultiIndex):
        # Multi-ticker: ('Close', 'SPY') or ('Adj Close', ...)
        if "Close" in raw.columns.get_level_values(0):
            closes = raw["Close"].copy()
        elif "Adj Close" in raw.columns.get_level_values(0):
            closes = raw["Adj Close"].copy()
        else:
            raise RuntimeError(f"unexpected yfinance columns: {raw.columns}")
    else:
        # Single ticker
        col = "Close" if "Close" in raw.columns else "Adj Close"
        closes = raw[[col]].copy()
        closes.columns = [tickers[0]]

    closes = closes.sort_index()
    closes = closes[tickers]
    # Drop rows where any ticker missing (aligned calendar)
    closes = closes.dropna(how="any")
    if closes.empty:
        raise RuntimeError("no overlapping trading days after dropna")

    validate_price_panel(closes, tickers)

    meta = {
        "source": "yfinance",
        "tickers": tickers,
        "start": start,
        "end": end,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(closes)),
        "first_date": str(closes.index[0].date()),
        "last_date": str(closes.index[-1].date()),
        "note": "real market data cache; not a mock",
    }
    cache.put(key, closes, meta)
    return closes
