"""Data Release Timeline — chronological view of indicator releases by month."""

from __future__ import annotations

from datetime import datetime
from calendar import month_abbr

import pandas as pd
import streamlit as st

from econ_monitor.config.indicators import INDICATORS, CATEGORY_ORDER
from econ_monitor.data import cache
from econ_monitor.analytics.transforms import apply_transform
from econ_monitor.ui.styles import (
    format_value, trend_color, trend_arrow, CATEGORY_COLORS, GRAY,
)


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📜 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Data Release Timeline</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption("Historical indicator releases organized by month")

    # ── Filters ──────────────────────────────────────────────────────────
    col_month, col_cat, col_spacer = st.columns([1.5, 1.5, 4])

    # Build month options from available data (last 24 months)
    now = pd.Timestamp.now()
    month_options = []
    for i in range(24):
        dt = now - pd.DateOffset(months=i)
        label = dt.strftime("%b %Y")
        month_options.append((label, dt.year, dt.month))

    with col_month:
        selected_label = st.selectbox(
            "Month",
            options=[m[0] for m in month_options],
            index=0,
            key="timeline_month",
        )

    sel_year = None
    sel_month = None
    for label, yr, mo in month_options:
        if label == selected_label:
            sel_year, sel_month = yr, mo
            break

    # Category filter
    categories = ["All"] + [c for c in CATEGORY_ORDER if c != "Regime"]
    with col_cat:
        selected_cat = st.selectbox(
            "Category",
            options=categories,
            index=0,
            key="timeline_cat",
        )

    # ── Gather data for selected month ───────────────────────────────────
    entries = _gather_month_data(sel_year, sel_month, selected_cat)

    if not entries:
        st.info(f"No data found for {selected_label}. Try a different month or category.")
        return

    # ── Summary metrics ──────────────────────────────────────────────────
    n_indicators = len(entries)
    n_improving = sum(1 for e in entries if e["direction"] == "improving")
    n_deteriorating = sum(1 for e in entries if e["direction"] == "deteriorating")
    n_stable = n_indicators - n_improving - n_deteriorating

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Releases", n_indicators)
    m2.metric("Improving", n_improving, delta=None)
    m3.metric("Stable", n_stable, delta=None)
    m4.metric("Deteriorating", n_deteriorating, delta=None)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Group by week ────────────────────────────────────────────────────
    weeks = _group_by_week(entries, sel_year, sel_month)

    for week_label, week_entries in weeks:
        # Week header
        st.markdown(
            f'<div style="color:#64748b;font-size:0.8em;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:1.5px;'
            f'margin:20px 0 10px 0;padding-bottom:6px;'
            f'border-bottom:1px solid rgba(255,255,255,0.06)">'
            f'📅 {week_label}</div>',
            unsafe_allow_html=True,
        )

        # Render each entry
        for entry in week_entries:
            _render_entry(entry)


# ── Data gathering ───────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def _gather_month_data(year: int, month: int, category: str) -> list[dict]:
    """Collect all indicator observations for a given month."""
    entries = []

    for fred_id, ind in INDICATORS.items():
        if ind.category == "Regime":
            continue
        if category != "All" and ind.category != category:
            continue

        df = cache.get_observations(fred_id)
        if df.empty or len(df) < 2:
            continue

        # Apply transform to get display values
        transformed = apply_transform(df["value"], ind.transform, ind.frequency).dropna()
        if transformed.empty:
            continue

        # Filter to selected month — use the observation date
        month_mask = (transformed.index.year == year) & (transformed.index.month == month)
        month_data = transformed[month_mask]

        if month_data.empty:
            continue

        # Get the latest observation in this month
        latest_date = month_data.index[-1]
        latest_val = float(month_data.iloc[-1])

        # Get previous observation (before this month)
        before = transformed[transformed.index < pd.Timestamp(year, month, 1)]
        prev_val = float(before.iloc[-1]) if not before.empty else None

        # Compute change
        if prev_val is not None:
            change = latest_val - prev_val
        else:
            change = 0.0

        # Determine direction using the same logic as overview
        from econ_monitor.analytics.transforms import trend_direction
        direction = trend_direction(transformed)

        entries.append({
            "fred_id": fred_id,
            "name": ind.name,
            "category": ind.category,
            "date": latest_date,
            "value": latest_val,
            "prev_value": prev_val,
            "change": change,
            "direction": direction,
            "higher_is": ind.higher_is,
            "unit": ind.unit,
            "transform": ind.transform,
            "frequency": ind.frequency,
        })

    # Sort by date descending
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def _group_by_week(entries: list[dict], year: int, month: int) -> list[tuple[str, list]]:
    """Group entries by week within the month."""
    if not entries:
        return []

    # Assign each entry to a week number (1-based from start of month)
    week_groups: dict[int, list] = {}
    for entry in entries:
        day = entry["date"].day
        week_num = (day - 1) // 7  # 0-indexed week
        week_groups.setdefault(week_num, []).append(entry)

    # Build sorted list of (label, entries) — newest week first
    result = []
    month_name = month_abbr[month]
    for week_num in sorted(week_groups.keys(), reverse=True):
        start_day = week_num * 7 + 1
        end_day = min(start_day + 6, 31)
        label = f"Week of {month_name} {start_day}–{end_day}"
        result.append((label, week_groups[week_num]))

    return result


# ── Rendering ────────────────────────────────────────────────────────────────

def _render_entry(entry: dict) -> None:
    """Render a single timeline entry as a styled row."""
    cat_color = CATEGORY_COLORS.get(entry["category"], GRAY)
    arrow = trend_arrow(entry["direction"], entry["higher_is"])
    color = trend_color(entry["direction"], entry["higher_is"])
    val_str = format_value(entry["value"], entry["unit"], entry["transform"])
    date_str = entry["date"].strftime("%b %d")

    # Previous value and change display
    if entry["prev_value"] is not None:
        prev_str = format_value(entry["prev_value"], entry["unit"], entry["transform"])
        change_val = entry["change"]
        if abs(change_val) < 0.01:
            change_str = "unchanged"
        else:
            sign = "+" if change_val > 0 else ""
            if entry["transform"] in ("yoy_pct", "mom_pct", "annualized"):
                change_str = f"{sign}{change_val:.1f}pp"
            elif entry["unit"] in ("thousands", "millions"):
                change_str = f"{sign}{change_val:,.0f}"
            else:
                change_str = f"{sign}{change_val:.2f}"
        prev_html = (
            f'<span style="color:#475569;font-size:0.82em;margin-left:8px">'
            f'from {prev_str}</span>'
        )
        change_html = (
            f'<span style="color:{color};font-size:0.85em;font-weight:600;'
            f'margin-left:6px">{arrow} {change_str}</span>'
        )
    else:
        prev_html = ""
        change_html = ""

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;'
        f'padding:10px 16px;margin:4px 0;border-radius:10px;'
        f'background:rgba(255,255,255,0.02);'
        f'border:1px solid rgba(255,255,255,0.04);'
        f'transition:all 0.2s ease">'
        # Category badge
        f'<span style="background:{cat_color}20;color:{cat_color};'
        f'font-size:0.65em;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;padding:3px 8px;border-radius:6px;'
        f'white-space:nowrap;min-width:70px;text-align:center">'
        f'{entry["category"]}</span>'
        # Indicator name
        f'<span style="color:#e2e8f0;font-weight:600;font-size:0.9em;'
        f'flex:1;min-width:180px">{entry["name"]}</span>'
        # Value
        f'<span style="color:#f1f5f9;font-weight:700;font-size:0.95em;'
        f'font-family:\'Inter\',monospace;min-width:90px;text-align:right">'
        f'{val_str}</span>'
        # Change
        f'{change_html}'
        # Previous
        f'{prev_html}'
        # Date
        f'<span style="color:#475569;font-size:0.8em;min-width:50px;'
        f'text-align:right;white-space:nowrap">{date_str}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
