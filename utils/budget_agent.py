"""
Budget Recommendation Agent — uninstall-constrained daily budget decisions.

Recommend-only. Operates at campaign / ad_set / ad_creative level on L3D data.

Decision framework (2x2 quadrant vs targets CAC ≤ tgt, Unin ≤ tgt):

  🟢 STAR    CAC✓ Unin✓  → SCALE  (+, capped at +50%, funded from freed pool)
  🟡 CHURNY  CAC✓ Unin✗  → TRIM   (−20%; cheap but every ₹ buys an uninstall)
  🟠 PRICEY  CAC✗ Unin✓  → HOLD + flag creative refresh (don't cut quality)
  🔴 DOG     CAC✗ Unin✗  → CUT    (−30% to −40%, severity-scaled)
  ⚪ NO_DATA  <3 orders   → FLAG

Reallocation: freed = Σ cuts+trims; redeployable = min(freed, Σ STAR +50% headroom);
stranded = freed − redeployable (needs creative refresh / new audiences).

CTF campaigns (named *experiment*) are excluded from budget decisions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

from utils.allocator import load_campaign_config

EXCLUDE_NAME_PATTERN = "experiment"   # CTF creative-testing campaigns

SCALE_CAP      = 0.50    # STAR ad sets can grow at most +50%
DOG_CUT_MIN    = 0.30    # mildest DOG cut
DOG_CUT_MAX    = 0.40    # worst DOG cut
CHURNY_TRIM    = 0.20    # flat trim on cheap-but-churny
MIN_ORDERS     = 3       # below this → NO_DATA

QUADRANT_META = {
    "STAR":    ("🟢", "SCALE"),
    "CHURNY":  ("🟡", "TRIM"),
    "PRICEY":  ("🟠", "HOLD · refresh creative"),
    "DOG":     ("🔴", "CUT"),
    "NO_DATA": ("⚪", "FLAG"),
}

LEVEL_COL = {"campaign": "campaign", "ad_set": "ad_set", "ad_creative": "ad_creative"}


# ── metrics builder ────────────────────────────────────────────────────────────

def build_level_metrics(df: pd.DataFrame, level: str = "ad_set",
                        days: int = 3, exclude_ctf: bool = True) -> pd.DataFrame:
    """
    L{days}D aggregate at the chosen level. Carries app + campaign for context.
    Returns per-unit: unit, campaign, app, spend, orders, unin, cancel,
    daily_spend, cac, unin_rate, cancel_rate, days_running.
    """
    if df.empty or level not in df.columns:
        return pd.DataFrame()

    d = df.copy()
    if exclude_ctf:
        d = d[~d["campaign"].str.contains(EXCLUDE_NAME_PATTERN, case=False, na=False)]
    if d.empty:
        return pd.DataFrame()

    dates = sorted(d["date_tz"].unique())
    cutoff = dates[-days] if len(dates) >= days else dates[0]
    sub = d[d["date_tz"] >= cutoff]
    n_days = max(1, len({x for x in dates if x >= cutoff}))

    # context columns to carry (most common value per unit)
    ctx = []
    if level != "campaign" and "campaign" in sub.columns:
        ctx.append("campaign")
    if "_app" in sub.columns:
        ctx.append("_app")

    agg_spec = dict(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
    )
    if "p0_cancel_users" in sub.columns:
        agg_spec["cancel"] = ("p0_cancel_users", "sum")

    g = sub.groupby(level, as_index=False).agg(**agg_spec)

    if ctx:
        meta = (sub.groupby(level)[ctx]
                   .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
                   .reset_index())
        g = g.merge(meta, on=level, how="left")

    if "cancel" not in g.columns:
        g["cancel"] = 0.0

    g = g.rename(columns={level: "unit", "_app": "app"})
    if "campaign" not in g.columns:
        g["campaign"] = g["unit"]
    if "app" not in g.columns:
        g["app"] = ""

    g["daily_spend"]  = g["spend"] / n_days
    g["cac"]          = np.where(g["orders"] > 0, g["spend"]  / g["orders"],       np.nan)
    g["unin_rate"]    = np.where(g["orders"] > 0, g["unin"]   / g["orders"] * 100, np.nan)
    g["cancel_rate"]  = np.where(g["orders"] > 0, g["cancel"] / g["orders"] * 100, np.nan)

    dr = (sub.groupby(level)["date_tz"].nunique()
             .reset_index().rename(columns={level: "unit", "date_tz": "days_running"}))
    g = g.merge(dr, on="unit", how="left")
    return g


# ── classification ──────────────────────────────────────────────────────────────

def classify(cac: float, unin: float, orders: float,
             cac_tgt: float, unin_tgt: float) -> str:
    if pd.isna(cac) or orders < MIN_ORDERS:
        return "NO_DATA"
    cac_ok  = cac  <= cac_tgt
    unin_ok = (not pd.isna(unin)) and unin <= unin_tgt
    if cac_ok and unin_ok:   return "STAR"
    if cac_ok and not unin_ok: return "CHURNY"
    if (not cac_ok) and unin_ok: return "PRICEY"
    return "DOG"


# ── main recommender ──────────────────────────────────────────────────────────

def recommend(df: pd.DataFrame, level: str = "ad_set",
              cac_tgt: float = 500, unin_tgt: float = 15,
              min_daily: float = 1000, days: int = 3) -> dict:
    """
    Returns dict with: actions (DataFrame), summary (dict),
    creative_refresh (DataFrame), quadrant (DataFrame).
    """
    m = build_level_metrics(df, level=level, days=days)
    empty = {"actions": pd.DataFrame(), "creative_refresh": pd.DataFrame(),
             "quadrant": pd.DataFrame(), "summary": {}}
    if m.empty:
        return empty

    m = m[m["daily_spend"] >= min_daily].copy()
    if m.empty:
        return empty

    m["quadrant"] = m.apply(
        lambda r: classify(r["cac"], r["unin_rate"], r["orders"], cac_tgt, unin_tgt), axis=1)

    # ── budget deltas ──────────────────────────────────────────────────────────
    def _delta(r):
        q = r["quadrant"]; d = r["daily_spend"]
        if q == "DOG":
            # severity by CAC overshoot, scaled into [CUT_MIN, CUT_MAX]
            sev = np.clip((r["cac"] / cac_tgt - 1.0), 0, 1)
            frac = DOG_CUT_MIN + (DOG_CUT_MAX - DOG_CUT_MIN) * sev
            return -round(d * frac, -2)
        if q == "CHURNY":
            return -round(d * CHURNY_TRIM, -2)
        return 0.0   # PRICEY / STAR(initial) / NO_DATA

    m["delta_rupees"] = m.apply(_delta, axis=1)

    freed = -m["delta_rupees"].sum()   # positive total freed

    # ── redeploy freed budget into STAR pool, capped at +SCALE_CAP each ─────────
    stars = m[m["quadrant"] == "STAR"].copy()
    star_headroom = (stars["daily_spend"] * SCALE_CAP).sum()
    target_redeploy = min(freed, star_headroom)
    redeployable = 0.0

    if not stars.empty and target_redeploy > 0 and star_headroom > 0:
        # distribute proportional to current spend, capped at +50% each.
        # floor to ₹100 so a rounded gain can never exceed the +50% cap.
        share = stars["daily_spend"] / stars["daily_spend"].sum()
        cap   = stars["daily_spend"] * SCALE_CAP
        gain  = np.minimum(share * target_redeploy, cap)
        gain  = (np.floor(gain / 100) * 100).clip(lower=0)
        m.loc[stars.index, "delta_rupees"] = gain
        redeployable = float(gain.sum())

    stranded = max(0.0, freed - redeployable)

    m["new_daily"] = (m["daily_spend"] + m["delta_rupees"]).clip(lower=0)

    # ── reason text ─────────────────────────────────────────────────────────────
    def _reason(r):
        q = r["quadrant"]
        cac_s  = f"₹{r['cac']:,.0f}" if pd.notna(r["cac"]) else "—"
        un_s   = f"{r['unin_rate']:.0f}%" if pd.notna(r["unin_rate"]) else "—"
        if q == "DOG":
            return f"CAC {cac_s} + Unin {un_s} both over target — cut"
        if q == "CHURNY":
            return f"Cheap ({cac_s}) but Unin {un_s} over target — trim, don't feed"
        if q == "PRICEY":
            return f"CAC {cac_s} high but Unin {un_s} clean — refresh creative, hold budget"
        if q == "STAR":
            return f"CAC {cac_s} + Unin {un_s} both clean — scale"
        return f"Only {int(r['orders'])} orders L3D — insufficient data"
    m["reason"] = m.apply(_reason, axis=1)

    icon = m["quadrant"].map(lambda q: QUADRANT_META[q][0])
    m["action"] = m["quadrant"].map(lambda q: QUADRANT_META[q][1])
    m["badge"]  = icon + " " + m["quadrant"]

    actions = m.sort_values(
        ["delta_rupees", "daily_spend"],
        key=lambda c: c.abs() if c.name == "delta_rupees" else c,
        ascending=[False, False],
    ).reset_index(drop=True)

    # ── summary ─────────────────────────────────────────────────────────────────
    tot_spend  = m["spend"].sum()
    tot_orders = m["orders"].sum()
    tot_unin   = m["unin"].sum()
    blended_cac  = tot_spend / tot_orders if tot_orders > 0 else np.nan
    blended_unin = tot_unin / tot_orders * 100 if tot_orders > 0 else np.nan

    summary = dict(
        blended_cac=blended_cac, blended_unin=blended_unin,
        total_daily=m["daily_spend"].sum(),
        freed=freed, redeployable=redeployable, stranded=stranded,
        n_units=len(m),
    )

    # ── creative-refresh priority list (PRICEY by spend) ────────────────────────
    cr = (m[m["quadrant"] == "PRICEY"]
          .sort_values("daily_spend", ascending=False)
          [["app", "unit", "campaign", "cac", "unin_rate", "daily_spend"]]
          .reset_index(drop=True))

    return {"actions": actions, "summary": summary,
            "creative_refresh": cr, "quadrant": quadrant_split(m, cac_tgt)}


def _window_cac_unin(df: pd.DataFrame, level: str, days: int) -> pd.DataFrame:
    """Per-unit CAC + unin over the last `days` days (helper for trend signals)."""
    dates = sorted(df["date_tz"].unique())
    cutoff = dates[-days] if len(dates) >= days else dates[0]
    sub = df[df["date_tz"] >= cutoff]
    g = sub.groupby(level, as_index=False).agg(
        spend=("total_cost", "sum"), orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"))
    g["cac"]  = np.where(g["orders"] > 0, g["spend"] / g["orders"], np.nan)
    g["unin_rate"] = np.where(g["orders"] > 0, g["unin"] / g["orders"] * 100, np.nan)
    return g.set_index(level)[["cac", "unin_rate"]]


def _intent_tags(name: str) -> str:
    """Infer strategic intent signals from a campaign/ad-set/creative name."""
    n = str(name).lower()
    tags = []
    for lang in ("tamil", "telugu", "kannada", "malayalam"):
        if lang in n:
            tags.append(lang); break
    if "retention" in n:                       tags.append("retention")
    if n.startswith("uac") or "_uac" in n or "uac_" in n: tags.append("uac/google")
    if "retargeting" in n or "pvs" in n or "viewed" in n or "_view" in n:
        tags.append("retargeting")
    if "acquisition" in n or "acq" in n:       tags.append("acquisition")
    if "low churn" in n or "low_churn" in n:   tags.append("low-churn-audience")
    if "decoy" in n:                           tags.append("decoy")
    return ", ".join(tags) if tags else "—"


def build_reasoning_context(df: pd.DataFrame, level: str = "ad_set",
                            cac_tgt: float = 500, unin_tgt: float = 15,
                            min_daily: float = 1000, top_n: int = 40) -> list[dict]:
    """
    Enrich the top-N units (by spend) with the signals the LLM needs:
    CAC trend (L3/L7/L14), uninstall trend, creative/campaign age, intent tags.
    Returns a list of compact dicts for the reasoner prompt.
    """
    base = build_level_metrics(df, level=level, days=3)
    if base.empty:
        return []
    base = base[base["daily_spend"] >= min_daily].copy()
    if base.empty:
        return []
    base["quadrant"] = base.apply(
        lambda r: classify(r["cac"], r["unin_rate"], r["orders"], cac_tgt, unin_tgt), axis=1)

    d = df[~df["campaign"].str.contains(EXCLUDE_NAME_PATTERN, case=False, na=False)]
    l7  = _window_cac_unin(d, level, 7)
    l14 = _window_cac_unin(d, level, 14)

    # age / lifecycle across the full available window
    age = (d.groupby(level)["date_tz"]
             .agg(first_seen="min", last_seen="max", active_days="nunique"))

    base = base.sort_values("daily_spend", ascending=False).head(top_n)

    recs = []
    for _, r in base.iterrows():
        u = r["unit"]
        cac3 = r["cac"]
        cac7 = l7["cac"].get(u, np.nan)
        cac14 = l14["cac"].get(u, np.nan)
        un3 = r["unin_rate"]
        un7 = l7["unin_rate"].get(u, np.nan)
        # trend: L3 vs L7
        if pd.notna(cac3) and pd.notna(cac7) and cac7 > 0:
            chg = (cac3 - cac7) / cac7 * 100
            cac_trend = ("rising" if chg > 12 else "falling" if chg < -12 else "stable")
        else:
            cac_trend = "n/a"
        a = age.loc[u] if u in age.index else None
        recs.append(dict(
            unit=str(u)[:60],
            app=r.get("app", ""),
            campaign=str(r.get("campaign", ""))[:50],
            quadrant=r["quadrant"],
            daily_spend=round(r["daily_spend"]),
            cac_l3=None if pd.isna(cac3) else round(cac3),
            cac_l7=None if pd.isna(cac7) else round(cac7),
            cac_l14=None if pd.isna(cac14) else round(cac14),
            cac_trend=cac_trend,
            unin_l3=None if pd.isna(un3) else round(un3, 1),
            unin_l7=None if pd.isna(un7) else round(un7, 1),
            active_days=int(a["active_days"]) if a is not None else None,
            first_seen=str(a["first_seen"]) if a is not None else None,
            intent=_intent_tags(u) if level != "campaign" else _intent_tags(r.get("campaign", u)),
        ))
    return recs


def quadrant_split(m: pd.DataFrame, cac_tgt: float = 500) -> pd.DataFrame:
    """4-row spend distribution + blended CAC per quadrant."""
    if m.empty:
        return pd.DataFrame()
    tot = m["daily_spend"].sum()
    rows = []
    for q in ["STAR", "CHURNY", "PRICEY", "DOG", "NO_DATA"]:
        b = m[m["quadrant"] == q]
        if b.empty:
            continue
        o = b["orders"].sum()
        rows.append(dict(
            quadrant=f"{QUADRANT_META[q][0]} {q}",
            daily_spend=b["daily_spend"].sum(),
            pct=b["daily_spend"].sum() / tot * 100 if tot else 0,
            cac=b["spend"].sum() / o if o > 0 else np.nan,
            unin=b["unin"].sum() / o * 100 if o > 0 else np.nan,
            n=len(b),
        ))
    return pd.DataFrame(rows)
