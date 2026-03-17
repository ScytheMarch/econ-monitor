"""Live Markets page — real-time prices, sparklines, and macro-market context."""

from __future__ import annotations

import streamlit as st


# ── Category definitions ─────────────────────────────────────────────────────
_CATEGORIES: dict[str, list[str]] = {
    "Major Indices": ["^GSPC", "^IXIC", "^DJI", "^RUT"],
    "Rates & Volatility": ["^TNX", "^IRX", "^VIX"],
    "Commodities & Dollar": ["CL=F", "GC=F", "DX-Y.NYB"],
    "Crypto": ["BTC-USD"],
}

_PERIOD_OPTIONS = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"),
}


def render() -> None:
    # ── Title ────────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '📈 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'Live Markets</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption("15-minute delayed quotes · Powered by Yahoo Finance")

    # ── Auto-refresh every 5 minutes ─────────────────────────────────────────
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=300_000, key="market_refresh")
    except ImportError:
        pass

    # ── Filters ──────────────────────────────────────────────────────────────
    filter_cols = st.columns([1.5, 1.5, 3, 2])
    with filter_cols[0]:
        cat_options = ["All"] + list(_CATEGORIES.keys())
        selected_cat = st.selectbox(
            "Category", cat_options, index=0, key="market_cat_filter",
        )
    with filter_cols[1]:
        selected_period = st.radio(
            "Period", list(_PERIOD_OPTIONS.keys()), index=0,
            horizontal=True, key="market_period_radio",
        )
    with filter_cols[3]:
        custom_ticker = st.text_input(
            "🔍 Look up ticker",
            placeholder="e.g. AAPL, MSFT, TSLA",
            key="market_custom_ticker",
        ).strip().upper()

    period, interval = _PERIOD_OPTIONS[selected_period]

    # ── Fetch data ───────────────────────────────────────────────────────────
    snapshot = _fetch_snapshot_cached()
    intraday = _fetch_intraday_cached(period, interval)

    if not snapshot:
        st.warning("Unable to fetch market data. Check your internet connection.")
        return

    # ── Custom ticker lookup ─────────────────────────────────────────────────
    if custom_ticker:
        _render_custom_ticker(custom_ticker, period, interval)
        st.markdown(
            '<hr style="margin:16px 0;border-color:rgba(99,102,241,0.12)">',
            unsafe_allow_html=True,
        )

    # ── Render by category ───────────────────────────────────────────────────
    if selected_cat == "All":
        cats_to_show = _CATEGORIES
    else:
        cats_to_show = {selected_cat: _CATEGORIES[selected_cat]}

    for cat_name, tickers in cats_to_show.items():
        _render_section(cat_name, snapshot, intraday, tickers)

    # ── Macro-Market Context Panel ───────────────────────────────────────────
    st.markdown(
        '<hr style="margin:16px 0;border-color:rgba(99,102,241,0.12)">',
        unsafe_allow_html=True,
    )
    _render_macro_context(snapshot)


# ── Cached data fetching ─────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner="Fetching market data...")
def _fetch_snapshot_cached() -> dict:
    from econ_monitor.data.market_data import fetch_market_snapshot
    snapshot = fetch_market_snapshot()
    return {
        ticker: {
            "ticker": q.ticker,
            "name": q.name,
            "category": q.category,
            "price": q.price,
            "change": q.change,
            "pct_change": q.pct_change,
            "volume": q.volume,
            "last_update": q.last_update,
            "fmt": q.fmt,
        }
        for ticker, q in snapshot.items()
    }


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_intraday_cached(period: str = "1d", interval: str = "5m") -> dict:
    from econ_monitor.data.market_data import fetch_multi_intraday
    result = fetch_multi_intraday(period=period, interval=interval)
    out = {}
    for ticker, df in result.items():
        if not df.empty:
            out[ticker] = {"data": df.to_dict(), "index": df.index.tolist()}
        else:
            out[ticker] = None
    return out


def _rebuild_intraday(cached: dict | None):
    """Rebuild a DataFrame from cached intraday dict."""
    import pandas as pd
    if cached is None:
        return pd.DataFrame()
    df = pd.DataFrame(cached["data"], index=cached["index"])
    return df


# ── Custom ticker lookup ──────────────────────────────────────────────────────

def _render_custom_ticker(ticker: str, period: str, interval: str) -> None:
    """Fetch and render a user-searched ticker with full chart + stats."""
    import yfinance as yf
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    tk = yf.Ticker(ticker)

    # ── Collect all data ──────────────────────────────────────────────────
    price = None
    prev_close = None
    name = ticker
    vol = None
    day_high = None
    day_low = None
    mkt_cap = None
    sector = ""
    industry = ""
    beta = None
    pe_ratio = None
    fwd_pe = None
    eps = None
    div_yield = None
    week52_high = None
    week52_low = None
    avg_vol = None
    open_price = None
    currency = "USD"

    # 1) fast_info (lightweight, works on Cloud)
    try:
        fi = tk.fast_info
        price = getattr(fi, "last_price", None)
        prev_close = getattr(fi, "previous_close", None)
        mkt_cap = getattr(fi, "market_cap", None)
        day_high = getattr(fi, "day_high", None)
        day_low = getattr(fi, "day_low", None)
        open_price = getattr(fi, "open", None)
        week52_high = getattr(fi, "year_high", None)
        week52_low = getattr(fi, "year_low", None)
        currency = getattr(fi, "currency", "USD") or "USD"
    except Exception:
        pass

    # 2) history for price fallback + chart data
    hist = pd.DataFrame()
    try:
        hist = tk.history(period=period, interval=interval)
        if price is None and not hist.empty and "Close" in hist.columns:
            price = float(hist["Close"].iloc[-1])
        if not hist.empty and "Volume" in hist.columns:
            vol = int(hist["Volume"].iloc[-1])
        if prev_close is None:
            daily = tk.history(period="5d", interval="1d")
            if not daily.empty and len(daily) >= 2:
                prev_close = float(daily["Close"].iloc[-2])
    except Exception:
        pass

    # 3) info for rich metadata (may fail on Cloud — graceful)
    info: dict = {}
    try:
        info = tk.info or {}
        name = info.get("shortName") or info.get("longName") or ticker
        sector = info.get("sector", "") or sector
        industry = info.get("industry", "")
        beta = info.get("beta")
        pe_ratio = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        eps = info.get("trailingEps")
        div_yield = info.get("dividendYield")
        avg_vol = info.get("averageVolume")
        if vol is None:
            vol = info.get("regularMarketVolume") or info.get("volume")
        if mkt_cap is None:
            mkt_cap = info.get("marketCap")
        if day_high is None:
            day_high = info.get("regularMarketDayHigh") or info.get("dayHigh")
        if day_low is None:
            day_low = info.get("regularMarketDayLow") or info.get("dayLow")
        if price is None:
            price = info.get("regularMarketPrice") or info.get("currentPrice")
        if prev_close is None:
            prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
        if open_price is None:
            open_price = info.get("regularMarketOpen") or info.get("open")
        if week52_high is None:
            week52_high = info.get("fiftyTwoWeekHigh")
        if week52_low is None:
            week52_low = info.get("fiftyTwoWeekLow")
    except Exception:
        pass

    if price is None:
        st.error(f"No data available for **{ticker}**. It may be delisted or invalid.")
        return

    # ── Computed values ────────────────────────────────────────────────────
    change = None
    pct = None
    if prev_close and prev_close > 0:
        change = price - prev_close
        pct = (change / prev_close) * 100

    is_up = (change or 0) >= 0
    chg_color = "#22c55e" if is_up else "#ef4444"
    arrow = "▲" if is_up else "▼"

    if pct is not None and change is not None:
        sign = "+" if is_up else ""
        change_str = (
            f'<span style="color:{chg_color};font-size:0.95em;font-weight:600">'
            f'{arrow} {sign}{change:,.2f} ({sign}{pct:.2f}%)</span>'
        )
    else:
        change_str = '<span style="color:#475569;font-size:0.82em">—</span>'

    # Format helpers
    def _fmt_big(n):
        if n is None:
            return "N/A"
        if n >= 1_000_000_000_000:
            return f"${n / 1_000_000_000_000:.2f}T"
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n / 1_000_000:.1f}M"
        return f"${n:,.0f}"

    def _fmt_vol(v):
        if v is None or v <= 0:
            return "N/A"
        if v >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}B"
        if v >= 1_000_000:
            return f"{v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"{v / 1_000:.0f}K"
        return f"{v:,}"

    def _na(v, fmt=""):
        if v is None:
            return '<span style="color:#475569">N/A</span>'
        if fmt == "$":
            return f"${v:,.2f}"
        if fmt == "%":
            return f"{v * 100:.2f}%"
        if fmt == ".2f":
            return f"{v:.2f}"
        if fmt == ".1f":
            return f"{v:.1f}"
        return f"{v}"

    # 52-week position
    pct_52w = None
    if week52_high and week52_low and week52_high > week52_low:
        pct_52w = (price - week52_low) / (week52_high - week52_low) * 100

    # ── Section header ────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:#64748b;font-size:0.75em;text-transform:uppercase;'
        f'letter-spacing:1.5px;font-weight:600;margin:16px 0 8px 0">Ticker Lookup</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Header bar (name, price, change) ──────────────────────────
    meta_parts = [x for x in [sector, industry] if x]
    meta_line = " · ".join(meta_parts) if meta_parts else ""
    meta_span = (
        f' <span style="color:#475569;font-size:0.7em;font-weight:400">'
        f'— {meta_line}</span>' if meta_line else ""
    )

    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.10),'
        f'rgba(139,92,246,0.06));border:1px solid rgba(99,102,241,0.2);'
        f'border-radius:14px;padding:20px 24px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:baseline;gap:16px;flex-wrap:wrap">'
        f'<div style="color:#e0e7ff;font-size:1.1em;font-weight:700">{name}'
        f' <span style="color:#64748b;font-weight:400">({ticker})</span>'
        f'{meta_span}</div>'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;gap:14px;margin-top:6px;'
        f'flex-wrap:wrap">'
        f'<span style="color:#f1f5f9;font-size:2.2em;font-weight:800;'
        f'letter-spacing:-1px">${price:,.2f}</span>'
        f'{change_str}'
        f'<span style="color:#475569;font-size:0.75em">{currency}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Row 2: Full chart with volume ────────────────────────────────────
    try:
        if hist.empty or "Close" not in hist.columns:
            hist = tk.history(period=period, interval=interval)
        if not hist.empty and "Close" in hist.columns:
            closes = hist["Close"].dropna()
            has_volume = "Volume" in hist.columns and hist["Volume"].sum() > 0

            if has_volume:
                fig = make_subplots(
                    rows=2, cols=1, shared_xaxes=True,
                    row_heights=[0.78, 0.22], vertical_spacing=0.02,
                )
            else:
                fig = go.Figure()

            line_color = "#22c55e" if closes.iloc[-1] >= closes.iloc[0] else "#ef4444"
            fill_color = (
                "rgba(34,197,94,0.08)" if line_color == "#22c55e"
                else "rgba(239,68,68,0.08)"
            )

            # Price line with area fill
            hover_tpl = (
                "<b>%{x|%b %d, %Y %I:%M %p}</b><br>"
                "Price: $%{y:,.2f}<extra></extra>"
            )
            fig.add_trace(go.Scatter(
                x=closes.index,
                y=closes.values,
                mode="lines",
                line=dict(color=line_color, width=2),
                fill="tozeroy",
                fillcolor=fill_color,
                showlegend=False,
                hovertemplate=hover_tpl,
            ), row=1, col=1) if has_volume else fig.add_trace(go.Scatter(
                x=closes.index,
                y=closes.values,
                mode="lines",
                line=dict(color=line_color, width=2),
                fill="tozeroy",
                fillcolor=fill_color,
                showlegend=False,
                hovertemplate=hover_tpl,
            ))

            # Volume bars
            if has_volume:
                vol_data = hist["Volume"].fillna(0)
                vol_colors = [
                    "rgba(99,102,241,0.4)" if hist["Close"].iloc[i] >= hist["Open"].iloc[i]
                    else "rgba(239,68,68,0.3)"
                    for i in range(len(hist))
                ] if "Open" in hist.columns else ["rgba(99,102,241,0.3)"] * len(hist)

                fig.add_trace(go.Bar(
                    x=vol_data.index,
                    y=vol_data.values,
                    marker_color=vol_colors,
                    showlegend=False,
                    hovertemplate="Vol: %{y:,.0f}<extra></extra>",
                ), row=2, col=1)

                fig.update_yaxes(
                    showgrid=False, showticklabels=False, row=2, col=1,
                )

            # Layout
            y_min = float(closes.min())
            y_max = float(closes.max())
            y_pad = (y_max - y_min) * 0.08 if y_max > y_min else 1.0

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=340 if has_volume else 280,
                margin=dict(l=8, r=8, t=8, b=8),
                hovermode="x unified",
                hoverlabel=dict(
                    bgcolor="#1e1b4b",
                    font_size=12,
                    font_color="#e2e8f0",
                    bordercolor="#818cf8",
                ),
            )

            fig.update_xaxes(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                tickfont=dict(size=10, color="#64748b"),
                linecolor="rgba(255,255,255,0.06)",
                row=1 if has_volume else None, col=1 if has_volume else None,
            )
            fig.update_yaxes(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                tickfont=dict(size=10, color="#64748b"),
                tickprefix="$",
                range=[y_min - y_pad, y_max + y_pad],
                linecolor="rgba(255,255,255,0.06)",
                row=1 if has_volume else None, col=1 if has_volume else None,
            )

            st.plotly_chart(
                fig, use_container_width=True,
                config={"displayModeBar": False},
                key=f"chart_custom_{ticker}",
            )
        else:
            st.caption("No chart data available for this ticker.")
    except Exception:
        st.caption("Unable to load chart data.")

    # ── Row 3: Two-panel stats layout ────────────────────────────────────
    def _stat_row(label: str, value: str, border: bool = True) -> str:
        border_css = "border-bottom:1px solid rgba(255,255,255,0.04);" if border else ""
        return (
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:7px 0;{border_css}">'
            f'<span style="color:#94a3b8;font-size:0.82em">{label}</span>'
            f'<span style="color:#e2e8f0;font-size:0.82em;font-weight:600">'
            f'{value}</span></div>'
        )

    # Color-coded values
    def _beta_html(b):
        if b is None:
            return '<span style="color:#475569">N/A</span>'
        c = "#22c55e" if 0.8 <= b <= 1.2 else "#eab308" if b < 0.8 else "#ef4444"
        tip = "Low volatility" if b < 0.8 else "Market-like" if b <= 1.2 else "High volatility"
        return f'<span style="color:{c}" title="{tip}">{b:.2f}</span>'

    def _pe_html(p):
        if p is None:
            return '<span style="color:#475569">N/A</span>'
        c = "#22c55e" if p < 20 else "#eab308" if p < 35 else "#ef4444"
        tip = "Value" if p < 20 else "Fair" if p < 35 else "Expensive"
        return f'<span style="color:{c}" title="{tip}">{p:.1f}</span>'

    def _eps_html(e):
        if e is None:
            return '<span style="color:#475569">N/A</span>'
        c = "#22c55e" if e > 0 else "#ef4444"
        return f'<span style="color:{c}">${e:.2f}</span>'

    left_col, right_col = st.columns(2)

    with left_col:
        # Trading data panel
        rows = []
        rows.append(_stat_row("Open", _na(open_price, "$")))
        rows.append(_stat_row("Previous Close", _na(prev_close, "$")))
        if day_high is not None and day_low is not None:
            rows.append(_stat_row("Day Range",
                f"${day_low:,.2f} – ${day_high:,.2f}"))
        else:
            rows.append(_stat_row("Day Range", _na(None)))
        # 52-week range with visual bar
        if week52_low is not None and week52_high is not None:
            bar_pct = max(0, min(100, pct_52w or 0))
            w52_val = (
                f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px">'
                f'<span>${week52_low:,.2f} – ${week52_high:,.2f}</span>'
                f'<div style="width:120px;background:rgba(255,255,255,0.06);'
                f'border-radius:3px;height:4px;overflow:hidden">'
                f'<div style="background:linear-gradient(90deg,#6366f1,#a78bfa);'
                f'height:100%;width:{bar_pct:.0f}%;border-radius:3px"></div>'
                f'</div></div>'
            )
            rows.append(_stat_row("52-Week Range", w52_val))
        else:
            rows.append(_stat_row("52-Week Range", _na(None)))
        rows.append(_stat_row("Volume", _fmt_vol(vol)))
        rows.append(_stat_row("Avg Volume", _fmt_vol(avg_vol), border=False))

        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,255,255,0.03),'
            f'rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.06);'
            f'border-radius:12px;padding:14px 18px">'
            f'<div style="color:#818cf8;font-size:0.72em;text-transform:uppercase;'
            f'letter-spacing:1px;font-weight:700;margin-bottom:8px">📊 Trading Data</div>'
            + "".join(rows)
            + '</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        # Fundamentals panel
        rows2 = []
        rows2.append(_stat_row("Market Cap", _fmt_big(mkt_cap)))
        rows2.append(_stat_row("Beta", _beta_html(beta)))
        rows2.append(_stat_row("P/E (TTM)", _pe_html(pe_ratio)))
        rows2.append(_stat_row("Forward P/E", _pe_html(fwd_pe)))
        rows2.append(_stat_row("EPS (TTM)", _eps_html(eps)))
        rows2.append(_stat_row("Dividend Yield",
            _na(div_yield, "%") if div_yield and div_yield > 0
            else '<span style="color:#475569">N/A</span>', border=False))

        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,255,255,0.03),'
            f'rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.06);'
            f'border-radius:12px;padding:14px 18px">'
            f'<div style="color:#818cf8;font-size:0.72em;text-transform:uppercase;'
            f'letter-spacing:1px;font-weight:700;margin-bottom:8px">📋 Fundamentals</div>'
            + "".join(rows2)
            + '</div>',
            unsafe_allow_html=True,
        )

    # Note about data availability on Cloud
    if not info:
        st.markdown(
            '<div style="color:#475569;font-size:0.7em;text-align:center;'
            'margin-top:6px;font-style:italic">'
            'ℹ️ Some fundamental data (beta, P/E, EPS) may be unavailable on '
            'Streamlit Cloud due to Yahoo Finance rate limits.</div>',
            unsafe_allow_html=True,
        )


# ── Section renderer ─────────────────────────────────────────────────────────

def _render_section(
    title: str,
    snapshot: dict,
    intraday: dict,
    tickers: list[str],
) -> None:
    from econ_monitor.ui.charts import intraday_sparkline

    st.markdown(
        f'<div style="color:#64748b;font-size:0.75em;text-transform:uppercase;'
        f'letter-spacing:1.5px;font-weight:600;margin:16px 0 8px 0">{title}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(tickers))
    for i, ticker in enumerate(tickers):
        with cols[i]:
            q = snapshot.get(ticker, {})
            price = q.get("price")
            change = q.get("change")
            pct = q.get("pct_change")
            fmt = q.get("fmt", ",.2f")
            name = q.get("name", ticker)

            # Price display
            price_str = f"{price:{fmt}}" if price is not None else "—"

            # Change display
            if pct is not None and change is not None:
                sign = "+" if change >= 0 else ""
                change_color = "#22c55e" if change >= 0 else "#ef4444"
                arrow = "▲" if change >= 0 else "▼"
                change_str = (
                    f'<span style="color:{change_color};font-size:0.82em">'
                    f'{arrow} {sign}{change:{fmt}} ({sign}{pct:.2f}%)</span>'
                )
            else:
                change_str = '<span style="color:#475569;font-size:0.82em">—</span>'

            # Volume
            vol = q.get("volume")
            if vol is not None and vol > 0:
                if vol >= 1_000_000_000:
                    vol_str = f"Vol: {vol / 1_000_000_000:.1f}B"
                elif vol >= 1_000_000:
                    vol_str = f"Vol: {vol / 1_000_000:.1f}M"
                elif vol >= 1_000:
                    vol_str = f"Vol: {vol / 1_000:.0f}K"
                else:
                    vol_str = f"Vol: {vol:,}"
            else:
                vol_str = ""

            # Card HTML
            st.markdown(
                f'<div style="background:linear-gradient(135deg,rgba(255,255,255,0.04),'
                f'rgba(255,255,255,0.015));border:1px solid rgba(255,255,255,0.08);'
                f'border-radius:12px;padding:14px 16px;min-height:100px">'
                f'<div style="color:#94a3b8;font-size:0.78em;font-weight:600;'
                f'margin-bottom:4px">{name}</div>'
                f'<div style="color:#f1f5f9;font-size:1.4em;font-weight:700;'
                f'letter-spacing:-0.5px">{price_str}</div>'
                f'{change_str}'
                f'<div style="color:#475569;font-size:0.7em;margin-top:2px">{vol_str}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Sparkline
            intra = _rebuild_intraday(intraday.get(ticker))
            fig = intraday_sparkline(intra, height=55)
            st.plotly_chart(
                fig, use_container_width=True,
                config={"displayModeBar": False},
                key=f"spark_{ticker}",
            )


# ── Macro-Market Context Panel ───────────────────────────────────────────────

def _render_macro_context(snapshot: dict) -> None:
    """Compare market signals vs regime score, flag divergences."""
    st.markdown(
        '<div style="color:#c7d2fe;font-weight:700;font-size:0.95em;margin-bottom:8px">'
        '🔗 Market-Macro Context</div>',
        unsafe_allow_html=True,
    )

    bullets = []

    # S&P direction vs regime
    sp = snapshot.get("^GSPC", {})
    sp_pct = sp.get("pct_change")
    if sp_pct is not None:
        direction = "up" if sp_pct >= 0 else "down"
        bullets.append(f"S&P 500 is {direction} {abs(sp_pct):.2f}% today")

    # VIX level interpretation
    vix = snapshot.get("^VIX", {})
    vix_price = vix.get("price")
    if vix_price is not None:
        if vix_price < 15:
            vix_read = "very low (complacency)"
        elif vix_price < 20:
            vix_read = "normal range"
        elif vix_price < 30:
            vix_read = "elevated (caution)"
        else:
            vix_read = "high (fear/stress)"
        bullets.append(f"VIX at {vix_price:.1f} — {vix_read}")

    # 10Y yield level
    tnx = snapshot.get("^TNX", {})
    tnx_price = tnx.get("price")
    if tnx_price is not None:
        bullets.append(f"10Y Treasury yield at {tnx_price:.3f}%")

    # Oil direction
    oil = snapshot.get("CL=F", {})
    oil_pct = oil.get("pct_change")
    oil_price = oil.get("price")
    if oil_pct is not None and oil_price is not None:
        oil_dir = "up" if oil_pct >= 0 else "down"
        bullets.append(f"Crude oil at ${oil_price:.2f} ({oil_dir} {abs(oil_pct):.2f}%)")

    # Dollar index
    dxy = snapshot.get("DX-Y.NYB", {})
    dxy_price = dxy.get("price")
    dxy_pct = dxy.get("pct_change")
    if dxy_price is not None and dxy_pct is not None:
        dxy_dir = "strengthening" if dxy_pct >= 0 else "weakening"
        bullets.append(f"Dollar index at {dxy_price:.2f} ({dxy_dir})")

    # Try to get regime score for comparison
    try:
        from econ_monitor.analytics.regime import compute_regime_score
        regime = compute_regime_score()
        regime_label = regime["label"]
        regime_score = regime["score"]
        bullets.append(f"Macro regime: {regime_label} (score: {regime_score:+.3f})")

        # Flag divergences
        if sp_pct is not None and regime_score < -0.15 and sp_pct > 0.5:
            bullets.append(
                "⚠️ <b>Divergence:</b> Markets rising despite weakening macro indicators — "
                "watch for potential correction"
            )
        elif sp_pct is not None and regime_score > 0.15 and sp_pct < -0.5:
            bullets.append(
                "⚠️ <b>Divergence:</b> Markets falling despite strong macro conditions — "
                "could be a buying opportunity or early warning"
            )
    except Exception:
        pass

    if bullets:
        bullet_html = "".join(
            f'<div style="color:#94a3b8;font-size:0.85em;padding:3px 0;line-height:1.5">'
            f'• {b}</div>'
            for b in bullets
        )
        st.markdown(
            f'<div style="background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.12);'
            f'border-radius:12px;padding:16px 20px">{bullet_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Market context unavailable — data may still be loading.")

    # Last update time
    any_update = next(
        (q.get("last_update") for q in snapshot.values() if q.get("last_update")),
        None,
    )
    if any_update:
        st.caption(f"Last updated: {any_update} · Data delayed ~15 min")
