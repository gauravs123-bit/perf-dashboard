"""
Budget allocator — reads campaign_config.csv + targets.csv,
scores Scaling/Experiment campaigns against monthly CAC+unin targets,
and returns a budget split for a given daily ₹ envelope.
"""

import os
import pandas as pd
import numpy as np

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

CAMPAIGN_CONFIG_PATH = os.path.join(_DATA_DIR, "campaign_config.csv")
TARGETS_PATH         = os.path.join(_DATA_DIR, "targets.csv")

TTMK_APPS = {"Arivu", "Vidhya", "Kali", "Nerchuko"}


# ── loaders ──────────────────────────────────────────────────────────────────

def load_campaign_config() -> pd.DataFrame:
    """Load campaign_config.csv, skip comment lines."""
    if not os.path.exists(CAMPAIGN_CONFIG_PATH):
        return pd.DataFrame(columns=["campaign_name", "type", "owner", "app"])
    rows = []
    with open(CAMPAIGN_CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(line)
    if not rows:
        return pd.DataFrame(columns=["campaign_name", "type", "owner", "app"])
    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(rows)),
                     names=["campaign_name", "type", "owner", "app"],
                     header=None)
    df["type"] = df["type"].str.strip()
    df["campaign_name"] = df["campaign_name"].str.strip()
    return df


def load_targets() -> dict:
    """Returns {group: {cac_target, unin_target, ctf_daily_cap, experiment_daily_cap}}"""
    if not os.path.exists(TARGETS_PATH):
        return {"TTMK": {"cac_target": 500, "unin_target": 15.0,
                         "ctf_daily_cap": 5000, "experiment_daily_cap": 3000}}
    df = pd.read_csv(TARGETS_PATH)
    return {r["group"]: r.to_dict() for _, r in df.iterrows()}


# ── L3D aggregation ───────────────────────────────────────────────────────────

def _l3d_agg(df: pd.DataFrame) -> pd.DataFrame:
    """3-day rolling aggregate per campaign."""
    if df.empty or "campaign" not in df.columns:
        return pd.DataFrame()
    dates = sorted(df["date_tz"].unique())
    cutoff = dates[-3] if len(dates) >= 3 else dates[0]
    sub = df[df["date_tz"] >= cutoff]
    agg_spec = dict(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
    )
    if "p0_cancel_users" in sub.columns:
        agg_spec["cancel"] = ("p0_cancel_users", "sum")
    g = sub.groupby("campaign", as_index=False).agg(**agg_spec)
    g["cac"]       = np.where(g["orders"] > 0, g["spend"]  / g["orders"],       np.nan)
    g["unin_rate"] = np.where(g["orders"] > 0, g["unin"]   / g["orders"] * 100, np.nan)
    if "cancel" in g.columns:
        g["cancel_rate"] = np.where(g["orders"] > 0, g["cancel"] / g["orders"] * 100, np.nan)
    # days running (to gauge how long experiment has been live)
    days_running = (sub.groupby("campaign")["date_tz"]
                      .nunique()
                      .reset_index()
                      .rename(columns={"date_tz": "days_in_window"}))
    g = g.merge(days_running, on="campaign", how="left")
    return g


# ── main allocator ────────────────────────────────────────────────────────────

def allocate(df_combined: pd.DataFrame, group: str, daily_envelope: float) -> dict:
    """
    df_combined : concat of all TTMK (or Seekho) app dfs
    group       : "TTMK" or "Seekho"
    daily_envelope : total ₹ to allocate today

    Returns:
        {
          "scaling":    DataFrame — campaign, l3d_cac, l3d_unin, efficiency_score,
                                    suggested_budget, status, reason
          "experiment": DataFrame — campaign, days_running, l3d_cac, l3d_unin,
                                    l3d_spend, verdict, reason
          "ctf":        DataFrame — campaign, l3d_spend, note
          "untagged":   list[str]  — campaigns with spend but no config entry
          "envelope_used": float
          "targets":    dict
        }
    """
    config  = load_campaign_config()
    targets = load_targets()
    tgt     = targets.get(group, targets.get("TTMK"))
    cac_tgt  = float(tgt["cac_target"])
    unin_tgt = float(tgt["unin_target"])
    ctf_cap  = float(tgt.get("ctf_daily_cap", 5000))
    exp_cap  = float(tgt.get("experiment_daily_cap", 3000))

    l3d = _l3d_agg(df_combined)
    if l3d.empty:
        return {"scaling": pd.DataFrame(), "experiment": pd.DataFrame(),
                "ctf": pd.DataFrame(), "untagged": [], "envelope_used": 0, "targets": tgt}

    # map campaign → type
    cfg_map = config.set_index("campaign_name")["type"].to_dict() if not config.empty else {}

    # detect untagged campaigns with meaningful spend
    active = set(l3d[l3d["spend"] > 0]["campaign"].tolist())
    untagged = [c for c in active if c not in cfg_map]

    # ── Scaling ──────────────────────────────────────────────────────────────
    scaling_camps = l3d[l3d["campaign"].map(cfg_map) == "Scaling"].copy()

    if not scaling_camps.empty:
        # efficiency score: inverse of (cac_ratio × unin_ratio), higher = better
        scaling_camps["cac_ratio"]  = scaling_camps["cac"]       / cac_tgt
        scaling_camps["unin_ratio"] = scaling_camps["unin_rate"] / unin_tgt

        def _status(row):
            if pd.isna(row["cac"]) or row["orders"] < 3:
                return "INSUFFICIENT_DATA", "Less than 3 orders in L3D"
            if row["cac_ratio"] > 1.0 and row["unin_ratio"] > 1.0:
                return "DEMOTE", f"CAC ₹{row['cac']:,.0f} ({row['cac_ratio']:.1f}x) + Unin {row['unin_rate']:.1f}% ({row['unin_ratio']:.1f}x) — both above target"
            if row["cac_ratio"] > 1.2:
                return "DEMOTE", f"CAC ₹{row['cac']:,.0f} ({row['cac_ratio']:.1f}x target) — too high"
            if row["unin_ratio"] > 1.5:
                return "DEMOTE", f"Unin {row['unin_rate']:.1f}% ({row['unin_ratio']:.1f}x target) — high churn"
            if row["cac_ratio"] <= 0.85 and row["unin_ratio"] <= 0.85:
                return "SCALE_UP", f"CAC ₹{row['cac']:,.0f} ({row['cac_ratio']:.1f}x) — efficient, low churn"
            return "MAINTAIN", f"CAC ₹{row['cac']:,.0f} ({row['cac_ratio']:.1f}x) — within target"

        scaling_camps[["status", "reason"]] = scaling_camps.apply(
            lambda r: pd.Series(_status(r)), axis=1)

        # only eligible campaigns (not DEMOTE/INSUFFICIENT) get budget
        eligible = scaling_camps[scaling_camps["status"].isin(["SCALE_UP", "MAINTAIN"])].copy()

        if not eligible.empty:
            # efficiency score: lower cac_ratio + lower unin_ratio = better
            # score = 1 / (cac_ratio * unin_ratio), normalized
            eligible["eff_score"] = 1.0 / (
                eligible["cac_ratio"].clip(lower=0.1) *
                eligible["unin_ratio"].clip(lower=0.1)
            )
            # SCALE_UP gets 1.3x weight
            eligible["weight"] = eligible["eff_score"] * eligible["status"].map(
                {"SCALE_UP": 1.3, "MAINTAIN": 1.0})
            total_weight = eligible["weight"].sum()
            eligible["suggested_budget"] = (
                (eligible["weight"] / total_weight * daily_envelope)
                .round(-2)   # round to nearest ₹100
            )
        else:
            eligible = eligible.assign(eff_score=0, weight=0, suggested_budget=0)

        # merge back suggested_budget into all scaling_camps
        scaling_camps = scaling_camps.merge(
            eligible[["campaign", "suggested_budget"]].rename(
                columns={"suggested_budget": "_sb"}),
            on="campaign", how="left")
        scaling_camps["suggested_budget"] = scaling_camps["_sb"].fillna(0)
        scaling_camps = scaling_camps.drop(columns=["_sb"])
        scaling_camps = scaling_camps.sort_values("suggested_budget", ascending=False)
        envelope_used = scaling_camps["suggested_budget"].sum()
    else:
        envelope_used = 0

    # ── Experiment ───────────────────────────────────────────────────────────
    exp_camps = l3d[l3d["campaign"].map(cfg_map) == "Experiment"].copy()

    if not exp_camps.empty:
        # L7D full window for days running
        dates_all = sorted(df_combined["date_tz"].unique())
        cutoff7 = dates_all[-7] if len(dates_all) >= 7 else dates_all[0]
        l7d_days = (df_combined[df_combined["date_tz"] >= cutoff7]
                    .groupby("campaign")["date_tz"].nunique()
                    .reset_index().rename(columns={"date_tz": "total_days"}))
        exp_camps = exp_camps.merge(l7d_days, on="campaign", how="left")
        exp_camps["total_days"] = exp_camps["total_days"].fillna(0).astype(int)

        def _exp_verdict(row):
            if row["orders"] < 5:
                return "CONTINUE", f"Only {row['orders']:.0f} orders — need more data (keep at ₹{exp_cap/1000:.0f}k/day)"
            if pd.isna(row["cac"]):
                return "CONTINUE", "No CAC yet — insufficient paid users"
            if row["cac"] <= cac_tgt * 0.9 and row["unin_rate"] <= unin_tgt:
                return "GRADUATE → Scaling", f"CAC ₹{row['cac']:,.0f} ✓  Unin {row['unin_rate']:.1f}% ✓  — move to Scaling"
            if row["cac"] > cac_tgt * 1.5 and row["total_days"] >= 5:
                return "KILL", f"CAC ₹{row['cac']:,.0f} ({row['cac']/cac_tgt:.1f}x) after {row['total_days']}d — not improving"
            if row["unin_rate"] > unin_tgt * 2 and row["total_days"] >= 5:
                return "KILL", f"Unin {row['unin_rate']:.1f}% ({row['unin_rate']/unin_tgt:.1f}x) after {row['total_days']}d — high churn"
            return "CONTINUE", f"CAC ₹{row['cac']:,.0f} ({row['cac']/cac_tgt:.1f}x) · {row['total_days']}d running — still gathering signal"

        exp_camps[["verdict", "reason"]] = exp_camps.apply(
            lambda r: pd.Series(_exp_verdict(r)), axis=1)
        exp_camps["daily_cap"] = exp_cap

    # ── CTF ──────────────────────────────────────────────────────────────────
    ctf_camps = l3d[l3d["campaign"].map(cfg_map) == "CTF"].copy()
    if not ctf_camps.empty:
        ctf_camps["daily_cap"] = ctf_cap
        ctf_camps["note"] = ctf_camps["campaign"].apply(
            lambda c: f"Fixed cap ₹{ctf_cap/1000:.0f}k/day — creative testing")

    return {
        "scaling":      scaling_camps if not scaling_camps.empty else pd.DataFrame(),
        "experiment":   exp_camps     if not exp_camps.empty     else pd.DataFrame(),
        "ctf":          ctf_camps     if not ctf_camps.empty     else pd.DataFrame(),
        "untagged":     untagged,
        "envelope_used": envelope_used,
        "targets":      tgt,
    }
