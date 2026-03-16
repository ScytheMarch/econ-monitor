"""Rules-based economic regime classification.

Uses actual data levels and rate-of-change signals (not just trend slope)
to produce a composite score from -1 (deep contraction) to +1 (strong expansion).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from econ_monitor.data import cache
from econ_monitor.analytics.transforms import apply_transform, mom_pct, yoy_pct


def _rate_signal(series_id: str, transform: str, frequency: str) -> float | None:
    """Score a signal based on rate of change: +1 improving, -1 deteriorating, 0 flat."""
    df = cache.get_observations(series_id)
    if df.empty or len(df) < 6:
        return None

    vals = df["value"]
    transformed = apply_transform(vals, transform, frequency).dropna()
    if len(transformed) < 3:
        return None

    recent = transformed.tail(6)
    latest = float(recent.iloc[-1])
    prev = float(recent.iloc[-2]) if len(recent) >= 2 else latest
    avg_3 = float(recent.tail(3).mean())
    avg_6 = float(recent.mean())

    # Score based on: latest vs previous + latest vs 3m avg + latest vs 6m avg
    score = 0.0
    if latest > prev:
        score += 0.33
    elif latest < prev:
        score -= 0.33

    if avg_6 != 0:
        if latest > avg_3 * 1.005:
            score += 0.33
        elif latest < avg_3 * 0.995:
            score -= 0.33

        if latest > avg_6 * 1.01:
            score += 0.34
        elif latest < avg_6 * 0.99:
            score -= 0.34

    return max(-1.0, min(1.0, score))


def _level_signal(series_id: str, bullish_above: float, bearish_below: float) -> float | None:
    """Score based on absolute level crossing thresholds."""
    df = cache.get_observations(series_id)
    if df.empty:
        return None

    latest = float(df["value"].iloc[-1])

    if latest > bullish_above:
        return 1.0
    elif latest < bearish_below:
        return -1.0
    else:
        # Linear interpolation between bearish and bullish
        mid = (bullish_above + bearish_below) / 2
        rng = (bullish_above - bearish_below) / 2
        if rng == 0:
            return 0.0
        return max(-1.0, min(1.0, (latest - mid) / rng))


def _latest_value(series_id: str) -> float | None:
    """Get the latest raw value for a series."""
    df = cache.get_observations(series_id)
    if df.empty:
        return None
    return float(df["value"].iloc[-1])


# Signal definitions: (name, compute_func, weight)
def _build_signals() -> list[dict]:
    """Build all regime signals with computed scores."""
    signals = []

    def _add(name: str, series_id: str, score: float | None, weight: float,
             interpretation: str = "", value: float | None = None,
             fmt: str = ".2f", suffix: str = ""):
        if score is not None:
            signals.append({
                "series_id": series_id,
                "name": name,
                "score": round(score, 2),
                "weight": weight,
                "interpretation": interpretation,
                "value": value,
                "fmt": fmt,
                "suffix": suffix,
            })

    # ── Labor ──────────────────────────────────────────────────────────────
    nfp = _rate_signal("PAYEMS", "net_change", "monthly")
    nfp_val = _latest_value("PAYEMS")
    if nfp is not None:
        if nfp > 0.2:
            nfp_interp = "Payroll gains accelerating — hiring momentum building"
        elif nfp < -0.2:
            nfp_interp = "Payroll gains decelerating — labor market cooling"
        else:
            nfp_interp = "Job growth steady — no clear shift in hiring"
        _add("Nonfarm Payrolls", "PAYEMS", nfp, 2.0, nfp_interp, nfp_val)

    ur = _rate_signal("UNRATE", "level", "monthly")
    ur_val = _latest_value("UNRATE")
    if ur is not None:
        inverted = -ur
        if ur < -0.2:
            ur_interp = f"Unemployment falling ({ur_val:.1f}%) — tight labor market"
        elif ur > 0.2:
            ur_interp = f"Unemployment rising ({ur_val:.1f}%) — labor slack emerging"
        else:
            ur_interp = f"Unemployment stable at {ur_val:.1f}%"
        _add("Unemployment Rate", "UNRATE", inverted, 1.5, ur_interp, ur_val, fmt=".1f", suffix="%")

    claims = _rate_signal("ICSA", "level", "weekly")
    claims_val = _latest_value("ICSA")
    if claims is not None:
        inverted = -claims
        if claims < -0.2:
            claims_interp = f"Initial claims declining ({claims_val:,.0f}) — fewer layoffs"
        elif claims > 0.2:
            claims_interp = f"Initial claims rising ({claims_val:,.0f}) — layoff pressure building"
        else:
            claims_interp = f"Claims stable around {claims_val:,.0f}"
        _add("Initial Jobless Claims", "ICSA", inverted, 1.0, claims_interp, claims_val, fmt=",.0f")

    # ── Output ─────────────────────────────────────────────────────────────
    ip = _rate_signal("INDPRO", "yoy_pct", "monthly")
    ip_val = _latest_value("INDPRO")
    if ip is not None:
        if ip > 0.2:
            ip_interp = "Industrial output expanding — manufacturing recovery"
        elif ip < -0.2:
            ip_interp = "Industrial output contracting — production weakness"
        else:
            ip_interp = "Industrial production flat — no clear momentum"
        _add("Industrial Production", "INDPRO", ip, 1.0, ip_interp, ip_val, fmt=".1f")

    cu = _level_signal("TCU", bullish_above=78, bearish_below=74)
    cu_val = _latest_value("TCU")
    if cu is not None:
        if cu > 0.2:
            cu_interp = f"Capacity utilization high ({cu_val:.1f}%) — economy running hot"
        elif cu < -0.2:
            cu_interp = f"Capacity utilization low ({cu_val:.1f}%) — significant slack"
        else:
            cu_interp = f"Capacity utilization moderate at {cu_val:.1f}%"
        _add("Capacity Utilization", "TCU", cu, 0.5, cu_interp, cu_val, fmt=".1f", suffix="%")

    # ── Consumer ───────────────────────────────────────────────────────────
    retail = _rate_signal("RSAFS", "mom_pct", "monthly")
    retail_val = _latest_value("RSAFS")
    if retail is not None:
        if retail > 0.2:
            retail_interp = "Retail sales rising — consumer spending strong"
        elif retail < -0.2:
            retail_interp = "Retail sales declining — consumer pullback"
        else:
            retail_interp = "Retail spending flat — consumers cautious"
        _add("Retail Sales", "RSAFS", retail, 1.0, retail_interp, retail_val, fmt=",.0f")

    sent = _rate_signal("UMCSENT", "level", "monthly")
    sent_val = _latest_value("UMCSENT")
    if sent is not None:
        if sent > 0.2:
            sent_interp = f"Consumer confidence improving ({sent_val:.1f}) — optimism growing"
        elif sent < -0.2:
            sent_interp = f"Consumer confidence falling ({sent_val:.1f}) — pessimism rising"
        else:
            sent_interp = f"Consumer sentiment stable at {sent_val:.1f}"
        _add("Consumer Sentiment (UMich)", "UMCSENT", sent, 0.5, sent_interp, sent_val, fmt=".1f")

    # ── Yield Curve ────────────────────────────────────────────────────────
    curve = _level_signal("T10Y2Y", bullish_above=0.5, bearish_below=-0.5)
    curve_val = _latest_value("T10Y2Y")
    if curve is not None:
        if curve_val is not None and curve_val < 0:
            curve_interp = f"Yield curve inverted ({curve_val:+.2f}%) — recession warning signal"
        elif curve_val is not None and curve_val > 0.5:
            curve_interp = f"Yield curve steep ({curve_val:+.2f}%) — expansion signal"
        else:
            curve_interp = f"Yield curve flat ({curve_val:+.2f}%) — uncertain outlook"
        _add("Yield Curve (10Y-2Y)", "T10Y2Y", curve, 1.5, curve_interp, curve_val, fmt="+.2f", suffix="%")

    # ── Credit / Stress ────────────────────────────────────────────────────
    hy = _level_signal("BAMLH0A0HYM2", bullish_above=5.0, bearish_below=3.0)
    hy_val = _latest_value("BAMLH0A0HYM2")
    if hy is not None:
        inverted = -hy
        if hy_val is not None and hy_val < 3.5:
            hy_interp = f"HY spreads tight ({hy_val:.2f}%) — markets risk-on"
        elif hy_val is not None and hy_val > 5.0:
            hy_interp = f"HY spreads wide ({hy_val:.2f}%) — credit stress elevated"
        else:
            hy_interp = f"HY spreads moderate ({hy_val:.2f}%) — no clear stress signal"
        _add("High Yield Credit Spread", "BAMLH0A0HYM2", inverted, 1.0, hy_interp, hy_val, fmt=".2f", suffix="%")

    vix = _level_signal("VIXCLS", bullish_above=25, bearish_below=15)
    vix_val = _latest_value("VIXCLS")
    if vix is not None:
        inverted = -vix
        if vix_val is not None and vix_val < 15:
            vix_interp = f"VIX low ({vix_val:.1f}) — markets calm, low fear"
        elif vix_val is not None and vix_val > 25:
            vix_interp = f"VIX elevated ({vix_val:.1f}) — significant fear/uncertainty"
        else:
            vix_interp = f"VIX moderate ({vix_val:.1f}) — normal volatility"
        _add("VIX (Fear Index)", "VIXCLS", inverted, 0.5, vix_interp, vix_val, fmt=".1f")

    return signals


def compute_regime_score() -> dict:
    """Compute composite regime score and individual signals."""
    signals = _build_signals()

    if not signals:
        return {"score": 0.0, "label": "No Data", "color": "#6b7280", "signals": []}

    total_weight = sum(s["weight"] for s in signals)
    weighted_sum = sum(s["score"] * s["weight"] for s in signals)
    composite = weighted_sum / total_weight if total_weight > 0 else 0.0

    if composite > 0.2:
        label, color = "Expansion", "#22c55e"
    elif composite < -0.2:
        label, color = "Contraction", "#ef4444"
    else:
        label, color = "Mixed", "#eab308"

    return {
        "score": round(composite, 3),
        "label": label,
        "color": color,
        "signals": signals,
    }
