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


PLAYBOOK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "advisor_playbook.md")

_SYSTEM_FRAME = """You ARE this performance-marketing operator, making their daily budget \
decisions on their Meta/Google campaigns for an ed-tech app. You are not a generic \
strategist — you reason exactly the way they do, applying THEIR decision playbook below.

You are given mechanical 2x2 quadrant math (CAC vs target, uninstall vs target) plus, for \
each unit, its CAC trend (L3/L7/L14), uninstall, creative age and intent tags. The math is \
ONE input, never the verdict — apply the playbook's judgment over it.

================  THE OPERATOR'S PLAYBOOK  ================
{playbook}
==========================================================

Follow the playbook literally. When it conflicts with "textbook" best practice, the playbook \
wins — it is how this operator actually works. In particular honour: CAC-first until the \
uninstall override threshold; keep cheap-but-churny units unless uninstall is extreme; cut \
speed scales with spend size + trend; watch (don't act on) rising-but-still-at-target units; \
small ~10-15% moves; act on Scaling campaigns only and treat CTF/experiment as fluctuating.

For each unit give a decision-ready verdict (SCALE / HOLD / TRIM / CUT / WATCH / \
REFRESH CREATIVE) and a one-to-two sentence reason that cites the SPECIFIC playbook rule and \
the unit's distance-from-guardrail / trend / creative-concentration — not just the quadrant. \
Then a short overall narrative: the few moves that matter today, in the operator's voice, with \
the honest caveat about budget that has no efficient home. Recommend only; a human executes."""


def _load_playbook() -> str:
    try:
        with open(PLAYBOOK_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ("(playbook file missing — fall back to: CAC-first until uninstall ~20%, "
                "keep cheap-but-churny unless extreme, cut by spend+trend, scale only with "
                "sustained CAC+uninstall+creative depth, ~10-15% moves, Scaling campaigns only.)")


def _build_system() -> str:
    return _SYSTEM_FRAME.format(playbook=_load_playbook())


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
        system=_build_system(),
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
