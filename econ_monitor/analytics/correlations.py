"""Cross-indicator correlations and divergence detection."""

from __future__ import annotations

import pandas as pd

from econ_monitor.data import cache
from econ_monitor.config.indicators import INDICATORS


def build_correlation_matrix(
    series_ids: list[str] | None = None,
    lookback_months: int = 36,
) -> pd.DataFrame:
    """Build a correlation matrix of month-over-month changes across indicators.

    Uses only monthly/quarterly series (resampled to monthly).
    """
    if series_ids is None:
        series_ids = [
            sid for sid, ind in INDICATORS.items()
            if ind.frequency in ("monthly", "quarterly")
        ]

    frames = {}
    for sid in series_ids:
        df = cache.get_observations(sid)
        if df.empty or len(df) < 6:
            continue
        # Resample to monthly end and take last value
        monthly = df["value"].resample("ME").last().dropna()
        # Use percent change for stationarity
        pct = monthly.pct_change().dropna()
        if len(pct) >= 6:
            frames[sid] = pct.tail(lookback_months)

    if len(frames) < 2:
        return pd.DataFrame()

    combined = pd.DataFrame(frames)
    return combined.corr()


def find_divergences(threshold: float = 0.6, lookback_months: int = 12) -> list[dict]:
    """Find pairs of indicators that historically correlate but are currently diverging.

    Returns list of {"pair": (id1, id2), "historical_corr": float, "recent_corr": float}
    """
    # Get long-term and short-term correlation matrices
    long_term = build_correlation_matrix(lookback_months=60)
    short_term = build_correlation_matrix(lookback_months=lookback_months)

    if long_term.empty or short_term.empty:
        return []

    common = list(set(long_term.columns) & set(short_term.columns))
    divergences = []

    for i, s1 in enumerate(common):
        for s2 in common[i + 1:]:
            hist = long_term.loc[s1, s2]
            recent = short_term.loc[s1, s2] if s2 in short_term.columns else hist

            # Flag if historically correlated (>threshold) but recently diverging
            if abs(hist) > threshold and abs(hist - recent) > 0.4:
                divergences.append({
                    "pair": (s1, s2),
                    "historical_corr": round(hist, 3),
                    "recent_corr": round(recent, 3),
                })

    return sorted(divergences, key=lambda d: abs(d["historical_corr"] - d["recent_corr"]), reverse=True)
