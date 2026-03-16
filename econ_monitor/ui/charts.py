"""Plotly chart builders for the economic monitor dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from econ_monitor.ui.styles import GREEN, RED, YELLOW, GRAY, BLUE, CATEGORY_COLORS

ORANGE = "#f97316"
CYAN = "#06b6d4"
PURPLE = "#8b5cf6"


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a hex color like '#ef4444' to 'rgba(239,68,68,0.08)'."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def time_series_chart(
    df: pd.DataFrame,
    title: str = "",
    unit: str = "",
    recession_periods: list[tuple[str, str]] | None = None,
    ma_windows: list[int] | None = None,
) -> go.Figure:
    """Line chart of a single indicator over time with optional MAs and recession shading."""
    fig = go.Figure()

    # Recession shading
    if recession_periods:
        for start, end in recession_periods:
            fig.add_vrect(
                x0=start, x1=end,
                fillcolor="rgba(239,68,68,0.08)",
                line_width=0,
                layer="below",
            )

    # Main series
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["value"],
        mode="lines",
        name="Value",
        line=dict(color=BLUE, width=2),
    ))

    # Moving averages
    if ma_windows:
        ma_colors = ["#f97316", "#8b5cf6", "#06b6d4"]
        for i, w in enumerate(ma_windows):
            ma = df["value"].rolling(window=w, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=ma,
                mode="lines",
                name=f"{w}-period MA",
                line=dict(color=ma_colors[i % len(ma_colors)], width=1, dash="dash"),
            ))

    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter, sans-serif", size=16, color="#e2e8f0")),
        yaxis_title=unit,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=60, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(family="Inter, sans-serif", color="#94a3b8")),
        hovermode="x unified",
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
    )
    return fig


def rate_of_change_chart(
    df: pd.DataFrame,
    title: str = "Rate of Change",
    transform_label: str = "Change %",
) -> go.Figure:
    """Bar chart showing period-over-period changes, colored by direction."""
    changes = df["value"].dropna()

    colors = [GREEN if v >= 0 else RED for v in changes]

    fig = go.Figure(go.Bar(
        x=changes.index,
        y=changes.values,
        marker_color=colors,
        name=transform_label,
    ))

    fig.update_layout(
        title=title,
        yaxis_title=transform_label,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=60, r=20, t=50, b=40),
    )
    return fig


def z_score_gauge(z: float | None, name: str = "") -> go.Figure:
    """Gauge chart showing how unusual the current reading is."""
    if z is None:
        z = 0

    # Clamp for display
    z_display = max(-3, min(3, z))

    if abs(z) < 1:
        color = GREEN
    elif abs(z) < 2:
        color = YELLOW
    else:
        color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=z_display,
        number=dict(suffix="σ"),
        title=dict(text=f"{name} Z-Score"),
        gauge=dict(
            axis=dict(range=[-3, 3], tickvals=[-3, -2, -1, 0, 1, 2, 3]),
            bar=dict(color=color),
            steps=[
                dict(range=[-3, -2], color="rgba(239,68,68,0.2)"),
                dict(range=[-2, -1], color="rgba(234,179,8,0.15)"),
                dict(range=[-1, 1], color="rgba(34,197,94,0.15)"),
                dict(range=[1, 2], color="rgba(234,179,8,0.15)"),
                dict(range=[2, 3], color="rgba(239,68,68,0.2)"),
            ],
        ),
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig


def regime_gauge(score: float, label: str, color: str) -> go.Figure:
    """Gauge chart showing the composite regime score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title=dict(text=f"Economic Regime: {label}"),
        gauge=dict(
            axis=dict(range=[-1, 1]),
            bar=dict(color=color),
            steps=[
                dict(range=[-1, -0.25], color="rgba(239,68,68,0.2)"),
                dict(range=[-0.25, 0.25], color="rgba(234,179,8,0.15)"),
                dict(range=[0.25, 1], color="rgba(34,197,94,0.15)"),
            ],
            threshold=dict(
                line=dict(color="white", width=2),
                thickness=0.75,
                value=score,
            ),
        ),
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
        margin=dict(l=20, r=20, t=50, b=10),
    )
    return fig


def correlation_heatmap(corr_matrix: pd.DataFrame, title: str = "Cross-Indicator Correlations") -> go.Figure:
    """Heatmap of indicator correlations."""
    from econ_monitor.config.indicators import INDICATORS

    # Map series IDs to short names
    labels = [INDICATORS[sid].name if sid in INDICATORS else sid for sid in corr_matrix.columns]

    fig = go.Figure(go.Heatmap(
        z=corr_matrix.values,
        x=labels,
        y=labels,
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        text=corr_matrix.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=9),
    ))

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600,
        margin=dict(l=120, r=20, t=50, b=120),
        xaxis=dict(tickangle=45),
    )
    return fig


def multi_series_chart(
    series_dict: dict[str, pd.DataFrame],
    title: str = "",
    normalize: bool = False,
) -> go.Figure:
    """Overlay multiple series on one chart. Optionally normalize to 100 at start."""
    fig = go.Figure()

    colors = list(CATEGORY_COLORS.values())
    for i, (name, df) in enumerate(series_dict.items()):
        if df.empty:
            continue
        values = df["value"]
        if normalize and len(values) > 0 and values.iloc[0] != 0:
            values = values / values.iloc[0] * 100

        fig.add_trace(go.Scatter(
            x=df.index,
            y=values,
            mode="lines",
            name=name,
            line=dict(color=colors[i % len(colors)], width=2),
        ))

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=60, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


# ── Probability model charts ─────────────────────────────────────────────────

_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94a3b8"),
    hovermode="x unified",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
)


def recession_probability_chart(
    history: pd.DataFrame,
    recession_periods: list[tuple[str, str]] | None = None,
) -> go.Figure:
    """Chart showing 3m/6m/12m recession probabilities over time."""
    fig = go.Figure()

    # Recession shading
    if recession_periods:
        for start, end in recession_periods:
            fig.add_vrect(
                x0=start, x1=end,
                fillcolor="rgba(239,68,68,0.08)",
                line_width=0, layer="below",
            )

    if not history.empty:
        # 3-month probability
        if "prob_3m" in history.columns:
            fig.add_trace(go.Scatter(
                x=history.index, y=history["prob_3m"],
                mode="lines", name="3-Month",
                line=dict(color=CYAN, width=1.5, dash="dot"),
            ))

        # 6-month probability
        if "prob_6m" in history.columns:
            fig.add_trace(go.Scatter(
                x=history.index, y=history["prob_6m"],
                mode="lines", name="6-Month",
                line=dict(color=ORANGE, width=2),
            ))

        # 12-month probability (primary)
        if "prob_12m" in history.columns:
            fig.add_trace(go.Scatter(
                x=history.index, y=history["prob_12m"],
                mode="lines", name="12-Month",
                line=dict(color=RED, width=2.5),
            ))

    # Reference lines
    fig.add_hline(y=20, line=dict(color="rgba(234,179,8,0.3)", width=1, dash="dash"))
    fig.add_hline(y=50, line=dict(color="rgba(239,68,68,0.3)", width=1, dash="dash"))

    fig.update_layout(
        title=dict(text="Recession Probability Over Time", font=dict(size=16, color="#e2e8f0")),
        yaxis_title="Probability (%)",
        yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.04)", zeroline=False),
        height=400,
        margin=dict(l=60, r=20, t=50, b=40),
        **{k: v for k, v in _LAYOUT_DEFAULTS.items() if k not in ("yaxis",)},
    )
    return fig


def leading_index_chart(
    history: pd.DataFrame,
    recession_periods: list[tuple[str, str]] | None = None,
) -> go.Figure:
    """Chart showing composite leading index with fill-to-zero."""
    fig = go.Figure()

    # Recession shading
    if recession_periods:
        for start, end in recession_periods:
            fig.add_vrect(
                x0=start, x1=end,
                fillcolor="rgba(239,68,68,0.08)",
                line_width=0, layer="below",
            )

    if not history.empty and "index" in history.columns:
        values = history["index"]

        # Positive region (green fill)
        pos = values.clip(lower=0)
        fig.add_trace(go.Scatter(
            x=history.index, y=pos,
            fill="tozeroy", fillcolor="rgba(34,197,94,0.15)",
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))

        # Negative region (red fill)
        neg = values.clip(upper=0)
        fig.add_trace(go.Scatter(
            x=history.index, y=neg,
            fill="tozeroy", fillcolor="rgba(239,68,68,0.15)",
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))

        # Main line
        fig.add_trace(go.Scatter(
            x=history.index, y=values,
            mode="lines", name="Leading Index",
            line=dict(color=BLUE, width=2.5),
        ))

    # Zero line
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.2)", width=1))

    fig.update_layout(
        title=dict(text="Composite Leading Index", font=dict(size=16, color="#e2e8f0")),
        yaxis_title="Index (std devs from mean)",
        height=400,
        margin=dict(l=60, r=20, t=50, b=40),
        **_LAYOUT_DEFAULTS,
    )
    return fig


def component_bar_chart(
    components: list[dict],
    value_key: str = "contribution",
    label_key: str = "name",
    title: str = "Component Contributions",
) -> go.Figure:
    """Horizontal bar chart of component contributions, green/red by sign."""
    # Filter out None values and sort by absolute value
    valid = [c for c in components if c.get(value_key) is not None]
    valid.sort(key=lambda c: abs(c[value_key]))

    labels = [c[label_key] for c in valid]
    values = [c[value_key] for c in valid]
    colors = [GREEN if v >= 0 else RED for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.3f}" for v in values],
        textposition="outside",
        textfont=dict(size=11, color="#94a3b8"),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#e2e8f0")),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(200, len(valid) * 45 + 60),
        margin=dict(l=160, r=60, t=40, b=20),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=True,
                   zerolinecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
    )
    return fig


def transition_matrix_heatmap(
    matrix: dict[str, dict[str, float]],
) -> go.Figure:
    """3x3 heatmap of regime transition probabilities."""
    labels = ["Expansion", "Mixed", "Contraction"]
    z = [[matrix.get(from_r, {}).get(to_r, 0) for to_r in labels] for from_r in labels]
    text = [[f"{v:.0%}" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"To: {l}" for l in labels],
        y=[f"From: {l}" for l in labels],
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=14, color="white"),
        colorscale=[
            [0.0, "rgba(15,15,25,0.9)"],
            [0.3, "rgba(99,102,241,0.2)"],
            [0.6, "rgba(99,102,241,0.4)"],
            [1.0, "rgba(99,102,241,0.7)"],
        ],
        zmin=0, zmax=1,
        showscale=False,
    ))

    fig.update_layout(
        title=dict(text="Regime Transition Matrix", font=dict(size=14, color="#e2e8f0")),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(l=120, r=20, t=50, b=40),
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
        xaxis=dict(side="top"),
    )
    return fig


def intraday_sparkline(
    df: pd.DataFrame,
    height: int = 60,
    color_up: str = GREEN,
    color_down: str = RED,
) -> go.Figure:
    """Tiny sparkline chart for intraday price data. No axes, no labels."""
    if df.empty or "Close" not in df.columns:
        # Return an empty figure with a centered "—"
        fig = go.Figure()
        fig.add_annotation(text="—", x=0.5, y=0.5, showarrow=False,
                           font=dict(color="#475569", size=14),
                           xref="paper", yref="paper")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        return fig

    closes = df["Close"].dropna()
    if len(closes) < 2:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        return fig

    # Color based on day direction
    line_color = color_up if closes.iloc[-1] >= closes.iloc[0] else color_down
    fill_color = _hex_to_rgba(line_color, 0.12)

    xs = closes.index  # Use actual datetime index
    y_min = float(closes.min())
    y_max = float(closes.max())
    # Small padding so the line doesn't sit on the edge
    y_pad = (y_max - y_min) * 0.1 if y_max > y_min else 1.0

    fig = go.Figure()
    # Invisible baseline at the min so fill covers the price area only
    fig.add_trace(go.Scatter(
        x=xs, y=[y_min] * len(xs),
        mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=xs,
        y=closes.values,
        mode="lines",
        line=dict(color=line_color, width=1.5),
        fill="tonexty",
        fillcolor=fill_color,
        showlegend=False,
        hovertemplate="%{x|%b %d, %I:%M %p}<br><b>%{y:,.2f}</b><extra></extra>",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[y_min - y_pad, y_max + y_pad]),
        hoverlabel=dict(
            bgcolor="#1e1b4b",
            font_size=11,
            font_color="#e2e8f0",
            bordercolor="#818cf8",
        ),
    )
    return fig
