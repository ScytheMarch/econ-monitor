"""AI Economic Brief page — Gemini-powered daily market analysis."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # ── Title ────────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="font-weight:700;letter-spacing:-0.5px;margin-bottom:4px">'
        '🤖 <span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        'AI Economic Brief</span></h2>',
        unsafe_allow_html=True,
    )
    st.caption("AI-powered macro analysis · Powered by Gemini")

    # ── Check availability ──────────────────────────────────────────────────
    from econ_monitor.analytics.ai_analysis import is_ai_available

    if not is_ai_available():
        _render_setup_instructions()
        return

    # ── Generate / cache the brief ──────────────────────────────────────────
    from econ_monitor.analytics.ai_analysis import build_full_context, context_hash

    ctx = build_full_context()
    ctx_h = context_hash(ctx)

    # Regenerate button
    col_regen, col_spacer = st.columns([1, 5])
    with col_regen:
        if st.button("🔄 Regenerate", key="regen_brief", help="Generate a fresh analysis"):
            _generate_brief_cached.clear()
            st.rerun()

    brief = _generate_brief_cached(ctx_h, ctx)

    if brief is None:
        st.warning("Unable to generate analysis. Check your Gemini API key and try again.")
        return

    # ── Headline ────────────────────────────────────────────────────────────
    headline = brief.get("headline", "Economic Analysis")
    st.markdown(
        f'<div style="font-size:1.5em;font-weight:800;color:#f1f5f9;'
        f'letter-spacing:-0.5px;margin:16px 0 12px 0;line-height:1.3;'
        f'padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.06)">'
        f'📰 {headline}</div>',
        unsafe_allow_html=True,
    )

    # ── Summary ─────────────────────────────────────────────────────────────
    summary = brief.get("summary", "")
    if summary:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.06),'
            f'rgba(139,92,246,0.03));border:1px solid rgba(99,102,241,0.12);'
            f'border-radius:14px;padding:24px 28px;margin:8px 0 16px 0">'
            f'<div style="color:#94a3b8;font-size:0.75em;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px">'
            f'📊 Market Analysis</div>'
            f'<div style="color:#cbd5e1;font-size:0.92em;line-height:1.75">'
            f'{_md_to_html(summary)}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Risks & Opportunities ───────────────────────────────────────────────
    risks = brief.get("risks", "")
    opps = brief.get("opportunities", "")

    if risks or opps:
        col_risk, col_opp = st.columns(2)

        with col_risk:
            st.markdown(
                f'<div style="background:rgba(239,68,68,0.04);'
                f'border:1px solid rgba(239,68,68,0.15);border-radius:14px;'
                f'padding:20px 24px;min-height:160px">'
                f'<div style="color:#fca5a5;font-weight:700;font-size:0.8em;'
                f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px">'
                f'🔴 Key Risks</div>'
                f'<div style="color:#94a3b8;font-size:0.88em;line-height:1.75">'
                f'{_md_to_html(risks) if risks else "No significant risks identified."}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        with col_opp:
            st.markdown(
                f'<div style="background:rgba(34,197,94,0.04);'
                f'border:1px solid rgba(34,197,94,0.15);border-radius:14px;'
                f'padding:20px 24px;min-height:160px">'
                f'<div style="color:#86efac;font-weight:700;font-size:0.8em;'
                f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px">'
                f'🟢 Opportunities</div>'
                f'<div style="color:#94a3b8;font-size:0.88em;line-height:1.75">'
                f'{_md_to_html(opps) if opps else "No clear opportunities identified."}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ── Watchlist ───────────────────────────────────────────────────────────
    watchlist = brief.get("watchlist", "")
    if watchlist:
        st.markdown(
            f'<div style="background:rgba(251,191,36,0.04);'
            f'border:1px solid rgba(251,191,36,0.15);border-radius:14px;'
            f'padding:20px 24px;margin:16px 0">'
            f'<div style="color:#fcd34d;font-weight:700;font-size:0.8em;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px">'
            f'👀 Watchlist</div>'
            f'<div style="color:#94a3b8;font-size:0.88em;line-height:1.75">'
            f'{_md_to_html(watchlist)}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Disclaimer ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:20px;padding:12px 16px;'
        'background:rgba(255,255,255,0.02);border-radius:8px;'
        'border:1px solid rgba(255,255,255,0.04)">'
        '<span style="color:#64748b;font-size:0.78em;line-height:1.5">'
        '⚠️ AI-generated analysis for informational purposes only. '
        'Not financial advice. Always verify with primary sources before making decisions.'
        '</span></div>',
        unsafe_allow_html=True,
    )


# ── Cached generation ───────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="🤖 Generating AI analysis...")
def _generate_brief_cached(ctx_hash: str, context: str) -> dict | None:
    from econ_monitor.analytics.ai_analysis import generate_market_brief
    return generate_market_brief(ctx_hash, context)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """Minimal markdown to HTML: bold, bullets, newlines."""
    import re
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b style="color:#e2e8f0">\1</b>', text)
    # Bullet lists (- item)
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                in_list = True
            result.append(
                f'<div style="display:flex;gap:8px;margin:4px 0">'
                f'<span style="color:#818cf8;flex-shrink:0">•</span>'
                f'<span>{stripped[2:]}</span></div>'
            )
        elif stripped:
            in_list = False
            result.append(f'<p style="margin:8px 0">{stripped}</p>')
    return "".join(result)


def _render_setup_instructions() -> None:
    """Show setup instructions when API key is not configured."""
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(99,102,241,0.06),'
        'rgba(139,92,246,0.03));border:1px solid rgba(99,102,241,0.2);'
        'border-radius:14px;padding:28px 32px;margin:20px 0;text-align:center">'
        '<div style="font-size:2.5em;margin-bottom:12px">🤖</div>'
        '<div style="color:#c7d2fe;font-size:1.2em;font-weight:700;margin-bottom:8px">'
        'AI Analysis Not Configured</div>'
        '<div style="color:#94a3b8;font-size:0.9em;line-height:1.7;max-width:500px;margin:0 auto">'
        'To enable AI-powered economic analysis, add your Google Gemini API key '
        'to the <code style="background:rgba(255,255,255,0.06);padding:2px 6px;'
        'border-radius:4px;font-size:0.9em">.env</code> file:<br><br>'
        '<code style="background:rgba(255,255,255,0.06);padding:6px 14px;'
        'border-radius:6px;font-size:0.95em;color:#c7d2fe">'
        'GEMINI_API_KEY=your-key-here</code><br><br>'
        'Get your free key at <span style="color:#818cf8">aistudio.google.com/apikey</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
