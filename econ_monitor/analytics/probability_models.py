"""Probability models for recession forecasting and regime analysis.

Three models:
  1. Recession Probability — sigmoid-scored multi-signal model (0-100%)
  2. Composite Leading Index — z-score weighted diffusion index
  3. Regime Transition Probabilities — historical transition matrix + momentum forecast
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd

from econ_monitor.data import cache
from econ_monitor.analytics.transforms import (
    z_score,
    moving_average,
    rate_of_change,
    yoy_pct,
    trend_direction,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    """Standard logistic sigmoid, clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def _get_series(series_id: str) -> pd.Series:
    """Fetch a series from cache and return as pd.Series (value column)."""
    df = cache.get_observations(series_id)
    if df.empty:
        return pd.Series(dtype=float)
    return df["value"]


def _get_recession_periods() -> list[tuple[str, str]]:
    """Extract recession start/end pairs from USREC data."""
    df = cache.get_observations("USREC")
    if df.empty:
        return []
    periods: list[tuple[str, str]] = []
    in_recession = False
    start = ""
    for date, row in df.iterrows():
        if row["value"] == 1 and not in_recession:
            start = str(date.date())
            in_recession = True
        elif row["value"] == 0 and in_recession:
            periods.append((start, str(date.date())))
            in_recession = False
    if in_recession:
        periods.append((start, str(df.index[-1].date())))
    return periods


# ── Model 1: Recession Probability ───────────────────────────────────────────

# Component definitions: (name, series_id, weight, horizon_factors {3m, 6m, 12m})
_RECESSION_COMPONENTS = [
    {
        "name": "Yield Curve (10Y-3M)",
        "series_id": "T10Y3M",
        "weight": 0.35,
        "horizon": {"3m": 0.4, "6m": 0.7, "12m": 1.0},
    },
    {
        "name": "Sahm Rule (Unemployment)",
        "series_id": "UNRATE",
        "weight": 0.30,
        "horizon": {"3m": 1.0, "6m": 0.8, "12m": 0.5},
    },
    {
        "name": "Credit Stress (HY Spread)",
        "series_id": "BAMLH0A0HYM2",
        "weight": 0.20,
        "horizon": {"3m": 0.8, "6m": 1.0, "12m": 0.7},
    },
    {
        "name": "Industrial Production",
        "series_id": "INDPRO",
        "weight": 0.15,
        "horizon": {"3m": 0.9, "6m": 1.0, "12m": 0.6},
    },
]


def _score_yield_curve(series: pd.Series) -> float | None:
    """Score yield curve: inverted = high recession signal."""
    if series.empty:
        return None
    spread = float(series.iloc[-1])
    return _sigmoid(-spread * 2.0)


def _score_sahm_rule(series: pd.Series) -> float | None:
    """Score Sahm Rule: 3-month avg minus 12-month trailing minimum of 3-month avg."""
    if len(series) < 15:
        return None
    ma3 = series.rolling(3, min_periods=1).mean()
    trailing_min = ma3.rolling(12, min_periods=6).min()
    delta = float(ma3.iloc[-1] - trailing_min.iloc[-1])

    if delta >= 0.5:
        return min(1.0, 0.5 + (delta - 0.5) * 1.0)
    elif delta >= 0.3:
        return 0.3
    else:
        return max(0.0, delta / 0.5 * 0.3)


def _score_credit_stress(series: pd.Series) -> float | None:
    """Score credit stress via z-score of HY spread."""
    if len(series) < 30:
        return None
    zs = z_score(series, lookback=60).dropna()
    if zs.empty:
        return None
    z_val = float(zs.iloc[-1])
    return _sigmoid((z_val - 1.0) * 1.5)


def _score_industrial_production(series: pd.Series) -> float | None:
    """Score IP: negative growth = recession signal."""
    if len(series) < 12:
        return None
    roc_6m = rate_of_change(series, periods=6).dropna()
    if roc_6m.empty:
        return None
    # Annualize the 6-month change
    roc_ann = float(roc_6m.iloc[-1]) * 2.0
    return _sigmoid(-roc_ann * 0.5)


_SCORERS = {
    "T10Y3M": _score_yield_curve,
    "UNRATE": _score_sahm_rule,
    "BAMLH0A0HYM2": _score_credit_stress,
    "INDPRO": _score_industrial_production,
}


def compute_recession_probability() -> dict:
    """Compute recession probability for 3, 6, and 12 month horizons.

    Returns dict with keys:
        prob_3m, prob_6m, prob_12m (float 0-100),
        components (list of dicts),
        interpretation (str), label (str), color (str),
        history (pd.DataFrame with prob_3m, prob_6m, prob_12m columns),
        recession_periods (list of tuples for chart shading)
    """
    components = []
    horizons = {"3m": 0.0, "6m": 0.0, "12m": 0.0}
    horizon_weights = {"3m": 0.0, "6m": 0.0, "12m": 0.0}

    for comp in _RECESSION_COMPONENTS:
        series = _get_series(comp["series_id"])
        scorer = _SCORERS[comp["series_id"]]
        score = scorer(series)

        if score is None:
            components.append({
                "name": comp["name"],
                "series_id": comp["series_id"],
                "value": None,
                "score": None,
                "weight": comp["weight"],
                "interpretation": "Insufficient data",
            })
            continue

        raw_value = float(series.iloc[-1]) if not series.empty else None

        # Build interpretation
        if score < 0.25:
            interp = "No recession signal"
        elif score < 0.5:
            interp = "Mild warning"
        elif score < 0.75:
            interp = "Moderate recession signal"
        else:
            interp = "Strong recession signal"

        components.append({
            "name": comp["name"],
            "series_id": comp["series_id"],
            "value": raw_value,
            "score": round(score, 3),
            "weight": comp["weight"],
            "interpretation": interp,
        })

        for h_key in horizons:
            factor = comp["horizon"][h_key]
            horizons[h_key] += score * comp["weight"] * factor
            horizon_weights[h_key] += comp["weight"] * factor

    # Normalize and map through sigmoid
    probs = {}
    for h_key in ["3m", "6m", "12m"]:
        if horizon_weights[h_key] > 0:
            raw = horizons[h_key] / horizon_weights[h_key]
            probs[h_key] = _sigmoid((raw - 0.35) * 8.0) * 100
        else:
            probs[h_key] = 0.0

    # Label based on 12m probability
    p12 = probs["12m"]
    if p12 < 20:
        label, color = "Low Risk", "#22c55e"
    elif p12 < 40:
        label, color = "Moderate", "#eab308"
    elif p12 < 60:
        label, color = "Elevated", "#f97316"
    else:
        label, color = "High Risk", "#ef4444"

    # Interpretation
    if p12 < 15:
        interpretation = (
            f"Recession probability is low at {p12:.0f}%. "
            "Most signals point to continued expansion with no near-term recession risk."
        )
    elif p12 < 35:
        interpretation = (
            f"Recession probability is moderate at {p12:.0f}%. "
            "Some warning signals are emerging — watch for deterioration in credit and labor markets."
        )
    elif p12 < 60:
        interpretation = (
            f"Recession probability is elevated at {p12:.0f}%. "
            "Multiple indicators are flashing warnings. Heightened vigilance recommended."
        )
    else:
        interpretation = (
            f"Recession probability is high at {p12:.0f}%. "
            "Multiple signals are in recession territory. Defensive positioning warranted."
        )

    # Build history (rolling over available data)
    history = _build_recession_history()

    return {
        "prob_3m": round(probs["3m"], 1),
        "prob_6m": round(probs["6m"], 1),
        "prob_12m": round(probs["12m"], 1),
        "components": components,
        "interpretation": interpretation,
        "label": label,
        "color": color,
        "history": history,
        "recession_periods": _get_recession_periods(),
    }


def _build_recession_history() -> pd.DataFrame:
    """Build monthly recession probability history for charting."""
    # Fetch all needed series
    all_series = {}
    for comp in _RECESSION_COMPONENTS:
        s = _get_series(comp["series_id"])
        if not s.empty:
            # Resample to month-end, forward fill
            all_series[comp["series_id"]] = s.resample("ME").last().ffill()

    if not all_series:
        return pd.DataFrame(columns=["prob_3m", "prob_6m", "prob_12m"])

    # Find common date range
    all_indices = [s.index for s in all_series.values() if not s.empty]
    if not all_indices:
        return pd.DataFrame(columns=["prob_3m", "prob_6m", "prob_12m"])

    min_date = max(idx.min() for idx in all_indices)
    max_date = min(idx.max() for idx in all_indices)

    dates = pd.date_range(min_date, max_date, freq="ME")
    if len(dates) < 24:
        return pd.DataFrame(columns=["prob_3m", "prob_6m", "prob_12m"])

    # Only compute over last 60 months for performance
    dates = dates[-60:]

    records = []
    for dt in dates:
        horizons = {"3m": 0.0, "6m": 0.0, "12m": 0.0}
        horizon_weights = {"3m": 0.0, "6m": 0.0, "12m": 0.0}

        for comp in _RECESSION_COMPONENTS:
            sid = comp["series_id"]
            if sid not in all_series:
                continue
            s = all_series[sid]
            s_up_to = s[s.index <= dt]
            if len(s_up_to) < 12:
                continue

            scorer = _SCORERS[sid]
            score = scorer(s_up_to)
            if score is None:
                continue

            for h_key in horizons:
                factor = comp["horizon"][h_key]
                horizons[h_key] += score * comp["weight"] * factor
                horizon_weights[h_key] += comp["weight"] * factor

        row = {}
        for h_key in ["3m", "6m", "12m"]:
            if horizon_weights[h_key] > 0:
                raw = horizons[h_key] / horizon_weights[h_key]
                row[f"prob_{h_key}"] = _sigmoid((raw - 0.35) * 8.0) * 100
            else:
                row[f"prob_{h_key}"] = 0.0

        records.append({"date": dt, **row})

    if not records:
        return pd.DataFrame(columns=["prob_3m", "prob_6m", "prob_12m"])

    df = pd.DataFrame(records).set_index("date")
    return df


# ── Model 2: Composite Leading Index ─────────────────────────────────────────

_LEADING_COMPONENTS = [
    {"name": "Yield Curve (10Y-2Y)", "series_id": "T10Y2Y", "weight": 0.20,
     "transform": "level", "invert": False},
    {"name": "Building Permits", "series_id": "PERMIT", "weight": 0.15,
     "transform": "yoy_pct", "invert": False},
    {"name": "Initial Claims", "series_id": "ICSA", "weight": 0.15,
     "transform": "level", "invert": True},
    {"name": "Consumer Sentiment", "series_id": "UMCSENT", "weight": 0.15,
     "transform": "level", "invert": False},
    {"name": "Durable Goods Orders", "series_id": "DGORDER", "weight": 0.15,
     "transform": "yoy_pct", "invert": False},
    {"name": "VIX", "series_id": "VIXCLS", "weight": 0.10,
     "transform": "level", "invert": True},
    {"name": "M2 Money Supply", "series_id": "M2SL", "weight": 0.10,
     "transform": "yoy_pct", "invert": False},
]


def compute_leading_index() -> dict:
    """Compute composite leading economic index.

    Returns dict with keys:
        value (float), trend (str), components (list), interpretation (str),
        history (pd.DataFrame with 'index' column),
        recession_periods (list)
    """
    components = []
    current_composite = 0.0
    total_weight = 0.0

    # Also build history
    component_series = {}

    for comp in _LEADING_COMPONENTS:
        raw = _get_series(comp["series_id"])
        if raw.empty or len(raw) < 30:
            components.append({
                "name": comp["name"],
                "series_id": comp["series_id"],
                "z_score": None,
                "weight": comp["weight"],
                "contribution": None,
            })
            continue

        # Apply transform if needed
        if comp["transform"] == "yoy_pct":
            freq_map = {"PERMIT": 12, "DGORDER": 12, "M2SL": 12}
            periods = freq_map.get(comp["series_id"], 12)
            transformed = yoy_pct(raw, periods=periods).dropna()
        else:
            transformed = raw.dropna()

        if len(transformed) < 30:
            components.append({
                "name": comp["name"],
                "series_id": comp["series_id"],
                "z_score": None,
                "weight": comp["weight"],
                "contribution": None,
            })
            continue

        # Compute z-score series
        zs = z_score(transformed, lookback=60).dropna()
        if zs.empty:
            continue

        latest_z = float(zs.iloc[-1])
        if comp["invert"]:
            zs = -zs
            latest_z = -latest_z

        contribution = latest_z * comp["weight"]
        current_composite += contribution
        total_weight += comp["weight"]

        components.append({
            "name": comp["name"],
            "series_id": comp["series_id"],
            "z_score": round(latest_z, 2),
            "weight": comp["weight"],
            "contribution": round(contribution, 3),
        })

        # Store for history building — resample to monthly
        monthly_z = zs.resample("ME").last().dropna()
        component_series[comp["series_id"]] = monthly_z

    # Compute trend
    if component_series:
        history = _build_leading_history(component_series)
        if not history.empty and len(history) >= 3:
            trend = trend_direction(history["index"], window=6)
        else:
            trend = "stable"
    else:
        history = pd.DataFrame(columns=["index"])
        trend = "stable"

    # Interpretation
    val = round(current_composite, 2)
    if val > 0.5:
        interpretation = (
            f"Leading index is strongly positive at {val:+.2f}, "
            "signaling robust economic expansion ahead. Most forward-looking indicators are above trend."
        )
    elif val > 0:
        interpretation = (
            f"Leading index is mildly positive at {val:+.2f}, "
            "suggesting continued but moderate growth. Some headwinds may be emerging."
        )
    elif val > -0.5:
        interpretation = (
            f"Leading index is mildly negative at {val:+.2f}, "
            "suggesting growth is slowing. Monitor for further deterioration."
        )
    else:
        interpretation = (
            f"Leading index is deeply negative at {val:+.2f}, "
            "flashing a strong slowdown signal. Multiple leading indicators are below trend."
        )

    return {
        "value": val,
        "trend": trend,
        "components": components,
        "interpretation": interpretation,
        "history": history,
        "recession_periods": _get_recession_periods(),
    }


def _build_leading_history(
    component_series: dict[str, pd.Series],
) -> pd.DataFrame:
    """Build the leading index time series from component z-scores."""
    if not component_series:
        return pd.DataFrame(columns=["index"])

    # Align to common monthly dates
    aligned = pd.DataFrame(component_series)
    aligned = aligned.dropna(how="all")

    if aligned.empty:
        return pd.DataFrame(columns=["index"])

    # Weight each component
    weight_map = {c["series_id"]: c["weight"] for c in _LEADING_COMPONENTS}
    composite = pd.Series(0.0, index=aligned.index)

    for col in aligned.columns:
        w = weight_map.get(col, 0.1)
        composite += aligned[col].fillna(0) * w

    # Limit to last 60 months
    composite = composite.tail(60)

    return pd.DataFrame({"index": composite})


# ── Model 3: Regime Transition Probabilities ──────────────────────────────────

# Signal definitions matching regime.py
_REGIME_SIGNAL_DEFS = [
    {"series_id": "PAYEMS", "weight": 2.0, "type": "rate", "transform": "net_change", "freq": "monthly"},
    {"series_id": "UNRATE", "weight": 1.5, "type": "rate", "transform": "level", "freq": "monthly", "invert": True},
    {"series_id": "ICSA", "weight": 1.0, "type": "rate", "transform": "level", "freq": "weekly", "invert": True},
    {"series_id": "INDPRO", "weight": 1.0, "type": "rate", "transform": "yoy_pct", "freq": "monthly"},
    {"series_id": "TCU", "weight": 0.5, "type": "level", "bullish": 78, "bearish": 74},
    {"series_id": "RSAFS", "weight": 1.0, "type": "rate", "transform": "mom_pct", "freq": "monthly"},
    {"series_id": "UMCSENT", "weight": 0.5, "type": "rate", "transform": "level", "freq": "monthly"},
    {"series_id": "T10Y2Y", "weight": 1.5, "type": "level", "bullish": 0.5, "bearish": -0.5},
    {"series_id": "BAMLH0A0HYM2", "weight": 1.0, "type": "level", "bullish": 5.0, "bearish": 3.0, "invert": True},
    {"series_id": "VIXCLS", "weight": 0.5, "type": "level", "bullish": 25, "bearish": 15, "invert": True},
]


def _classify_regime(score: float) -> str:
    """Classify a regime score into a label."""
    if score > 0.2:
        return "Expansion"
    elif score < -0.2:
        return "Contraction"
    return "Mixed"


def _compute_regime_at_point(
    monthly_data: dict[str, pd.Series],
    date: pd.Timestamp,
) -> float | None:
    """Compute a simplified regime score at a given point in time."""
    total_weight = 0.0
    weighted_sum = 0.0

    for sig in _REGIME_SIGNAL_DEFS:
        sid = sig["series_id"]
        if sid not in monthly_data:
            continue

        s = monthly_data[sid]
        s_up_to = s[s.index <= date]
        if len(s_up_to) < 6:
            continue

        if sig["type"] == "level":
            val = float(s_up_to.iloc[-1])
            bullish = sig["bullish"]
            bearish = sig["bearish"]
            if val > bullish:
                score = 1.0
            elif val < bearish:
                score = -1.0
            else:
                mid = (bullish + bearish) / 2
                rng = (bullish - bearish) / 2
                score = (val - mid) / rng if rng != 0 else 0.0
                score = max(-1.0, min(1.0, score))
        else:
            # Rate signal: simplified — compare latest to recent average
            recent = s_up_to.tail(6)
            latest = float(recent.iloc[-1])
            avg = float(recent.mean())
            if avg != 0:
                diff_pct = (latest - avg) / abs(avg)
                score = max(-1.0, min(1.0, diff_pct * 5))
            else:
                score = 0.0

        if sig.get("invert"):
            score = -score

        weighted_sum += score * sig["weight"]
        total_weight += sig["weight"]

    if total_weight == 0:
        return None

    return weighted_sum / total_weight


def compute_transition_probabilities() -> dict:
    """Compute regime transition matrix and forecast probabilities.

    Returns dict with keys:
        current_regime (str), transition_matrix (dict of dicts),
        momentum (float), forecast (str), forecast_probs (dict),
        regime_history (pd.DataFrame with 'score' and 'regime' columns),
        interpretation (str)
    """
    # Fetch all signal series, resample to monthly
    monthly_data: dict[str, pd.Series] = {}
    for sig in _REGIME_SIGNAL_DEFS:
        s = _get_series(sig["series_id"])
        if not s.empty:
            monthly_data[sig["series_id"]] = s.resample("ME").last().ffill()

    if not monthly_data:
        return _empty_transition_result()

    # Find common date range
    all_indices = [s.index for s in monthly_data.values()]
    min_date = max(idx.min() for idx in all_indices)
    max_date = min(idx.max() for idx in all_indices)
    dates = pd.date_range(min_date, max_date, freq="ME")

    if len(dates) < 24:
        return _empty_transition_result()

    # Compute regime score at each month (last 120 months for good transition stats)
    dates = dates[-120:]
    scores = []
    for dt in dates:
        s = _compute_regime_at_point(monthly_data, dt)
        if s is not None:
            scores.append({"date": dt, "score": s, "regime": _classify_regime(s)})

    if len(scores) < 12:
        return _empty_transition_result()

    history_df = pd.DataFrame(scores).set_index("date")

    # Build transition matrix
    regimes = history_df["regime"].values
    transitions: dict[str, dict[str, int]] = {
        r: {"Expansion": 0, "Mixed": 0, "Contraction": 0}
        for r in ["Expansion", "Mixed", "Contraction"]
    }
    for i in range(len(regimes) - 1):
        from_r = regimes[i]
        to_r = regimes[i + 1]
        transitions[from_r][to_r] += 1

    # Normalize to probabilities
    trans_matrix: dict[str, dict[str, float]] = {}
    for from_r, counts in transitions.items():
        total = sum(counts.values())
        if total > 0:
            trans_matrix[from_r] = {
                to_r: round(c / total, 3) for to_r, c in counts.items()
            }
        else:
            trans_matrix[from_r] = {"Expansion": 0.33, "Mixed": 0.34, "Contraction": 0.33}

    # Current regime and momentum
    current_regime = str(history_df["regime"].iloc[-1])
    recent_scores = history_df["score"].tail(6)
    momentum = 0.0
    if len(recent_scores) >= 3:
        momentum = float(recent_scores.iloc[-1] - recent_scores.iloc[-3]) / 3.0

    # Forecast: base transition + momentum adjustment
    base_probs = dict(trans_matrix[current_regime])
    forecast_probs = _adjust_forecast(base_probs, current_regime, momentum)

    # Forecast label
    max_other = max(
        v for k, v in forecast_probs.items() if k != current_regime
    ) if len(forecast_probs) > 1 else 0
    if max_other > 0.25:
        forecast = "Transition risk elevated"
    elif abs(momentum) > 0.1:
        forecast = "Regime shifting"
    else:
        forecast = "Regime likely to persist"

    # Stability = probability of staying in current regime
    stability = forecast_probs.get(current_regime, 0.5)

    # Interpretation
    interpretation = _build_transition_interpretation(
        current_regime, momentum, stability, forecast_probs
    )

    return {
        "current_regime": current_regime,
        "transition_matrix": trans_matrix,
        "momentum": round(momentum, 4),
        "forecast": forecast,
        "forecast_probs": forecast_probs,
        "stability": round(stability * 100, 1),
        "regime_history": history_df,
        "interpretation": interpretation,
    }


def _adjust_forecast(
    base: dict[str, float],
    current: str,
    momentum: float,
) -> dict[str, float]:
    """Adjust base transition probabilities using momentum."""
    probs = dict(base)

    # Strong negative momentum in Expansion → raise Mixed/Contraction
    if current == "Expansion" and momentum < -0.05:
        shift = min(0.15, abs(momentum) * 1.5)
        probs["Expansion"] -= shift
        probs["Mixed"] += shift * 0.6
        probs["Contraction"] += shift * 0.4

    # Strong positive momentum in Contraction → raise Mixed/Expansion
    elif current == "Contraction" and momentum > 0.05:
        shift = min(0.15, momentum * 1.5)
        probs["Contraction"] -= shift
        probs["Mixed"] += shift * 0.6
        probs["Expansion"] += shift * 0.4

    # Mixed regime: momentum direction matters
    elif current == "Mixed":
        if momentum > 0.05:
            shift = min(0.10, momentum * 1.0)
            probs["Mixed"] -= shift
            probs["Expansion"] += shift
        elif momentum < -0.05:
            shift = min(0.10, abs(momentum) * 1.0)
            probs["Mixed"] -= shift
            probs["Contraction"] += shift

    # Clamp and renormalize
    for k in probs:
        probs[k] = max(0.01, probs[k])
    total = sum(probs.values())
    probs = {k: round(v / total, 3) for k, v in probs.items()}
    return probs


def _build_transition_interpretation(
    current: str,
    momentum: float,
    stability: float,
    probs: dict[str, float],
) -> str:
    """Build plain-English interpretation for transition analysis."""
    parts = [f"The economy is currently in **{current}** mode."]

    if abs(momentum) < 0.03:
        parts.append("Momentum is flat, suggesting the current regime is stable.")
    elif momentum > 0:
        parts.append(f"Momentum is positive ({momentum:+.3f}/month), indicating improving conditions.")
    else:
        parts.append(f"Momentum is negative ({momentum:+.3f}/month), indicating deteriorating conditions.")

    parts.append(
        f"Based on historical patterns and current momentum, "
        f"there is a {stability:.0%} chance the current regime persists next month."
    )

    # Highlight biggest transition risk
    other_risks = {k: v for k, v in probs.items() if k != current}
    if other_risks:
        max_risk = max(other_risks, key=other_risks.get)
        max_prob = other_risks[max_risk]
        if max_prob > 0.15:
            parts.append(
                f"The highest transition risk is toward {max_risk} ({max_prob:.0%})."
            )

    return " ".join(parts)


def _empty_transition_result() -> dict:
    """Return empty/default transition result when data is insufficient."""
    return {
        "current_regime": "Unknown",
        "transition_matrix": {
            r: {"Expansion": 0.33, "Mixed": 0.34, "Contraction": 0.33}
            for r in ["Expansion", "Mixed", "Contraction"]
        },
        "momentum": 0.0,
        "forecast": "Insufficient data",
        "forecast_probs": {"Expansion": 0.33, "Mixed": 0.34, "Contraction": 0.33},
        "stability": 33.0,
        "regime_history": pd.DataFrame(columns=["score", "regime"]),
        "interpretation": "Insufficient historical data to compute transition probabilities.",
    }
