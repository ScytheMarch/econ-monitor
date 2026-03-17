"""Indicator Guide — plain-English reference for every tracked indicator."""

from __future__ import annotations

import streamlit as st

from econ_monitor.config.indicators import (
    INDICATORS, CATEGORY_ORDER, get_indicators_by_category, WHY_IT_MATTERS,
)
from econ_monitor.data import cache
from econ_monitor.ui.styles import CATEGORY_COLORS, GRAY, GREEN, RED, YELLOW


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📖 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Indicator Guide</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Quick reference for every economic indicator tracked by this dashboard. "
        "What it measures, why it matters, and key thresholds to watch."
    )

    # ── How to Read This Dashboard (collapsible tutorial) ─────────────
    with st.expander("📘 **How to Read This Dashboard** — Z-scores, signals, gauges & key thresholds", expanded=False):
        st.markdown(
            '<div style="font-size:0.92em;color:#cbd5e1;line-height:1.7">'

            # Z-Score explanation
            '<div style="margin-bottom:16px">'
            '<div style="color:#c7d2fe;font-weight:700;font-size:1.05em;margin-bottom:6px">'
            '📊 What is a Z-Score?</div>'
            'A Z-score tells you <b>how unusual</b> the current reading is compared to recent history. '
            'It measures how many standard deviations (σ) the value is from the average.<br><br>'
            '<div style="display:grid;grid-template-columns:auto 1fr;gap:4px 16px;font-size:0.92em;'
            'padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid rgba(255,255,255,0.06)">'
            '<span style="color:#6b7280;font-weight:600">0σ</span><span>Exactly at the historical average</span>'
            '<span style="color:#eab308;font-weight:600">±1σ</span><span>Moderate move — worth noting but not unusual</span>'
            '<span style="color:#f97316;font-weight:600">±2σ</span><span>Large move — this happens &lt;5% of the time</span>'
            '<span style="color:#ef4444;font-weight:600">±3σ</span><span>Extreme — very rare, top/bottom ~1% of readings</span>'
            '</div>'
            '</div>'

            # Signal colors
            '<div style="margin-bottom:16px">'
            '<div style="color:#c7d2fe;font-weight:700;font-size:1.05em;margin-bottom:6px">'
            '🚦 Signal Colors</div>'
            'On each indicator\'s Significance tab, you\'ll see a color-coded signal card:<br><br>'
            '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:0.92em">'
            '<span>🟢 <b style="color:#22c55e">Favorable</b></span>'
            '<span>Conditions improving — inflation cooling, jobs growing, stress easing</span>'
            '<span>🟡 <b style="color:#eab308">Watch</b></span>'
            '<span>Notable but not alarming — keep an eye on the next reading</span>'
            '<span>🔴 <b style="color:#ef4444">Warning</b></span>'
            '<span>Stress signal — inflation rising sharply, jobs dropping, credit tightening</span>'
            '<span>⚪ <b style="color:#94a3b8">Neutral</b></span>'
            '<span>Within normal range — no strong signal in either direction</span>'
            '</div>'
            '</div>'

            # Direction badges
            '<div style="margin-bottom:16px">'
            '<div style="color:#c7d2fe;font-weight:700;font-size:1.05em;margin-bottom:6px">'
            '↕️ What "Higher Is" Means</div>'
            'Each indicator has a direction tag explaining what happens when the number goes up:<br><br>'
            '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:0.92em">'
            '<span style="background:#22c55e;color:white;padding:1px 8px;border-radius:10px;font-size:0.85em;font-weight:700">↑ = GROWTH</span>'
            '<span>Higher is good — more jobs, more output, stronger economy</span>'
            '<span style="background:#ef4444;color:white;padding:1px 8px;border-radius:10px;font-size:0.85em;font-weight:700">↑ = INFLATION</span>'
            '<span>Higher is concerning — prices rising faster, squeezing budgets</span>'
            '<span style="background:#eab308;color:black;padding:1px 8px;border-radius:10px;font-size:0.85em;font-weight:700">↑ = WEAKNESS</span>'
            '<span>Higher is bad — more unemployment claims, more delinquencies</span>'
            '<span style="background:#6b7280;color:white;padding:1px 8px;border-radius:10px;font-size:0.85em;font-weight:700">NEUTRAL</span>'
            '<span>Depends on context — yield levels, spreads, etc.</span>'
            '</div>'
            '</div>'

            # Key thresholds cheat sheet
            '<div style="margin-bottom:16px">'
            '<div style="color:#c7d2fe;font-weight:700;font-size:1.05em;margin-bottom:6px">'
            '🎯 Key Thresholds Cheat Sheet</div>'
            '<div style="font-size:0.92em">'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">10Y-2Y Yield Spread (T10Y2Y)</div>'
            '<b style="color:#22c55e">Positive (e.g. +1.5)</b> = Normal — long-term rates above short-term, economy expected to grow<br>'
            '<b style="color:#eab308">Near zero (±0.2)</b> = Flattening — market uncertainty about growth outlook<br>'
            '<b style="color:#ef4444">Negative (e.g. -0.5)</b> = Inverted — recession warning, every recession since 1970 was preceded by this<br>'
            '<span style="color:#94a3b8">When it <i>un-inverts</i> (goes from negative back to positive), recession may be imminent — that\'s the "re-steepening" signal</span>'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">2Y vs 10Y Treasury Yields (DGS2 / DGS10)</div>'
            '<b style="color:#ef4444">2Y rising, 10Y falling</b> = Curve flattening/inverting — market expects rate cuts ahead (recession risk)<br>'
            '<b style="color:#22c55e">2Y falling, 10Y rising</b> = Curve steepening — market expects growth + inflation (bullish)<br>'
            '<b>Both rising</b> = Fed tightening, inflation fears across the board<br>'
            '<b>Both falling</b> = Flight to safety, slowdown expected'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">Unemployment Rate (UNRATE)</div>'
            '<b style="color:#22c55e">Below 4%</b> = Full employment — labor market is tight<br>'
            '<b style="color:#eab308">4-5%</b> = Normal range<br>'
            '<b style="color:#ef4444">Above 5%</b> = Elevated — signals economic weakness<br>'
            '<span style="color:#94a3b8">The Sahm Rule: if the 3-month average rises 0.5% from its 12-month low, recession has likely started</span>'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">Core PCE / Core CPI (Inflation)</div>'
            '<b style="color:#22c55e">Below 2% YoY</b> = Fed\'s target — "mission accomplished"<br>'
            '<b style="color:#eab308">2-3% YoY</b> = Slightly hot — Fed may hold rates<br>'
            '<b style="color:#ef4444">Above 3% YoY</b> = Too hot — Fed likely hiking or holding high<br>'
            '<b style="color:#ef4444">Above 5% YoY</b> = Crisis-level — aggressive tightening expected'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">Initial Jobless Claims (ICSA)</div>'
            '<b style="color:#22c55e">Below 220K</b> = Very healthy labor market<br>'
            '<b style="color:#eab308">220-280K</b> = Normal range<br>'
            '<b style="color:#ef4444">Above 300K</b> = Trouble — layoffs accelerating<br>'
            '<b style="color:#ef4444">Above 400K</b> = Recessionary territory'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">Nonfarm Payrolls (PAYEMS)</div>'
            '<b style="color:#22c55e">Above 200K/mo</b> = Strong job growth<br>'
            '<b style="color:#eab308">100-200K/mo</b> = Moderate — economy coasting<br>'
            '<b style="color:#ef4444">Below 100K/mo</b> = Weak — barely keeping up with population growth<br>'
            '<b style="color:#ef4444">Negative</b> = Economy is shedding jobs — recession signal'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">VIX — Fear Index (VIXCLS)</div>'
            '<b style="color:#22c55e">Below 15</b> = Calm markets, possible complacency<br>'
            '<b style="color:#eab308">15-25</b> = Normal range<br>'
            '<b style="color:#ef4444">25-35</b> = Elevated fear, increased hedging<br>'
            '<b style="color:#ef4444">Above 35</b> = Panic — usually during market crashes'
            '</div>'

            '<div style="padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:10px;'
            'border:1px solid rgba(255,255,255,0.06)">'
            '<div style="color:#818cf8;font-weight:700;margin-bottom:4px">High Yield Credit Spread (BAMLH0A0HYM2)</div>'
            '<b style="color:#22c55e">Below 3%</b> = Very tight — markets confident (maybe too confident)<br>'
            '<b style="color:#eab308">3-5%</b> = Normal — healthy risk premium<br>'
            '<b style="color:#ef4444">5-8%</b> = Stress — investors demanding more compensation for risk<br>'
            '<b style="color:#ef4444">Above 8%</b> = Crisis — credit markets seizing up'
            '</div>'

            '</div></div>'

            # How to use the dashboard
            '<div>'
            '<div style="color:#c7d2fe;font-weight:700;font-size:1.05em;margin-bottom:6px">'
            '💡 Quick Tips</div>'
            '<div style="font-size:0.92em">'
            '• <b>Streaks matter</b> — 4+ consecutive rises/falls in an indicator usually signal a real trend, not noise<br>'
            '• <b>Watch for divergences</b> — if the stock market is rallying but macro data is weakening, one of them is wrong<br>'
            '• <b>Z-scores are relative</b> — a +2σ reading in CPI is alarming; a +2σ reading in GDP is great. The signal card color tells you which<br>'
            '• <b>Yield curve inversions lead by 12-18 months</b> — an inversion today doesn\'t mean recession tomorrow<br>'
            '• <b>Click any indicator → Detail page</b> for the full chart, Z-score gauge, and significance analysis'
            '</div>'
            '</div>'

            '</div>',
            unsafe_allow_html=True,
        )

    # Quick legend
    st.markdown(
        '<div style="display:flex;gap:20px;margin-bottom:16px;font-size:0.85em;color:#9ca3af">'
        '<span><span style="color:#22c55e;font-weight:700">▲ Expansionary</span> = higher is good for growth</span>'
        '<span><span style="color:#ef4444;font-weight:700">▲ Inflationary</span> = higher means price pressure</span>'
        '<span><span style="color:#eab308;font-weight:700">▲ Contractionary</span> = higher signals weakness</span>'
        '<span><span style="color:#6b7280;font-weight:700">— Neutral</span> = direction is context-dependent</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Search filter
    search = st.text_input("🔎 Filter indicators", placeholder="e.g. CPI, jobs, yield curve...")

    groups = get_indicators_by_category()

    for cat in CATEGORY_ORDER:
        indicators = groups.get(cat, [])
        if not indicators:
            continue

        # Filter
        if search:
            search_lower = search.lower()
            indicators = [
                ind for ind in indicators
                if search_lower in ind.name.lower()
                or search_lower in ind.fred_id.lower()
                or search_lower in ind.description.lower()
                or search_lower in WHY_IT_MATTERS.get(ind.fred_id, "").lower()
            ]
            if not indicators:
                continue

        cat_color = CATEGORY_COLORS.get(cat, GRAY)

        # Collapsed by default — search expands all matches
        with st.expander(f"**{cat}** ({len(indicators)} indicators)", expanded=bool(search)):
            for ind in indicators:
                _render_guide_entry(ind, cat_color)


def _interpret_reading(ind, latest: float, prev: float, change: float, unit_suffix: str) -> str:
    """Generate a plain-English sentence explaining what the current reading means."""
    abs_change = abs(change)
    went_up = change > 0
    went_down = change < 0

    # ── Percentage-based transforms (YoY, MoM, annualized) ────────────
    if ind.transform == "yoy_pct":
        if ind.higher_is == "inflationary":
            if latest > 0:
                base = f"Prices rose {latest:.1f}% from a year ago"
            elif latest < 0:
                base = f"Prices fell {abs(latest):.1f}% from a year ago"
            else:
                base = "Prices unchanged from a year ago"
            if went_up:
                return base + " — inflation accelerating"
            elif went_down:
                return base + " — inflation cooling"
            return base
        elif ind.higher_is == "expansionary":
            if went_up:
                return f"Growing {latest:.1f}% year-over-year — accelerating"
            elif went_down and latest > 0:
                return f"Growing {latest:.1f}% year-over-year — slowing"
            elif latest < 0:
                return f"Contracting {abs(latest):.1f}% year-over-year"
            return f"Growing {latest:.1f}% year-over-year"
        else:
            direction = "up" if latest > 0 else "down"
            return f"{direction.title()} {abs(latest):.1f}% from a year ago"

    if ind.transform == "mom_pct":
        direction = "up" if latest > 0 else "down" if latest < 0 else "flat"
        return f"{direction.title()} {abs(latest):.1f}% from prior month"

    if ind.transform == "annualized":
        if latest > 0:
            return f"Growing at a {latest:.1f}% annualized pace"
        elif latest < 0:
            return f"Contracting at a {abs(latest):.1f}% annualized pace"
        return "Flat growth"

    # ── Net change (like NFP: +126K jobs added) ───────────────────────
    if ind.transform == "net_change":
        sfx = unit_suffix or ""
        if latest > 0:
            return f"Economy added {latest:,.0f}{sfx} — positive growth"
        elif latest < 0:
            return f"Economy lost {abs(latest):,.0f}{sfx} — contraction signal"
        return "No change from prior month"

    # ── Level-based indicators ────────────────────────────────────────
    if ind.unit == "percent":
        # Things like unemployment rate, fed funds rate
        if ind.higher_is == "contractionary":
            if went_up:
                return f"Rate at {latest:.1f}% — rising is a warning sign"
            elif went_down:
                return f"Rate at {latest:.1f}% — falling is a positive sign"
            return f"Rate holding steady at {latest:.1f}%"
        elif ind.higher_is == "expansionary":
            if went_up:
                return f"Rate at {latest:.1f}% — rising signals strength"
            elif went_down:
                return f"Rate at {latest:.1f}% — falling signals weakness"
            return f"Rate steady at {latest:.1f}%"
        elif ind.higher_is == "inflationary":
            if went_up:
                return f"At {latest:.1f}% — rising adds inflation pressure"
            elif went_down:
                return f"At {latest:.1f}% — easing reduces pressure"
            return f"Holding at {latest:.1f}%"
        return f"Currently at {latest:.1f}%"

    if ind.unit == "index":
        if ind.higher_is == "contractionary":
            # VIX-style: higher = more fear
            if went_up:
                return f"Index at {latest:.1f} — elevated, signals stress"
            elif went_down:
                return f"Index at {latest:.1f} — easing, calmer conditions"
            return f"Index steady at {latest:.1f}"
        elif ind.higher_is == "expansionary":
            if went_up:
                return f"Index at {latest:.1f} — rising signals strength"
            elif went_down:
                return f"Index at {latest:.1f} — falling signals softening"
            return f"Index steady at {latest:.1f}"
        return f"Index at {latest:.1f}"

    if ind.unit == "ratio":
        if went_up:
            return f"Spread at {latest:.2f} — widening"
        elif went_down:
            return f"Spread at {latest:.2f} — narrowing"
        return f"Spread at {latest:.2f}"

    # Fallback for thousands/millions/billions in level mode
    sfx = unit_suffix or ""
    if went_up:
        return f"At {latest:,.0f}{sfx} — rising"
    elif went_down:
        return f"At {latest:,.0f}{sfx} — declining"
    return f"At {latest:,.0f}{sfx}"


def _render_guide_entry(ind, cat_color: str) -> None:
    """Render a single indicator guide entry."""
    explainer = WHY_IT_MATTERS.get(ind.fred_id, "")

    # Semantic direction badge — explain what "higher" means for this indicator
    if ind.higher_is == "expansionary":
        dir_badge = '<span style="background:#22c55e;color:white;padding:1px 8px;border-radius:10px;font-size:0.7em;font-weight:700" title="Higher values = economic growth">↑ = GROWTH</span>'
    elif ind.higher_is == "inflationary":
        dir_badge = '<span style="background:#ef4444;color:white;padding:1px 8px;border-radius:10px;font-size:0.7em;font-weight:700" title="Higher values = more inflation pressure">↑ = INFLATION</span>'
    elif ind.higher_is == "contractionary":
        dir_badge = '<span style="background:#eab308;color:black;padding:1px 8px;border-radius:10px;font-size:0.7em;font-weight:700" title="Higher values = economic weakness">↑ = WEAKNESS</span>'
    else:
        dir_badge = '<span style="background:#6b7280;color:white;padding:1px 8px;border-radius:10px;font-size:0.7em;font-weight:700" title="Direction depends on context">NEUTRAL</span>'

    # Frequency badge
    freq_colors = {
        "daily": "#3b82f6",
        "weekly": "#8b5cf6",
        "monthly": "#f59e0b",
        "quarterly": "#ec4899",
    }
    freq_color = freq_colors.get(ind.frequency, "#6b7280")
    freq_badge = (
        f'<span style="background:{freq_color};color:white;padding:1px 8px;'
        f'border-radius:10px;font-size:0.7em;font-weight:600">{ind.frequency.upper()}</span>'
    )

    # Current + previous value display
    from econ_monitor.ui.styles import format_value
    from econ_monitor.analytics.transforms import apply_transform

    # Human-readable transform labels — reads as "Down 0.1 pts from prior year" etc.
    transform_context = {
        "yoy_pct": "from prior year",
        "mom_pct": "from prior month",
        "net_change": "from prior month",
        "annualized": "annualized rate",
        "level": "",
    }
    reading_context = transform_context.get(ind.transform, "")

    df = cache.get_observations(ind.fred_id)
    if not df.empty and len(df) >= 2:
        transformed = apply_transform(df["value"], ind.transform, ind.frequency).dropna()
        if len(transformed) >= 2:
            latest_num = float(transformed.iloc[-1])
            prev_num = float(transformed.iloc[-2])
            latest_date = transformed.index[-1]
            prev_date = transformed.index[-2]

            # Format the date nicely
            latest_date_nice = latest_date.strftime("%b %Y")
            prev_date_nice = prev_date.strftime("%b %Y")

            try:
                disp_latest = format_value(latest_num, ind.unit, ind.transform)
                disp_prev = format_value(prev_num, ind.unit, ind.transform)
            except (ValueError, TypeError):
                disp_latest = f"{latest_num:.2f}"
                disp_prev = f"{prev_num:.2f}"

            # Unit suffix so numbers have meaning — "92K jobs" not just "92"
            unit_suffix_map = {
                "thousands": "K",
                "millions": "M",
                "billions": "B",
            }
            unit_suffix = unit_suffix_map.get(ind.unit, "")

            # For non-percentage units, append the suffix to the displayed values
            if unit_suffix and ind.transform not in ("yoy_pct", "mom_pct", "annualized"):
                disp_latest = disp_latest + unit_suffix
                disp_prev = disp_prev + unit_suffix

            change = latest_num - prev_num
            if change > 0:
                arrow = "▲"
                change_word = "Up"
                chg_color = "#22c55e" if ind.higher_is == "expansionary" else "#ef4444" if ind.higher_is in ("inflationary", "contractionary") else "#9ca3af"
            elif change < 0:
                arrow = "▼"
                change_word = "Down"
                chg_color = "#ef4444" if ind.higher_is == "expansionary" else "#22c55e" if ind.higher_is in ("inflationary", "contractionary") else "#9ca3af"
            else:
                arrow = "▬"
                change_word = "Flat"
                chg_color = "#6b7280"

            # Change description — use "pts" for percentage-based transforms, unit suffix for others
            if ind.transform in ("yoy_pct", "mom_pct", "annualized") or (ind.unit == "percent" and not unit_suffix):
                chg_desc = f"{abs(change):.1f} pts"
            elif ind.unit in ("thousands", "millions", "billions") and abs(change) >= 1:
                chg_desc = f"{abs(change):,.0f}{unit_suffix}"
            else:
                chg_desc = f"{abs(change):.2f}"

            # Plain-English interpretation of the current reading
            interpretation = _interpret_reading(ind, latest_num, prev_num, change, unit_suffix)

            val_html = (
                f'<div style="text-align:right;line-height:1.5">'
                # Latest reading — big and clear
                f'<div>'
                f'<span style="color:#9ca3af;font-size:0.72em;text-transform:uppercase;letter-spacing:0.5px">Latest</span> '
                f'<span style="color:#e5e7eb;font-weight:700;font-size:1.15em">{disp_latest}</span>'
                f' <span style="color:{chg_color};font-weight:700;font-size:0.9em">{arrow}</span>'
                f'</div>'
                # Previous reading
                f'<div style="margin-top:1px">'
                f'<span style="color:#6b7280;font-size:0.72em;text-transform:uppercase;letter-spacing:0.5px">Prior</span> '
                f'<span style="color:#6b7280;font-size:0.88em">{disp_prev}</span>'
                f'</div>'
                # Plain-English what-it-means line
                f'<div style="margin-top:4px;color:{chg_color};font-size:0.78em;font-style:italic">'
                f'{interpretation}'
                f'</div>'
                # Date of latest reading
                f'<div style="color:#4b5563;font-size:0.68em;margin-top:2px">'
                f'as of {latest_date_nice}'
                f'</div>'
                f'</div>'
            )
        else:
            val_html = '<span style="color:#6b7280">Insufficient data</span>'
    else:
        val_html = '<span style="color:#6b7280">No data</span>'

    html = (
        f'<div style="border-left:3px solid {cat_color};padding:12px 16px;margin-bottom:10px;'
        f'background:rgba(255,255,255,0.03);border-radius:0 8px 8px 0">'
        # Header row
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">'
        f'<div>'
        f'<strong style="font-size:1.05em">{ind.name}</strong> '
        f'<span style="color:#6b7280;font-size:0.8em">({ind.fred_id})</span> '
        f'{dir_badge} {freq_badge}'
        f'</div>'
        f'<div>{val_html}</div>'
        f'</div>'
        # Description
        f'<div style="color:#9ca3af;font-size:0.82em;margin-top:4px">{ind.description}</div>'
    )

    # Explainer
    if explainer:
        # Strip markdown bold for HTML rendering
        clean_explainer = explainer.replace("**", "")
        html += (
            f'<div style="margin-top:8px;padding:8px 12px;background:rgba(59,130,246,0.06);'
            f'border-radius:6px;font-size:0.88em;color:#d1d5db">{clean_explainer}</div>'
        )

    # Transform info
    transform_labels = {
        "level": "Raw level",
        "yoy_pct": "Year-over-year % change",
        "mom_pct": "Month-over-month % change",
        "net_change": "Month-over-month net change",
        "annualized": "Annualized quarter-over-quarter %",
    }
    transform_label = transform_labels.get(ind.transform, ind.transform)
    html += (
        f'<div style="margin-top:6px;font-size:0.78em;color:#6b7280">'
        f'Display: {transform_label} · Unit: {ind.unit} · '
        f'<a href="{ind.release_url}" style="color:#3b82f6" target="_blank">Source ↗</a>'
        f'</div>'
    )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Nav to detail page
    if st.button("View Detail →", key=f"guide_nav_{ind.fred_id}", type="secondary"):
        st.session_state["detail_indicator"] = ind.fred_id
        st.switch_page(st.session_state["_pages"]["detail"])
