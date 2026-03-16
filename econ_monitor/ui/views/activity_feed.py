"""Activity feed page: reverse-chronological log of data changes."""

from __future__ import annotations

import streamlit as st
from datetime import datetime

from econ_monitor.config.indicators import INDICATORS
from econ_monitor.data import cache
from econ_monitor.ui.styles import CATEGORY_COLORS, GREEN, RED, GRAY


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📡 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Activity Feed</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption("Recent data releases and updates detected by the monitor")

    col_limit, col_filter = st.columns([1, 2])
    with col_limit:
        limit = st.selectbox("Show last", [25, 50, 100, 200], index=1)
    with col_filter:
        categories = ["All"] + sorted(set(
            ind.category for ind in INDICATORS.values()
        ))
        cat_filter = st.selectbox("Category", categories)

    feed = cache.get_activity_feed(limit=limit)

    if not feed:
        st.info(
            "No activity yet. The feed populates as new economic data is detected. "
            "Run the initial data fetch or wait for the FRED poller."
        )
        return

    if cat_filter != "All":
        feed = [entry for entry in feed if entry.get("category") == cat_filter]

    if not feed:
        st.info(f"No activity for category: {cat_filter}")
        return

    for entry in feed:
        _render_feed_entry(entry)


def _render_feed_entry(entry: dict) -> None:
    series_id = entry.get("series_id", "")
    ind = INDICATORS.get(series_id)
    name = ind.name if ind else series_id
    category = entry.get("category", "Unknown")
    cat_color = CATEGORY_COLORS.get(category, GRAY)
    event_type = entry.get("event_type", "update")
    message = entry.get("message", "")
    old_val = entry.get("old_value")
    new_val = entry.get("new_value")
    timestamp = entry.get("timestamp", "")

    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%b %d, %Y %H:%M UTC")
    except (ValueError, TypeError):
        time_str = timestamp

    if old_val is not None and new_val is not None:
        if ind and ind.higher_is in ("contractionary", "inflationary"):
            direction_color = RED if new_val > old_val else GREEN
        else:
            direction_color = GREEN if new_val > old_val else RED
        change_str = f"{old_val:,.2f} → {new_val:,.2f}"
    else:
        direction_color = GRAY
        change_str = ""

    st.markdown(
        f"""<div style="border-left:3px solid {cat_color};padding:8px 12px;margin-bottom:8px;
                        background:rgba(255,255,255,0.03);border-radius:0 4px 4px 0">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="background:{cat_color};color:white;padding:1px 8px;border-radius:10px;
                                 font-size:0.75em;font-weight:600">{category}</span>
                    <strong style="margin-left:8px">{name}</strong>
                    <span style="color:#9ca3af;margin-left:8px;font-size:0.85em">{event_type}</span>
                </div>
                <small style="color:#9ca3af">{time_str}</small>
            </div>
            <div style="margin-top:4px">
                {"<span style='color:" + direction_color + ";font-weight:600'>" + change_str + "</span>" if change_str else ""}
                {"<span style='color:#d1d5db;margin-left:8px'>" + message + "</span>" if message else ""}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
