"""
Budget Reasoner — LLM reasoning layer over the mechanical quadrant math.

The 2x2 quadrant engine (budget_agent.py) is deterministic arithmetic. This module
feeds that math — plus the context it's blind to (CAC trend vs one-day blip,
strategic intent, creative age) — to Claude, which writes the actual reasoned
recommendation. Math becomes an input, not the verdict.

Reads ANTHROPIC_API_KEY from Streamlit secrets or env. Degrades gracefully:
if no key, raises NoAPIKey so the view can fall back to the mechanical table.
"""

from __future__ import annotations

import os
import json
from typing import Optional

MODEL = "claude-opus-4-6"


class NoAPIKey(Exception):
    pass


def _api_key() -> str:
    # Streamlit secrets first, then env, then .env file directly.
    try:
        import streamlit as st
        k = (st.secrets.get("ANTHROPIC_API_KEY", "") or "").strip()
        if k:
            return k
    except Exception:
        pass
    k = (os.getenv("ANTHROPIC_API_KEY", "") or "").strip()
    if k:
        return k
    # Fallback: read .env directly. A pre-existing empty env var blocks
    # load_dotenv()'s default (override=False), so parse the file ourselves.
    try:
        from dotenv import dotenv_values
        for path in (os.path.join(os.path.dirname(__file__), "..", ".env"), ".env"):
            vals = dotenv_values(path)
            k = (vals.get("ANTHROPIC_API_KEY", "") or "").strip()
            if k:
                return k
    except Exception:
        pass
    return ""


SYSTEM = """You are a senior performance-marketing strategist reviewing daily budget \
decisions for an ed-tech app's Meta/Google campaigns.

You are given mechanical 2x2 quadrant math (CAC vs target, uninstall vs target) for each \
ad unit. Treat that math as ONE input, not the verdict. A calculator can sort units into \
boxes; your job is the judgment it cannot do. Specifically weigh:

- TREND vs ONE-DAY BLIP: a unit that just spiked for a single day is different from one \
that has been degrading across L3D→L7D→L14D. Do not recommend cutting on a blip; do not \
wait on a sustained decline. The biggest past mistake was scaling spend INTO a unit \
exactly as it began saturating.
- STRATEGIC INTENT: retention/retargeting/UAC audiences behave differently from cold \
acquisition. A higher CAC on a warm/quality (low-uninstall) audience may be worth holding. \
Language-expansion or new-market bets may be deliberately subsidized.
- CREATIVE AGE / LIFECYCLE: a brand-new creative (few active days) needs time before \
judging; an old one at high CAC is genuinely fatigued and the 'refresh creative' call is real.

HARD CONSTRAINT: uninstall rate must NOT rise. Cheap-CAC, high-uninstall units are a trap — \
never recommend feeding them. Total spend should stay roughly flat (reallocate, don't slash).

For each unit give a concise, decision-ready verdict (SCALE / HOLD / TRIM / CUT / WATCH / \
REFRESH CREATIVE) and a one-to-two sentence reason grounded in the trend/intent/age signals — \
not just the quadrant. Then write a short overall narrative: the 2-3 moves that matter today \
and the honest caveat about what budget has no efficient home."""


def _build_prompt(group: str, level: str, targets: dict,
                  summary: dict, records: list[dict]) -> str:
    tgt = f"CAC ≤ ₹{targets['cac']:,.0f}, Uninstall ≤ {targets['unin']:.0f}%"
    head = (
        f"Group: {group}  |  Level: {level}  |  Targets: {tgt}\n"
        f"Blended CAC ₹{summary['blended_cac']:,.0f} · Uninstall {summary['blended_unin']:.1f}% · "
        f"Daily spend ₹{summary['total_daily']:,.0f}\n"
        f"Mechanical math: freed ₹{summary['freed']:,.0f}, "
        f"safely-redeployable ₹{summary['redeployable']:,.0f}, "
        f"stranded ₹{summary['stranded']:,.0f}\n\n"
        f"Units (top by spend) — each with quadrant + the signals the math ignores:\n"
    )
    lines = []
    for r in records:
        lines.append(
            f"- {r['unit']} [{r['app']}] q={r['quadrant']} ₹{r['daily_spend']:,}/day | "
            f"CAC L3 ₹{r['cac_l3']} / L7 ₹{r['cac_l7']} / L14 ₹{r['cac_l14']} ({r['cac_trend']}) | "
            f"unin L3 {r['unin_l3']}% / L7 {r['unin_l7']}% | "
            f"age {r['active_days']}d since {r['first_seen']} | intent: {r['intent']}"
        )
    return head + "\n".join(lines)


# structured output schema
_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string"},
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "unit": {"type": "string"},
                    "verdict": {"type": "string",
                                "enum": ["SCALE", "HOLD", "TRIM", "CUT", "WATCH",
                                         "REFRESH CREATIVE"]},
                    "reason": {"type": "string"},
                },
                "required": ["unit", "verdict", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["narrative", "units"],
    "additionalProperties": False,
}


def reason(group: str, level: str, targets: dict,
           summary: dict, records: list[dict]) -> dict:
    """
    Returns {"narrative": str, "units": [{unit, verdict, reason}, ...]}.
    Raises NoAPIKey if no key configured.
    """
    key = _api_key()
    if not key:
        raise NoAPIKey("ANTHROPIC_API_KEY not set in secrets or env")
    if not records:
        return {"narrative": "No units with meaningful spend to reason about.", "units": []}

    import anthropic
    client = anthropic.Anthropic(api_key=key)

    prompt = _build_prompt(group, level, targets, summary, records)
    # Stream with a generous cap: schema-constrained JSON over ~40 units plus
    # adaptive thinking can exceed 8K and silently truncate (→ invalid JSON).
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        # effort=low keeps adaptive thinking shallow — this is a daily snap
        # judgment over pre-computed signals, not a deep research task. Big
        # latency win for an interactive tab.
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA},
                       "effort": "low"},
    ) as stream:
        resp = stream.get_final_message()

    text = next((b.text for b in resp.content if b.type == "text"), "{}")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"narrative": text, "units": []}
