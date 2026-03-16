"""Economic calendar page: upcoming releases, weekly tracker, and data freshness."""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from econ_monitor.config.indicators import INDICATORS, CATEGORY_ORDER
from econ_monitor.data import cache
from econ_monitor.analytics.transforms import apply_transform, mom_pct
from econ_monitor.analytics.significance import compute_significance
from econ_monitor.ui.styles import CATEGORY_COLORS, GRAY, GREEN, RED, YELLOW


# ── Weekly / High-frequency indicators ────────────────────────────────────
_WEEKLY_INDICATORS = {
    "ICSA": {"name": "Initial Jobless Claims", "day": "Thursday", "source": "DOL"},
    "T10Y2Y": {"name": "10Y-2Y Spread", "day": "Daily", "source": "Treasury"},
    "T10Y3M": {"name": "10Y-3M Spread", "day": "Daily", "source": "Treasury"},
    "DGS10": {"name": "10Y Treasury Yield", "day": "Daily", "source": "Treasury"},
    "DGS2": {"name": "2Y Treasury Yield", "day": "Daily", "source": "Treasury"},
    "BAMLH0A0HYM2": {"name": "HY Credit Spread", "day": "Daily", "source": "ICE/FRED"},
    "VIXCLS": {"name": "VIX", "day": "Daily", "source": "CBOE"},
    "DTWEXBGS": {"name": "Dollar Index (DXY)", "day": "Daily", "source": "Fed"},
}

# Monthly release schedule with approximate timing
_MONTHLY_RELEASES = [
    {"name": "Nonfarm Payrolls + Unemployment", "ids": ["PAYEMS", "UNRATE", "CES0500000003"],
     "timing": "1st Friday", "source": "BLS", "importance": "HIGH"},
    {"name": "CPI / Core CPI", "ids": ["CPIAUCSL", "CPILFESL"],
     "timing": "10th-14th", "source": "BLS", "importance": "HIGH"},
    {"name": "PPI", "ids": ["PPIFIS"],
     "timing": "13th-16th", "source": "BLS", "importance": "MEDIUM"},
    {"name": "Retail Sales", "ids": ["RSAFS"],
     "timing": "14th-17th", "source": "Census", "importance": "HIGH"},
    {"name": "Industrial Production", "ids": ["INDPRO", "TCU"],
     "timing": "15th-17th", "source": "Fed", "importance": "MEDIUM"},
    {"name": "Housing Starts / Permits", "ids": ["HOUST", "PERMIT"],
     "timing": "17th-20th", "source": "Census", "importance": "MEDIUM"},
    {"name": "Existing Home Sales", "ids": ["EXHOSLUSM495S"],
     "timing": "20th-23rd", "source": "NAR", "importance": "MEDIUM"},
    {"name": "New Home Sales", "ids": ["HSN1F"],
     "timing": "24th-27th", "source": "Census", "importance": "MEDIUM"},
    {"name": "PCE / Core PCE / Income / Spending", "ids": ["PCEPI", "PCEPILFE", "PI", "PCE", "PSAVERT"],
     "timing": "Last week", "source": "BEA", "importance": "HIGH"},
    {"name": "GDP", "ids": ["GDPC1"],
     "timing": "Late month (quarterly)", "source": "BEA", "importance": "HIGH"},
    {"name": "UMich Consumer Sentiment", "ids": ["UMCSENT"],
     "timing": "Mid-month (prelim) + End-month (final)", "source": "UMich", "importance": "MEDIUM"},
    {"name": "JOLTS", "ids": ["JTSJOL"],
     "timing": "~5 weeks lag", "source": "BLS", "importance": "MEDIUM"},
    {"name": "Trade Balance", "ids": ["BOPGSTB"],
     "timing": "5th-8th", "source": "BEA", "importance": "LOW"},
    {"name": "M2 Money Supply", "ids": ["M2SL"],
     "timing": "3rd week", "source": "Fed", "importance": "LOW"},
    {"name": "Case-Shiller HPI", "ids": ["CSUSHPINSA"],
     "timing": "Last Tuesday (2-month lag)", "source": "S&P", "importance": "LOW"},
]


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📅 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Economic Calendar</span></h2>',
        unsafe_allow_html=True,
    )

    tab_upcoming, tab_weekly, tab_freshness = st.tabs([
        "Release Schedule", "Weekly / Daily Tracker", "Data Freshness",
    ])

    with tab_upcoming:
        _render_upcoming()

    with tab_weekly:
        _render_weekly_tracker()

    with tab_freshness:
        _render_freshness()


def _render_upcoming() -> None:
    """Show the monthly release schedule with last values and data age."""
    st.subheader("Monthly Release Schedule")
    st.caption("Sorted by typical release timing within the month")

    now = datetime.now()
    current_day = now.day

    for release in _MONTHLY_RELEASES:
        importance = release["importance"]
        if importance == "HIGH":
            imp_color = RED
            imp_badge = "HIGH"
        elif importance == "MEDIUM":
            imp_color = YELLOW
            imp_badge = "MED"
        else:
            imp_color = GRAY
            imp_badge = "LOW"

        # Get latest data for all IDs in this release
        latest_info = []
        for sid in release["ids"]:
            ind = INDICATORS.get(sid)
            if not ind:
                continue
            date, val = cache.get_latest(sid)
            if date and val is not None:
                # How old is the data?
                try:
                    data_date = pd.to_datetime(date)
                    age_days = (pd.Timestamp.now() - data_date).days
                except Exception:
                    age_days = 999
                latest_info.append({
                    "name": ind.name,
                    "date": date,
                    "value": val,
                    "age_days": age_days,
                    "unit": ind.unit,
                    "transform": ind.transform,
                })

        # Determine if this release is "due soon" based on data age
        max_age = max((li["age_days"] for li in latest_info), default=0)
        if max_age > 35:
            status = "DUE"
            status_color = "#f97316"
        elif max_age > 25:
            status = "SOON"
            status_color = YELLOW
        else:
            status = "RECENT"
            status_color = GREEN

        # Render as card
        vals_html = ""
        for li in latest_info[:3]:  # Show up to 3 sub-indicators
            from econ_monitor.ui.styles import format_value
            fv = format_value(li["value"], li["unit"], li["transform"])
            vals_html += (
                f"<span style='color:#d1d5db;margin-right:12px'>"
                f"{li['name']}: <b>{fv}</b> "
                f"<small>({li['date']})</small></span>"
            )

        st.markdown(
            f"""<div style="border-left:3px solid {imp_color};padding:8px 12px;margin-bottom:6px;
                            background:rgba(255,255,255,0.03);border-radius:0 4px 4px 0">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="background:{imp_color};color:white;padding:1px 6px;border-radius:8px;
                                     font-size:0.7em;font-weight:700">{imp_badge}</span>
                        <strong style="margin-left:8px">{release['name']}</strong>
                        <span style="color:#9ca3af;margin-left:8px;font-size:0.85em">
                            {release['timing']} · {release['source']}</span>
                    </div>
                    <span style="background:{status_color};color:white;padding:1px 8px;border-radius:8px;
                                 font-size:0.7em;font-weight:700">{status}</span>
                </div>
                <div style="margin-top:4px;font-size:0.9em">{vals_html}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Weekly
    st.subheader("Recurring Weekly / Daily")
    st.markdown("""
| Indicator | Frequency | Source | Notes |
|-----------|-----------|--------|-------|
| Initial Jobless Claims | Every Thursday | DOL | Leading labor indicator |
| Treasury Yields (2Y, 10Y) | Daily | Treasury | Yield curve signal |
| Yield Curve Spreads | Daily | FRED | Recession predictor |
| VIX | Daily | CBOE | Fear gauge |
| HY Credit Spread | Daily | ICE/FRED | Credit stress |
| Dollar Index | Daily | Fed | Currency strength |
""")


def _render_weekly_tracker() -> None:
    """Dedicated weekly/daily indicators tracker with mini analysis."""
    st.subheader("Weekly & Daily Indicator Tracker")
    st.caption("High-frequency indicators updated daily or weekly")

    for sid, info in _WEEKLY_INDICATORS.items():
        ind = INDICATORS.get(sid)
        if not ind:
            continue

        df = cache.get_observations(sid)
        if df.empty:
            continue

        latest_date, latest_val = cache.get_latest(sid)
        prev_date, prev_val = cache.get_previous(sid)

        if latest_val is None:
            continue

        # Change
        if prev_val is not None:
            change = latest_val - prev_val
            pct_change = (change / abs(prev_val) * 100) if prev_val != 0 else 0
        else:
            change = 0
            pct_change = 0

        # Direction coloring (semantic)
        if ind.higher_is == "contractionary":
            dir_color = RED if change > 0 else GREEN if change < 0 else GRAY
        elif ind.higher_is == "expansionary":
            dir_color = GREEN if change > 0 else RED if change < 0 else GRAY
        else:
            dir_color = GRAY

        # 5-day / 20-day context
        recent_5 = df["value"].tail(5)
        recent_20 = df["value"].tail(20)
        avg_5 = recent_5.mean() if len(recent_5) > 0 else latest_val
        avg_20 = recent_20.mean() if len(recent_20) > 0 else latest_val
        hi_20 = recent_20.max() if len(recent_20) > 0 else latest_val
        lo_20 = recent_20.min() if len(recent_20) > 0 else latest_val

        st.markdown(
            f"""<div style="border-left:3px solid {dir_color};padding:8px 12px;margin-bottom:6px;
                            background:rgba(255,255,255,0.03);border-radius:0 4px 4px 0">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <strong>{info['name']}</strong>
                        <span style="color:#9ca3af;margin-left:8px;font-size:0.85em">
                            {info['day']} · {info['source']}</span>
                    </div>
                    <span style="color:{dir_color};font-size:1.1em;font-weight:700">
                        {latest_val:.2f}</span>
                </div>
                <div style="margin-top:4px;font-size:0.85em;color:#9ca3af">
                    <span style="color:{dir_color}">{'▲' if change > 0 else '▼' if change < 0 else '▬'}
                        {change:+.2f} ({pct_change:+.1f}%)</span>
                    <span style="margin-left:16px">5d avg: {avg_5:.2f}</span>
                    <span style="margin-left:12px">20d avg: {avg_20:.2f}</span>
                    <span style="margin-left:12px">20d range: {lo_20:.2f} – {hi_20:.2f}</span>
                    <span style="margin-left:12px">as of {latest_date}</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_freshness() -> None:
    st.subheader("Data Freshness")
    st.caption("How recently each indicator was fetched")

    rows = []
    for fred_id, ind in INDICATORS.items():
        meta = cache.get_metadata(fred_id)
        latest_date, latest_val = cache.get_latest(fred_id)

        last_fetched = "Never"
        stale = True
        if meta and meta.get("last_fetched"):
            last_fetched = meta["last_fetched"][:19].replace("T", " ")
            stale = cache.is_stale(fred_id, max_age_hours=24)

        rows.append({
            "Indicator": ind.name,
            "Category": ind.category,
            "Frequency": ind.frequency,
            "Last Data Point": latest_date or "N/A",
            "Last Fetched": last_fetched,
            "Status": "Fresh" if not stale else "Stale",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True)

    total = len(rows)
    fresh = sum(1 for r in rows if r["Status"] == "Fresh")
    stale = total - fresh

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Indicators", total)
    col2.metric("Fresh (< 24h)", fresh)
    col3.metric("Stale", stale)
