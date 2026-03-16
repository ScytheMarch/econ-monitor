"""Color constants, design tokens, and styling for the dashboard."""

# Traffic light colors
GREEN = "#22c55e"
YELLOW = "#eab308"
RED = "#ef4444"
GRAY = "#6b7280"
BLUE = "#3b82f6"
DARK_BG = "#0e1117"

# ── Design Tokens ────────────────────────────────────────────────────────

# Text colors
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
TEXT_DIM = "#475569"

# Accent
ACCENT_INDIGO = "#6366f1"
ACCENT_VIOLET = "#8b5cf6"

# Card styling
CARD_BG = "linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015))"
CARD_BORDER = "1px solid rgba(255,255,255,0.08)"
CARD_RADIUS = "12px"
CARD_PADDING = "14px 18px"
CARD_PADDING_LG = "20px 24px"

# Spacing
SPACE_XS = "4px"
SPACE_SM = "8px"
SPACE_MD = "12px"
SPACE_LG = "16px"
SPACE_XL = "24px"


def glass_card(content: str, border_color: str = "rgba(255,255,255,0.08)",
               padding: str = CARD_PADDING) -> str:
    """Wrap HTML content in a standard frosted-glass card div."""
    return (
        f'<div style="background:{CARD_BG};border:1px solid {border_color};'
        f'border-radius:{CARD_RADIUS};padding:{padding};'
        f'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.15)'
        f'">{content}</div>'
    )


def section_header(text: str) -> str:
    """Return styled uppercase section header HTML."""
    return (
        f'<div style="color:{TEXT_MUTED};font-size:0.75em;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:1.5px;'
        f'margin:20px 0 12px 0">{text}</div>'
    )

# Category colors for badges
CATEGORY_COLORS = {
    "Inflation": "#f97316",     # Orange
    "Labor": "#3b82f6",         # Blue
    "Output": "#8b5cf6",        # Purple
    "Consumer": "#06b6d4",      # Cyan
    "Business": "#ec4899",      # Pink
    "Housing": "#84cc16",       # Lime
    "Trade": "#14b8a6",         # Teal
    "Monetary": "#f59e0b",      # Amber
    "Fixed Income": "#6366f1",  # Indigo
    "Market": "#ef4444",        # Red
    "Regime": "#6b7280",        # Gray
}

# Trend direction to traffic light
TREND_COLORS = {
    "improving": GREEN,
    "stable": YELLOW,
    "deteriorating": RED,
}

TREND_ARROWS = {
    "improving": "▲",
    "stable": "▬",
    "deteriorating": "▼",
}


def trend_color(direction: str, higher_is: str) -> str:
    """Get the appropriate color based on trend direction and indicator semantics.

    For 'contractionary' or 'inflationary' indicators, improving (rising) is actually bad.
    """
    if higher_is in ("contractionary", "inflationary"):
        # Flip: rising is bad, falling is good
        flipped = {
            "improving": "deteriorating",
            "deteriorating": "improving",
            "stable": "stable",
        }
        direction = flipped.get(direction, direction)

    return TREND_COLORS.get(direction, GRAY)


def trend_arrow(direction: str, higher_is: str) -> str:
    """Get the appropriate arrow with semantic flipping."""
    if higher_is in ("contractionary", "inflationary"):
        flipped = {
            "improving": "deteriorating",
            "deteriorating": "improving",
            "stable": "stable",
        }
        direction = flipped.get(direction, direction)

    return TREND_ARROWS.get(direction, "▬")


def format_value(value: float | None, unit: str, transform: str) -> str:
    """Format a value for display based on its unit and transform."""
    if value is None:
        return "N/A"
    if transform in ("yoy_pct", "mom_pct", "annualized"):
        return f"{value:+.1f}%"
    if unit == "percent":
        return f"{value:.1f}%"
    if unit == "index":
        return f"{value:.1f}"
    if unit in ("thousands", "millions", "billions"):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:.1f}"
    if unit == "ratio":
        return f"{value:.2f}"
    return f"{value:.2f}"
