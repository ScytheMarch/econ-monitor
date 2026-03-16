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
    filter_cols = st.columns([2, 2, 4])
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

    period, interval = _PERIOD_OPTIONS[selected_period]

    # ── Fetch data ───────────────────────────────────────────────────────────
    snapshot = _fetch_snapshot_cached()
    intraday = _fetch_intraday_cached(period, interval)

    if not snapshot:
        st.warning("Unable to fetch market data. Check your internet connection.")
        return

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
