"""Streamlit entry point for the Economic Monitor dashboard.

Views live in ui/views/ (NOT ui/pages/) to prevent Streamlit auto-page discovery.
"""

from __future__ import annotations

import streamlit as st


def overview_page():
    from econ_monitor.ui.views.overview import render
    render()

def indicator_detail_page():
    from econ_monitor.ui.views.indicator_detail import render
    render()

def activity_feed_page():
    from econ_monitor.ui.views.activity_feed import render
    render()

def calendar_page_fn():
    from econ_monitor.ui.views.calendar_view import render
    render()

def guide_page_fn():
    from econ_monitor.ui.views.guide import render
    render()

def models_page_fn():
    from econ_monitor.ui.views.probability_models import render
    render()

def markets_page_fn():
    from econ_monitor.ui.views.markets import render
    render()

def ai_brief_page_fn():
    from econ_monitor.ui.views.ai_brief import render
    render()

def timeline_page_fn():
    from econ_monitor.ui.views.timeline import render
    render()


# ── Navigation ────────────────────────────────────────────────────────────
_page_overview = st.Page(overview_page, title="Overview", icon="📊", default=True)
_page_detail = st.Page(indicator_detail_page, title="Indicator Detail", icon="🔍")
_page_feed = st.Page(activity_feed_page, title="Activity Feed", icon="📡")
_page_calendar = st.Page(calendar_page_fn, title="Economic Calendar", icon="📅")
_page_guide = st.Page(guide_page_fn, title="Indicator Guide", icon="📖")
_page_models = st.Page(models_page_fn, title="Models", icon="🎯")
_page_ai_brief = st.Page(ai_brief_page_fn, title="AI Brief", icon="🤖")
_page_markets = st.Page(markets_page_fn, title="Markets", icon="📈")
_page_timeline = st.Page(timeline_page_fn, title="Timeline", icon="📜")

_all_pages = [_page_overview, _page_detail, _page_feed, _page_calendar, _page_guide, _page_models, _page_ai_brief, _page_markets, _page_timeline]
pg = st.navigation(_all_pages, position="hidden")

# Store page refs so other views can use st.switch_page()
st.session_state["_pages"] = {
    "overview": _page_overview,
    "detail": _page_detail,
    "feed": _page_feed,
    "calendar": _page_calendar,
    "guide": _page_guide,
    "models": _page_models,
    "ai_brief": _page_ai_brief,
    "markets": _page_markets,
    "timeline": _page_timeline,
}

st.set_page_config(
    page_title="Economic Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS — premium glass-on-dark theme ──────────────────────────────
st.markdown("""
<style>
/* ── Import modern font ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global foundation ──────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Rich textured background ─────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(ellipse at 15% 10%, rgba(99, 102, 241, 0.06) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 40%),
        radial-gradient(ellipse at 50% 50%, rgba(30, 27, 46, 0.8) 0%, transparent 70%),
        linear-gradient(145deg, #08080f 0%, #0c0b14 30%, #10101c 60%, #0a0a12 100%) !important;
}

/* Subtle noise-like grain overlay for depth */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        repeating-conic-gradient(rgba(255,255,255,0.008) 0% 25%, transparent 0% 50%) 0 0 / 3px 3px,
        radial-gradient(ellipse at 20% 60%, rgba(99, 102, 241, 0.035) 0%, transparent 50%),
        radial-gradient(ellipse at 75% 25%, rgba(168, 85, 247, 0.025) 0%, transparent 45%),
        radial-gradient(ellipse at 50% 90%, rgba(59, 130, 246, 0.02) 0%, transparent 40%);
    pointer-events: none;
    z-index: 0;
}

/* ── Hide sidebar completely (using top nav instead) ───────────────── */
section[data-testid="stSidebar"] {
    display: none !important;
}

[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* ── Hide Streamlit toolbar (Deploy button / hamburger menu) ───────── */
[data-testid="stToolbar"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

.stDeployButton {
    display: none !important;
}

/* ── Top nav bar compact button sizing ──────────────────────────────── */
.top-nav-bar .stButton > button {
    padding: 3px 1px !important;
    font-size: 0.68em !important;
    white-space: nowrap !important;
    min-height: 34px !important;
    max-height: 34px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    gap: 2px !important;
}
.top-nav-bar .stButton > button span[data-testid="stIconEmoji"] {
    font-size: 0.9em !important;
    margin-right: 1px !important;
}

/* ── Headers ────────────────────────────────────────────────────────── */
.stMarkdown h1, .stMarkdown h2 {
    font-weight: 700 !important;
    letter-spacing: -0.3px;
}

.stMarkdown h3 {
    font-weight: 600 !important;
    letter-spacing: -0.2px;
}

/* ── Metric cards — frosted glass ──────────────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg,
        rgba(255,255,255,0.05) 0%,
        rgba(255,255,255,0.02) 100%) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    padding: 18px 22px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(99, 102, 241, 0.25) !important;
    background: linear-gradient(135deg,
        rgba(99, 102, 241, 0.08) 0%,
        rgba(139, 92, 246, 0.04) 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3),
                0 0 20px rgba(99, 102, 241, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

[data-testid="stMetric"] label {
    font-size: 0.7em !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #64748b !important;
    font-weight: 600 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 700 !important;
    font-size: 1.8em !important;
    color: #f1f5f9 !important;
}

/* ── Buttons (secondary / default) ──────────────────────────────────── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {
    background: linear-gradient(135deg,
        rgba(255,255,255,0.04) 0%,
        rgba(255,255,255,0.02) 100%) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.2px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    padding: 8px 20px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15) !important;
}

.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind]):hover {
    background: linear-gradient(135deg,
        rgba(99, 102, 241, 0.12) 0%,
        rgba(139, 92, 246, 0.06) 100%) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
    color: #c7d2fe !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
}

/* ── Buttons (primary / active) ────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #7c3aed 50%, #8b5cf6 100%) !important;
    border: 1px solid rgba(129, 140, 248, 0.4) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.2px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    padding: 8px 20px !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.25),
                0 2px 8px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #818cf8 0%, #8b5cf6 50%, #a78bfa 100%) !important;
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.35),
                0 4px 15px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0px) scale(0.98);
}

/* ── Selectboxes / Inputs — frosted ───────────────────────────────── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.25s ease !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2) !important;
}

.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1),
                inset 0 1px 3px rgba(0, 0, 0, 0.2) !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.02);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(8px);
    position: sticky;
    top: 0;
    z-index: 99;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    padding: 8px 16px !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.15) !important;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.1) !important;
}

/* ── Prevent tab-click scroll jump ─────────────────────────────────── */
.stTabs [data-baseweb="tab-panel"] {
    overflow-anchor: none;
}

/* Disable Streamlit's auto-scroll-to-changed-element behavior */
[data-stale="false"] {
    scroll-margin-top: 0 !important;
}

.stTabs {
    scroll-margin-top: 0 !important;
    overflow-anchor: none;
}

/* ── Expanders — frosted glass ─────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.25s ease !important;
    backdrop-filter: blur(8px) !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(99, 102, 241, 0.06) !important;
    border-color: rgba(99, 102, 241, 0.18) !important;
}

details {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.015) !important;
    transition: all 0.25s ease !important;
    backdrop-filter: blur(8px) !important;
}

details:hover {
    border-color: rgba(99, 102, 241, 0.15) !important;
}

details[open] {
    border-color: rgba(99, 102, 241, 0.2) !important;
    background: rgba(99, 102, 241, 0.025) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
}

/* ── Plotly charts — glass container ───────────────────────────────── */
.js-plotly-plot .plotly .main-svg {
    border-radius: 14px;
}

[data-testid="stPlotlyChart"] {
    background: linear-gradient(135deg,
        rgba(255,255,255,0.02) 0%,
        rgba(255,255,255,0.008) 100%) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    padding: 8px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.25s ease !important;
}

[data-testid="stPlotlyChart"]:hover {
    border-color: rgba(99, 102, 241, 0.12) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}

/* ── Progress bar ───────────────────────────────────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.3) !important;
}

/* ── Dividers ───────────────────────────────────────────────────────── */
hr {
    border-color: rgba(255,255,255,0.05) !important;
    margin: 16px 0 !important;
}

/* ── Dataframes ─────────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    overflow: hidden;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15) !important;
}

/* ── Toast / success / warning ──────────────────────────────────────── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
}

/* ── Scrollbar ──────────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.2);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.4);
}

/* ── Smooth transitions on all interactive elements ─────────────────── */
a, button, input, select, details, [role="tab"] {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* ── Caption text ───────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-size: 0.8em !important;
    letter-spacing: 0.3px;
}

/* ── Main content block ─────────────────────────────────────────────── */
.stMainBlockContainer {
    padding-top: 0.5rem !important;
}

/* ── Top nav bar styling ─────────────────────────────────────────────── */
.top-nav-bar {
    background: linear-gradient(135deg,
        rgba(15, 15, 25, 0.95) 0%,
        rgba(20, 18, 35, 0.92) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    padding: 8px 0 4px 0;
    margin: -1rem -1rem 12px -1rem;
}

/* ── Tighter tab panel spacing ─────────────────────────────────────── */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 8px !important;
    overflow-anchor: none;
}

/* ── Compact metric card padding ───────────────────────────────────── */
[data-testid="stMetric"] {
    padding: 12px 16px !important;
}

/* ── Compact radio buttons (for time range selector) ───────────────── */
.stRadio > div {
    gap: 0.3rem !important;
}

/* ── Column containers ─────────────────────────────────────────────── */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    transition: all 0.25s ease !important;
}
</style>
""", unsafe_allow_html=True)

# ── Prevent scroll-jump on tab click ─────────────────────────────────────
st.markdown("""
<script>
// Override scrollIntoView on tab panels to prevent Streamlit's auto-scroll
(function() {
    const orig = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function(opts) {
        // Only block scroll if this is inside a tab panel
        if (this.closest && this.closest('[data-baseweb="tab-panel"]')) return;
        if (this.closest && this.closest('.stTabs')) return;
        return orig.call(this, opts);
    };
})();
</script>
""", unsafe_allow_html=True)

# ── Helper functions (must be defined before nav bar references them) ──────

def _refresh_all() -> None:
    from econ_monitor.data.openbb_client import fetch_series
    from econ_monitor.config.indicators import INDICATORS as _IND
    from econ_monitor.data import cache as _cache

    progress = st.sidebar.progress(0, text="Refreshing...")
    stale_ids = [sid for sid in _IND if _cache.is_stale(sid, max_age_hours=1)]

    if not stale_ids:
        st.sidebar.success("All data is fresh!")
        return

    for i, sid in enumerate(stale_ids):
        ind = _IND[sid]
        try:
            df = fetch_series(sid, lookback_years=5)
            if not df.empty:
                _cache.upsert_observations(sid, df)
                _cache.upsert_metadata(sid)
        except Exception as e:
            st.sidebar.warning(f"Failed to refresh {ind.name}: {e}")
        progress.progress((i + 1) / len(stale_ids), text=f"Refreshing {ind.name}...")

    progress.empty()
    st.sidebar.success(f"Refreshed {len(stale_ids)} indicators")
    st.rerun()


def _initial_fetch() -> None:
    from econ_monitor.data.openbb_client import fetch_series, get_series_info
    from econ_monitor.config.indicators import INDICATORS as _IND
    from econ_monitor.data import cache as _cache

    progress = st.sidebar.progress(0, text="Fetching all indicators...")
    total = len(_IND)
    errors = []

    for i, (sid, ind) in enumerate(_IND.items()):
        try:
            df = fetch_series(sid, lookback_years=5)
            if not df.empty:
                _cache.upsert_observations(sid, df)
                try:
                    info = get_series_info(sid)
                    _cache.upsert_metadata(
                        sid,
                        title=info.get("title", ind.name),
                        frequency=info.get("frequency", ind.frequency),
                        units=info.get("units", ind.unit),
                        last_updated=info.get("last_updated", ""),
                    )
                except Exception:
                    _cache.upsert_metadata(sid, title=ind.name, frequency=ind.frequency, units=ind.unit)
            else:
                errors.append(f"{ind.name}: empty response")
        except Exception as e:
            errors.append(f"{ind.name}: {e}")

        progress.progress((i + 1) / total, text=f"Fetching {ind.name}...")

    progress.empty()

    if errors:
        st.sidebar.warning(f"Fetched with {len(errors)} errors")
        with st.sidebar.expander("Errors"):
            for err in errors:
                st.text(err)
    else:
        st.sidebar.success(f"Successfully fetched all {total} indicators!")

    st.rerun()


# ── Horizontal top nav bar ─────────────────────────────────────────────────
from econ_monitor.config.indicators import INDICATORS, CATEGORY_ORDER
from econ_monitor.data import cache

# Build quick-jump data
_label_to_id = {}
_options_list = []
for _cat in CATEGORY_ORDER:
    _cat_inds = [(ind.name, fid) for fid, ind in INDICATORS.items()
                if ind.category == _cat and ind.category != "Regime"]
    if not _cat_inds:
        continue
    for _name, _fid in sorted(_cat_inds, key=lambda x: x[0]):
        _label = f"{_cat} \u203a {_name}"
        _options_list.append(_label)
        _label_to_id[_label] = _fid

st.session_state["_jump_map"] = _label_to_id

def _on_quick_jump():
    pick = st.session_state.get("topbar_quick_jump", "")
    mapping = st.session_state.get("_jump_map", {})
    if pick and pick in mapping:
        st.session_state["detail_indicator"] = mapping[pick]
        st.session_state["_do_jump"] = True
        st.session_state["topbar_quick_jump"] = ""

# Top bar layout: title | nav buttons | quick-jump | actions
st.markdown('<div class="top-nav-bar">', unsafe_allow_html=True)
_nav_col_title, _nav_col_links, _nav_col_jump, _nav_col_actions = st.columns([0.6, 7.5, 1.5, 0.5])

with _nav_col_title:
    st.markdown(
        '<div style="font-size:0.85em;font-weight:800;padding:4px 0;white-space:nowrap">'
        '<span style="background:linear-gradient(135deg,#818cf8,#a78bfa);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
        '📊 Econ</span></div>',
        unsafe_allow_html=True,
    )

with _nav_col_links:
    _page_labels = ["Home", "Detail", "Feed", "Cal", "Guide", "Models", "AI", "Markets", "History"]
    _page_icons = ["📊", "🔍", "📡", "📅", "📖", "🎯", "🤖", "📈", "📜"]
    _page_refs = [_page_overview, _page_detail, _page_feed, _page_calendar, _page_guide, _page_models, _page_ai_brief, _page_markets, _page_timeline]

    _btn_cols = st.columns(9)
    for _i, (_label, _icon, _pref) in enumerate(zip(_page_labels, _page_icons, _page_refs)):
        with _btn_cols[_i]:
            if st.button(_label, key=f"nav_{_i}", icon=_icon,
                        use_container_width=True, type="secondary"):
                st.switch_page(_pref)

with _nav_col_jump:
    st.selectbox(
        "Jump to Indicator",
        options=[""] + _options_list,
        key="topbar_quick_jump",
        placeholder="Search indicators...",
        on_change=_on_quick_jump,
        label_visibility="collapsed",
    )

with _nav_col_actions:
    _act_cols = st.columns(2)
    with _act_cols[0]:
        if st.button("🔄", key="refresh_btn", help="Refresh All Data", use_container_width=True):
            _refresh_all()
    with _act_cols[1]:
        if st.button("📥", key="fetch_btn", help="Initial Data Fetch", use_container_width=True):
            _initial_fetch()

if st.session_state.pop("_do_jump", False):
    st.switch_page(_page_detail)

st.markdown('</div>', unsafe_allow_html=True)

# ── Run ───────────────────────────────────────────────────────────────────
pg.run()
