"""Overview page: significant movers, regime gauge, traffic-light grid by category tabs."""

from __future__ import annotations

import streamlit as st

from econ_monitor.config.indicators import INDICATORS, CATEGORY_ORDER, get_indicators_by_category, WHY_IT_MATTERS
from econ_monitor.data import cache
from econ_monitor.analytics.transforms import apply_transform, trend_direction
from econ_monitor.analytics.significance import compute_significance
from econ_monitor.analytics.regime import compute_regime_score
from econ_monitor.ui.styles import (
    trend_color, trend_arrow, format_value, CATEGORY_COLORS, GRAY, GREEN, RED, YELLOW,
)
from econ_monitor.ui import charts


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📊 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Economic Dashboard</span></h2>',
        unsafe_allow_html=True,
    )

    # ── 1. Significant Movers FIRST (most actionable) ──────────────────
    _render_significant_movers()

    # ── 2. Regime (compact) ────────────────────────────────────────────
    regime = compute_regime_score()
    col_gauge, col_ctx = st.columns([1, 2])
    with col_gauge:
        fig = charts.regime_gauge(regime["score"], regime["label"], regime["color"])
        st.plotly_chart(fig, key="regime_gauge")

    with col_ctx:
        _render_regime_context(regime)

    # Signals collapsed by default
    if regime["signals"]:
        with st.expander("📋 Regime Signal Details", expanded=False):
            _render_regime_signals(regime["signals"])

    # ── 3. Traffic-light grid — CATEGORY TABS ──────────────────────────
    st.markdown(
        '<div style="margin-top:16px;margin-bottom:8px;font-size:1.1em;font-weight:700;'
        'color:#94a3b8;letter-spacing:-0.2px">📈 All Indicators</div>',
        unsafe_allow_html=True,
    )

    groups = get_indicators_by_category()
    tab_cats = [cat for cat in CATEGORY_ORDER if groups.get(cat)]
    tab_labels = [f"{cat}" for cat in tab_cats]

    tabs = st.tabs(tab_labels)
    for tab, cat in zip(tabs, tab_cats):
        with tab:
            indicators = groups[cat]
            cols = st.columns(min(len(indicators), 4))
            for i, ind in enumerate(indicators):
                col = cols[i % len(cols)]
                with col:
                    _render_indicator_card(ind)


# ═══════════════════════════════════════════════════════════════════════════
# Regime context & signals
# ═══════════════════════════════════════════════════════════════════════════

def _render_regime_context(regime: dict) -> None:
    """Explain the regime score in plain English."""
    score = regime["score"]
    label = regime["label"]
    color = regime["color"]
    signals = regime.get("signals", [])

    if not signals:
        st.info("No data loaded yet. Click **Initial Data Fetch** in the sidebar.")
        return

    bulls = [s for s in signals if s["score"] > 0.2]
    bears = [s for s in signals if s["score"] < -0.2]
    neutral = [s for s in signals if -0.2 <= s["score"] <= 0.2]

    if label == "Expansion":
        headline = "Strong expansion" if score > 0.5 else "Modest expansion"
        desc = ("Broad-based strength across most signals."
                if score > 0.5 else
                "Growth signals slightly outweigh contraction.")
    elif label == "Contraction":
        headline = "Broad contraction" if score < -0.5 else "Mild contraction tilt"
        desc = ("Most indicators flashing warning signs."
                if score < -0.5 else
                "Weakness emerging in several areas, not yet widespread.")
    else:
        headline = "Mixed signals"
        desc = "Expansion and contraction signals roughly balanced."

    # Top drivers
    top_bull = sorted(bulls, key=lambda s: s["score"], reverse=True)[:2]
    top_bear = sorted(bears, key=lambda s: s["score"])[:2]

    drivers_html = ""
    if top_bull:
        names = ", ".join(s["name"] for s in top_bull)
        drivers_html += (
            f'<div style="margin-top:6px">'
            f'<span style="color:#22c55e;font-weight:600">Tailwinds:</span> '
            f'<span style="color:#d1d5db">{names}</span></div>'
        )
    if top_bear:
        names = ", ".join(s["name"] for s in top_bear)
        drivers_html += (
            f'<div style="margin-top:3px">'
            f'<span style="color:#ef4444;font-weight:600">Headwinds:</span> '
            f'<span style="color:#d1d5db">{names}</span></div>'
        )

    count_html = (
        f'<span style="color:#22c55e;font-weight:600">{len(bulls)}</span> bullish · '
        f'<span style="color:#eab308;font-weight:600">{len(neutral)}</span> neutral · '
        f'<span style="color:#ef4444;font-weight:600">{len(bears)}</span> bearish'
    )

    html = (
        f'<div style="background:rgba(255,255,255,0.04);border:1px solid {color};'
        f'border-radius:10px;padding:14px 18px">'
        f'<div style="font-weight:700;font-size:1.1em;color:{color}">{headline}</div>'
        f'<div style="color:#9ca3af;font-size:0.85em;margin-top:4px">{desc}</div>'
        f'<div style="margin-top:8px;font-size:0.85em">{count_html}</div>'
        f'{drivers_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_regime_signals(signals: list[dict]) -> None:
    """Render regime signals as a compact HTML table."""
    rows_html = ""
    for sig in signals:
        score = sig["score"]
        name = sig.get("name", sig["series_id"])
        interp = sig.get("interpretation", "")

        if score > 0.2:
            icon, scolor = "🟢", GREEN
        elif score < -0.2:
            icon, scolor = "🔴", RED
        else:
            icon, scolor = "🟡", YELLOW

        rows_html += (
            f'<tr style="border-bottom:1px solid rgba(255,255,255,0.04)">'
            f'<td style="padding:6px 8px;white-space:nowrap">{icon}</td>'
            f'<td style="padding:6px 8px;font-weight:600">{name}</td>'
            f'<td style="padding:6px 8px;color:{scolor};font-weight:700;text-align:right">'
            f'{score:+.2f}</td>'
            f'<td style="padding:6px 8px;color:#9ca3af;font-size:0.85em">{interp}</td>'
            f'</tr>'
        )

    html = (
        f'<table style="width:100%;border-collapse:collapse;font-size:0.9em">'
        f'<thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08)">'
        f'<th style="padding:4px 8px;text-align:left;width:30px"></th>'
        f'<th style="padding:4px 8px;text-align:left;color:#64748b;font-size:0.8em;'
        f'text-transform:uppercase;letter-spacing:0.5px">Signal</th>'
        f'<th style="padding:4px 8px;text-align:right;color:#64748b;font-size:0.8em;'
        f'text-transform:uppercase;letter-spacing:0.5px">Score</th>'
        f'<th style="padding:4px 8px;text-align:left;color:#64748b;font-size:0.8em;'
        f'text-transform:uppercase;letter-spacing:0.5px">Reading</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# Significant movers
# ═══════════════════════════════════════════════════════════════════════════

def _render_significant_movers() -> None:
    """Spotlight for statistically significant movers and persistent streaks."""
    movers = []
    streakers = []

    for fred_id, ind in INDICATORS.items():
        if ind.category == "Regime":
            continue
        df = cache.get_observations(fred_id)
        if df.empty or len(df) < 6:
            continue

        sig = compute_significance(df["value"], ind.transform, ind.frequency, ind.higher_is)
        z = sig["z_score"]
        streak = sig["streak"]

        if abs(z) >= 1.0:
            movers.append((ind, sig))
        if abs(streak) >= 3:
            streakers.append((ind, sig))

    if not movers and not streakers:
        st.caption("No significant movers or persistent streaks detected.")
        return

    if movers:
        st.markdown(
            '<div style="font-size:1.0em;font-weight:700;color:#94a3b8;margin-bottom:6px">'
            '📡 Significant Movers</div>',
            unsafe_allow_html=True,
        )
        movers.sort(key=lambda x: abs(x[1]["z_score"]), reverse=True)
        for ind, sig in movers:
            _render_mover_card(ind, sig)

    # Persistent streaks (exclude those already shown)
    mover_ids = {ind.fred_id for ind, _ in movers} if movers else set()
    unique_streakers = [(ind, sig) for ind, sig in streakers if ind.fred_id not in mover_ids]

    if unique_streakers:
        st.markdown(
            '<div style="font-size:1.0em;font-weight:700;color:#94a3b8;margin:12px 0 6px 0">'
            '🔄 Persistent Patterns</div>',
            unsafe_allow_html=True,
        )
        unique_streakers.sort(key=lambda x: abs(x[1]["streak"]), reverse=True)
        for ind, sig in unique_streakers:
            _render_streak_card(ind, sig)


def _render_mover_card(ind, sig: dict) -> None:
    """Render a single significant mover card with nav button."""
    z = sig["z_score"]
    pctl = sig["percentile"]
    streak = sig["streak"]
    mag = sig["magnitude"]
    mag_color = sig["magnitude_color"]
    change = sig.get("change", 0)
    latest = sig.get("latest")

    if change and change > 0:
        arrow = "▲"
        dir_color = RED if ind.higher_is in ("contractionary", "inflationary") else GREEN
    elif change and change < 0:
        arrow = "▼"
        dir_color = GREEN if ind.higher_is in ("contractionary", "inflationary") else RED
    else:
        arrow, dir_color = "▬", GRAY

    cat_color = CATEGORY_COLORS.get(ind.category, GRAY)
    disp = format_value(latest, ind.unit, ind.transform) if latest is not None else "N/A"

    streak_badge = ""
    if abs(streak) >= 2:
        s_dir = "▲" if streak > 0 else "▼"
        streak_badge = (
            f'<span style="background:#7c3aed;color:white;padding:1px 8px;'
            f'border-radius:10px;font-size:0.7em;font-weight:700;margin-left:6px">'
            f'{s_dir}{abs(streak)} STREAK</span>'
        )

    html = (
        f'<div style="border-left:4px solid {mag_color};padding:10px 14px;'
        f'margin-bottom:8px;background:rgba(255,255,255,0.04);border-radius:0 8px 8px 0">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<span style="background:{cat_color};color:white;padding:1px 8px;border-radius:10px;'
        f'font-size:0.7em;font-weight:600">{ind.category}</span> '
        f'<strong style="margin-left:6px;font-size:1.05em">{ind.name}</strong> '
        f'<span style="background:{mag_color};color:white;padding:1px 8px;border-radius:10px;'
        f'font-size:0.7em;font-weight:700;margin-left:6px;text-transform:uppercase">{mag}</span>'
        f'{streak_badge}'
        f'</div>'
        f'<span style="color:{dir_color};font-size:1.2em;font-weight:700">'
        f'{arrow} {disp}</span>'
        f'</div>'
        f'<div style="margin-top:6px;font-size:0.85em;color:#d1d5db">'
        f'<span style="color:{dir_color};font-weight:600">{z:+.1f}\u03c3</span> '
        f'<span style="color:#9ca3af;margin-left:8px">P{pctl:.0f}</span> '
        f'<span style="color:#9ca3af;margin-left:10px">'
        f'{sig["interpretation"].replace("**", "")}</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Nav button
    if st.button("Details →", key=f"mover_nav_{ind.fred_id}", type="secondary"):
        st.session_state["detail_indicator"] = ind.fred_id
        st.switch_page(st.session_state["_pages"]["detail"])


def _render_streak_card(ind, sig: dict) -> None:
    """Render a persistent streak card."""
    streak = sig["streak"]
    z = sig["z_score"]
    pctl = sig["percentile"]
    latest = sig.get("latest")
    cat_color = CATEGORY_COLORS.get(ind.category, GRAY)
    disp = format_value(latest, ind.unit, ind.transform) if latest is not None else "N/A"

    s_dir = "▲" if streak > 0 else "▼"
    s_label = "consecutive increases" if streak > 0 else "consecutive decreases"

    if ind.higher_is in ("contractionary", "inflationary"):
        pattern_color = RED if streak > 0 else GREEN
    elif ind.higher_is == "expansionary":
        pattern_color = GREEN if streak > 0 else RED
    else:
        pattern_color = YELLOW

    html = (
        f'<div style="border-left:4px solid #7c3aed;padding:8px 14px;margin-bottom:6px;'
        f'background:rgba(124,58,237,0.06);border-radius:0 8px 8px 0">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<span style="background:{cat_color};color:white;padding:1px 8px;border-radius:10px;'
        f'font-size:0.7em;font-weight:600">{ind.category}</span> '
        f'<strong style="margin-left:6px">{ind.name}</strong> '
        f'<span style="color:#7c3aed;margin-left:8px;font-weight:600;font-size:0.9em">'
        f'{s_dir} {abs(streak)} {s_label}</span>'
        f'</div>'
        f'<span style="color:{pattern_color};font-weight:700">{disp}</span>'
        f'</div>'
        f'<div style="margin-top:4px;font-size:0.85em;color:#9ca3af">'
        f'{z:+.1f}\u03c3 \u00b7 P{pctl:.0f} \u00b7 '
        f'{sig["interpretation"].replace("**", "")}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if st.button("Details →", key=f"streak_nav_{ind.fred_id}", type="secondary"):
        st.session_state["detail_indicator"] = ind.fred_id
        st.switch_page(st.session_state["_pages"]["detail"])


# ═══════════════════════════════════════════════════════════════════════════
# Indicator cards
# ═══════════════════════════════════════════════════════════════════════════

def _render_indicator_card(ind) -> None:
    """Render a single indicator card with significance analysis."""
    df = cache.get_observations(ind.fred_id)

    # Special handling for NBER Recession Indicator
    if ind.fred_id == "USREC":
        _render_nber_card(ind, df)
        return

    if df.empty or len(df) < 2:
        st.metric(label=ind.name, value="No data", delta=None)
        return

    transformed = apply_transform(df["value"], ind.transform, ind.frequency)
    clean = transformed.dropna()

    if clean.empty:
        st.metric(label=ind.name, value="N/A", delta=None)
        return

    latest_val = clean.iloc[-1]
    prev_val = clean.iloc[-2] if len(clean) >= 2 else None
    delta = latest_val - prev_val if prev_val is not None else None

    direction = trend_direction(clean, window=6)
    color = trend_color(direction, ind.higher_is)
    arrow = trend_arrow(direction, ind.higher_is)

    display_val = format_value(latest_val, ind.unit, ind.transform)

    delta_str = None
    if delta is not None:
        if ind.transform in ("yoy_pct", "mom_pct", "annualized"):
            delta_str = f"{delta:+.2f}pp"
        else:
            delta_str = f"{delta:+,.1f}"

    st.metric(label=ind.name, value=display_val, delta=delta_str)

    # Significance analysis
    sig = compute_significance(df["value"], ind.transform, ind.frequency, ind.higher_is)

    mag = sig["magnitude"]
    mag_color = sig["magnitude_color"]
    z = sig["z_score"]
    pctl = sig["percentile"]
    streak = sig["streak"]

    streak_text = ""
    if abs(streak) >= 2:
        streak_dir = "▲" if streak > 0 else "▼"
        streak_text = f" \u00b7 {streak_dir}{abs(streak)} streak"

    html = (
        f'<div style="height:3px;background:{color};border-radius:2px;margin:-8px 0 4px 0"></div>'
        f'<div style="margin:2px 0">'
        f'<span style="background:{mag_color};color:white;padding:1px 6px;border-radius:8px;'
        f'font-size:0.7em;font-weight:700;text-transform:uppercase">{mag}</span> '
        f'<span style="color:#9ca3af;font-size:0.8em;margin-left:4px">'
        f'{z:+.1f}\u03c3 \u00b7 P{pctl:.0f}{streak_text}</span>'
        f'</div>'
        f'<small style="color:#9ca3af">{arrow} '
        f'{"Up" if direction == "improving" else "Down" if direction == "deteriorating" else "Flat"}'
        f'</small>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Nav button to detail page
    if st.button("Details →", key=f"card_nav_{ind.fred_id}", type="secondary"):
        st.session_state["detail_indicator"] = ind.fred_id
        st.switch_page(st.session_state["_pages"]["detail"])


def _render_nber_card(ind, df) -> None:
    """Special card for the binary NBER recession indicator."""
    if df.empty:
        st.metric(label=ind.name, value="No data")
        return

    latest = int(df["value"].iloc[-1])
    latest_date = df.index[-1]

    if latest == 1:
        status, status_color, icon = "RECESSION", RED, "🔴"
        msg = "The NBER has officially declared a recession."
    else:
        status, status_color, icon = "EXPANSION", GREEN, "🟢"
        recessions = df[df["value"] == 1]
        if not recessions.empty:
            last_rec_end = recessions.index[-1]
            months_since = (latest_date - last_rec_end).days // 30
            msg = f"Current expansion: ~{months_since} months."
        else:
            msg = "No recession in available data."

    html = (
        f'<div style="text-align:center;padding:10px 0">'
        f'<div style="font-size:0.85em;color:#9ca3af;margin-bottom:4px">{ind.name}</div>'
        f'<div style="font-size:2.2em">{icon}</div>'
        f'<div style="font-size:1.1em;font-weight:700;color:{status_color};margin-top:4px">'
        f'{status}</div>'
        f'<div style="font-size:0.8em;color:#9ca3af;margin-top:6px">{msg}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
