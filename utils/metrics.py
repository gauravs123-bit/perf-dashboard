from __future__ import annotations

import re
import pandas as pd
import numpy as np

# ── colour constants ────────────────────────────────────────────────────────
APP_COLORS = {
    "Arivu":    "#7F77DD",
    "Kali":     "#1D9E75",
    "Vidhya":   "#D85A30",
    "Nerchuko": "#D4537E",
    "Seekho":   "#F5A623",
}
SOURCE_COLORS = {
    "facebook": "#378ADD",
    "google":   "#E24B4A",
}


# ── derived metric helpers ──────────────────────────────────────────────────
def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    d0 = df["D0_paid_users"].replace(0, np.nan)
    installs = df["installs"].replace(0, np.nan)
    cost = df["total_cost"]

    df["p0_uninstall_rate"] = (df["p0_unin_users"] / d0 * 100).fillna(0)
    df["D0_CAC_calc"]       = (cost / d0).fillna(0)
    df["CPI_calc"]          = (cost / installs).fillna(0)
    df["conv_rate"]         = (d0 / installs * 100).fillna(0)
    df["cancel_rate"]       = (df["p0_cancel_users"] / d0 * 100).fillna(0)
    df["exit_rate"]         = (df["p0_exit_users"] / d0 * 100).fillna(0)
    return df


# ── latest-day summary (for header strip) ──────────────────────────────────
def latest_summary(df: pd.DataFrame, metric_col: str) -> dict:
    """Return latest value, previous value, and 7-day series for sparkline."""
    if df.empty or metric_col not in df.columns:
        return {"latest": 0, "prev": 0, "series": []}

    daily = (
        df.groupby("date_tz")
        .apply(lambda g: _aggregate_metric(g, metric_col))
        .reset_index(name=metric_col)
        .sort_values("date_tz")
    )
    last7 = daily.tail(7)
    series = last7[metric_col].tolist()
    latest = series[-1] if series else 0
    prev   = series[-2] if len(series) >= 2 else 0
    return {"latest": latest, "prev": prev, "series": series}


def _aggregate_metric(g: pd.DataFrame, metric_col: str) -> float:
    """Re-derive rate metrics from aggregated numerator/denominator."""
    if metric_col == "p0_uninstall_rate":
        d = g["D0_paid_users"].sum()
        return g["p0_unin_users"].sum() / d * 100 if d else 0
    if metric_col in ("D0_CAC", "D0_CAC_calc"):
        d = g["D0_paid_users"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col == "CPI_calc":
        d = g["installs"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col == "conv_rate":
        d = g["installs"].sum()
        return g["D0_paid_users"].sum() / d * 100 if d else 0
    if metric_col in ("CPC", "CPC_calc"):
        d = g["clicks"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col in ("CPM", "CPM_calc"):
        d = g["impressions"].sum()
        return g["total_cost"].sum() / d * 1000 if d else 0
    # additive metrics
    if metric_col in g.columns:
        return g[metric_col].sum()
    return 0


# ── L7D cross-app series ────────────────────────────────────────────────────
def l7d_series(df: pd.DataFrame, metric_col: str) -> dict:
    """Return {"dates": [...], "values": [...]} for the last 7 days."""
    if df.empty:
        return {"dates": [], "values": []}
    daily = (
        df.groupby("date_tz")
        .apply(lambda g: _aggregate_metric(g, metric_col))
        .reset_index(name=metric_col)
        .sort_values("date_tz")
        .tail(7)
    )
    return {"dates": daily["date_tz"].tolist(), "values": daily[metric_col].tolist()}


# ── 7-day trend table ───────────────────────────────────────────────────────
def build_trend_table(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    daily = df.groupby("date_tz").apply(
        lambda g: pd.Series({m: _aggregate_metric(g, m) for m in metrics})
    ).reset_index().sort_values("date_tz", ascending=False).head(7)
    return daily


# ── source split ────────────────────────────────────────────────────────────
def source_split(df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    """Returns source-level aggregation with the primary metric + absolute numbers."""
    if df.empty:
        return pd.DataFrame()
    latest_date = df["date_tz"].max()
    day_df = df[df["date_tz"] == latest_date].copy()

    src_lower = day_df["source"].str.lower()
    day_df["source_group"] = np.where(
        src_lower.str.contains("facebook|meta", na=False), "Facebook",
        np.where(src_lower.str.contains("google|goog", na=False), "Google", "Other")
    )

    grp = day_df.groupby("source_group", as_index=False).agg(
        total_cost=("total_cost", "sum"),
        D0_paid_users=("D0_paid_users", "sum"),
        p0_unin_users=("p0_unin_users", "sum"),
        installs=("installs", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
    )
    total_cost_sum = grp["total_cost"].sum() or np.nan
    grp["spend_share"] = grp["total_cost"] / total_cost_sum * 100

    # re-derive all rate metrics from aggregated raws
    d0 = grp["D0_paid_users"].replace(0, np.nan)
    grp["p0_uninstall_rate"] = (grp["p0_unin_users"] / d0 * 100).fillna(0)
    grp["D0_CAC_calc"]       = (grp["total_cost"] / d0).fillna(0)
    grp["CPI_calc"]          = (grp["total_cost"] / grp["installs"].replace(0, np.nan)).fillna(0)
    grp["conv_rate"]         = (d0 / grp["installs"].replace(0, np.nan) * 100).fillna(0)
    grp["CPC"]               = (grp["total_cost"] / grp["clicks"].replace(0, np.nan)).fillna(0)
    grp["CPM"]               = (grp["total_cost"] / grp["impressions"].replace(0, np.nan) * 1000).fillna(0)

    # primary metric column name for donut chart compatibility
    if metric_col not in grp.columns:
        grp[metric_col] = 0
    return grp


# ── campaign-level aggregation ──────────────────────────────────────────────
def campaign_table(df: pd.DataFrame, date: object | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    day_df = df[df["date_tz"] == date] if date else df[df["date_tz"] == df["date_tz"].max()]
    grp = day_df.groupby(["campaign", "source"], as_index=False).agg(
        D0_paid_users=("D0_paid_users", "sum"),
        p0_unin_users=("p0_unin_users", "sum"),
        total_cost=("total_cost", "sum"),
        installs=("installs", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        p0_cancel_users=("p0_cancel_users", "sum"),
        p0_exit_users=("p0_exit_users", "sum"),
    )
    total_cost = grp["total_cost"].sum() or np.nan
    grp["spend_share"] = grp["total_cost"] / total_cost * 100
    grp = add_derived_metrics(grp)
    # re-derive CPC and CPM from aggregated clicks/impressions
    grp["CPC"] = np.where(grp["clicks"] > 0, grp["total_cost"] / grp["clicks"], 0)
    grp["CPM"] = np.where(grp["impressions"] > 0, grp["total_cost"] / grp["impressions"] * 1000, 0)
    return grp.sort_values("total_cost", ascending=False)


# ── ad-set-level aggregation ────────────────────────────────────────────────
def adset_table(df: pd.DataFrame, campaign_filter: str | None = None,
                date: object | None = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    day_df = df[df["date_tz"] == date] if date else df[df["date_tz"] == df["date_tz"].max()]
    if campaign_filter:
        day_df = day_df[day_df["campaign"] == campaign_filter]
    grp = day_df.groupby(["ad_set", "campaign", "source"], as_index=False).agg(
        D0_paid_users=("D0_paid_users", "sum"),
        p0_unin_users=("p0_unin_users", "sum"),
        total_cost=("total_cost", "sum"),
        installs=("installs", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        p0_cancel_users=("p0_cancel_users", "sum"),
        p0_exit_users=("p0_exit_users", "sum"),
        p0_time_spent=("p0_time_spent", "sum") if "p0_time_spent" in day_df.columns else ("D0_paid_users", "sum"),
    )
    total_cost = grp["total_cost"].sum() or np.nan
    grp["spend_share"] = grp["total_cost"] / total_cost * 100
    grp = add_derived_metrics(grp)
    # re-derive CPC and CPM from aggregated clicks/impressions
    grp["CPC"] = np.where(grp["clicks"] > 0, grp["total_cost"] / grp["clicks"], 0)
    grp["CPM"] = np.where(grp["impressions"] > 0, grp["total_cost"] / grp["impressions"] * 1000, 0)
    return grp.sort_values("total_cost", ascending=False)


# ── creative-level aggregation (Meta only) ──────────────────────────────────
def _agg_creative_window(df: pd.DataFrame, dates: list,
                         campaign_filter: str | None,
                         adset_filter: str | None) -> pd.DataFrame:
    """Aggregate raw columns for a set of dates, grouped by ad_creative only."""
    win = df[df["date_tz"].isin(dates)]
    if campaign_filter:
        win = win[win["campaign"] == campaign_filter]
    if adset_filter:
        win = win[win["ad_set"] == adset_filter]
    if win.empty:
        return pd.DataFrame()
    # Group by ad_creative only to avoid duplicate key issues.
    # Keep the most common campaign/ad_set for display purposes.
    meta = (win.groupby("ad_creative")[["campaign", "ad_set"]]
               .agg(lambda x: x.mode().iloc[0])
               .reset_index())
    agg = win.groupby("ad_creative", as_index=False).agg(
        D0_paid_users=("D0_paid_users", "sum"),
        p0_unin_users=("p0_unin_users", "sum"),
        total_cost=("total_cost", "sum"),
        installs=("installs", "sum"),
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        p0_cancel_users=("p0_cancel_users", "sum"),
        p0_exit_users=("p0_exit_users", "sum"),
    )
    return agg.merge(meta, on="ad_creative", how="left")


def _derive_creative_metrics(grp: pd.DataFrame, suffix: str = "") -> pd.DataFrame:
    grp = grp.reset_index(drop=True)
    # Accept either original column names or already-renamed ones
    cost_col  = "total_cost"  if "total_cost"  in grp.columns else f"spend{suffix}"
    click_col = "clicks"      if "clicks"      in grp.columns else f"clicks{suffix}"
    impr_col  = "impressions" if "impressions" in grp.columns else f"impressions{suffix}"

    cost  = grp[cost_col].to_numpy(dtype=float)
    paid  = grp["D0_paid_users"].to_numpy(dtype=float)
    unin  = grp["p0_unin_users"].to_numpy(dtype=float)
    inst  = grp["installs"].to_numpy(dtype=float)
    click = grp[click_col].to_numpy(dtype=float)
    impr  = grp[impr_col].to_numpy(dtype=float)

    grp[f"CAC{suffix}"]     = np.where(paid > 0, cost / paid,        0)
    grp[f"p0_rate{suffix}"] = np.where(paid > 0, unin / paid * 100,  0)
    grp[f"CPI{suffix}"]     = np.where(inst > 0, cost / inst,        0)
    grp[f"conv{suffix}"]    = np.where(inst > 0, paid / inst * 100,  0)
    grp[f"CTR{suffix}"]     = np.where(impr > 0, click / impr * 100, 0)
    grp[f"spend{suffix}"]   = cost
    return grp


def _agg_metrics(df: pd.DataFrame, dates: list,
                 campaign_filter: str | None,
                 adset_filter: str | None) -> pd.DataFrame:
    """Aggregate into per-creative metrics for a date window, returns clean single-index df."""
    win = df[df["date_tz"].isin(dates)]
    if campaign_filter:
        win = win[win["campaign"] == campaign_filter]
    if adset_filter:
        win = win[win["ad_set"] == adset_filter]
    if win.empty:
        return pd.DataFrame()

    agg = win.groupby("ad_creative", as_index=False).agg(
        spend=("total_cost", "sum"),
        paid=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
        inst=("installs", "sum"),
        clicks=("clicks", "sum"),
        impr=("impressions", "sum"),
        cancel=("p0_cancel_users", "sum"),
    ).reset_index(drop=True)

    p = agg["paid"].to_numpy(dtype=float)
    s = agg["spend"].to_numpy(dtype=float)
    u = agg["unin"].to_numpy(dtype=float)
    i = agg["inst"].to_numpy(dtype=float)
    c = agg["clicks"].to_numpy(dtype=float)
    m = agg["impr"].to_numpy(dtype=float)

    result = pd.DataFrame({"ad_creative": agg["ad_creative"]})
    result["spend"]    = s
    result["orders"]   = p                                   # D0_paid_users
    result["unin"]     = u                                   # p0_unin_users
    result["inst"]     = i
    result["CAC"]      = np.where(p > 0, s / p,       np.nan)
    result["p0_rate"]  = np.where(p > 0, u / p * 100, np.nan)
    result["CPI"]      = np.where(i > 0, s / i,       0)
    result["conv"]     = np.where(i > 0, p / i * 100, 0)
    result["CTR"]      = np.where(m > 0, c / m * 100, 0)
    result["CPC"]      = np.where(c > 0, s / c,       0)
    result["CPM"]      = np.where(m > 0, s / m * 1000,0)
    return result


def creative_table(df: pd.DataFrame, campaign_filter: str | None = None,
                   adset_filter: str | None = None) -> pd.DataFrame:
    """
    Returns one row per creative with YD / L3D / L7D metrics.
    Sorted by L7D spend descending.
    """
    if df.empty:
        return pd.DataFrame()

    all_dates = sorted(df["date_tz"].unique())
    yd  = _agg_metrics(df, all_dates[-1:], campaign_filter, adset_filter)
    l3d = _agg_metrics(df, all_dates[-3:], campaign_filter, adset_filter)
    l7d = _agg_metrics(df, all_dates[-7:], campaign_filter, adset_filter)

    if l7d.empty:
        return pd.DataFrame()

    # rename each window's columns with suffix before merging
    def _suffix(frame, sfx):
        return frame.rename(columns={c: f"{c}{sfx}" for c in frame.columns if c != "ad_creative"})

    result = _suffix(l7d, "_l7d")
    if not yd.empty:
        result = result.merge(_suffix(yd, "_yd"),   on="ad_creative", how="left")
    if not l3d.empty:
        result = result.merge(_suffix(l3d, "_l3d"), on="ad_creative", how="left")

    # attach campaign/ad_set from the most common mapping
    meta = (df.groupby("ad_creative")[["campaign", "ad_set"]]
              .agg(lambda x: x.mode().iloc[0])
              .reset_index())
    result = result.merge(meta, on="ad_creative", how="left")

    total_spend = result["spend_l7d"].sum() or np.nan
    result["spend_share_l7d"] = result["spend_l7d"].to_numpy(dtype=float) / total_spend * 100

    # fillna(0) only for volume/spend cols; leave CAC/rate NaN so "no orders" is visible
    nan_ok_cols = [c for c in result.columns if any(
        c.startswith(p) for p in ("CAC_", "p0_rate_")
    )]
    fill_cols = [c for c in result.columns if c not in nan_ok_cols]
    result[fill_cols] = result[fill_cols].fillna(0)
    result = result.sort_values("spend_l7d", ascending=False).reset_index(drop=True)

    # attach parsed dimensions
    parsed = result["ad_creative"].apply(parse_creative_name)
    for col in ["category", "gender", "creative_type", "production", "track", "team", "launch_month"]:
        result[col] = [d[col] for d in parsed]

    # ── creative tags ──
    cac = result["CAC_l7d"]
    spend = result["spend_l7d"]
    has_cac = cac.notna() & (cac > 0)

    p25  = cac[has_cac].quantile(0.25) if has_cac.any() else 0
    p50  = cac[has_cac].quantile(0.50) if has_cac.any() else 0
    p75  = cac[has_cac].quantile(0.75) if has_cac.any() else 0
    med_spend = spend.median() if not spend.empty else 0

    def _tag(row):
        c, s, hc = row["CAC_l7d"], row["spend_yd"], has_cac[row.name]
        if not hc or s <= 0:
            return "—"
        if c > p75 and s >= med_spend:
            return "🔴 Pause"
        if c > p75 and s < med_spend:
            return "🟡 Review"
        if p50 < c <= p75 and s >= med_spend:
            return "🟡 Review"
        if c <= p25:
            return "🟢 Scale"
        return "—"

    result["tag"] = result.apply(_tag, axis=1)

    return result


def morning_pulse(df: pd.DataFrame, ref_date=None) -> dict:
    """
    Compute ref_date vs prior-day summary + campaign movers.
    ref_date: use this date as 'today'; defaults to latest date in df.
    Returns dict with keys: yd_date, d1_date, yd, d1, campaigns, alerts.
    """
    if df.empty:
        return {}

    dates = sorted(df["date_tz"].unique())
    if len(dates) < 2:
        return {}

    if ref_date is not None and ref_date in dates:
        idx = dates.index(ref_date)
        if idx == 0:
            return {}
        yd, d1 = dates[idx], dates[idx - 1]
    else:
        yd, d1 = dates[-1], dates[-2]

    yd_df = df[df["date_tz"] == yd]
    d1_df = df[df["date_tz"] == d1]

    def _totals(d):
        spend  = d["total_cost"].sum()
        orders = d["D0_paid_users"].sum()
        unin   = d["p0_unin_users"].sum()
        cancel = d["p0_cancel_users"].sum() if "p0_cancel_users" in d.columns else 0
        return {
            "spend":        spend,
            "orders":       orders,
            "unin":         unin,
            "cancel":       cancel,
            "cac":          spend  / orders * 1  if orders > 0 else 0,
            "unin_rate":    unin   / orders * 100 if orders > 0 else 0,
            "cancel_rate":  cancel / orders * 100 if orders > 0 else 0,
        }

    yd_t = _totals(yd_df)
    d1_t = _totals(d1_df)

    def _delta(now, prev):
        return ((now - prev) / prev * 100) if prev else 0

    # campaign-level movers
    def _camp_agg(d):
        if "campaign" not in d.columns:
            return pd.DataFrame(columns=["campaign","spend","orders","unin","cac","unin_rate"])
        g = d.groupby("campaign", as_index=False).agg(
            spend=("total_cost", "sum"),
            orders=("D0_paid_users", "sum"),
            unin=("p0_unin_users", "sum"),
        )
        g["cac"]       = np.where(g["orders"] > 0, g["spend"] / g["orders"], np.nan)
        g["unin_rate"] = np.where(g["orders"] > 0, g["unin"]  / g["orders"] * 100, np.nan)
        return g

    cy = _camp_agg(yd_df).rename(columns={"spend":"spend_yd","orders":"orders_yd",
                                            "unin":"unin_yd","cac":"cac_yd","unin_rate":"unin_rate_yd"})
    cd = _camp_agg(d1_df).rename(columns={"spend":"spend_d1","orders":"orders_d1",
                                            "unin":"unin_d1","cac":"cac_d1","unin_rate":"unin_rate_d1"})
    camps = cy.merge(cd[["campaign","spend_d1","orders_d1","cac_d1","unin_rate_d1"]],
                     on="campaign", how="outer").fillna(0)
    camps["cac_delta"]       = camps["cac_yd"]       - camps["cac_d1"]
    camps["unin_rate_delta"] = camps["unin_rate_yd"] - camps["unin_rate_d1"]
    camps["spend_share"]     = camps["spend_yd"] / (camps["spend_yd"].sum() or np.nan) * 100

    # auto alerts
    alerts = []
    cac_delta  = _delta(yd_t["cac"],       d1_t["cac"])
    unin_delta = _delta(yd_t["unin_rate"], d1_t["unin_rate"])
    spend_delta= _delta(yd_t["spend"],     d1_t["spend"])

    if abs(cac_delta) >= 10:
        direction = "rose" if cac_delta > 0 else "dropped"
        alerts.append(("🔴" if cac_delta > 0 else "🟢",
                        f"D0 CAC {direction} {abs(cac_delta):.0f}% vs prior day "
                        f"(₹{yd_t['cac']:.0f} vs ₹{d1_t['cac']:.0f})"))

    if abs(unin_delta) >= 10:
        direction = "rose" if unin_delta > 0 else "dropped"
        alerts.append(("🔴" if unin_delta > 0 else "🟢",
                        f"Uninstall rate {direction} {abs(unin_delta):.0f}% "
                        f"({yd_t['unin_rate']:.1f}% vs {d1_t['unin_rate']:.1f}%)"))

    cancel_delta = _delta(yd_t["cancel_rate"], d1_t["cancel_rate"])
    if abs(cancel_delta) >= 10:
        direction = "rose" if cancel_delta > 0 else "dropped"
        alerts.append(("🔴" if cancel_delta > 0 else "🟢",
                        f"Cancel rate {direction} {abs(cancel_delta):.0f}% vs prior day "
                        f"({yd_t['cancel_rate']:.1f}% vs {d1_t['cancel_rate']:.1f}%)"))

    if abs(spend_delta) >= 20:
        direction = "up" if spend_delta > 0 else "down"
        alerts.append(("🟡", f"Spend {direction} {abs(spend_delta):.0f}% "
                        f"(₹{yd_t['spend']:,.0f} vs ₹{d1_t['spend']:,.0f})"))

    # top 3 worst campaigns by CAC delta (only those with meaningful spend)
    med_spend = camps["spend_yd"].median()
    worst = camps[camps["spend_yd"] >= med_spend * 0.3].nlargest(3, "cac_delta")
    best  = camps[camps["spend_yd"] >= med_spend * 0.3].nsmallest(3, "cac_delta")

    for _, row in worst.iterrows():
        if row["cac_delta"] > 50:
            alerts.append(("🔴", f"[{row['campaign'][:40]}] CAC +₹{row['cac_delta']:.0f} vs prior day"))

    return {
        "yd_date": yd, "d1_date": d1,
        "yd": yd_t, "d1": d1_t,
        "campaigns": camps,
        "worst_camps": worst,
        "best_camps":  best,
        "alerts": alerts,
        "deltas": {"cac": cac_delta, "unin_rate": unin_delta, "spend": spend_delta,
                   "orders": _delta(yd_t["orders"], d1_t["orders"]),
                   "cancel_rate": cancel_delta},
    }


def diagnose_contribution(df: pd.DataFrame, level: str,
                          campaign_filter: str | None = None,
                          adset_filter: str | None = None) -> pd.DataFrame:
    """
    YD contribution breakdown at any level (source/campaign/ad_set/ad_creative).
    Returns spend%, orders%, unin% of YD totals + unin_delta = unin% - orders%.
    Red = orders% < spend% AND unin% > spend%.
    Green = orders% > spend% AND unin% < spend%.
    """
    if df.empty:
        return pd.DataFrame()

    yd = sorted(df["date_tz"].unique())[-1]
    win = df[df["date_tz"] == yd].copy()
    if campaign_filter:
        win = win[win["campaign"] == campaign_filter]
    if adset_filter:
        win = win[win["ad_set"] == adset_filter]
    if win.empty or level not in win.columns:
        return pd.DataFrame()

    g = win.groupby(level, as_index=False).agg(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
    )

    ts = g["spend"].sum()  or np.nan
    to = g["orders"].sum() or np.nan
    tu = g["unin"].sum()   or np.nan

    g["spend_pct"]  = g["spend"]  / ts * 100
    g["orders_pct"] = g["orders"] / to * 100
    g["unin_pct"]   = g["unin"]   / tu * 100
    g["unin_delta"] = g["unin_pct"] - g["orders_pct"]

    def _signal(row):
        if row["orders_pct"] < row["spend_pct"] and row["unin_pct"] > row["spend_pct"]:
            return "🔴 High Risk"
        if row["orders_pct"] > row["spend_pct"] and row["unin_pct"] < row["spend_pct"]:
            return "🟢 Efficient"
        return "⚪ Neutral"

    g["signal"] = g.apply(_signal, axis=1)
    return g.sort_values("spend_pct", ascending=False).reset_index(drop=True)


def creative_yd_contribution(df: pd.DataFrame,
                              campaign_filter: str | None = None,
                              adset_filter: str | None = None) -> pd.DataFrame:
    """
    For yesterday only: per-creative spend%, orders%, uninstall% of daily totals.
    Also computes uninstall_contribution = unin% - orders% (positive = disproportionate uninstalls).
    Sorted by spend% descending.
    """
    if df.empty:
        return pd.DataFrame()

    yd = sorted(df["date_tz"].unique())[-1]
    win = df[df["date_tz"] == yd].copy()
    if campaign_filter:
        win = win[win["campaign"] == campaign_filter]
    if adset_filter:
        win = win[win["ad_set"] == adset_filter]
    if win.empty:
        return pd.DataFrame()

    g = win.groupby("ad_creative", as_index=False).agg(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
    )

    total_spend  = g["spend"].sum()  or np.nan
    total_orders = g["orders"].sum() or np.nan
    total_unin   = g["unin"].sum()   or np.nan

    g["spend_pct"]  = g["spend"]  / total_spend  * 100
    g["orders_pct"] = g["orders"] / total_orders * 100
    g["unin_pct"]   = g["unin"]   / total_unin   * 100
    g["unin_contribution"] = g["unin_pct"] - g["orders_pct"]   # +ve = punching above weight

    # attach campaign/adset
    meta = (df[df["date_tz"] == yd].groupby("ad_creative")[["campaign", "ad_set"]]
              .agg(lambda x: x.mode().iloc[0]).reset_index())
    g = g.merge(meta, on="ad_creative", how="left")

    return g.sort_values("spend_pct", ascending=False).reset_index(drop=True)


def parse_creative_name(name: str) -> dict:
    """Extract structured dimensions from a creative name string."""
    nl = name.lower()

    # Category — first underscore-segment
    first_seg = nl.split("_")[0]
    category_map = {
        "astro": "Astro", "biz": "Business", "career": "Career",
        "eng": "English", "finance": "Finance",
    }
    category = category_map.get(first_seg, first_seg.capitalize() or "Unknown")

    # Gender
    if "female" in nl:
        gender = "Female"
    elif "male" in nl:
        gender = "Male"
    else:
        gender = "Unknown"

    # Creative type — order matters (repte/repex before rep)
    type_map = [
        ("microdrama", "Microdrama"),
        ("repte",      "Repurposed (Tested)"),
        ("repex",      "Repurposed (Extended)"),
        ("_exp_",      "Explainer"),
        ("_rep_",      "Repurposed"),
        ("ugc",        "UGC"),
    ]
    creative_type = "Other"
    for kw, label in type_map:
        if kw in nl:
            creative_type = label
            break

    # Production method
    if "actor" in nl:
        production = "Actor"
    elif "ai vo" in nl or "ai_vo" in nl:
        production = "AI Voice-Over"
    elif "_ai_" in nl or nl.endswith("_ai"):
        production = "AI"
    else:
        production = "Other"

    # Track ID — try patterns in priority order
    track_m = re.search(r"track(\d+)", nl)
    iter_m  = re.search(r"iteration\s*(\d+)", nl)
    hook_m  = re.search(r"hook(\d+)", nl)
    batch_m = re.search(r"(?<=[_\s])(\d{1,3})(?=[_\s])", nl)
    if track_m:
        track = f"Track {track_m.group(1)}"
    elif iter_m:
        track = f"Iteration {iter_m.group(1)}"
    elif hook_m:
        track = f"Hook {hook_m.group(1)}"
    elif batch_m:
        track = f"Batch {batch_m.group(1)}"
    else:
        track = "N/A"

    # Team
    if "_wdm_" in nl or nl.endswith("_wdm"):
        team = "WDM"
    elif "_sling_" in nl or nl.endswith("_sling"):
        team = "Sling"
    else:
        team = "Other"

    # Launch month
    month_m = re.search(r"\d{2}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", nl)
    launch_month = month_m.group(1).capitalize() if month_m else "Unknown"

    return dict(category=category, gender=gender, creative_type=creative_type,
                production=production, track=track, team=team, launch_month=launch_month)


def creative_pivot(cr_df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    Aggregate creative_table() output by a parsed dimension.
    Returns one row per dimension value with spend, orders, CAC, p0_rate.
    """
    if cr_df.empty or dimension not in cr_df.columns:
        return pd.DataFrame()

    g = cr_df.groupby(dimension, as_index=False).agg(
        n_creatives=("ad_creative", "count"),
        total_spend=("spend_l7d", "sum"),
        total_orders=("orders_l7d", "sum"),
        total_unin=("unin_l7d", "sum"),
    )

    s = g["total_spend"].to_numpy(dtype=float)
    p = g["total_orders"].to_numpy(dtype=float)
    u = g["total_unin"].to_numpy(dtype=float)

    g["avg_cac"]    = np.where(p > 0, s / p, 0)
    g["avg_p0"]     = np.where(p > 0, u / p * 100, 0)
    total = s.sum() or np.nan
    g["spend_share"] = s / total * 100

    return g.sort_values("total_spend", ascending=False).reset_index(drop=True)


def creative_l3d(df: pd.DataFrame, metric_col: str,
                 campaign_filter: str | None = None) -> pd.DataFrame:
    """Returns long-form daily data for L3D trend per creative."""
    if df.empty:
        return pd.DataFrame()
    dates = sorted(df["date_tz"].unique())[-3:]
    if campaign_filter:
        df = df[df["campaign"] == campaign_filter]
    frames = []
    for d in dates:
        day_df = df[df["date_tz"] == d]
        grp = day_df.groupby("ad_creative", as_index=False).agg(
            D0_paid_users=("D0_paid_users", "sum"),
            p0_unin_users=("p0_unin_users", "sum"),
            total_cost=("total_cost", "sum"),
            installs=("installs", "sum"),
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
        )
        d0 = grp["D0_paid_users"].replace(0, np.nan)
        if metric_col == "p0_uninstall_rate":
            grp["_val"] = (grp["p0_unin_users"] / d0 * 100).fillna(0)
        elif metric_col == "D0_CAC_calc":
            grp["_val"] = (grp["total_cost"] / d0).fillna(0)
        elif metric_col == "CTR":
            grp["_val"] = np.where(grp["impressions"] > 0,
                                   grp["clicks"] / grp["impressions"] * 100, 0)
        else:
            grp["_val"] = grp[metric_col] if metric_col in grp.columns else 0
        grp["date_tz"] = d
        frames.append(grp[["ad_creative", "date_tz", "_val"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── Kitagawa decomposition ──────────────────────────────────────────────────

def _kit_uninstall_pair(df: pd.DataFrame, level: str,
                        d0_date, d1_date) -> pd.DataFrame:
    """Single day-transition Kitagawa for uninstall rate."""
    group_col = level

    def _agg(day_df):
        g = day_df.groupby(group_col, as_index=False).agg(
            D0_paid=("D0_paid_users", "sum"),
            unin=("p0_unin_users", "sum"),
        )
        total = g["D0_paid"].sum() or np.nan
        g["share"] = g["D0_paid"] / total
        g["rate"]  = np.where(g["D0_paid"] > 0, g["unin"] / g["D0_paid"] * 100, 0)
        return g

    d0 = _agg(df[df["date_tz"] == d0_date]).set_index(group_col)
    d1 = _agg(df[df["date_tz"] == d1_date]).set_index(group_col)
    c = d0.join(d1, lsuffix="_d0", rsuffix="_d1", how="outer").fillna(0)
    # Overall weighted-avg rate on D1 (baseline).
    # Using deviation from mean so gaining share in a below-avg campaign
    # correctly shows as an improvement, not near-zero.
    overall_rate_d1 = (c["rate_d1"] * c["share_d1"]).sum()
    c["rate_effect"]  = (c["rate_d0"] - c["rate_d1"]) * c["share_d0"]
    c["mix_effect"]   = (c["share_d0"] - c["share_d1"]) * (c["rate_d1"] - overall_rate_d1)
    c["contribution"] = c["rate_effect"] + c["mix_effect"]
    c = c.reset_index().rename(columns={group_col: "group"})
    c["d0_date"] = d0_date
    c["d1_date"] = d1_date
    return c


def _kit_cac_pair(df: pd.DataFrame, level: str,
                  d0_date, d1_date) -> pd.DataFrame:
    """Single day-transition Kitagawa for D0 CAC.

    CAC = total_spend / D0_paid = Σ(cac_i × paid_share_i), so the correct
    decomposition weight is D0_paid share — not spend share.
    Using spend share breaks the additive identity.
    """
    group_col = level

    def _agg(day_df):
        g = day_df.groupby(group_col, as_index=False).agg(
            spend=("total_cost", "sum"),
            D0_paid=("D0_paid_users", "sum"),
            installs=("installs", "sum"),
        )
        total_paid  = g["D0_paid"].sum() or np.nan
        total_spend = g["spend"].sum() or np.nan
        # paid_share is the correct weight for Kitagawa on a ratio metric
        g["paid_share"]  = g["D0_paid"] / total_paid
        g["spend_share"] = g["spend"] / total_spend   # kept for tooltip/scatter use
        g["cac"]  = np.where(g["D0_paid"] > 0, g["spend"] / g["D0_paid"], 0)
        g["cpi"]  = np.where(g["installs"] > 0, g["spend"] / g["installs"], 0)
        g["conv"] = np.where(g["installs"] > 0, g["D0_paid"] / g["installs"] * 100, 0)
        return g

    # Only include groups with D0_paid > 0 on each day so that
    # Σ(cac_i × paid_share_i) == total_spend / total_D0_paid exactly.
    # Groups with zero paid users but positive spend have undefined CAC
    # and would break the additive identity.
    d0 = _agg(df[(df["date_tz"] == d0_date) & (df["D0_paid_users"] > 0)]).set_index(group_col)
    d1 = _agg(df[(df["date_tz"] == d1_date) & (df["D0_paid_users"] > 0)]).set_index(group_col)
    c = d0.join(d1, lsuffix="_d0", rsuffix="_d1", how="outer").fillna(0)
    # overall_cac_d1 = Σ(cac_i × paid_share_i) = total_spend_d1 / total_D0_paid_d1
    overall_cac_d1 = (c["cac_d1"] * c["paid_share_d1"]).sum()
    c["rate_effect"]  = (c["cac_d0"] - c["cac_d1"]) * c["paid_share_d0"]
    c["mix_effect"]   = (c["paid_share_d0"] - c["paid_share_d1"]) * (c["cac_d1"] - overall_cac_d1)
    c["contribution"] = c["rate_effect"] + c["mix_effect"]
    c = c.reset_index().rename(columns={group_col: "group"})
    c["d0_date"] = d0_date
    c["d1_date"] = d1_date
    return c


def kitagawa_uninstall(df: pd.DataFrame, level: str = "campaign") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    dates = sorted(df["date_tz"].unique())
    if len(dates) < 2:
        return pd.DataFrame()
    result = _kit_uninstall_pair(df, level, dates[-1], dates[-2])
    return result.sort_values("contribution", ascending=False)


def kitagawa_cac(df: pd.DataFrame, level: str = "campaign") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    dates = sorted(df["date_tz"].unique())
    if len(dates) < 2:
        return pd.DataFrame()
    result = _kit_cac_pair(df, level, dates[-1], dates[-2])
    return result.sort_values("contribution", ascending=False)


def kitagawa_rolling_uninstall(
    df: pd.DataFrame, level: str = "campaign", n_transitions: int = 7
) -> tuple[pd.DataFrame, dict]:
    """
    Returns (pivot_df, detail_dict) for the last n_transitions day transitions.
    pivot_df  : rows = groups, cols = transition labels, values = contribution
    detail_dict: {label: full kit_df for that transition}
    """
    if df.empty:
        return pd.DataFrame(), {}
    dates = sorted(df["date_tz"].unique())
    if len(dates) < 2:
        return pd.DataFrame(), {}

    dates = dates[-(n_transitions + 1):]
    detail: dict = {}
    frames = []

    for i in range(len(dates) - 1):
        d1_date, d0_date = dates[i], dates[i + 1]
        label = f"{_fmt_date(d1_date)}→{_fmt_date(d0_date)}"
        kit = _kit_uninstall_pair(df, level, d0_date, d1_date)
        kit["transition"] = label
        detail[label] = kit
        frames.append(kit[["group", "transition", "contribution"]])

    if not frames:
        return pd.DataFrame(), {}

    pivot = _build_pivot(frames, dates, n_transitions)
    return pivot, detail


def kitagawa_rolling_cac(
    df: pd.DataFrame, level: str = "campaign", n_transitions: int = 7
) -> tuple[pd.DataFrame, dict]:
    """Same as kitagawa_rolling_uninstall but for D0 CAC."""
    if df.empty:
        return pd.DataFrame(), {}
    dates = sorted(df["date_tz"].unique())
    if len(dates) < 2:
        return pd.DataFrame(), {}

    dates = dates[-(n_transitions + 1):]
    detail: dict = {}
    frames = []

    for i in range(len(dates) - 1):
        d1_date, d0_date = dates[i], dates[i + 1]
        label = f"{_fmt_date(d1_date)}→{_fmt_date(d0_date)}"
        kit = _kit_cac_pair(df, level, d0_date, d1_date)
        kit["transition"] = label
        detail[label] = kit
        frames.append(kit[["group", "transition", "contribution"]])

    if not frames:
        return pd.DataFrame(), {}

    pivot = _build_pivot(frames, dates, n_transitions)
    return pivot, detail


def _fmt_date(d) -> str:
    import datetime
    if hasattr(d, "strftime"):
        return d.strftime("%b%-d")
    return str(d)


def _build_pivot(frames: list, dates: list, n_transitions: int) -> pd.DataFrame:
    long_df = pd.concat(frames, ignore_index=True)
    pivot = long_df.pivot_table(
        index="group", columns="transition",
        values="contribution", fill_value=0,
    )
    # sort rows by sum of absolute contributions (biggest movers first)
    pivot["_abs_sum"] = pivot.abs().sum(axis=1)
    pivot = pivot.sort_values("_abs_sum", ascending=False).drop(columns="__abs_sum", errors="ignore")
    pivot = pivot.drop(columns="_abs_sum")
    # keep columns in chronological order
    ordered_cols = [
        f"{_fmt_date(dates[i])}→{_fmt_date(dates[i + 1])}"
        for i in range(len(dates) - 1)
    ]
    pivot = pivot[[c for c in ordered_cols if c in pivot.columns]]
    return pivot


# ── spend vs CAC quadrant table ─────────────────────────────────────────────
def spend_cac_quadrants(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if df.empty:
        return {}
    latest = df[df["date_tz"] == df["date_tz"].max()].copy()
    grp = latest.groupby(["ad_set", "source"], as_index=False).agg(
        spend=("total_cost", "sum"),
        D0_paid=("D0_paid_users", "sum"),
    )
    total_spend = grp["spend"].sum() or np.nan
    grp["spend_share"] = grp["spend"] / total_spend * 100
    grp["cac"] = np.where(grp["D0_paid"] > 0, grp["spend"] / grp["D0_paid"], 0)

    med_spend = grp["spend_share"].median()
    med_cac   = grp["cac"].median()

    hs_hc = grp[(grp["spend_share"] >= med_spend) & (grp["cac"] >= med_cac)]
    ls_hc = grp[(grp["spend_share"] <  med_spend) & (grp["cac"] >= med_cac)]
    hs_lc = grp[(grp["spend_share"] >= med_spend) & (grp["cac"] <  med_cac)]
    ls_lc = grp[(grp["spend_share"] <  med_spend) & (grp["cac"] <  med_cac)]

    return {
        "High Spend / High CAC": hs_hc,
        "Low Spend / High CAC":  ls_hc,
        "High Spend / Low CAC":  hs_lc,
        "Low Spend / Low CAC":   ls_lc,
    }
