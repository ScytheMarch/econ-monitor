"""Probability Models page — recession forecasting, leading index, regime transitions."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # ── Title ──────────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '🎯 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Probability Models</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption("Forward-looking recession probability, composite leading indicators, and regime transition analysis")

    # ── Compute all models ─────────────────────────────────────────────────────
    recession = _compute_recession_cached()
    leading = _compute_leading_cached()
    transitions = _compute_transitions_cached()

    # ── Hero metrics row ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        prob = recession["prob_12m"]
        st.metric(
            "Recession Prob (12m)",
            f"{prob:.0f}%",
            delta=f"{recession['label']}",
            delta_color="inverse" if prob > 30 else "off",
        )

    with col2:
        idx_val = leading["value"]
        trend_map = {"improving": "Up", "deteriorating": "Down", "stable": "Flat"}
        trend_label = trend_map.get(leading["trend"], "Flat")
        st.metric(
            "Leading Index",
            f"{idx_val:+.2f}",
            delta=trend_label,
            delta_color="normal" if idx_val >= 0 else "inverse",
        )

    with col3:
        st.metric(
            "Regime Stability",
            f"{transitions['stability']:.0f}%",
            delta=transitions["current_regime"],
            delta_color="off",
        )

    st.markdown('<hr style="margin:8px 0;border-color:rgba(99,102,241,0.12)">', unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_recession, tab_leading, tab_transitions = st.tabs([
        "📉 Recession Probability",
        "📊 Leading Index",
        "🔄 Regime Transitions",
    ])

    # ── Tab 1: Recession Probability ──────────────────────────────────────────
    with tab_recession:
        _render_recession_tab(recession)

    # ── Tab 2: Leading Index ──────────────────────────────────────────────────
    with tab_leading:
        _render_leading_tab(leading)

    # ── Tab 3: Regime Transitions ─────────────────────────────────────────────
    with tab_transitions:
        _render_transitions_tab(transitions)


# ── Cached computation wrappers ──────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Computing recession model...")
def _compute_recession_cached() -> dict:
    from econ_monitor.analytics.probability_models import compute_recession_probability
    result = compute_recession_probability()
    # Convert DataFrame to dict for caching (Streamlit can't hash DataFrames well)
    if hasattr(result.get("history"), "to_dict"):
        result["_history_dict"] = result["history"].to_dict()
        result["_history_index"] = result["history"].index.tolist()
    return result


@st.cache_data(ttl=3600, show_spinner="Computing leading index...")
def _compute_leading_cached() -> dict:
    from econ_monitor.analytics.probability_models import compute_leading_index
    result = compute_leading_index()
    if hasattr(result.get("history"), "to_dict"):
        result["_history_dict"] = result["history"].to_dict()
        result["_history_index"] = result["history"].index.tolist()
    return result


@st.cache_data(ttl=3600, show_spinner="Computing transitions...")
def _compute_transitions_cached() -> dict:
    from econ_monitor.analytics.probability_models import compute_transition_probabilities
    result = compute_transition_probabilities()
    if hasattr(result.get("regime_history"), "to_dict"):
        result["_regime_history_dict"] = result["regime_history"].to_dict()
        result["_regime_history_index"] = result["regime_history"].index.tolist()
    return result


def _rebuild_history(result: dict) -> "pd.DataFrame":
    """Rebuild a DataFrame from the cached dict representation."""
    import pandas as pd
    if "_history_dict" in result and "_history_index" in result:
        df = pd.DataFrame(result["_history_dict"], index=result["_history_index"])
        df.index = pd.DatetimeIndex(df.index)
        return df
    if "history" in result and hasattr(result["history"], "empty"):
        return result["history"]
    return pd.DataFrame()


def _rebuild_regime_history(result: dict) -> "pd.DataFrame":
    """Rebuild regime history DataFrame from cached dict."""
    import pandas as pd
    if "_regime_history_dict" in result and "_regime_history_index" in result:
        df = pd.DataFrame(result["_regime_history_dict"], index=result["_regime_history_index"])
        df.index = pd.DatetimeIndex(df.index)
        return df
    if "regime_history" in result and hasattr(result["regime_history"], "empty"):
        return result["regime_history"]
    return pd.DataFrame()


# ── Tab renderers ────────────────────────────────────────────────────────────

def _info_box(title: str, body: str) -> None:
    """Render a styled educational info box."""
    st.markdown(
        f'<div style="background:rgba(99,102,241,0.04);border-left:3px solid rgba(99,102,241,0.4);'
        f'border-radius:0 10px 10px 0;padding:12px 16px;margin:8px 0">'
        f'<div style="color:#c7d2fe;font-weight:700;font-size:0.85em;margin-bottom:6px">{title}</div>'
        f'<div style="color:#94a3b8;font-size:0.82em;line-height:1.55">{body}</div></div>',
        unsafe_allow_html=True,
    )


def _evidence_box(title: str, body: str) -> None:
    """Render a styled analysis/evidence box."""
    st.markdown(
        f'<div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.15);'
        f'border-radius:12px;padding:14px 18px;margin:8px 0">'
        f'<span style="color:#c7d2fe;font-weight:600">{title}:</span> '
        f'<span style="color:#94a3b8">{body}</span></div>',
        unsafe_allow_html=True,
    )


def _render_recession_tab(data: dict) -> None:
    from econ_monitor.ui.charts import recession_probability_chart, component_bar_chart

    # Educational intro
    _info_box(
        "How This Model Works",
        "This model estimates recession probability using four signals that historically "
        "precede economic downturns. Each signal is scored 0 (no risk) to 1 (high risk) "
        "and weighted by predictive power. The composite is mapped through a sigmoid function "
        "to produce a 0-100% probability for three time horizons. "
        "<b>Below 20%</b> = low risk, <b>20-40%</b> = watch closely, "
        "<b>40-60%</b> = elevated concern, <b>above 60%</b> = high alert."
    )

    # Probability metrics row
    c1, c2, c3 = st.columns(3)
    c1.metric("3-Month", f"{data['prob_3m']:.1f}%")
    c2.metric("6-Month", f"{data['prob_6m']:.1f}%")
    c3.metric("12-Month", f"{data['prob_12m']:.1f}%")

    # Main probability chart
    history = _rebuild_history(data)
    if not history.empty:
        fig = recession_probability_chart(
            history,
            recession_periods=data.get("recession_periods"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient historical data to chart recession probabilities.")

    # Interpretation
    _evidence_box("Analysis", data["interpretation"])

    # AI Deep Analysis
    _render_ai_interpretation(
        "Recession Probability Model",
        f"3m={data['prob_3m']:.1f}%, 6m={data['prob_6m']:.1f}%, "
        f"12m={data['prob_12m']:.1f}% — {data['interpretation']}",
    )

    # Component breakdown
    with st.expander("📋 Component Breakdown"):
        # Signal explainers
        _info_box(
            "Understanding the Signals",
            "<b>Yield Curve (10Y-3M)</b> — The spread between 10-year and 3-month Treasury yields. "
            "When it inverts (goes negative), it has preceded every US recession since the 1960s, "
            "typically 6-18 months ahead. Weight: 35%.<br><br>"
            "<b>Sahm Rule (Unemployment)</b> — Triggers when the 3-month average unemployment rate "
            "rises 0.5+ percentage points above its trailing 12-month low. Named after economist "
            "Claudia Sahm, this has a perfect track record identifying the early stages of recession. "
            "Weight: 30%.<br><br>"
            "<b>Credit Stress (HY Spread)</b> — The difference between high-yield corporate bond rates "
            "and Treasury rates. Widening spreads mean investors are demanding more compensation for risk, "
            "signaling financial stress. We use the z-score to measure how unusual current spreads are. "
            "Weight: 20%.<br><br>"
            "<b>Industrial Production</b> — Tracks real output of factories, mines, and utilities. "
            "Declining production growth is one of the earliest signs of economic weakening since "
            "manufacturing leads the broader economy. Weight: 15%."
        )

        components = data.get("components", [])
        if components:
            # Bar chart of scores
            scored = [c for c in components if c.get("score") is not None]
            if scored:
                bar_data = [
                    {"name": c["name"], "contribution": c["score"] * c["weight"]}
                    for c in scored
                ]
                fig = component_bar_chart(bar_data, title="Weighted Signal Scores")
                st.plotly_chart(fig, use_container_width=True)

            # Table
            _render_component_table(components, show_score=True)

    # How to read it
    with st.expander("📖 How to Read This"):
        _info_box(
            "Reading the Chart",
            "<b>The dashed yellow line at 20%</b> marks the boundary between low risk and "
            "moderate concern. Staying below this line is normal during expansions.<br><br>"
            "<b>The dashed red line at 50%</b> marks elevated risk. If the 12-month line "
            "crosses above this, historical data suggests a recession is more likely than not.<br><br>"
            "<b>3-month (dotted cyan)</b> responds fastest to labor market and credit changes. "
            "<b>6-month (orange)</b> balances near-term and forward signals. "
            "<b>12-month (red, thickest)</b> is most influenced by the yield curve, which "
            "provides the longest lead time.<br><br>"
            "<b>Gray shaded areas</b> show actual NBER recessions for historical context."
        )


def _render_leading_tab(data: dict) -> None:
    from econ_monitor.ui.charts import leading_index_chart, component_bar_chart

    # Educational intro
    _info_box(
        "How This Model Works",
        "The Composite Leading Index combines 7 forward-looking indicators into a single number, "
        "similar to the Conference Board's Leading Economic Index (LEI). Each component is "
        "standardized using z-scores (how many standard deviations from its rolling mean) "
        "then weighted by predictive importance. "
        "<b>Positive values</b> = above-average conditions signaling growth ahead. "
        "<b>Negative values</b> = below-average conditions warning of slowdown. "
        "The further from zero, the stronger the signal."
    )

    # Metric
    trend_map = {"improving": "Up ▲", "deteriorating": "Down ▼", "stable": "Flat ▬"}
    st.metric(
        "Current Leading Index",
        f"{data['value']:+.2f}",
        delta=trend_map.get(data["trend"], "Flat"),
    )

    # Main chart
    history = _rebuild_history(data)
    if not history.empty:
        fig = leading_index_chart(
            history,
            recession_periods=data.get("recession_periods"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data to chart leading index history.")

    # Interpretation
    _evidence_box("Analysis", data["interpretation"])

    # AI Deep Analysis
    _render_ai_interpretation(
        "Composite Leading Index",
        f"Value={data['value']:+.2f}, trend={data['trend']} — {data['interpretation']}",
    )

    # Component contributions
    with st.expander("📋 Component Breakdown"):
        _info_box(
            "What Each Component Measures",
            "<b>Yield Curve (10Y-2Y)</b> — The bond market's forecast of future growth. "
            "A steep curve means bond traders expect stronger growth ahead; a flat or inverted "
            "curve signals pessimism. Weight: 20%.<br><br>"
            "<b>Building Permits</b> — Permits filed today become construction activity 6-12 months "
            "from now. Rising permits = builders expect demand; falling = they're pulling back. "
            "Year-over-year change used. Weight: 15%.<br><br>"
            "<b>Initial Claims (inverted)</b> — Weekly new unemployment filings. Fewer claims = "
            "healthy labor market. This is inverted so lower claims push the index positive. "
            "The most timely weekly signal available. Weight: 15%.<br><br>"
            "<b>Consumer Sentiment</b> — University of Michigan survey of consumer expectations. "
            "Consumers typically cut spending 2-3 quarters before a recession shows up in GDP. "
            "Weight: 15%.<br><br>"
            "<b>Durable Goods Orders</b> — Orders for long-lasting manufactured items (machines, "
            "vehicles, appliances). Businesses order less when they expect a slowdown. "
            "Year-over-year change used. Weight: 15%.<br><br>"
            "<b>VIX (inverted)</b> — The 'fear index' measuring expected stock market volatility. "
            "Low VIX = calm markets (positive for index). High VIX = stress (negative). Weight: 10%.<br><br>"
            "<b>M2 Money Supply</b> — Broad measure of money in the economy. Growing M2 supports "
            "future spending; shrinking M2 constrains it. Year-over-year change used. Weight: 10%."
        )

        components = data.get("components", [])
        if components:
            valid = [c for c in components if c.get("contribution") is not None]
            if valid:
                fig = component_bar_chart(valid, title="Component Contributions (z-score x weight)")
                st.plotly_chart(fig, use_container_width=True)

            _render_component_table(components, show_score=False)

    with st.expander("📖 How to Read This"):
        _info_box(
            "Reading the Chart",
            "The chart shows the composite index over time. "
            "<b>Green shading above zero</b> means leading indicators are above their historical average — "
            "the economy is likely to grow. <b>Red shading below zero</b> means indicators are below "
            "average — slowdown risk is rising.<br><br>"
            "Watch for <b>the trend direction</b> more than the absolute level. A falling index "
            "(even if still positive) can be an early warning. Historically, the index turns negative "
            "3-6 months before recessions begin (shown as gray shaded areas).<br><br>"
            "The <b>component bar chart</b> shows which indicators are pulling the index up (green) "
            "vs dragging it down (red). Longer bars = stronger influence."
        )


def _render_transitions_tab(data: dict) -> None:
    from econ_monitor.ui.charts import transition_matrix_heatmap

    # Educational intro
    _info_box(
        "How This Model Works",
        "This model analyzes how the economy transitions between three states: "
        "<b>Expansion</b> (broad growth), <b>Mixed</b> (conflicting signals), and "
        "<b>Contraction</b> (widespread weakness). It computes a regime score from "
        "10 economic signals each month, classifies the regime, then counts how often "
        "each transition has occurred historically to build a probability matrix.<br><br>"
        "The <b>forecast</b> adjusts these base probabilities using current momentum — "
        "if the regime score is deteriorating rapidly, the probability of transitioning "
        "to a weaker state increases, and vice versa."
    )

    # Current regime + forecast row
    col1, col2 = st.columns([1, 2])

    with col1:
        regime = data["current_regime"]
        regime_colors = {"Expansion": "#22c55e", "Contraction": "#ef4444", "Mixed": "#eab308"}
        color = regime_colors.get(regime, "#6b7280")

        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border:1px solid {color}40;'
            f'border-radius:12px;padding:16px;text-align:center">'
            f'<div style="color:#64748b;font-size:0.75em;text-transform:uppercase;'
            f'letter-spacing:1.2px;font-weight:600">Current Regime</div>'
            f'<div style="color:{color};font-size:1.8em;font-weight:800;margin:4px 0">{regime}</div>'
            f'<div style="color:#94a3b8;font-size:0.85em">Momentum: {data["momentum"]:+.4f}/mo</div>'
            f'<div style="color:#64748b;font-size:0.8em;margin-top:4px">{data["forecast"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        # Forecast probability metrics
        probs = data.get("forecast_probs", {})
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("P(Expansion)", f"{probs.get('Expansion', 0):.0%}")
        pc2.metric("P(Mixed)", f"{probs.get('Mixed', 0):.0%}")
        pc3.metric("P(Contraction)", f"{probs.get('Contraction', 0):.0%}")

    # Transition matrix heatmap
    matrix = data.get("transition_matrix", {})
    if matrix:
        _info_box(
            "Reading the Transition Matrix",
            "Each cell shows the historical probability of moving from one regime (row) "
            "to another (column) in a single month. <b>High diagonal values</b> (top-left to "
            "bottom-right) mean regimes tend to persist — which is normal since economic states "
            "are sticky. <b>Off-diagonal values</b> show transition probabilities. For example, "
            "if Expansion→Contraction is 2%, it means a direct jump from expansion to contraction "
            "happens only 2% of the time — the economy usually passes through Mixed first."
        )
        fig = transition_matrix_heatmap(matrix)
        st.plotly_chart(fig, use_container_width=True)

    # Regime score history
    regime_hist = _rebuild_regime_history(data)
    if not regime_hist.empty and "score" in regime_hist.columns:
        import plotly.graph_objects as go
        fig = go.Figure()
        scores = regime_hist["score"]

        # Color-coded fill
        pos = scores.clip(lower=0)
        fig.add_trace(go.Scatter(
            x=regime_hist.index, y=pos,
            fill="tozeroy", fillcolor="rgba(34,197,94,0.12)",
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        neg = scores.clip(upper=0)
        fig.add_trace(go.Scatter(
            x=regime_hist.index, y=neg,
            fill="tozeroy", fillcolor="rgba(239,68,68,0.12)",
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))

        fig.add_trace(go.Scatter(
            x=regime_hist.index, y=scores,
            mode="lines", name="Regime Score",
            line=dict(color="#818cf8", width=2.5),
        ))

        # Threshold lines
        fig.add_hline(y=0.2, line=dict(color="rgba(34,197,94,0.3)", width=1, dash="dash"))
        fig.add_hline(y=-0.2, line=dict(color="rgba(239,68,68,0.3)", width=1, dash="dash"))
        fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.15)", width=1))

        fig.update_layout(
            title=dict(text="Regime Score History", font=dict(size=14, color="#e2e8f0")),
            yaxis_title="Score (-1 to +1)",
            yaxis=dict(range=[-1.1, 1.1], gridcolor="rgba(255,255,255,0.04)"),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(l=60, r=20, t=50, b=40),
            font=dict(family="Inter, sans-serif", color="#94a3b8"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Interpretation
    _evidence_box("Analysis", data["interpretation"].replace("**", ""))

    # AI Deep Analysis
    _render_ai_interpretation(
        "Regime Transition Model",
        f"Regime={data['current_regime']}, stability={data['stability']:.0f}%, "
        f"momentum={data['momentum']:+.4f} — {data['forecast']}",
    )

    with st.expander("📖 How to Read This"):
        _info_box(
            "Understanding Regime Scores & Momentum",
            "<b>Regime Score (-1 to +1)</b> — A composite of 10 economic signals weighted by "
            "importance. Scores above +0.2 classify as Expansion, below -0.2 as Contraction, "
            "and in between as Mixed. The score is plotted over time so you can see the trajectory.<br><br>"
            "<b>Momentum</b> — The rate of change in the regime score (per month). Positive momentum "
            "means conditions are improving; negative means deteriorating. Even if you're in Expansion, "
            "negative momentum could signal a coming transition.<br><br>"
            "<b>Forecast Probabilities</b> — These combine historical transition patterns with "
            "current momentum. If the economy has been in Expansion and momentum turns sharply negative, "
            "the model increases the probability of transitioning to Mixed or Contraction beyond "
            "what historical averages alone would suggest.<br><br>"
            "<b>Green dashed line (+0.2)</b> — Expansion threshold. "
            "<b>Red dashed line (-0.2)</b> — Contraction threshold. "
            "Scores between these lines = Mixed regime."
        )


# ── AI interpretation ────────────────────────────────────────────────────────

def _render_ai_interpretation(model_name: str, model_summary: str) -> None:
    """Render AI deep analysis expander for a model tab (silent if unavailable)."""
    from econ_monitor.analytics.ai_analysis import is_ai_available

    if not is_ai_available():
        return

    with st.expander("🤖 AI Deep Analysis"):
        from econ_monitor.analytics.ai_analysis import build_full_context, context_hash

        ctx = build_full_context()
        ctx_h = context_hash(ctx)
        analysis = _get_ai_model_analysis(ctx_h, model_name, model_summary, ctx)

        if analysis:
            st.markdown(
                f'<div style="color:#cbd5e1;font-size:0.9em;line-height:1.7;'
                f'padding:4px 0">{analysis}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Unable to generate AI analysis. Check your API key.")


@st.cache_data(ttl=3600, show_spinner="Generating AI interpretation...")
def _get_ai_model_analysis(
    ctx_hash: str, model_name: str, model_summary: str, full_context: str,
) -> str | None:
    from econ_monitor.analytics.ai_analysis import analyze_model_output
    return analyze_model_output(ctx_hash, model_name, model_summary, full_context)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _render_component_table(components: list[dict], show_score: bool = True) -> None:
    """Render a styled HTML table of model components."""
    rows = ""
    for c in components:
        val = c.get("value")
        val_str = f"{val:.2f}" if val is not None else "N/A"

        if show_score:
            score = c.get("score")
            score_str = f"{score:.3f}" if score is not None else "N/A"
            if score is not None:
                if score > 0.5:
                    badge_color = "#ef4444"
                elif score > 0.25:
                    badge_color = "#eab308"
                else:
                    badge_color = "#22c55e"
                score_cell = (
                    f'<span style="color:{badge_color};font-weight:600">{score_str}</span>'
                )
            else:
                score_cell = f'<span style="color:#475569">{score_str}</span>'

            rows += (
                f'<tr>'
                f'<td style="padding:6px 12px;color:#e2e8f0">{c["name"]}</td>'
                f'<td style="padding:6px 12px;color:#94a3b8">{val_str}</td>'
                f'<td style="padding:6px 12px">{score_cell}</td>'
                f'<td style="padding:6px 12px;color:#64748b">{c["weight"]}</td>'
                f'<td style="padding:6px 12px;color:#64748b;font-size:0.85em">'
                f'{c.get("interpretation", "")}</td>'
                f'</tr>'
            )
        else:
            z = c.get("z_score")
            z_str = f"{z:+.2f}" if z is not None else "N/A"
            contrib = c.get("contribution")
            contrib_str = f"{contrib:+.3f}" if contrib is not None else "N/A"

            rows += (
                f'<tr>'
                f'<td style="padding:6px 12px;color:#e2e8f0">{c["name"]}</td>'
                f'<td style="padding:6px 12px;color:#94a3b8">{z_str}</td>'
                f'<td style="padding:6px 12px;color:#94a3b8">{c["weight"]}</td>'
                f'<td style="padding:6px 12px;color:#94a3b8">{contrib_str}</td>'
                f'</tr>'
            )

    if show_score:
        header = (
            '<tr style="border-bottom:1px solid rgba(255,255,255,0.1)">'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Signal</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Value</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Score</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Weight</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Signal</th>'
            '</tr>'
        )
    else:
        header = (
            '<tr style="border-bottom:1px solid rgba(255,255,255,0.1)">'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Component</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Z-Score</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Weight</th>'
            '<th style="padding:6px 12px;text-align:left;color:#64748b;font-weight:600">Contribution</th>'
            '</tr>'
        )

    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;font-size:0.9em">'
        f'{header}{rows}</table>',
        unsafe_allow_html=True,
    )
