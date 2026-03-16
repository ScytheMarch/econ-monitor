"""Significance analysis for recent economic data changes.

Computes how meaningful a new reading is relative to historical context:
- Percentile rank within recent history
- Standard deviation move
- Comparison to trailing averages
- Directional streak analysis
- Economic interpretation
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from econ_monitor.analytics.transforms import (
    apply_transform, z_score, latest_z_score, moving_average,
)


def compute_significance(
    raw_series: pd.Series,
    transform: str,
    frequency: str,
    higher_is: str,
) -> dict:
    """Compute a full significance analysis for the latest data point.

    Args:
        raw_series: Raw values with DatetimeIndex
        transform: The indicator's transform type (yoy_pct, level, etc.)
        frequency: Data frequency (monthly, weekly, etc.)
        higher_is: Semantic direction (inflationary, expansionary, etc.)

    Returns dict with:
        - magnitude: "small" | "moderate" | "large" | "extreme"
        - magnitude_color: hex color
        - z_score: float
        - percentile: float (0-100)
        - vs_3m_avg: percent difference from 3-month average
        - vs_6m_avg: percent difference from 6-month average
        - vs_12m_avg: percent difference from 12-month average
        - streak: int (positive = consecutive increases, negative = decreases)
        - interpretation: str (plain-English summary)
    """
    transformed = apply_transform(raw_series, transform, frequency)
    clean = transformed.dropna()

    if len(clean) < 6:
        return _empty_result()

    latest = float(clean.iloc[-1])
    prev = float(clean.iloc[-2])

    # ── Z-score ───────────────────────────────────────────────────────────
    z = latest_z_score(clean, lookback=60) or 0.0

    # ── Percentile rank ───────────────────────────────────────────────────
    lookback = clean.tail(60)
    percentile = float((lookback < latest).sum() / len(lookback) * 100)

    # ── Versus moving averages ────────────────────────────────────────────
    def _vs_avg(window: int) -> float | None:
        if len(clean) < window:
            return None
        avg = float(clean.tail(window).mean())
        if avg == 0:
            return 0.0
        return round((latest - avg) / abs(avg) * 100, 2)

    vs_3m = _vs_avg(3)
    vs_6m = _vs_avg(6)
    vs_12m = _vs_avg(12)

    # ── Streak ────────────────────────────────────────────────────────────
    diffs = clean.diff().dropna().tail(12)
    streak = 0
    if len(diffs) > 0:
        last_sign = 1 if diffs.iloc[-1] > 0 else -1
        for val in reversed(diffs.values):
            if (val > 0 and last_sign > 0) or (val < 0 and last_sign < 0):
                streak += last_sign
            else:
                break

    # ── Magnitude classification ──────────────────────────────────────────
    abs_z = abs(z)
    if abs_z < 0.5:
        magnitude = "small"
        magnitude_color = "#6b7280"  # gray
    elif abs_z < 1.0:
        magnitude = "moderate"
        magnitude_color = "#eab308"  # yellow
    elif abs_z < 2.0:
        magnitude = "large"
        magnitude_color = "#f97316"  # orange
    else:
        magnitude = "extreme"
        magnitude_color = "#ef4444"  # red

    # ── Interpretation ────────────────────────────────────────────────────
    change = latest - prev
    change_dir = "rose" if change > 0 else "fell" if change < 0 else "was unchanged"

    # What does this mean economically?
    if higher_is == "inflationary":
        if change > 0:
            econ_signal = "hotter inflation pressure"
        elif change < 0:
            econ_signal = "cooling inflation"
        else:
            econ_signal = "stable inflation"
    elif higher_is == "expansionary":
        if change > 0:
            econ_signal = "strengthening economic activity"
        elif change < 0:
            econ_signal = "weakening economic activity"
        else:
            econ_signal = "steady economic activity"
    elif higher_is == "contractionary":
        if change > 0:
            econ_signal = "increasing economic stress"
        elif change < 0:
            econ_signal = "easing economic stress"
        else:
            econ_signal = "stable conditions"
    else:
        econ_signal = "neutral shift"

    # Streak context
    streak_text = ""
    if abs(streak) >= 3:
        streak_dir = "increases" if streak > 0 else "decreases"
        streak_text = f" This marks {abs(streak)} consecutive {streak_dir}."

    # Percentile context
    if percentile >= 90:
        pctl_text = f"at the {percentile:.0f}th percentile (near highs)"
    elif percentile <= 10:
        pctl_text = f"at the {percentile:.0f}th percentile (near lows)"
    else:
        pctl_text = f"at the {percentile:.0f}th percentile"

    interpretation = (
        f"The latest reading {change_dir} by {abs(change):.2f}, signaling {econ_signal}. "
        f"This is a **{magnitude}** move ({z:+.1f}σ), {pctl_text} of recent history."
        f"{streak_text}"
    )

    # vs averages context
    avg_texts = []
    if vs_3m is not None and abs(vs_3m) > 1:
        avg_texts.append(f"{'above' if vs_3m > 0 else 'below'} 3m avg by {abs(vs_3m):.1f}%")
    if vs_12m is not None and abs(vs_12m) > 2:
        avg_texts.append(f"{'above' if vs_12m > 0 else 'below'} 12m avg by {abs(vs_12m):.1f}%")

    if avg_texts:
        interpretation += " Currently " + " and ".join(avg_texts) + "."

    return {
        "magnitude": magnitude,
        "magnitude_color": magnitude_color,
        "z_score": round(z, 2),
        "percentile": round(percentile, 1),
        "vs_3m_avg": vs_3m,
        "vs_6m_avg": vs_6m,
        "vs_12m_avg": vs_12m,
        "streak": streak,
        "latest": latest,
        "previous": prev,
        "change": round(change, 4),
        "interpretation": interpretation,
    }


def _empty_result() -> dict:
    return {
        "magnitude": "unknown",
        "magnitude_color": "#6b7280",
        "z_score": 0,
        "percentile": 50,
        "vs_3m_avg": None,
        "vs_6m_avg": None,
        "vs_12m_avg": None,
        "streak": 0,
        "latest": None,
        "previous": None,
        "change": None,
        "interpretation": "Insufficient data for significance analysis.",
    }
