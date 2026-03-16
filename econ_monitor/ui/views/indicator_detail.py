"""Indicator detail page: deep-dive charts and significance analysis."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from econ_monitor.config.indicators import INDICATORS, WHY_IT_MATTERS
from econ_monitor.data import cache
from econ_monitor.analytics.transforms import (
    apply_transform, mom_pct, yoy_pct,
    latest_z_score, compute_summary, trend_direction,
)
from econ_monitor.analytics.significance import compute_significance
from econ_monitor.ui import charts
from econ_monitor.ui.styles import format_value, trend_color, trend_arrow


def _get_recession_periods() -> list[tuple[str, str]]:
    df = cache.get_observations("USREC")
    if df.empty:
        return []
    periods = []
    in_recession = False
    start = None
    for date, row in df.iterrows():
        if row["value"] == 1 and not in_recession:
            start = date.strftime("%Y-%m-%d")
            in_recession = True
        elif row["value"] == 0 and in_recession:
            periods.append((start, date.strftime("%Y-%m-%d")))
            in_recession = False
    if in_recession and start:
        periods.append((start, df.index[-1].strftime("%Y-%m-%d")))
    return periods


def render() -> None:
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:0">'
        '🔍 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Indicator Detail</span></h2>',
        unsafe_allow_html=True,
    )

    selected_id = st.session_state.get("detail_indicator")

    # Build options grouped by category
    from econ_monitor.config.indicators import CATEGORY_ORDER
    ordered_ids = []
    id_to_label = {}
    for cat in CATEGORY_ORDER:
        cat_inds = [(ind.fred_id, ind.name) for ind in INDICATORS.values() if ind.category == cat]
        for fid, name in sorted(cat_inds, key=lambda x: x[1]):
            ordered_ids.append(fid)
            id_to_label[fid] = f"{cat} \u203a {name}"

    selected_id = st.selectbox(
        "Select Indicator",
        options=ordered_ids,
        format_func=lambda x: id_to_label.get(x, x),
        index=ordered_ids.index(selected_id) if selected_id in ordered_ids else 0,
    )

    if not selected_id:
        return

    ind = INDICATORS[selected_id]
    st.session_state["detail_indicator"] = selected_id

    df = cache.get_observations(selected_id)
    if df.empty:
        st.warning(f"No data available for {ind.name}. Run initial data fetch first.")
        return

    # ── Time range — compact horizontal radio ──────────────────────────
    range_options = {
        "3M": 100, "6M": 200, "1Y": 380, "2Y": 750,
        "3Y": 1110, "5Y": 1850, "10Y": 3660, "Max": None,
    }
    prev_range = st.session_state.get("detail_range", "5Y")
    if prev_range not in range_options:
        prev_range = "5Y"

    selected_range = st.radio(
        "Time Range",
        options=list(range_options.keys()),
        index=list(range_options.keys()).index(prev_range),
        horizontal=True,
        key="detail_range_radio",
    )
    st.session_state["detail_range"] = selected_range

    days = range_options[selected_range]
    if days:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
        plot_df = df[df.index >= cutoff]
    else:
        plot_df = df

    # ── Pre-compute everything we need ─────────────────────────────────
    sig = compute_significance(df["value"], ind.transform, ind.frequency, ind.higher_is)
    full_transformed = apply_transform(df["value"], ind.transform, ind.frequency)
    z_full = latest_z_score(full_transformed, lookback=60)

    if days:
        transformed_plot = full_transformed[full_transformed.index >= cutoff]
    else:
        transformed_plot = full_transformed
    summary = compute_summary(transformed_plot)

    direction = trend_direction(full_transformed.dropna(), window=6)
    color = trend_color(direction, ind.higher_is)
    arrow = trend_arrow(direction, ind.higher_is)

    # ── Metrics row (always visible hero) ──────────────────────────────
    # Use short trend labels so they don't truncate in narrow columns
    _short_trend = {
        "improving": "Up",
        "deteriorating": "Down",
        "stable": "Flat",
    }
    trend_label = f"{arrow} {_short_trend.get(direction, direction.title())}"

    if summary:
        # Build list of metrics to show, then use only as many columns as needed
        metrics = [
            ("Latest", format_value(summary.get("latest"), ind.unit, ind.transform)),
            ("Previous", format_value(summary.get("previous"), ind.unit, ind.transform)),
        ]
        change = summary.get("change")
        if change is not None:
            metrics.append(("Change", f"{change:+.2f}"))
        metrics.append(("Z-Score", f"{sig['z_score']:+.2f}\u03c3"))
        metrics.append(("Trend", trend_label))
        if sig["streak"] != 0:
            streak_dir = "\u25b2" if sig["streak"] > 0 else "\u25bc"
            metrics.append(("Streak", f"{streak_dir} {abs(sig['streak'])}"))

        cols = st.columns(len(metrics))
        for i, (label, val) in enumerate(metrics):
            cols[i].metric(label, val)

    # ── Main chart (always visible hero) ───────────────────────────────
    transform_labels = {
        "yoy_pct": "YoY %",
        "mom_pct": "MoM %",
        "net_change": "Net Change",
        "annualized": "Annualized %",
    }

    if ind.transform != "level":
        chart_series = transformed_plot.dropna()
        chart_df = pd.DataFrame({"value": chart_series})
        chart_unit = transform_labels.get(ind.transform, ind.unit)
        chart_title = f"{ind.name} ({chart_unit})"
    else:
        chart_df = plot_df
        chart_unit = ind.unit
        chart_title = ind.name

    recession_periods = _get_recession_periods()
    fig_main = charts.time_series_chart(
        chart_df,
        title=chart_title,
        unit=chart_unit,
        recession_periods=recession_periods,
        ma_windows=[3, 6, 12] if ind.frequency in ("monthly", "quarterly") else [20, 50, 200],
    )
    st.plotly_chart(fig_main, key=f"ts_{selected_id}")

    # ── TABS for secondary content ─────────────────────────────────────
    tab_sig, tab_roc, tab_yoy, tab_info = st.tabs([
        "📊 Significance", "📉 Rate of Change", "📈 Year-over-Year", "ℹ️ Series Info"
    ])

    # ── Tab: Significance & Trends ─────────────────────────────────────
    with tab_sig:
        # Significance box
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,255,255,0.03),rgba(255,255,255,0.01));'
            f'border-left:4px solid {sig["magnitude_color"]};border:1px solid rgba(255,255,255,0.06);'
            f'border-left:4px solid {sig["magnitude_color"]};'
            f'padding:14px 18px;border-radius:0 12px 12px 0;margin:8px 0 16px 0;'
            f'backdrop-filter:blur(10px)">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
            f'<span style="font-size:0.75em;color:#64748b;text-transform:uppercase;font-weight:700;'
            f'letter-spacing:0.8px">Significance</span>'
            f'<span style="background:{sig["magnitude_color"]};color:white;padding:1px 10px;border-radius:20px;'
            f'font-size:0.7em;font-weight:700;text-transform:uppercase">{sig["magnitude"]}</span>'
            f'</div>'
            f'<div style="font-size:0.95em;color:#e2e8f0;line-height:1.5">'
            f'{sig["interpretation"].replace("**", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Plain-English interpretation card ──────────────────────────
        _z = sig["z_score"]
        _abs_z = abs(_z)
        _change = sig.get("change", 0) or 0
        _streak = sig.get("streak", 0)
        _hi = ind.higher_is

        # Determine signal: is this good, bad, or neutral for the economy?
        # "good" = favorable conditions, "bad" = stress/concern, "watch" = notable
        if _hi == "inflationary":
            if _change > 0 and _abs_z >= 1.0:
                _signal = "warning"
                _signal_icon = "🔴"
                _signal_label = "Warning"
                _signal_summary = "Rising inflation pressure — erodes purchasing power and may prompt Fed tightening"
            elif _change < 0 and _abs_z >= 0.5:
                _signal = "favorable"
                _signal_icon = "🟢"
                _signal_label = "Favorable"
                _signal_summary = "Inflation cooling — eases pressure on consumers and supports potential rate cuts"
            elif _abs_z >= 2.0:
                _signal = "warning"
                _signal_icon = "🔴"
                _signal_label = "Warning"
                _signal_summary = "Inflation at extreme levels relative to recent history"
            elif _abs_z >= 1.0:
                _signal = "watch"
                _signal_icon = "🟡"
                _signal_label = "Watch"
                _signal_summary = "Inflation elevated but not yet at extreme levels"
            else:
                _signal = "neutral"
                _signal_icon = "⚪"
                _signal_label = "Neutral"
                _signal_summary = "Inflation within normal range — no immediate concern"

        elif _hi == "expansionary":
            if _change > 0 and _abs_z >= 0.5:
                _signal = "favorable"
                _signal_icon = "🟢"
                _signal_label = "Favorable"
                _signal_summary = "Economic activity strengthening — positive for growth and employment"
            elif _change < 0 and _abs_z >= 1.0:
                _signal = "warning"
                _signal_icon = "🔴"
                _signal_label = "Warning"
                _signal_summary = "Economic activity weakening significantly — watch for slowdown signals"
            elif _change < 0:
                _signal = "watch"
                _signal_icon = "🟡"
                _signal_label = "Watch"
                _signal_summary = "Growth slowing — not yet alarming but worth monitoring"
            else:
                _signal = "neutral"
                _signal_icon = "⚪"
                _signal_label = "Neutral"
                _signal_summary = "Economic activity within normal range"

        elif _hi == "contractionary":
            if _change > 0 and _abs_z >= 0.5:
                _signal = "warning"
                _signal_icon = "🔴"
                _signal_label = "Warning"
                _signal_summary = "Stress indicator rising — signals increasing economic headwinds"
            elif _change < 0 and _abs_z >= 0.5:
                _signal = "favorable"
                _signal_icon = "🟢"
                _signal_label = "Favorable"
                _signal_summary = "Stress easing — conditions improving"
            elif _abs_z >= 2.0:
                _signal = "warning"
                _signal_icon = "🔴"
                _signal_label = "Warning"
                _signal_summary = "At extreme levels — historically associated with economic stress"
            else:
                _signal = "neutral"
                _signal_icon = "⚪"
                _signal_label = "Neutral"
                _signal_summary = "Within normal range"

        else:  # neutral
            if _abs_z >= 2.0:
                _signal = "watch"
                _signal_icon = "🟡"
                _signal_label = "Watch"
                _signal_summary = "Unusually far from historical norms — worth paying attention to"
            else:
                _signal = "neutral"
                _signal_icon = "⚪"
                _signal_label = "Neutral"
                _signal_summary = "Within normal range — no strong directional signal"

        # Add streak context
        if abs(_streak) >= 4:
            _streak_dir = "rising" if _streak > 0 else "falling"
            _signal_summary += f". Now {_streak_dir} for {abs(_streak)} straight readings"

        # Signal card colors
        _signal_colors = {
            "favorable": ("#22c55e", "rgba(34,197,94,0.08)", "rgba(34,197,94,0.2)"),
            "watch": ("#eab308", "rgba(234,179,8,0.08)", "rgba(234,179,8,0.2)"),
            "warning": ("#ef4444", "rgba(239,68,68,0.08)", "rgba(239,68,68,0.2)"),
            "neutral": ("#64748b", "rgba(100,116,139,0.06)", "rgba(100,116,139,0.15)"),
        }
        _sc_text, _sc_bg, _sc_border = _signal_colors[_signal]

        st.markdown(
            f'<div style="background:{_sc_bg};border:1px solid {_sc_border};'
            f'border-radius:12px;padding:14px 18px;margin:8px 0 16px 0">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
            f'<span style="font-size:1.1em">{_signal_icon}</span>'
            f'<span style="color:{_sc_text};font-weight:700;font-size:0.82em;'
            f'text-transform:uppercase;letter-spacing:0.8px">{_signal_label}</span>'
            f'</div>'
            f'<div style="color:#e2e8f0;font-size:0.9em;line-height:1.5">'
            f'{_signal_summary}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Trailing averages
        avg_cols = st.columns(3)
        for i, (label, val) in enumerate([
            ("vs 3-Month Avg", sig["vs_3m_avg"]),
            ("vs 6-Month Avg", sig["vs_6m_avg"]),
            ("vs 12-Month Avg", sig["vs_12m_avg"]),
        ]):
            if val is not None:
                avg_cols[i].metric(label, f"{val:+.1f}%")
            else:
                avg_cols[i].metric(label, "N/A")

        # Z-score gauge
        fig_z = charts.z_score_gauge(z_full, name=ind.name)
        st.plotly_chart(fig_z, key=f"zg_{selected_id}")

    # ── Tab: Rate of Change ────────────────────────────────────────────
    with tab_roc:
        roc_df = None
        roc_title = ""

        if ind.transform == "level" and ind.frequency in ("monthly", "quarterly"):
            full_mom = mom_pct(df["value"]).dropna()
            if days:
                full_mom = full_mom[full_mom.index >= cutoff]
            roc_df = pd.DataFrame({"value": full_mom}).dropna()
            roc_title = "Month-over-Month % Change"

        elif ind.transform in ("yoy_pct", "mom_pct", "annualized"):
            full_delta = full_transformed.diff().dropna()
            if days:
                full_delta = full_delta[full_delta.index >= cutoff]
            roc_df = pd.DataFrame({"value": full_delta}).dropna()
            transform_name = ind.transform.replace("_", " ").title()
            roc_title = f"Change in {transform_name} (Acceleration)"

        if roc_df is not None and len(roc_df) >= 3:
            fig_roc = charts.rate_of_change_chart(roc_df, title=roc_title)
            st.plotly_chart(fig_roc, key=f"roc_{selected_id}")
        else:
            st.caption("Not enough data for rate of change chart at this range.")

    # ── Tab: Year-over-Year ────────────────────────────────────────────
    with tab_yoy:
        if ind.frequency in ("monthly", "quarterly") and len(df) > 24:
            periods_map = {"monthly": 12, "quarterly": 4}
            yoy = yoy_pct(df["value"], periods=periods_map.get(ind.frequency, 12)).dropna()
            if days:
                yoy = yoy[yoy.index >= cutoff]
            if len(yoy) >= 3:
                yoy_df = pd.DataFrame({"value": yoy})
                fig_yoy = charts.rate_of_change_chart(
                    yoy_df, title="YoY % Change", transform_label="YoY %")
                st.plotly_chart(fig_yoy, key=f"yoy_{selected_id}")
            else:
                st.caption("Not enough data for YoY chart at this range.")
        else:
            st.caption("YoY analysis requires monthly or quarterly data with 2+ years of history.")

    # ── Tab: Series Info ───────────────────────────────────────────────
    with tab_info:
        # Explainer
        explainer = WHY_IT_MATTERS.get(selected_id)
        if explainer:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(139,92,246,0.04));'
                f'border-left:3px solid #6366f1;border:1px solid rgba(99,102,241,0.12);'
                f'border-left:3px solid #6366f1;'
                f'padding:12px 16px;border-radius:0 10px 10px 0;margin-bottom:16px;'
                f'font-size:0.88em;color:#cbd5e1;backdrop-filter:blur(10px)">'
                f'<span style="color:#818cf8;font-weight:600;font-size:0.75em;text-transform:uppercase;'
                f'letter-spacing:0.8px">What This Measures</span><br>'
                f'{explainer.replace("**", "")}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"*{ind.description}*")
        st.markdown(f"**FRED ID:** `{ind.fred_id}`")
        st.markdown(f"**Frequency:** {ind.frequency}")
        st.markdown(f"**Release page:** [{ind.release_url}]({ind.release_url})")
        st.markdown(f"**Observations:** {len(df)}")

        meta = cache.get_metadata(selected_id)
        if meta:
            with st.expander("Raw Metadata"):
                st.json(meta)
