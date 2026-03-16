"""AI-powered economic analysis using Google Gemini.

Generates market briefs, indicator change explanations, and deep model interpretations.
Uses Gemini free tier (15 RPM, 1M tokens/day).
Gracefully degrades when API key is not configured (all functions return None).
"""

from __future__ import annotations

import hashlib
import json

from econ_monitor.config.settings import settings


def _get_model(max_tokens: int = 1500):
    """Lazy-initialize Gemini model. Returns None if no API key."""
    try:
        api_key = getattr(settings, "gemini_api_key", "") or ""
        if not api_key:
            return None
        from google import genai
        client = genai.Client(api_key=api_key)
        return client, max_tokens
    except Exception:
        return None


def is_ai_available() -> bool:
    """Check if AI analysis is available (API key configured + SDK installed)."""
    try:
        return _get_model() is not None
    except Exception:
        return False


# ── Context Builders ─────────────────────────────────────────────────────────

def _build_indicator_context() -> str:
    """Assemble current indicator values into a structured text block."""
    from econ_monitor.config.indicators import INDICATORS, CATEGORY_ORDER
    from econ_monitor.data import cache
    from econ_monitor.analytics.transforms import apply_transform
    from econ_monitor.ui.styles import format_value

    lines = []
    for cat in CATEGORY_ORDER:
        cat_inds = [(fid, ind) for fid, ind in INDICATORS.items() if ind.category == cat]
        if not cat_inds:
            continue
        lines.append(f"\n## {cat}")
        for fid, ind in sorted(cat_inds, key=lambda x: x[1].name):
            date_str, raw_val = cache.get_latest(fid)
            if raw_val is None:
                continue
            df = cache.get_observations(fid)
            if df.empty or len(df) < 2:
                continue
            transformed = apply_transform(df["value"], ind.transform, ind.frequency).dropna()
            if transformed.empty:
                continue
            latest = float(transformed.iloc[-1])
            disp = format_value(latest, ind.unit, ind.transform)
            lines.append(
                f"- {ind.name} ({fid}): {disp} as of {date_str} "
                f"[{ind.transform}, higher_is={ind.higher_is}]"
            )
    return "\n".join(lines)


def _build_regime_context() -> str:
    """Assemble regime score and signals into text."""
    from econ_monitor.analytics.regime import compute_regime_score

    regime = compute_regime_score()
    lines = [
        f"Regime Score: {regime['score']:.3f} ({regime['label']})",
    ]
    for sig in regime.get("signals", []):
        lines.append(
            f"  - {sig['name']}: score={sig['score']:+.2f}, {sig.get('interpretation', '')}"
        )
    return "\n".join(lines)


def _build_model_context() -> str:
    """Assemble probability model outputs into text."""
    from econ_monitor.analytics.probability_models import (
        compute_recession_probability,
        compute_leading_index,
        compute_transition_probabilities,
    )

    rec = compute_recession_probability()
    lead = compute_leading_index()
    trans = compute_transition_probabilities()

    return (
        f"Recession Probability: 3m={rec['prob_3m']:.1f}%, 6m={rec['prob_6m']:.1f}%, "
        f"12m={rec['prob_12m']:.1f}% — {rec['interpretation']}\n"
        f"Leading Index: {lead['value']:+.2f}, trend={lead['trend']} — {lead['interpretation']}\n"
        f"Regime: {trans['current_regime']}, stability={trans['stability']:.0f}%, "
        f"momentum={trans['momentum']:+.4f} — {trans['forecast']}"
    )


def _build_activity_context(limit: int = 15) -> str:
    """Recent activity feed items."""
    from econ_monitor.data import cache

    feed = cache.get_activity_feed(limit=limit)
    if not feed:
        return "No recent activity."
    lines = []
    for item in feed:
        lines.append(
            f"- [{item.get('timestamp', '')[:16]}] {item.get('series_id', '')}: "
            f"{item.get('message', '')}"
        )
    return "\n".join(lines)


def build_full_context() -> str:
    """Assemble the complete context for the AI."""
    return (
        "# Current Economic Data\n"
        f"{_build_indicator_context()}\n\n"
        "# Regime Analysis\n"
        f"{_build_regime_context()}\n\n"
        "# Probability Models\n"
        f"{_build_model_context()}\n\n"
        "# Recent Data Changes\n"
        f"{_build_activity_context()}\n"
    )


def context_hash(context: str) -> str:
    """Short hash of context for cache keying."""
    return hashlib.md5(context.encode()).hexdigest()[:12]


# ── Public API ───────────────────────────────────────────────────────────────

def generate_market_brief(ctx_hash: str, context: str) -> dict[str, str] | None:
    """Generate a daily market brief from Gemini.

    Returns dict with keys: headline, summary, risks, opportunities, watchlist
    or None if unavailable.
    """
    result = _get_model(max_tokens=4000)
    if result is None:
        return None

    client, max_tokens = result

    system_prompt = (
        "You are a senior macro strategist writing a daily economic brief. "
        "You have access to current U.S. economic indicator data, regime analysis, "
        "and probability models. Write concise, opinionated analysis. "
        "Use specific numbers from the data. Be direct about risks and opportunities.\n\n"
        "Return a JSON object with exactly these keys:\n"
        "- headline: 1 punchy sentence (string)\n"
        "- summary: 2-3 short paragraphs of analysis (string, use \\n\\n between paragraphs)\n"
        "- risks: 3-5 key risks, each on a new line starting with - (string)\n"
        "- opportunities: 3-5 opportunities, each on a new line starting with - (string)\n"
        "- watchlist: 3-5 indicators to watch and why, each on a new line starting with - (string)\n\n"
        "Keep each section concise. Total response under 800 words."
    )

    prompt = f"{system_prompt}\n\nHere is today's data:\n\n{context}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
                "response_mime_type": "application/json",
            },
        )

        text = response.text
        # Handle markdown code fences if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        # Extract JSON object if there's extra text around it
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            text = match.group(0)
        return json.loads(text.strip())
    except (json.JSONDecodeError, IndexError):
        return {"headline": "Analysis generated", "summary": text,
                "risks": "", "opportunities": "", "watchlist": ""}
    except Exception as e:
        return {"headline": "Error generating analysis", "summary": str(e),
                "risks": "", "opportunities": "", "watchlist": ""}


def analyze_model_output(
    ctx_hash: str,
    model_name: str,
    model_data_summary: str,
    full_context: str,
) -> str | None:
    """Generate deep interpretation of a probability model's output.

    Returns a 2-4 paragraph analysis string, or None if unavailable.
    """
    result = _get_model(max_tokens=800)
    if result is None:
        return None

    client, max_tokens = result

    system_prompt = (
        "You are a senior macro strategist. Provide a deep, opinionated interpretation "
        "of this economic model's output. Reference specific data points. "
        "Identify what's driving the result and what would change the outlook. "
        "Be concise but substantive — 2-4 paragraphs. No markdown headers. No JSON."
    )

    prompt = (
        f"{system_prompt}\n\n"
        f"Model: {model_name}\n"
        f"Output: {model_data_summary}\n\n"
        f"Full economic context:\n{full_context}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
            },
        )
        return response.text
    except Exception:
        return None
