"""Real-time market data via yfinance (15-min delayed)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


# ── Ticker Registry ──────────────────────────────────────────────────────────

MARKET_TICKERS: dict[str, dict] = {
    # Major indices
    "^GSPC":    {"name": "S&P 500",      "category": "Indices",     "fmt": ",.2f"},
    "^IXIC":    {"name": "Nasdaq",        "category": "Indices",     "fmt": ",.2f"},
    "^DJI":     {"name": "Dow Jones",     "category": "Indices",     "fmt": ",.2f"},
    "^RUT":     {"name": "Russell 2000",  "category": "Indices",     "fmt": ",.2f"},
    # Rates & volatility
    "^TNX":     {"name": "10Y Treasury",  "category": "Rates",       "fmt": ".3f"},
    "^IRX":     {"name": "13W T-Bill",    "category": "Rates",       "fmt": ".3f"},
    "^VIX":     {"name": "VIX",           "category": "Rates",       "fmt": ".2f"},
    # Commodities & dollar
    "CL=F":     {"name": "Crude Oil",     "category": "Commodities", "fmt": ".2f"},
    "GC=F":     {"name": "Gold",          "category": "Commodities", "fmt": ",.2f"},
    "DX-Y.NYB": {"name": "Dollar Index",  "category": "Commodities", "fmt": ".3f"},
    # Crypto
    "BTC-USD":  {"name": "Bitcoin",       "category": "Crypto",      "fmt": ",.2f"},
}


@dataclass
class MarketQuote:
    ticker: str
    name: str
    category: str
    price: float | None
    change: float | None
    pct_change: float | None
    volume: int | None
    last_update: str
    fmt: str = ",.2f"


def _empty_quote(ticker: str) -> MarketQuote:
    meta = MARKET_TICKERS.get(ticker, {"name": ticker, "category": "Other", "fmt": ",.2f"})
    return MarketQuote(
        ticker=ticker,
        name=meta["name"],
        category=meta["category"],
        price=None,
        change=None,
        pct_change=None,
        volume=None,
        last_update=datetime.now().strftime("%H:%M:%S"),
        fmt=meta.get("fmt", ",.2f"),
    )


def fetch_market_snapshot() -> dict[str, MarketQuote]:
    """Fetch current prices for all tracked tickers.

    Returns dict mapping ticker -> MarketQuote.
    """
    import yfinance as yf

    results: dict[str, MarketQuote] = {}
    tickers_str = " ".join(MARKET_TICKERS.keys())

    try:
        batch = yf.Tickers(tickers_str)
        for ticker, meta in MARKET_TICKERS.items():
            try:
                # Use fast_info for speed (avoids full page scrape)
                info = batch.tickers[ticker].fast_info
                price = getattr(info, "last_price", None)
                prev_close = getattr(info, "previous_close", None)
                change = (price - prev_close) if price and prev_close else None
                pct = (change / prev_close * 100) if change and prev_close else None

                results[ticker] = MarketQuote(
                    ticker=ticker,
                    name=meta["name"],
                    category=meta["category"],
                    price=price,
                    change=change,
                    pct_change=pct,
                    volume=getattr(info, "last_volume", None),
                    last_update=datetime.now().strftime("%H:%M:%S"),
                    fmt=meta.get("fmt", ",.2f"),
                )
            except Exception:
                results[ticker] = _empty_quote(ticker)
    except Exception:
        for ticker in MARKET_TICKERS:
            results[ticker] = _empty_quote(ticker)

    return results


def fetch_intraday(ticker: str, period: str = "1d", interval: str = "15m") -> pd.DataFrame:
    """Fetch intraday OHLCV data for sparkline charts.

    Returns DataFrame with columns: Open, High, Low, Close, Volume.
    """
    import yfinance as yf

    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_multi_intraday(
    period: str = "1d", interval: str = "15m",
) -> dict[str, pd.DataFrame]:
    """Fetch intraday data for all tickers."""
    results = {}
    for ticker in MARKET_TICKERS:
        results[ticker] = fetch_intraday(ticker, period, interval)
    return results
