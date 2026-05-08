"""
Performance Marketing Dashboard
Uninstall Dashboard  |  CAC Dashboard
"""
from __future__ import annotations

import re as _re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.fetcher import fetch_app_data, refresh_app_data, APP_QUERY_IDS, fetch_creative_data, CREATIVE_QUERY_IDS
from utils.metrics import (
    add_derived_metrics, latest_summary, build_trend_table,
    source_split, campaign_table, adset_table, creative_table, creative_l3d,
    creative_pivot, creative_yd_contribution, diagnose_contribution, morning_pulse,
    kitagawa_uninstall, kitagawa_cac,
    kitagawa_rolling_uninstall, kitagawa_rolling_cac,
    spend_cac_quadrants, APP_COLORS,
)
from utils.charts import (
    sparkline, kpi_values, trend_bar, source_donut,
    campaign_bar, kitagawa_waterfall, kitagawa_heatmap, spend_cac_scatter,
    l3d_group_trend, creative_trend, pivot_bar_chart, overview_trend_chart,
)

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Perf Marketing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── dark theme tweaks ────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  /* ── Base ── */
  html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
  [data-testid="stAppViewContainer"] { background:#080808; }
  [data-testid="stHeader"]           { background:#080808; display:none; }
  .block-container { padding-top:1.5rem; padding-bottom:2rem; max-width:1200px; }

  /* scrollbar */
  ::-webkit-scrollbar { width:4px; height:4px; }
  ::-webkit-scrollbar-track { background:#0d0d0d; }
  ::-webkit-scrollbar-thumb { background:#222; border-radius:4px; }

  /* ── Streamlit metric cards (used in non-pulse views) ── */
  [data-testid="metric-container"] {
      background:#111; border:1px solid #1c1c1c; border-radius:12px; padding:14px 18px;
  }
  [data-testid="stMetricValue"] { font-size:1.35rem; font-weight:700; letter-spacing:-.02em; }
  [data-testid="stMetricDelta"] { font-size:0.75rem; }
  button[data-baseweb="tab"]    { font-size:0.85rem; font-weight:600; }
  [data-testid="stDataFrame"]   { border-radius:10px; overflow:hidden; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background:#050505 !important;
      border-right:1px solid #111 !important;
  }
  [data-testid="stSidebar"] > div:first-child { padding:1.4rem 1rem 1rem; }

  /* hide radio circles */
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display:none !important; }
  [data-testid="stSidebar"] .stRadio > div { gap:2px !important; }
  [data-testid="stSidebar"] .stRadio label {
      font-size:0.83rem; padding:7px 12px !important; border-radius:7px;
      color:#3c3c3c !important; font-weight:500; transition:background .1s, color .1s;
      cursor:pointer; display:flex !important; align-items:center; gap:7px; width:100%;
  }
  [data-testid="stSidebar"] .stRadio label:hover {
      background:#111 !important; color:#888 !important;
  }
  [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { margin:0; }
  [data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] { display:none; }
  [data-testid="stSidebar"] hr { border-color:#131313; margin:10px 0; }

  /* ── nav buttons (replace radio) ── */
  [data-testid="stSidebar"] .nav-btn button,
  [data-testid="stSidebar"] .nav-btn [data-testid="stBaseButton-secondary"] {
      background:transparent !important; border:none !important; box-shadow:none !important;
      color:#3c3c3c !important; font-size:0.83rem !important;
      font-weight:500 !important; text-align:left !important;
      padding:7px 12px !important; border-radius:7px !important;
      width:100% !important; transition:background .1s, color .1s !important;
      justify-content:flex-start !important;
  }
  [data-testid="stSidebar"] .nav-btn button:hover {
      background:#111 !important; color:#888 !important;
  }
  [data-testid="stSidebar"] .nav-btn-active button,
  [data-testid="stSidebar"] .nav-btn-active [data-testid="stBaseButton-secondary"] {
      background:var(--app-color-subtle, #161616) !important;
      color:var(--app-color, #e8e8e8) !important;
      font-weight:600 !important; border:none !important; box-shadow:none !important;
  }
  [data-testid="stSidebar"] .nav-btn-active button:hover {
      background:var(--app-color-subtle, #161616) !important;
      color:var(--app-color, #e8e8e8) !important;
  }

  /* sidebar group label */
  .sb-group-label {
      font-size:0.58rem; font-weight:700; letter-spacing:.16em;
      text-transform:uppercase; color:#383838; margin:18px 0 4px 2px;
  }

  /* sidebar refresh button */
  [data-testid="stSidebar"] .stButton > button {
      background:#0a0a0a !important; border:1px solid #1c1c1c !important;
      color:#444 !important; border-radius:8px !important;
      font-size:0.79rem !important; font-weight:500 !important;
      padding:8px 14px !important; width:100%; transition:all .15s;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
      background:#151515 !important; color:#aaa !important; border-color:#282828 !important;
  }

  /* ── Morning Pulse KPI cards ── */
  .pulse-card {
      background:#0d0d0d; border:1px solid #181818; border-radius:12px;
      padding:16px 16px; height:100%; position:relative; overflow:hidden;
      transition: border-color .15s, background .15s;
  }
  .pulse-card:hover { border-color:#252525; background:#0f0f0f; }
  .pulse-card::after {
      content:''; position:absolute; top:0; left:0; right:0; height:2px;
      border-radius:12px 12px 0 0;
  }
  .pulse-card-red::after   { background:linear-gradient(90deg,#E24B4A,transparent); }
  .pulse-card-green::after { background:linear-gradient(90deg,#1D9E75,transparent); }
  .pulse-card-grey::after  { background:linear-gradient(90deg,#2a2a2a,transparent); }
  .pulse-label { font-size:0.58rem; color:#3a3a3a; text-transform:uppercase;
                 letter-spacing:.16em; margin-bottom:10px; font-weight:700; }
  .pulse-value { font-size:1.75rem; font-weight:700; color:#f2f2f2;
                 letter-spacing:-.03em; line-height:1; margin-bottom:4px; }
  .pulse-yday  { font-size:0.66rem; color:#2e2e2e; margin-bottom:10px; }
  .pulse-delta-row { display:flex; align-items:center; justify-content:space-between; }
  .pulse-delta-bad  { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      font-weight:700; padding:3px 10px; border-radius:20px;
                      background:rgba(226,75,74,.12); color:#E24B4A;
                      border:1px solid rgba(226,75,74,.18); }
  .pulse-delta-good { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      font-weight:700; padding:3px 10px; border-radius:20px;
                      background:rgba(29,158,117,.12); color:#1D9E75;
                      border:1px solid rgba(29,158,117,.18); }
  .pulse-delta-neu  { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      padding:3px 10px; border-radius:20px;
                      background:#111; color:#333; border:1px solid #1a1a1a; }
  .pulse-pct { font-size:0.62rem; color:#2e2e2e; }

  /* ── Section header ── */
  .section-hdr { display:flex; align-items:center; gap:10px; margin:28px 0 14px; }
  .section-hdr-line { flex:1; height:1px; background:#131313; }
  .section-hdr-text { font-size:0.58rem; font-weight:700; letter-spacing:.16em;
                      text-transform:uppercase; color:#2e2e2e; white-space:nowrap; }

  /* ── Alert pills ── */
  .alert-pill { display:inline-flex; align-items:center; gap:5px; padding:5px 13px;
                border-radius:20px; font-size:0.78rem; font-weight:500; margin:0 4px 5px 0; }
  .alert-pill-red    { background:rgba(226,75,74,.1);  color:#ff8080; border:1px solid rgba(226,75,74,.2); }
  .alert-pill-green  { background:rgba(29,158,117,.1); color:#4cdf96; border:1px solid rgba(29,158,117,.2); }
  .alert-pill-yellow { background:rgba(255,180,0,.08); color:#ffc947; border:1px solid rgba(255,180,0,.2); }

  /* ── Shared section label ── */
  .section-label { font-size:0.6rem; text-transform:uppercase; letter-spacing:.14em;
                   color:#3a3a3a; margin-bottom:12px; margin-top:0; font-weight:700; }

  /* ── Contributor cards ── */
  .contrib-card { background:#0d0d0d; border:1px solid #161616; border-radius:12px;
                  padding:13px 15px; margin-bottom:6px; }
  .contrib-tag  { display:inline-flex; align-items:center; gap:3px; font-size:0.67rem;
                  background:#131313; padding:3px 9px; border-radius:10px;
                  border:1px solid #1c1c1c; margin-right:4px; }

  /* ── Campaign table ── */
  .camp-table { width:100%; border-collapse:collapse; }
  .camp-table th {
      font-size:0.58rem; color:#2e2e2e; text-transform:uppercase; letter-spacing:.12em;
      font-weight:700; padding:8px 12px; text-align:right; border-bottom:1px solid #161616;
      background:#090909;
  }
  .camp-table th:first-child { text-align:left; }
  .camp-table td {
      padding:9px 12px; font-size:0.78rem; color:#999; border-bottom:1px solid #0f0f0f;
      text-align:right; white-space:nowrap;
  }
  .camp-table td:first-child { text-align:left; }
  .camp-table tr:hover td { background:#0d0d0d; }
  .camp-table tr:last-child td { border-bottom:none; }
  .src-dot { display:inline-block; width:7px; height:7px; border-radius:50%;
             margin-right:6px; flex-shrink:0; }
  .src-badge { font-size:0.6rem; background:#161616; border:1px solid #1e1e1e;
               border-radius:4px; padding:1px 6px; color:#444; margin-left:5px; }
  .dod-pill-bad  { display:inline-flex; align-items:center; font-size:0.68rem; font-weight:700;
                   padding:2px 8px; border-radius:5px; background:rgba(226,75,74,.15); color:#E24B4A; }
  .dod-pill-good { display:inline-flex; align-items:center; font-size:0.68rem; font-weight:700;
                   padding:2px 8px; border-radius:5px; background:rgba(29,158,117,.15); color:#1D9E75; }
  .dod-pill-neu  { display:inline-flex; align-items:center; font-size:0.68rem;
                   padding:2px 8px; border-radius:5px; background:#141414; color:#333; }

  /* ── Clickable row name buttons ── */
  .camp-name-btn button, .adset-name-btn button {
    background:transparent !important; border:none !important;
    box-shadow:none !important; padding:6px 4px !important;
    text-align:left !important; width:100% !important;
    color:#ccc !important; font-size:0.82rem !important;
    font-weight:500 !important; border-radius:0 !important;
    white-space:nowrap !important; overflow:hidden !important;
    text-overflow:ellipsis !important; display:block !important;
  }
  .adset-name-btn button { font-size:0.78rem !important; color:#aaa !important; padding:5px 4px !important; }
  .camp-name-btn button:hover, .adset-name-btn button:hover {
    background:rgba(255,255,255,0.04) !important; color:#fff !important;
  }
  /* ── Chart popover trigger ── */
  .chart-pop-btn button {
    background:transparent !important; border:1px solid #1e1e1e !important;
    color:#444 !important; font-size:0.75rem !important;
    padding:4px 7px !important; border-radius:6px !important;
    box-shadow:none !important; width:100% !important;
  }
  .chart-pop-btn button:hover { border-color:#333 !important; color:#888 !important; }

  /* ── Header strip ── */
  .strip-card { background:#0d0d0d; border:1px solid #161616; border-radius:10px;
                padding:10px 14px; text-align:center; cursor:pointer;
                transition:border-color .15s; }
  .strip-app-name  { font-size:0.68rem; color:#444; margin-bottom:2px; font-weight:500; }
  .strip-value     { font-size:1.05rem; font-weight:700; letter-spacing:-.02em; }
  .strip-delta-pos { color:#1D9E75; font-size:0.72rem; }
  .strip-delta-neg { color:#E24B4A; font-size:0.72rem; }

  /* strip switch button — compact pill */
  .strip-click-btn { margin-top:4px; }
  .strip-click-btn button {
      background:#0d0d0d !important; border:1px solid #1e1e1e !important;
      box-shadow:none !important; color:#333 !important;
      font-size:0.7rem !important; font-weight:500 !important;
      padding:3px 10px !important; border-radius:20px !important;
      width:auto !important; min-height:0 !important; height:auto !important;
      transition:color .12s, border-color .12s !important;
      display:inline-flex !important;
  }
  .strip-click-btn button:hover {
      color:#aaa !important; border-color:#333 !important;
      background:#111 !important;
  }

  /* section pill nav */
  div[data-testid="stHorizontalBlock"] .stRadio [data-testid="stWidgetLabel"] { display:none; }
</style>
""", unsafe_allow_html=True)

APPS = list(APP_QUERY_IDS.keys())

# ════════════════════════════════════════════════════════════════════════════
#  helpers
# ════════════════════════════════════════════════════════════════════════════

def safe_fetch(app_name: str) -> pd.DataFrame:
    try:
        df = fetch_app_data(app_name)
        return add_derived_metrics(df)
    except Exception as e:
        st.error(f"Error fetching {app_name}: {e}")
        return pd.DataFrame()


def fmt(val: float, decimals: int = 1, prefix: str = "", suffix: str = "") -> str:
    if val == 0:
        return "—"
    return f"{prefix}{val:,.{decimals}f}{suffix}"


# ════════════════════════════════════════════════════════════════════════════
#  header strip
# ════════════════════════════════════════════════════════════════════════════

def render_header_strip(metric_col: str, label: str, decimals: int = 1,
                        prefix: str = "", suffix: str = ""):
    cols = st.columns(len(APPS))
    for i, app in enumerate(APPS):
        color = APP_COLORS[app]
        df = safe_fetch(app)
        info = latest_summary(df, metric_col)
        latest, prev, series = info["latest"], info["prev"], info["series"]
        val_str, delta_str = kpi_values(latest, prev, f".{decimals}f")
        delta_class = "strip-delta-pos" if (latest - prev) <= 0 else "strip-delta-neg"
        # for CAC/CPI lower is better; for uninstall rate lower is better
        if metric_col in ("p0_uninstall_rate", "D0_CAC_calc", "CPI_calc"):
            delta_class = "strip-delta-pos" if (latest - prev) <= 0 else "strip-delta-neg"
        else:
            delta_class = "strip-delta-pos" if (latest - prev) >= 0 else "strip-delta-neg"

        with cols[i]:
            is_selected = st.session_state.get("sb_app") == app
            border_style = f"border-top:3px solid {color};border-color:{color};" if is_selected else f"border-top:3px solid {color};"
            st.markdown(f"""
            <div class="strip-card" style="{border_style}">
                <div class="strip-app-name">{app} — {label}</div>
                <div class="strip-value" style="color:{color};">{prefix}{val_str}{suffix}</div>
                <div class="{delta_class}">{delta_str} DoD</div>
            </div>
            """, unsafe_allow_html=True)
            if series:
                fig = sparkline(series, color)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("<div class='strip-click-btn'>", unsafe_allow_html=True)
            if st.button(f"{app} →", key=f"strip_app_{app}"):
                st.session_state["sb_app"] = app
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  shared kpi row
# ════════════════════════════════════════════════════════════════════════════

def kpi_row(df: pd.DataFrame, metrics: list[tuple]):
    """
    metrics: list of (col_name, label, prefix, suffix, decimals)
    """
    latest_date = df["date_tz"].max() if not df.empty else None
    cols = st.columns(len(metrics))
    for i, (col, label, prefix, suffix, decimals) in enumerate(metrics):
        if df.empty or latest_date is None:
            cols[i].metric(label, "—")
            continue
        day_df = df[df["date_tz"] == latest_date]
        prev_dates = sorted(df["date_tz"].unique())
        prev_date = prev_dates[-2] if len(prev_dates) >= 2 else None

        from utils.metrics import _aggregate_metric
        val = _aggregate_metric(day_df, col)
        prev_val = _aggregate_metric(df[df["date_tz"] == prev_date], col) if prev_date else val

        val_str, delta_str = kpi_values(val, prev_val, f".{decimals}f")
        cols[i].metric(
            label,
            f"{prefix}{val_str}{suffix}",
            delta_str,
            delta_color="inverse" if col in ("p0_uninstall_rate", "D0_CAC_calc", "CPI_calc", "CPC", "CPM") else "normal",
        )


# ════════════════════════════════════════════════════════════════════════════
#  UNINSTALL DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

def _overview_kpi_cards(df: pd.DataFrame, metrics: list[tuple], app: str):
    """
    Render a row of KPI stat cards with embedded sparklines.
    metrics: [(col, label, prefix, suffix, higher_is_bad)]
    """
    cols = st.columns(len(metrics))
    for i, (col, label, prefix, suffix, higher_is_bad) in enumerate(metrics):
        info   = latest_summary(df, col)
        latest, prev, series = info["latest"], info["prev"], info["series"]
        delta  = ((latest - prev) / prev * 100) if prev else 0
        is_bad = (delta > 0 and higher_is_bad) or (delta < 0 and not higher_is_bad)
        d_class = "pulse-delta-bad" if is_bad else ("pulse-delta-good" if delta != 0 else "pulse-delta-neu")
        c_class = "pulse-card-red" if is_bad else ("pulse-card-green" if not is_bad and delta != 0 else "pulse-card-grey")
        arrow   = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        sign    = "+" if delta > 0 else ""

        if col in ("D0_paid_users", "p0_unin_users", "total_cost", "installs", "clicks"):
            val_str = f"{prefix}{latest:,.0f}{suffix}"
        elif col in ("D0_CAC_calc", "CPI_calc", "CPC", "CPM"):
            val_str = f"{prefix}{latest:,.0f}{suffix}"
        else:
            val_str = f"{prefix}{latest:.1f}{suffix}"

        with cols[i]:
            st.markdown(f"""
            <div class="pulse-card {c_class}" style="padding:14px 16px">
              <div class="pulse-label">{label}</div>
              <div class="pulse-value" style="font-size:1.35rem">{val_str}</div>
              <div class="{d_class}">{arrow} {sign}{delta:.1f}%</div>
            </div>""", unsafe_allow_html=True)
            if series:
                st.plotly_chart(
                    sparkline(series, "#E24B4A" if is_bad else "#1D9E75"),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"ov_spark_{app}_{col}",
                )


def _overview_source_cards(src: pd.DataFrame, primary_col: str, primary_label: str,
                           primary_suffix: str = "", primary_prefix: str = ""):
    """Render source breakdown as inline stat cards instead of a raw table."""
    src_colors = {"Facebook": "#378ADD", "Google": "#E24B4A", "Other": "#888"}
    cards_html = ""
    for _, row in src.iterrows():
        s     = row["source_group"]
        sc    = src_colors.get(s, "#888")
        spend = row["total_cost"]
        spct  = row["spend_share"]
        pval  = row[primary_col] if primary_col in row else 0
        paid  = int(row["D0_paid_users"])
        cards_html += f"""
        <div style="flex:1;min-width:120px;background:#0d0d0d;border:1px solid #1a1a1a;
                    border-top:2px solid {sc};border-radius:10px;padding:12px 14px">
          <div style="font-size:0.6rem;color:{sc};font-weight:700;letter-spacing:.1em;
                      text-transform:uppercase;margin-bottom:8px">{s}</div>
          <div style="font-size:0.75rem;color:#666;margin-bottom:2px">Spend</div>
          <div style="font-size:1rem;font-weight:700;color:#ddd;margin-bottom:6px">
            ₹{spend:,.0f} <span style="font-size:0.68rem;color:#444">({spct:.0f}%)</span>
          </div>
          <div style="font-size:0.75rem;color:#666;margin-bottom:2px">{primary_label}</div>
          <div style="font-size:0.95rem;font-weight:600;color:#ccc;margin-bottom:6px">
            {primary_prefix}{pval:.1f}{primary_suffix}
          </div>
          <div style="font-size:0.75rem;color:#666;margin-bottom:2px">D0 Orders</div>
          <div style="font-size:0.85rem;color:#aaa">{paid:,}</div>
        </div>"""
    st.markdown(
        f"<div style='display:flex;gap:10px;flex-wrap:wrap'>{cards_html}</div>",
        unsafe_allow_html=True,
    )


def uninstall_overview(df: pd.DataFrame, app_color: str, app: str = ""):
    # ── KPI cards with sparklines ──
    _overview_kpi_cards(df, [
        ("p0_uninstall_rate", "P0 Uninstall Rate", "",  "%", True),
        ("cancel_rate",       "Cancel Rate",        "",  "%", True),
        ("D0_paid_users",     "D0 Orders",          "",  "",  False),
        ("p0_unin_users",     "Uninstalls",         "",  "",  True),
        ("total_cost",        "Spend",              "₹", "",  False),
    ], app=app)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── 7-day trend chart + source split ──
    trend_cols = ["p0_uninstall_rate", "D0_paid_users", "p0_unin_users", "total_cost"]
    trend_df   = build_trend_table(df, trend_cols)
    src        = source_split(df, "p0_uninstall_rate")

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("<div class='section-label'>7-day trend</div>", unsafe_allow_html=True)
        if not trend_df.empty:
            st.plotly_chart(
                overview_trend_chart(
                    trend_df,
                    primary_col="p0_uninstall_rate",
                    secondary_col="total_cost",
                    primary_label="P0 Uninstall Rate",
                    secondary_label="Spend",
                    primary_suffix="%",
                    secondary_prefix="₹",
                    color=app_color,
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"uninst_overview_trend_{app}",
            )
            # clean summary table below chart
            disp = trend_df[["date_tz", "p0_uninstall_rate", "D0_paid_users",
                              "p0_unin_users", "total_cost"]].copy()
            disp["date_tz"] = disp["date_tz"].astype(str)
            disp = disp.rename(columns={
                "date_tz": "Date", "p0_uninstall_rate": "P0 Rate %",
                "D0_paid_users": "D0 Orders", "p0_unin_users": "Uninstalls",
                "total_cost": "Spend (₹)",
            })
            disp["P0 Rate %"]  = disp["P0 Rate %"].round(2)
            disp["Spend (₹)"]  = disp["Spend (₹)"].round(0)
            st.dataframe(disp, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("<div class='section-label'>Source split — latest day</div>", unsafe_allow_html=True)
        if not src.empty:
            st.plotly_chart(
                source_donut(src, "p0_uninstall_rate", ""),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"uninst_overview_donut_{app}",
            )
            _overview_source_cards(src, "p0_uninstall_rate", "P0 Rate", primary_suffix="%")


def uninstall_campaigns(df: pd.DataFrame, app_color: str, app: str = ""):
    camp_df = campaign_table(df)
    if camp_df.empty:
        st.info("No data available.")
        return

    st.plotly_chart(
        campaign_bar(camp_df, "p0_uninstall_rate", app_color, "P0 Uninstall Rate by Campaign"),
        use_container_width=True,
        key=f"uninst_camp_bar_{app}",
    )

    st.plotly_chart(
        l3d_group_trend(df, "campaign", "p0_uninstall_rate",
                        title="L3D P0 Uninstall Rate — Top Campaigns",
                        metric_label="P0 Rate", suffix="%"),
        use_container_width=True,
        key=f"uninst_camp_l3d_{app}",
    )

    # clickable table
    st.subheader("Campaign Table")
    display_cols = ["campaign", "source", "D0_paid_users", "p0_unin_users",
                    "p0_uninstall_rate", "cancel_rate", "total_cost", "spend_share"]
    rename_map = {
        "campaign": "Campaign", "source": "Source",
        "D0_paid_users": "D0 Paid", "p0_unin_users": "Uninstalls",
        "p0_uninstall_rate": "P0 Rate %", "cancel_rate": "Cancel %",
        "total_cost": "Spend", "spend_share": "Spend %",
    }
    disp = camp_df[[c for c in display_cols if c in camp_df.columns]].rename(columns=rename_map)
    for num_col in ["P0 Rate %", "Cancel %", "Spend %"]:
        if num_col in disp.columns:
            disp[num_col] = disp[num_col].round(2)
    if "Spend" in disp.columns:
        disp["Spend"] = disp["Spend"].round(0)

    selected = st.dataframe(
        disp,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"uninst_camp_table_{app}",
    )
    # drill-down
    if selected and selected.get("selection", {}).get("rows"):
        row_idx = selected["selection"]["rows"][0]
        camp_name = camp_df.iloc[row_idx]["campaign"]
        st.markdown(f"**Ad Sets for:** `{camp_name}`")
        uninstall_adsets(df, app_color, app=app, campaign_filter=camp_name, context="drilldown")


def uninstall_adsets(df: pd.DataFrame, app_color: str, app: str = "",
                     campaign_filter: str | None = None, context: str = "main"):
    all_campaigns = sorted(df["campaign"].dropna().unique().tolist())
    if campaign_filter is None:
        options = ["All"] + all_campaigns
        selected_camp = st.selectbox("Filter by Campaign", options,
                                     key=f"uninst_camp_filter_{app}_{context}")
        campaign_filter = None if selected_camp == "All" else selected_camp

    ad_df = adset_table(df, campaign_filter=campaign_filter)
    if ad_df.empty:
        st.info("No ad-set data.")
        return

    display_cols = ["ad_set", "campaign", "source", "D0_paid_users", "p0_unin_users",
                    "p0_uninstall_rate", "spend_share", "cancel_rate", "exit_rate"]
    rename_map = {
        "ad_set": "Ad Set", "campaign": "Campaign", "source": "Source",
        "D0_paid_users": "D0 Paid", "p0_unin_users": "Uninstalls",
        "p0_uninstall_rate": "P0 Rate %", "spend_share": "Spend %",
        "cancel_rate": "Cancel %", "exit_rate": "Exit %",
    }
    disp = ad_df[[c for c in display_cols if c in ad_df.columns]].rename(columns=rename_map)
    for col in ["P0 Rate %", "Spend %", "Cancel %", "Exit %"]:
        if col in disp.columns:
            disp[col] = disp[col].round(2)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    filtered_df = df[df["campaign"] == campaign_filter] if campaign_filter else df
    st.plotly_chart(
        l3d_group_trend(filtered_df, "ad_set", "p0_uninstall_rate",
                        title="L3D P0 Uninstall Rate — Top Ad Sets",
                        metric_label="P0 Rate", suffix="%"),
        use_container_width=True,
        key=f"uninst_adset_l3d_{app}_{context}",
    )


def uninstall_rise(df: pd.DataFrame, app: str = ""):
    c1, c2 = st.columns([1, 2])
    with c1:
        level = st.radio("Group by", ["campaign", "ad_set"], horizontal=True,
                         key=f"uninst_rise_level_{app}")
    with c2:
        view = st.radio("View", ["Latest day", "7-day heatmap"], horizontal=True,
                        key=f"uninst_rise_view_{app}")

    if view == "Latest day":
        kit_df = kitagawa_uninstall(df, level=level)
        if kit_df.empty:
            st.info("Need at least 2 days of data for decomposition.")
            return
        d0, d1 = kit_df["d0_date"].iloc[0], kit_df["d1_date"].iloc[0]
        st.caption(f"Comparing **{d0}** (D0) vs **{d1}** (D1)")
        st.plotly_chart(
            kitagawa_waterfall(kit_df, "P0 Uninstall Rate — Kitagawa Decomposition"),
            use_container_width=True,
            key=f"uninst_rise_waterfall_{app}",
        )
        st.subheader("Decomposition Table")
        disp = kit_df[["group", "rate_d0", "rate_d1", "share_d0",
                       "rate_effect", "mix_effect", "contribution"]].copy()
        for c in ["rate_d0", "rate_d1", "rate_effect", "mix_effect", "contribution"]:
            disp[c] = disp[c].round(3)
        disp["share_d0"] = (disp["share_d0"] * 100).round(2)
        disp.columns = ["Group", "Rate D0%", "Rate D1%", "Share D0%",
                        "Rate Effect", "Mix Effect", "Contribution"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

    else:  # 7-day heatmap
        with st.spinner("Computing 7-day decomposition…"):
            pivot, detail = kitagawa_rolling_uninstall(df, level=level)
        if pivot.empty:
            st.info("Need at least 2 days of data.")
            return
        st.plotly_chart(
            kitagawa_heatmap(pivot, detail, mode="uninstall",
                             title="P0 Uninstall Rate — 7-day Kitagawa Heatmap"),
            use_container_width=True,
            key=f"uninst_rise_heatmap_{app}",
        )
        st.caption("Red = worsening (rate rising) · Green = improving · "
                   "Rows sorted by total absolute contribution")


# ════════════════════════════════════════════════════════════════════════════
#  CREATIVE TAB (Meta only, Kali for now)
# ════════════════════════════════════════════════════════════════════════════

def creative_tab(app: str, mode: str = "uninstall"):
    """
    mode: 'uninstall' or 'cac'
    Shown only for apps with creative query IDs.
    """
    if app not in CREATIVE_QUERY_IDS:
        st.info(f"Creative-level data not yet available for {app}.")
        return

    try:
        df = fetch_creative_data(app)
    except Exception as e:
        st.error(f"Could not load creative data: {e}")
        return

    if df.empty:
        st.warning("No creative data returned for the current window. "
                   "This is Meta-only data — check the Redash query date range.")
        return

    df = add_derived_metrics(df)
    st.caption("Meta only · YD / L3D / L7D · Sorted by L7D Spend")

    # ── filters ──
    f1, f2 = st.columns(2)
    with f1:
        campaigns = ["All"] + sorted(df["campaign"].dropna().unique().tolist())
        sel_camp = st.selectbox("Campaign", campaigns, key=f"creative_camp_{app}_{mode}")
        camp_filter = None if sel_camp == "All" else sel_camp
    with f2:
        adset_pool = (df[df["campaign"] == camp_filter] if camp_filter else df)
        adsets = ["All"] + sorted(adset_pool["ad_set"].dropna().unique().tolist())
        sel_adset = st.selectbox("Ad Set", adsets, key=f"creative_adset_{app}_{mode}")
        adset_filter = None if sel_adset == "All" else sel_adset

    # ── table ──
    cr_df = creative_table(df, campaign_filter=camp_filter, adset_filter=adset_filter)
    if cr_df.empty:
        st.info("No data for selected filters.")
        return

    if mode == "uninstall":
        display_cols = [
            "tag", "ad_creative", "ad_set", "campaign",
            "spend_yd", "orders_yd", "CAC_yd", "unin_yd",
            "spend_l3d", "orders_l3d", "CAC_l3d", "unin_l3d",
            "spend_l7d", "spend_share_l7d", "orders_l7d", "CAC_l7d", "unin_l7d",
            "p0_rate_yd", "p0_rate_l3d", "p0_rate_l7d",
        ]
        rename_map = {
            "tag": "Tag",
            "ad_creative": "Creative", "ad_set": "Ad Set", "campaign": "Campaign",
            "spend_yd": "Spend YD", "orders_yd": "D0 Orders YD", "CAC_yd": "D0 CAC YD", "unin_yd": "Unin YD",
            "spend_l3d": "Spend L3D", "orders_l3d": "D0 Orders L3D", "CAC_l3d": "D0 CAC L3D", "unin_l3d": "Unin L3D",
            "spend_l7d": "Spend L7D", "spend_share_l7d": "Spend %",
            "orders_l7d": "D0 Orders L7D", "CAC_l7d": "D0 CAC L7D", "unin_l7d": "Unin L7D",
            "p0_rate_yd": "P0 Rate YD", "p0_rate_l3d": "P0 Rate L3D",
            "p0_rate_l7d": "P0 Rate L7D",
        }
        round_cols = {
            "Spend YD": 0, "Spend L3D": 0, "Spend L7D": 0,
            "D0 CAC YD": 0, "D0 CAC L3D": 0, "D0 CAC L7D": 0,
            "P0 Rate YD": 2, "P0 Rate L3D": 2, "P0 Rate L7D": 2,
            "Spend %": 1,
        }
        trend_metric, trend_label, prefix, suffix = "p0_uninstall_rate", "P0 Rate", "", "%"
    else:
        display_cols = [
            "tag", "ad_creative", "ad_set", "campaign",
            "spend_yd", "orders_yd", "CAC_yd",
            "spend_l3d", "orders_l3d", "CAC_l3d",
            "spend_l7d", "spend_share_l7d", "orders_l7d", "CAC_l7d",
        ]
        rename_map = {
            "tag": "Tag",
            "ad_creative": "Creative", "ad_set": "Ad Set", "campaign": "Campaign",
            "spend_yd": "Spend YD", "orders_yd": "D0 Orders YD", "CAC_yd": "D0 CAC YD",
            "spend_l3d": "Spend L3D", "orders_l3d": "D0 Orders L3D", "CAC_l3d": "D0 CAC L3D",
            "spend_l7d": "Spend L7D", "spend_share_l7d": "Spend %",
            "orders_l7d": "D0 Orders L7D", "CAC_l7d": "D0 CAC L7D",
        }
        round_cols = {
            "Spend YD": 0, "Spend L3D": 0, "Spend L7D": 0,
            "D0 CAC YD": 0, "D0 CAC L3D": 0, "D0 CAC L7D": 0,
            "Spend %": 1,
        }
        trend_metric, trend_label, prefix, suffix = "D0_CAC_calc", "D0 CAC", "₹", ""

    disp = cr_df[[c for c in display_cols if c in cr_df.columns]].rename(columns=rename_map)
    for col, decimals in round_cols.items():
        if col in disp.columns:
            disp[col] = disp[col].round(decimals)

    st.subheader(f"Creative Performance — {sel_camp or 'All Campaigns'}")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── YD Contribution ──
    with st.expander("YD Contribution — Spend % · Orders % · Uninstall %", expanded=False):
        contrib = creative_yd_contribution(df, campaign_filter=camp_filter, adset_filter=adset_filter)
        if contrib.empty:
            st.info("No yesterday data available.")
        else:
            contrib_disp = contrib[["ad_creative", "campaign", "ad_set",
                                    "spend", "spend_pct",
                                    "orders", "orders_pct",
                                    "unin", "unin_pct",
                                    "unin_contribution"]].rename(columns={
                "ad_creative":       "Creative",
                "campaign":          "Campaign",
                "ad_set":            "Ad Set",
                "spend":             "Spend YD (₹)",
                "spend_pct":         "Spend %",
                "orders":            "D0 Orders",
                "orders_pct":        "Orders %",
                "unin":              "Uninstalls",
                "unin_pct":          "Unin % of Total",
                "unin_contribution": "Unin vs Orders Δ",
            })
            for c in ["Spend %", "Orders %", "Unin % of Total", "Unin vs Orders Δ"]:
                contrib_disp[c] = contrib_disp[c].round(1)
            contrib_disp["Spend YD (₹)"] = contrib_disp["Spend YD (₹)"].round(0)
            st.caption("Unin % of Total = creative uninstalls / all-creative uninstalls · Unin vs Orders Δ = Unin% − Orders% · 🔴 Orders% < Spend% AND Unin% > Spend% · 🟢 vice versa")

            def _highlight_risk(row):
                if (row["Orders %"] < row["Spend %"]) and (row["Unin % of Total"] > row["Spend %"]):
                    return ["background-color: #3d1515; color: #ff6b6b"] * len(row)
                if (row["Orders %"] > row["Spend %"]) and (row["Unin % of Total"] < row["Spend %"]):
                    return ["background-color: #0f2d1f; color: #4caf87"] * len(row)
                return [""] * len(row)

            st.dataframe(
                contrib_disp.style.apply(_highlight_risk, axis=1),
                use_container_width=True,
                hide_index=True,
            )

    # ── Dimension Insights ──
    DIMENSIONS = {
        "Category":      "category",
        "Gender":        "gender",
        "Creative Type": "creative_type",
        "Production":    "production",
        "Track":         "track",
        "Team":          "team",
        "Launch Month":  "launch_month",
    }
    with st.expander("Dimension Insights", expanded=False):
        dim_label = st.radio(
            "Group by",
            list(DIMENSIONS.keys()),
            horizontal=True,
            key=f"creative_pivot_dim_{app}_{mode}",
        )
        dim_col = DIMENSIONS[dim_label]
        pivot_df = creative_pivot(cr_df, dim_col)
        if not pivot_df.empty:
            st.plotly_chart(
                pivot_bar_chart(pivot_df, dim_col, color=APP_COLORS.get(app, "#7F77DD")),
                use_container_width=True,
                key=f"creative_pivot_chart_{app}_{mode}",
            )
            # summary table
            summary = pivot_df.rename(columns={
                dim_col:         dim_label,
                "n_creatives":   "Creatives",
                "total_spend":   "Spend L7D",
                "spend_share":   "Spend %",
                "total_orders":  "D0 Orders",
                "avg_cac":       "Avg D0 CAC",
                "avg_p0":        "Avg P0 Rate %",
            })
            for c, d in [("Spend L7D", 0), ("Avg D0 CAC", 0), ("Avg P0 Rate %", 2), ("Spend %", 1)]:
                if c in summary.columns:
                    summary[c] = summary[c].round(d)
            display_summary_cols = [dim_label, "Creatives", "Spend L7D", "Spend %",
                                    "D0 Orders", "Avg D0 CAC", "Avg P0 Rate %"]
            st.dataframe(
                summary[[c for c in display_summary_cols if c in summary.columns]],
                use_container_width=True,
                hide_index=True,
            )


def morning_pulse_view(df: pd.DataFrame, app: str, color: str, mode: str = "uninstall"):
    # ── date selector ──
    avail_dates = sorted(df["date_tz"].unique())[-7:]  # last 7 dates
    # only dates that have a prior day in the data
    all_dates   = sorted(df["date_tz"].unique())
    selectable  = [d for d in avail_dates if all_dates.index(d) > 0]

    date_key = f"mp_date_{app}"
    if date_key not in st.session_state or st.session_state[date_key] not in selectable:
        st.session_state[date_key] = selectable[-1] if selectable else None

    # pill-style date buttons
    hex_col = color.lstrip("#")
    r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
    pills_html = ""
    for d in reversed(selectable):
        is_sel = st.session_state[date_key] == d
        bg     = f"rgba({r},{g},{b},0.15)" if is_sel else "#111"
        border = color if is_sel else "#1e1e1e"
        fc     = color if is_sel else "#555"
        fw     = "700" if is_sel else "400"
        label  = "Today" if d == selectable[-1] else str(d)
        pills_html += (
            f"<span style='background:{bg};border:1px solid {border};border-radius:20px;"
            f"padding:4px 12px;font-size:0.72rem;color:{fc};font-weight:{fw};cursor:default'>{label}</span>"
        )

    btn_cols = st.columns(len(selectable) + 4)
    for i, d in enumerate(reversed(selectable)):
        with btn_cols[i]:
            label = "Today" if d == selectable[-1] else str(d)
            is_sel = st.session_state[date_key] == d
            if is_sel:
                st.markdown(
                    f"<div style='background:rgba({r},{g},{b},0.15);border:1px solid {color};"
                    f"border-radius:20px;padding:5px 0;text-align:center;"
                    f"font-size:0.72rem;color:{color};font-weight:700'>{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button(label, key=f"mp_date_btn_{app}_{d}", use_container_width=True):
                    st.session_state[date_key] = d
                    st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    sel_date = st.session_state[date_key]
    # filter df to dates up to sel_date so Kitagawa uses the right pair
    df_sel = df[df["date_tz"] <= sel_date]
    pulse = morning_pulse(df_sel, ref_date=sel_date)
    if not pulse:
        st.warning("Need at least 2 days of data for Morning Pulse.")
        return

    yd, d1  = pulse["yd"], pulse["d1"]
    deltas  = pulse["deltas"]
    yd_date = str(pulse["yd_date"])
    d1_date = str(pulse["d1_date"])
    is_latest = (sel_date == selectable[-1])

    # ── date badge ──
    today_lbl = "Today" if is_latest else str(yd_date)
    yday_lbl  = "Yesterday" if is_latest else str(d1_date)
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:20px'>"
        f"<div style='background:#111;border:1px solid #1e1e1e;border-radius:20px;"
        f"padding:5px 14px;font-size:0.75rem;color:#666;display:inline-flex;align-items:center;gap:6px'>"
        f"<span style='color:#555'>📅</span>"
        f"<b style='color:#ddd'>{today_lbl} ({yd_date})</b>"
        f"<span style='color:#333'>vs</span>"
        f"<span style='color:#444'>{yday_lbl} ({d1_date})</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── KPI cards ──
    d1 = pulse["d1"]

    def _kpi_card(label, today_val, yday_val, abs_delta, delta_fmt, higher_is_bad=False, base_val=None):
        is_bad  = (abs_delta > 0 and higher_is_bad) or (abs_delta < 0 and not higher_is_bad)
        d_class = "pulse-delta-bad" if is_bad else ("pulse-delta-good" if abs_delta != 0 else "pulse-delta-neu")
        arrow   = "▲" if abs_delta > 0 else ("▼" if abs_delta < 0 else "—")
        c_class = "pulse-card-red" if is_bad else ("pulse-card-green" if not is_bad and abs_delta != 0 else "pulse-card-grey")
        sign    = "+" if abs_delta > 0 else ""
        delta_str = f"{arrow} {sign}{delta_fmt(abs(abs_delta))}"
        pct_str = ""
        if base_val and base_val != 0 and abs_delta != 0:
            pct = abs_delta / abs(base_val) * 100
            pct_str = f"<span class='pulse-pct'>{'+' if pct>0 else ''}{pct:.1f}%</span>"
        return (
            f"<div class='pulse-card {c_class}'>"
            f"<div class='pulse-label'>{label}</div>"
            f"<div class='pulse-value'>{today_val}</div>"
            f"<div class='pulse-yday'>yday {yday_val}</div>"
            f"<div class='pulse-delta-row'><div class='{d_class}'>{delta_str}</div>{pct_str}</div>"
            f"</div>"
        )

    cols = st.columns(5)
    cards = [
        ("Spend",          f"₹{yd['spend']:,.0f}",            f"₹{d1['spend']:,.0f}",
         yd['spend'] - d1['spend'],              lambda v: f"₹{v:,.0f}",     False,  d1['spend']),
        ("D0 Orders",      f"{yd['orders']:,.0f}",             f"{d1['orders']:,.0f}",
         yd['orders'] - d1['orders'],            lambda v: f"{v:,.0f}",      False,  d1['orders']),
        ("D0 CAC",         f"₹{yd['cac']:,.0f}",              f"₹{d1['cac']:,.0f}",
         yd['cac'] - d1['cac'],                  lambda v: f"₹{v:.0f}",      True,   d1['cac']),
        ("Uninstall %",    f"{yd['unin_rate']:.1f}%",         f"{d1['unin_rate']:.1f}%",
         yd['unin_rate'] - d1['unin_rate'],      lambda v: f"{v:.1f}pp",     True,   d1['unin_rate']),
        ("Cancel %",       f"{yd.get('cancel_rate',0):.1f}%", f"{d1.get('cancel_rate',0):.1f}%",
         yd.get('cancel_rate',0)-d1.get('cancel_rate',0), lambda v: f"{v:.1f}pp", True, d1.get('cancel_rate',0)),
    ]
    for col, (label, today_val, yday_val, abs_delta, delta_fmt, hib, base_val) in zip(cols, cards):
        with col:
            st.markdown(_kpi_card(label, today_val, yday_val, abs_delta, delta_fmt, hib, base_val), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── alerts ──
    if pulse["alerts"]:
        pills_html = ""
        for emoji, msg in pulse["alerts"]:
            cls = "alert-pill-red" if emoji == "🔴" else ("alert-pill-green" if emoji == "🟢" else "alert-pill-yellow")
            pills_html += f"<span class='alert-pill {cls}'>{emoji} {msg}</span>"
        st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px'>{pills_html}</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='margin-bottom:16px'><span class='alert-pill alert-pill-green'>🟢 All metrics within normal range</span></div>",
            unsafe_allow_html=True,
        )

    # ── 7-day daily breakdown table ──
    dates_all = sorted(df["date_tz"].unique())[-7:]
    rows_html = ""
    prev_cac   = None
    prev_unin  = None
    prev_spend = None
    for i, dt in enumerate(dates_all):
        d_df    = df[df["date_tz"] == dt]
        sp      = d_df["total_cost"].sum()
        orders  = d_df["D0_paid_users"].sum()
        cac     = sp / orders if orders > 0 else 0
        unin    = d_df["p0_unin_users"].sum()
        unin_rt = unin / orders * 100 if orders > 0 else 0
        is_today = (dt == sel_date)
        is_yday  = (dt == pulse["d1_date"])
        row_bg  = "#181824" if is_today else ("#111" if is_yday else "transparent")
        date_lbl = f"<b style='color:#ddd'>{dt}</b>" if is_today else f"<span style='color:#555'>{dt}</span>"

        def _delta_cell(now, prev, fmt, higher_is_bad=True):
            if prev is None or prev == 0:
                return "<td style='text-align:right;padding:5px 10px;color:#333'>—</td>"
            diff = now - prev
            is_bad = (diff > 0 and higher_is_bad) or (diff < 0 and not higher_is_bad)
            col = "#E24B4A" if is_bad else "#1D9E75"
            arrow = "▲" if diff > 0 else "▼"
            return f"<td style='text-align:right;padding:5px 10px;font-size:0.68rem;color:{col}'>{arrow}{fmt(abs(diff))}</td>"

        cac_delta_cell  = _delta_cell(cac,     prev_cac,   lambda v: f"₹{v:.0f}",  True)
        unin_delta_cell = _delta_cell(unin_rt, prev_unin,  lambda v: f"{v:.1f}pp", True)
        spend_delta_cell= _delta_cell(sp,      prev_spend, lambda v: f"₹{v:,.0f}", False)

        rows_html += (
            f"<tr style='background:{row_bg};border-bottom:1px solid #111'>"
            f"<td style='padding:5px 10px;font-size:0.75rem;white-space:nowrap'>{date_lbl}</td>"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#ccc'>₹{sp:,.0f}</td>"
            f"{spend_delta_cell}"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#ccc'>{orders:,.0f}</td>"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#ccc'>₹{cac:,.0f}</td>"
            f"{cac_delta_cell}"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#ccc'>{unin_rt:.1f}%</td>"
            f"{unin_delta_cell}"
            f"</tr>"
        )
        prev_cac   = cac
        prev_unin  = unin_rt
        prev_spend = sp

    th = "style='text-align:right;padding:5px 10px;font-size:0.65rem;color:#333;font-weight:600;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #1e1e1e'"
    thl = "style='padding:5px 10px;font-size:0.65rem;color:#333;font-weight:600;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #1e1e1e'"
    st.markdown(
        f"<div style='margin-bottom:20px;overflow-x:auto'>"
        f"<table style='width:100%;border-collapse:collapse'>"
        f"<thead><tr>"
        f"<th {thl}>Date</th>"
        f"<th {th}>Spend</th><th {th}>Δ</th>"
        f"<th {th}>Orders</th>"
        f"<th {th}>CAC</th><th {th}>Δ</th>"
        f"<th {th}>Unin%</th><th {th}>Δ</th>"
        f"</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-hdr'><div class='section-hdr-line'></div><div class='section-hdr-text'>Campaign Contributors</div><div class='section-hdr-line'></div></div>", unsafe_allow_html=True)

    # ── Top Contributors (Kitagawa) — always show both CAC + Uninstall ──
    kit_cac   = kitagawa_cac(df_sel,       level="campaign")
    kit_unin  = kitagawa_uninstall(df_sel, level="campaign")

    def _kit_card(row, accent, is_cac):
        contrib  = row["contribution"]
        rate_eff = row["rate_effect"]
        mix_eff  = row["mix_effect"]
        rate_d0  = row.get("cac_d0", row.get("rate_d0", 0))
        c_col    = "#E24B4A" if contrib > 0 else "#1D9E75"
        re_col   = "#E24B4A" if rate_eff > 0 else "#1D9E75"
        me_col   = "#E24B4A" if mix_eff  > 0 else "#1D9E75"
        c_arrow  = "▲" if contrib > 0 else "▼"
        re_arrow = "▲" if rate_eff > 0 else "▼"
        me_arrow = "▲" if mix_eff  > 0 else "▼"
        if is_cac:
            rate_str    = f"₹{rate_d0:,.0f}"
            contrib_str = f"{c_arrow} ₹{abs(contrib):.0f}"
            re_str      = f"₹{abs(rate_eff):.0f}"
            me_str      = f"₹{abs(mix_eff):.0f}"
            rate_lbl    = "CAC Today"
        else:
            rate_str    = f"{rate_d0:.1f}%"
            contrib_str = f"{c_arrow} {abs(contrib):.2f}pp"
            re_str      = f"{abs(rate_eff):.2f}pp"
            me_str      = f"{abs(mix_eff):.2f}pp"
            rate_lbl    = "P0 Rate Today"
        name = row['group']
        short = name[:52] + "…" if len(name) > 52 else name
        return f"""
        <div class="contrib-card" style="border-left:3px solid {accent}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
            <div style="flex:1;min-width:0">
              <div style="font-size:0.84rem;font-weight:600;color:#ddd;margin-bottom:6px;line-height:1.3">{short}</div>
              <div style="display:flex;gap:5px;flex-wrap:wrap">
                <span class="contrib-tag" style="color:{re_col}">Rate&nbsp;{re_arrow}&nbsp;{re_str}</span>
                <span class="contrib-tag" style="color:{me_col}">Mix&nbsp;{me_arrow}&nbsp;{me_str}</span>
              </div>
            </div>
            <div style="text-align:right;flex-shrink:0;min-width:70px">
              <div style="font-size:0.62rem;color:#444;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px">{rate_lbl}</div>
              <div style="font-size:0.88rem;color:#888;margin-bottom:4px">{rate_str}</div>
              <div style="font-size:1.05rem;font-weight:700;color:{c_col};letter-spacing:-.01em">{contrib_str}</div>
            </div>
          </div>
        </div>"""

    def _render_kit_col(kit_df, is_cac):
        if kit_df.empty:
            st.markdown("<div style='color:#444;font-size:0.82rem;padding:8px'>No data</div>", unsafe_allow_html=True)
            return
        worsened = kit_df[kit_df["contribution"] > 0].head(3)
        improved = kit_df[kit_df["contribution"] < 0].tail(2)
        st.markdown("<div style='font-size:0.72rem;color:#E24B4A;font-weight:600;margin-bottom:5px;letter-spacing:.06em;text-transform:uppercase'>↑ Worsened</div>", unsafe_allow_html=True)
        if worsened.empty:
            st.markdown("<div style='color:#333;font-size:0.8rem;margin-bottom:8px'>—</div>", unsafe_allow_html=True)
        for _, row in worsened.iterrows():
            st.markdown(_kit_card(row, "#E24B4A", is_cac), unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.72rem;color:#1D9E75;font-weight:600;margin:10px 0 5px;letter-spacing:.06em;text-transform:uppercase'>↓ Improved</div>", unsafe_allow_html=True)
        if improved.empty:
            st.markdown("<div style='color:#333;font-size:0.8rem'>—</div>", unsafe_allow_html=True)
        for _, row in improved.sort_values("contribution").iterrows():
            st.markdown(_kit_card(row, "#1D9E75", is_cac), unsafe_allow_html=True)

    # date label from whichever is available
    ref_df  = kit_cac if not kit_cac.empty else kit_unin
    if not ref_df.empty:
        kit_d0 = str(ref_df["d0_date"].iloc[0])
        kit_d1 = str(ref_df["d1_date"].iloc[0])
        st.markdown(
            f"<div class='section-label'>Campaign contributors &nbsp;·&nbsp; {kit_d1} → {kit_d0}</div>",
            unsafe_allow_html=True,
        )
        col_cac, col_unin = st.columns(2)
        with col_cac:
            st.markdown("<div style='font-size:0.8rem;color:#aaa;font-weight:600;margin-bottom:8px'>💰 CAC Rise</div>", unsafe_allow_html=True)
            _render_kit_col(kit_cac, is_cac=True)
        with col_unin:
            st.markdown("<div style='font-size:0.8rem;color:#aaa;font-weight:600;margin-bottom:8px'>📉 Uninstall Rise</div>", unsafe_allow_html=True)
            _render_kit_col(kit_unin, is_cac=False)
    else:
        st.info("Need at least 2 days of data.")

    # camps for drill-down fallback
    camps = pulse["campaigns"].copy()
    camps = camps[camps["spend_yd"] > 0]
    # kit_df used by drill-down level 1 list — use CAC as primary ordering
    kit_df = kit_cac if not kit_cac.empty else kit_unin

    # ── Drill-down ──
    st.markdown("<div class='section-hdr'><div class='section-hdr-line'></div><div class='section-hdr-text'>Drill Down — Campaign → Ad Set → Creative</div><div class='section-hdr-line'></div></div>", unsafe_allow_html=True)

    def _trend_chart(filter_df, label: str, *, n_days: int = 14):
        """Render a compact CAC + uninstall-rate dual-line chart inside a popover."""
        if filter_df is None or filter_df.empty or "date_tz" not in filter_df.columns:
            st.caption("No trend data"); return
        daily = (filter_df.groupby("date_tz")
                 .agg(spend=("total_cost","sum"),
                      orders=("D0_paid_users","sum"),
                      unin=("p0_unin_users","sum"))
                 .reset_index().sort_values("date_tz").tail(n_days))
        daily["cac"]      = daily["spend"]  / daily["orders"].clip(lower=1)
        daily["unin_rate"]= daily["unin"]   / daily["orders"].clip(lower=1) * 100
        st.caption(f"**{label[:60]}** — last {len(daily)}d")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["date_tz"].astype(str), y=daily["cac"],
            name="CAC (₹)", line=dict(color="#E24B4A", width=2),
            hovertemplate="%{x}<br>CAC ₹%{y:.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=daily["date_tz"].astype(str), y=daily["unin_rate"],
            name="Unin%", line=dict(color="#378ADD", width=2, dash="dot"),
            yaxis="y2",
            hovertemplate="%{x}<br>Unin %{y:.1f}%<extra></extra>"))
        fig.update_layout(
            height=220, margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d",
            font=dict(color="#666", size=10),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=9)),
            xaxis=dict(showgrid=False, tickfont=dict(size=8), tickangle=-30),
            yaxis=dict(title="CAC ₹", showgrid=True, gridcolor="#151515",
                       tickfont=dict(size=8), tickprefix="₹"),
            yaxis2=dict(title="Unin%", overlaying="y", side="right",
                        showgrid=False, tickfont=dict(size=8), ticksuffix="%"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # session state keys
    camp_key  = f"dd_camp_{app}_{mode}"
    adset_key = f"dd_adset_{app}_{mode}"
    if camp_key  not in st.session_state: st.session_state[camp_key]  = None
    if adset_key not in st.session_state: st.session_state[adset_key] = None

    sel_camp  = st.session_state[camp_key]
    sel_adset = st.session_state[adset_key]

    # Overall app-level Kitagawa at ad_set level (contribution to total app delta)
    kit_adset_cac  = kitagawa_cac(df_sel,       level="ad_set")
    kit_adset_unin = kitagawa_uninstall(df_sel, level="ad_set")
    adset_cac_map  = {r["group"]: r for _, r in kit_adset_cac.iterrows()}  if not kit_adset_cac.empty  else {}
    adset_unin_map = {r["group"]: r for _, r in kit_adset_unin.iterrows()} if not kit_adset_unin.empty else {}

    # adset display list for selected campaign
    adset_contrib = diagnose_contribution(df_sel, "ad_set", campaign_filter=sel_camp) if sel_camp else None

    # Overall app-level Kitagawa at creative level + creative data
    cr_raw = None
    cr_sel = None
    kit_cr_cac_map  = {}
    kit_cr_unin_map = {}
    if app in CREATIVE_QUERY_IDS:
        try:
            cr_raw = add_derived_metrics(fetch_creative_data(app))
            cr_sel = cr_raw[cr_raw["date_tz"] <= sel_date] if "date_tz" in cr_raw.columns else cr_raw
            kit_cr_cac  = kitagawa_cac(cr_sel,       level="ad_creative")
            kit_cr_unin = kitagawa_uninstall(cr_sel, level="ad_creative")
            kit_cr_cac_map  = {r["group"]: r for _, r in kit_cr_cac.iterrows()}  if not kit_cr_cac.empty  else {}
            kit_cr_unin_map = {r["group"]: r for _, r in kit_cr_unin.iterrows()} if not kit_cr_unin.empty else {}
        except Exception:
            cr_raw = None
            cr_sel = None

    def _contrib_pill(val, fmt_fn, good_is_negative=True):
        """Render a small contribution pill: red if worsening, green if improving."""
        if val == 0:
            return ""
        is_bad = (val > 0 and good_is_negative) or (val < 0 and not good_is_negative)
        col    = "#E24B4A" if is_bad else "#1D9E75"
        arrow  = "▲" if val > 0 else "▼"
        return (f"<span style='font-size:0.68rem;font-weight:700;color:{col};"
                f"background:rgba({'226,75,74' if is_bad else '29,158,117'},.1);"
                f"border-radius:8px;padding:2px 7px;margin-left:4px'>{arrow}{fmt_fn(abs(val))}</span>")

    def _creative_card(cr_name, cr_spend, cr_orders, cr_unin, sig,
                       cac_contrib=None, unin_contrib=None):
        cac      = cr_spend / cr_orders if cr_orders > 0 else None
        unin_rt  = cr_unin  / cr_orders * 100 if cr_orders > 0 else None
        b_col    = "#E24B4A" if sig == "🔴 High Risk" else ("#1D9E75" if sig == "🟢 Efficient" else "#2a2a2a")
        cac_str  = f"₹{cac:,.0f}" if cac is not None else "—"
        unin_str = f"{unin_rt:.1f}%" if unin_rt is not None else "—"
        contrib_html = ""
        if cac_contrib is not None:
            contrib_html += _contrib_pill(cac_contrib, lambda v: f"₹{v:.0f}", good_is_negative=True)
        if unin_contrib is not None:
            contrib_html += _contrib_pill(unin_contrib, lambda v: f"{v:.2f}pp", good_is_negative=True)
        cac_col  = 'E24B4A' if cac and cac > 500 else 'aaa'
        unin_col = 'E24B4A' if unin_rt and unin_rt > 30 else 'aaa'
        return (
            f"<div style='background:#0f0f0f;border:1px solid #1e1e1e;border-left:3px solid {b_col};"
            f"border-radius:9px;padding:9px 14px;margin-bottom:4px'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:4px'>"
            f"<span style='font-size:0.68rem;color:#444'>{sig}</span>"
            f"{contrib_html}"
            f"</div>"
            f"<div style='font-size:0.82rem;font-weight:600;color:#ccc;white-space:nowrap;"
            f"overflow:hidden;text-overflow:ellipsis;margin-bottom:6px'>{cr_name[:70]}</div>"
            f"<div style='display:flex;gap:6px;flex-wrap:wrap'>"
            f"<span style='font-size:0.7rem;background:#181818;padding:2px 8px;border-radius:10px;color:#aaa'>₹{cr_spend:,.0f} spend</span>"
            f"<span style='font-size:0.7rem;background:#181818;padding:2px 8px;border-radius:10px;color:#aaa'>{int(cr_orders)} orders</span>"
            f"<span style='font-size:0.7rem;background:#181818;padding:2px 8px;border-radius:10px;color:#aaa'>{int(cr_unin)} unin</span>"
            f"<span style='font-size:0.7rem;background:#181818;padding:2px 8px;border-radius:10px;color:#{cac_col}'>{cac_str} CAC</span>"
            f"<span style='font-size:0.7rem;background:#181818;padding:2px 8px;border-radius:10px;color:#{unin_col}'>{unin_str} unin%</span>"
            f"</div></div>"
        )

    # ── inline file-tree — sorted by YD spend descending ──
    if not camps.empty:
        camps_sorted = camps.sort_values("spend_yd", ascending=False)
        all_camps = camps_sorted["campaign"].tolist()
    else:
        all_camps = kit_df["group"].tolist() if not kit_df.empty else []

    # build campaign → source lookup
    camp_source_map: dict[str, str] = {}
    if "campaign" in df_sel.columns and "source" in df_sel.columns:
        for c_name, grp in df_sel.groupby("campaign")["source"]:
            sources = grp.dropna().unique().tolist()
            camp_source_map[c_name] = " · ".join(str(s) for s in sources if s)

    # build campaign-level Kitagawa maps (kit_cac/kit_unin already computed above)
    camp_cac_map  = {r["group"]: r for _, r in kit_cac.iterrows()}  if not kit_cac.empty  else {}
    camp_unin_map = {r["group"]: r for _, r in kit_unin.iterrows()} if not kit_unin.empty else {}

    # creative concentration: how many creatives = 90% of spend per campaign / adset
    def _conc90(cr_df, group_col):
        """Returns {group: n_creatives_for_90pct_spend}"""
        if cr_df is None or cr_df.empty or group_col not in cr_df.columns:
            return {}
        result = {}
        yd_cr = cr_df[cr_df["date_tz"] == sel_date] if "date_tz" in cr_df.columns else cr_df
        for grp, gdf in yd_cr.groupby(group_col):
            spend_by_cr = gdf.groupby("ad_creative")["total_cost"].sum().sort_values(ascending=False)
            total = spend_by_cr.sum()
            if total == 0:
                result[grp] = 0
                continue
            cumsum = spend_by_cr.cumsum()
            result[grp] = int((cumsum < total * 0.9).sum()) + 1
        return result

    camp_conc  = _conc90(cr_sel, "campaign") if cr_sel is not None else {}
    adset_conc = _conc90(cr_sel, "ad_set")   if cr_sel is not None else {}

    # build camp metrics lookup from pulse campaigns df
    camps_metrics = {}
    if not camps.empty:
        for _, crow in camps.iterrows():
            camps_metrics[crow["campaign"]] = crow

    # ── table header ──
    _TH = "font-size:0.58rem;text-transform:uppercase;letter-spacing:0.08em;color:#444;padding:5px 0 5px 0;border-bottom:1px solid #1a1a1a;"
    h0, h1, h2, h3, h4, h5, h6 = st.columns([5, 1.6, 1.1, 1.2, 1.2, 1.6, 0.7])
    with h0: st.markdown(f"<div style='{_TH}'>Campaign</div>", unsafe_allow_html=True)
    with h1: st.markdown(f"<div style='{_TH};text-align:right'>Spend</div>", unsafe_allow_html=True)
    with h2: st.markdown(f"<div style='{_TH};text-align:right'>Orders</div>", unsafe_allow_html=True)
    with h3: st.markdown(f"<div style='{_TH};text-align:right'>CAC</div>", unsafe_allow_html=True)
    with h4: st.markdown(f"<div style='{_TH};text-align:right'>Unin%</div>", unsafe_allow_html=True)
    with h5: st.markdown(f"<div style='{_TH};text-align:right'>DoD CAC · Unin</div>", unsafe_allow_html=True)
    with h6: st.markdown(f"<div style='{_TH}'></div>", unsafe_allow_html=True)

    for ci, camp_name in enumerate(all_camps):
        is_open  = sel_camp == camp_name
        row_bg   = f"color-mix(in srgb, {color} 6%, transparent)" if is_open else "transparent"
        _TD      = f"font-size:0.78rem;color:#bbb;padding:8px 0;border-bottom:1px solid #111;background:{row_bg};"

        # source dot + badge
        src_str   = camp_source_map.get(camp_name, "")
        src_lower = src_str.lower()
        if "facebook" in src_lower or "meta" in src_lower:
            dot_col = "#378ADD"
        elif "google" in src_lower:
            dot_col = "#34A853"
        elif "snap" in src_lower:
            dot_col = "#F5A623"
        else:
            dot_col = "#555"
        src_badge = (f"<span class='src-badge'>{src_str}</span>") if src_str else ""

        # metrics
        cm       = camps_metrics.get(camp_name)
        spend_str  = f"₹{cm['spend_yd']:,.0f}"  if cm is not None and pd.notna(cm.get('spend_yd',  None)) else "—"
        orders_str = f"{int(cm['orders_yd']):,}" if cm is not None and pd.notna(cm.get('orders_yd', None)) else "—"
        cac_val    = cm.get('cac_yd')            if cm is not None else None
        unin_val   = cm.get('unin_rate_yd')      if cm is not None else None
        cac_str    = f"₹{cac_val:,.0f}"          if cac_val  is not None and pd.notna(cac_val)  else "—"
        unin_str   = f"{unin_val:.1f}%"          if unin_val is not None and pd.notna(unin_val) else "—"
        cac_col    = "#E24B4A" if cac_val  is not None and pd.notna(cac_val)  and cac_val  > 500 else "#999"
        unin_col   = "#E24B4A" if unin_val is not None and pd.notna(unin_val) and unin_val > 25  else "#999"

        # DoD pills — CAC contribution + unin contribution
        c_cac_row  = camp_cac_map.get(camp_name)
        c_unin_row = camp_unin_map.get(camp_name)
        if c_cac_row is not None and c_cac_row["contribution"] != 0:
            cv = c_cac_row["contribution"]
            dod_cac = f"<span class='{'dod-pill-bad' if cv>0 else 'dod-pill-good'}'>{'▲' if cv>0 else '▼'}₹{abs(cv):.0f}</span>"
        else:
            dod_cac = "<span class='dod-pill-neu'>—</span>"
        if c_unin_row is not None and c_unin_row["contribution"] != 0:
            uv = c_unin_row["contribution"]
            dod_unin = f"<span class='{'dod-pill-bad' if uv>0 else 'dod-pill-good'}'>{'▲' if uv>0 else '▼'}{abs(uv):.2f}pp</span>"
        else:
            dod_unin = ""
        dod_html = f"<div style='display:flex;flex-direction:column;align-items:flex-end;gap:2px'>{dod_cac}{dod_unin}</div>"

        # conc badge (small, appended after name)
        conc_n = camp_conc.get(camp_name)
        conc_badge = (f"<span style='font-size:0.58rem;background:#161616;border:1px solid #1e1e1e;"
                      f"border-radius:4px;padding:1px 5px;color:#444;flex-shrink:0'>{conc_n}cr·90%</span>"
                      ) if conc_n is not None else ""

        camp_display = (camp_name[:38] + "…") if len(camp_name) > 39 else camp_name

        r0, r1, r2, r3, r4, r5, r6 = st.columns([5, 1.6, 1.1, 1.2, 1.2, 1.6, 0.55])
        with r0:
            # dot + badges rendered before button; button = click-to-expand
            prefix_html = (
                f"<div style='display:flex;align-items:center;gap:6px;pointer-events:none;"
                f"position:absolute;left:6px;top:50%;transform:translateY(-50%);z-index:0'>"
                f"<span class='src-dot' style='background:{dot_col}'></span>"
                f"{src_badge}{conc_badge}"
                f"</div>")
            st.markdown(
                f"<div style='position:relative;border-bottom:1px solid #111;background:{row_bg}'>",
                unsafe_allow_html=True)
            st.markdown("<div class='camp-name-btn'>", unsafe_allow_html=True)
            if st.button(camp_display, key=f"dd_btn_camp_{app}_{mode}_{ci}",
                         use_container_width=True, help=camp_name):
                st.session_state[camp_key]  = None if is_open else camp_name
                st.session_state[adset_key] = None
                st.rerun()
            st.markdown("</div></div>", unsafe_allow_html=True)
        with r1:
            st.markdown(f"<div style='{_TD};text-align:right'>{spend_str}</div>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"<div style='{_TD};text-align:right'>{orders_str}</div>", unsafe_allow_html=True)
        with r3:
            st.markdown(f"<div style='{_TD};text-align:right;color:{cac_col}'>{cac_str}</div>", unsafe_allow_html=True)
        with r4:
            st.markdown(f"<div style='{_TD};text-align:right;color:{unin_col}'>{unin_str}</div>", unsafe_allow_html=True)
        with r5:
            st.markdown(f"<div style='{_TD};text-align:right'>{dod_html}</div>", unsafe_allow_html=True)
        with r6:
            st.markdown("<div class='chart-pop-btn'>", unsafe_allow_html=True)
            with st.popover("📈", use_container_width=True):
                camp_df = df_sel[df_sel["campaign"] == camp_name] if "campaign" in df_sel.columns else pd.DataFrame()
                _trend_chart(camp_df, camp_name)
            st.markdown("</div>", unsafe_allow_html=True)

        # inline ad sets immediately below the selected campaign
        if is_open and adset_contrib is not None:
            with st.container():
                if adset_contrib.empty:
                    st.markdown("<div style='color:#444;font-size:0.8rem;padding:8px 0 8px 12px'>No ad set data</div>", unsafe_allow_html=True)
                for ai, (_, arow) in enumerate(adset_contrib.iterrows()):
                    aname    = arow["ad_set"]
                    is_aopen = sel_adset == aname
                    sig      = arow["signal"]
                    b_col    = "#E24B4A" if sig == "🔴 High Risk" else ("#1D9E75" if sig == "🟢 Efficient" else "#555")

                    # Kitagawa contribution for this adset
                    cac_row  = adset_cac_map.get(aname)
                    unin_row = adset_unin_map.get(aname)
                    a_conc_n = adset_conc.get(aname)

                    # adset DoD pill
                    if cac_row is not None and cac_row["contribution"] != 0:
                        acv = cac_row["contribution"]
                        adod_cls  = "dod-pill-bad" if acv > 0 else "dod-pill-good"
                        adod_html = f"<span class='{adod_cls}'>{'▲' if acv > 0 else '▼'}₹{abs(acv):.0f}</span>"
                    else:
                        adod_html = "<span class='dod-pill-neu'>—</span>"

                    _ATD = (f"font-size:0.75rem;color:#999;padding:7px 0 7px 16px;"
                            f"border-bottom:1px solid #0e0e0e;border-left:2px solid {b_col};"
                            f"background:{'#0d0d18' if is_aopen else '#080808'};")
                    a_conc_badge = (
                        f"<span style='font-size:0.58rem;background:#161616;border:1px solid #1e1e1e;"
                        f"border-radius:4px;padding:1px 5px;color:#444;flex-shrink:0'>{a_conc_n}cr·90%</span>"
                    ) if a_conc_n is not None else ""
                    if unin_row is not None and unin_row["contribution"] != 0:
                        _uv = unin_row["contribution"]
                        _uc = "#E24B4A" if _uv > 0 else "#1D9E75"
                        _ubg = "226,75,74" if _uv > 0 else "29,158,117"
                        _uarrow = "▲" if _uv > 0 else "▼"
                        _uval = f"{abs(_uv):.2f}pp unin"
                        unin_pill = (f"<span style='font-size:0.68rem;font-weight:700;color:{_uc};"
                                     f"background:rgba({_ubg},.12);border-radius:8px;padding:1px 6px'>"
                                     f"{_uarrow}{_uval}</span>")
                    else:
                        unin_pill = ""

                    _a_spend  = f"{arow['spend_pct']:.1f}%"  if pd.notna(arow.get('spend_pct'))  else "—"
                    _a_orders = f"{arow['orders_pct']:.1f}%" if pd.notna(arow.get('orders_pct')) else "—"
                    _a_unin   = f"{arow['unin_pct']:.1f}%"  if pd.notna(arow.get('unin_pct'))   else "—"
                    _a_unin_col = "#E24B4A" if (pd.notna(arow.get('unin_pct')) and pd.notna(arow.get('orders_pct'))
                                                and arow['unin_pct'] > arow['orders_pct'] + 5) else "#999"

                    a0, a1, a2, a3, a4, a5, a6 = st.columns([5, 1.6, 1.1, 1.2, 1.2, 1.6, 0.55])
                    with a0:
                        aname_disp = (aname[:38] + "…") if len(aname) > 39 else aname
                        sig_badge = (f"<span style='font-size:0.6rem;padding:1px 5px;border-radius:4px;"
                                     f"background:{b_col}22;color:{b_col};pointer-events:none'>{sig.split()[0]}</span>")
                        st.markdown(
                            f"<div style='position:relative;border-bottom:1px solid #0e0e0e;"
                            f"border-left:2px solid {b_col};background:{'#0d0d18' if is_aopen else '#080808'}'>"
                            f"<div style='padding:2px 0 2px 8px'>{sig_badge} {a_conc_badge}</div>",
                            unsafe_allow_html=True)
                        st.markdown("<div class='adset-name-btn'>", unsafe_allow_html=True)
                        if app in CREATIVE_QUERY_IDS:
                            if st.button(aname_disp, key=f"dd_btn_adset_{app}_{mode}_{ci}_{ai}",
                                         use_container_width=True, help=aname):
                                st.session_state[adset_key] = None if is_aopen else aname
                                st.rerun()
                        else:
                            st.markdown(f"<div style='font-size:0.78rem;color:#aaa;padding:4px 4px'>{aname_disp}</div>",
                                        unsafe_allow_html=True)
                        st.markdown("</div></div>", unsafe_allow_html=True)
                    with a1:
                        st.markdown(f"<div style='{_ATD};text-align:right'>{_a_spend}</div>", unsafe_allow_html=True)
                    with a2:
                        st.markdown(f"<div style='{_ATD};text-align:right'>{_a_orders}</div>", unsafe_allow_html=True)
                    with a3:
                        st.markdown(f"<div style='{_ATD};text-align:right'>—</div>", unsafe_allow_html=True)
                    with a4:
                        st.markdown(f"<div style='{_ATD};text-align:right;color:{_a_unin_col}'>{_a_unin}</div>", unsafe_allow_html=True)
                    with a5:
                        st.markdown(f"<div style='{_ATD};text-align:right'>{adod_html} {unin_pill}</div>", unsafe_allow_html=True)
                    with a6:
                        st.markdown("<div class='chart-pop-btn'>", unsafe_allow_html=True)
                        with st.popover("📈", use_container_width=True):
                            adset_df = (df_sel[(df_sel.get("campaign", pd.Series()) == sel_camp) &
                                               (df_sel.get("ad_set", pd.Series()) == aname)]
                                        if "ad_set" in df_sel.columns else pd.DataFrame())
                            _trend_chart(adset_df, aname)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # inline creatives immediately below the selected ad set
                    if is_aopen and cr_sel is not None:
                        cr_abs = creative_yd_contribution(cr_sel, campaign_filter=sel_camp, adset_filter=aname)
                        st.markdown("<div style='padding-left:16px;border-left:2px solid #1a1a1a;margin-left:6px;margin-bottom:3px'>", unsafe_allow_html=True)
                        if cr_abs.empty:
                            st.markdown("<div style='color:#333;font-size:0.78rem;padding:4px'>No creative data</div>", unsafe_allow_html=True)
                        else:
                            for _, crow in cr_abs.iterrows():
                                # compute signal inline
                                if crow["orders_pct"] < crow["spend_pct"] and crow["unin_pct"] > crow["spend_pct"]:
                                    sig = "🔴 High Risk"
                                elif crow["orders_pct"] > crow["spend_pct"] and crow["unin_pct"] < crow["spend_pct"]:
                                    sig = "🟢 Efficient"
                                else:
                                    sig = "⚪ Neutral"
                                cr_name = crow["ad_creative"]
                                cac_c  = kit_cr_cac_map.get(cr_name, {}).get("contribution")
                                unin_c = kit_cr_unin_map.get(cr_name, {}).get("contribution")
                                st.markdown(_creative_card(
                                    cr_name,
                                    crow["spend"], crow["orders"], crow["unin"],
                                    sig,
                                    cac_contrib=cac_c,
                                    unin_contrib=unin_c,
                                ), unsafe_allow_html=True)



def diagnose_tab(df: pd.DataFrame, app: str, mode: str = "uninstall"):
    """
    Top-down drill-down: Source → Campaign → Ad Set → Creative.
    Each level shows spend% / orders% / unin% of YD totals with signal coloring.
    """
    has_creative = app in CREATIVE_QUERY_IDS

    def _render_table(contrib_df, key_suffix):
        if contrib_df.empty:
            st.info("No data for yesterday.")
            return

        cols_order = [c for c in [contrib_df.columns[0], "signal", "spend", "spend_pct",
                                   "orders", "orders_pct", "unin", "unin_pct", "unin_delta"]
                      if c in contrib_df.columns]
        disp = contrib_df[cols_order].copy()
        rename = {
            contrib_df.columns[0]: contrib_df.columns[0].replace("_", " ").title(),
            "signal": "Signal", "spend": "Spend YD",
            "spend_pct": "Spend %", "orders": "D0 Orders",
            "orders_pct": "Orders %", "unin": "Uninstalls",
            "unin_pct": "Unin % of Total", "unin_delta": "Unin vs Orders Δ",
        }
        disp = disp.rename(columns=rename)
        for c in ["Spend %", "Orders %", "Unin % of Total", "Unin vs Orders Δ"]:
            if c in disp.columns:
                disp[c] = disp[c].round(1)
        if "Spend YD" in disp.columns:
            disp["Spend YD"] = disp["Spend YD"].round(0)

        def _hl(row):
            if row.get("Signal") == "🔴 High Risk":
                return ["background-color:#3d1515; color:#ff6b6b"] * len(row)
            if row.get("Signal") == "🟢 Efficient":
                return ["background-color:#0f2d1f; color:#4caf87"] * len(row)
            return [""] * len(row)

        st.dataframe(disp.style.apply(_hl, axis=1),
                     use_container_width=True, hide_index=True,
                     key=f"diagnose_{key_suffix}")

    # ── Step 1: Source ──
    st.markdown("#### Step 1 — Source")
    if "source" in df.columns:
        src = diagnose_contribution(df, "source")
        _render_table(src, f"src_{app}_{mode}")
    else:
        st.info("No source column available.")

    st.markdown("---")

    # ── Step 2: Campaign ──
    st.markdown("#### Step 2 — Campaign")
    camp_contrib = diagnose_contribution(df, "campaign")
    _render_table(camp_contrib, f"camp_{app}_{mode}")

    campaigns = ["All"] + sorted(df["campaign"].dropna().unique().tolist())
    sel_camp = st.selectbox("Drill into Campaign →", campaigns,
                            key=f"diag_camp_{app}_{mode}")
    camp_filter = None if sel_camp == "All" else sel_camp

    st.markdown("---")

    # ── Step 3: Ad Set ──
    st.markdown("#### Step 3 — Ad Set")
    adset_contrib = diagnose_contribution(df, "ad_set", campaign_filter=camp_filter)
    _render_table(adset_contrib, f"adset_{app}_{mode}")

    adsets = ["All"] + sorted(
        (df[df["campaign"] == camp_filter] if camp_filter else df)["ad_set"].dropna().unique().tolist()
    )
    sel_adset = st.selectbox("Drill into Ad Set →", adsets,
                             key=f"diag_adset_{app}_{mode}")
    adset_filter = None if sel_adset == "All" else sel_adset

    # ── Step 4: Creative (Meta only) ──
    if has_creative:
        st.markdown("---")
        st.markdown("#### Step 4 — Creative (Meta)")
        try:
            cr_df_raw = fetch_creative_data(app)
            if not cr_df_raw.empty:
                cr_df_raw = add_derived_metrics(cr_df_raw)
                cr_contrib = diagnose_contribution(cr_df_raw, "ad_creative",
                                                   campaign_filter=camp_filter,
                                                   adset_filter=adset_filter)
                _render_table(cr_contrib, f"creative_{app}_{mode}")
            else:
                st.info("No creative data available.")
        except Exception as e:
            st.error(f"Could not load creative data: {e}")




# ════════════════════════════════════════════════════════════════════════════
#  CAC DASHBOARD
# ════════════════════════════════════════════════════════════════════════════

def cac_overview(df: pd.DataFrame, app_color: str, app: str = ""):
    # ── KPI cards with sparklines ──
    _overview_kpi_cards(df, [
        ("D0_CAC_calc", "D0 CAC",    "₹", "",  True),
        ("CPI_calc",    "CPI",        "₹", "",  True),
        ("conv_rate",   "Conv Rate",  "",  "%", False),
        ("CPC",         "CPC",        "₹", "",  True),
        ("CPM",         "CPM",        "₹", "",  True),
    ], app=app)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── 7-day trend chart + source split ──
    trend_cols = ["D0_CAC_calc", "CPI_calc", "CPC", "CPM", "conv_rate", "total_cost"]
    trend_df   = build_trend_table(df, trend_cols)
    src        = source_split(df, "D0_CAC_calc")

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("<div class='section-label'>7-day trend</div>", unsafe_allow_html=True)
        if not trend_df.empty:
            st.plotly_chart(
                overview_trend_chart(
                    trend_df,
                    primary_col="D0_CAC_calc",
                    secondary_col="total_cost",
                    primary_label="D0 CAC",
                    secondary_label="Spend",
                    primary_prefix="₹",
                    secondary_prefix="₹",
                    color=app_color,
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"cac_overview_trend_{app}",
            )
            disp = trend_df[["date_tz", "D0_CAC_calc", "CPI_calc",
                              "conv_rate", "CPC", "total_cost"]].copy()
            disp["date_tz"] = disp["date_tz"].astype(str)
            disp = disp.rename(columns={
                "date_tz": "Date", "D0_CAC_calc": "D0 CAC (₹)", "CPI_calc": "CPI (₹)",
                "conv_rate": "Conv %", "CPC": "CPC (₹)", "total_cost": "Spend (₹)",
            })
            for c in ["D0 CAC (₹)", "CPI (₹)", "CPC (₹)"]:
                if c in disp.columns:
                    disp[c] = disp[c].round(0)
            disp["Conv %"]    = disp["Conv %"].round(2)
            disp["Spend (₹)"] = disp["Spend (₹)"].round(0)
            st.dataframe(disp, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("<div class='section-label'>Source split — latest day</div>", unsafe_allow_html=True)
        if not src.empty:
            st.plotly_chart(
                source_donut(src, "D0_CAC_calc", ""),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"cac_overview_donut_{app}",
            )
            _overview_source_cards(src, "D0_CAC_calc", "D0 CAC", primary_prefix="₹")


def cac_campaigns(df: pd.DataFrame, app_color: str, app: str = ""):
    camp_df = campaign_table(df)
    if camp_df.empty:
        st.info("No data available.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            campaign_bar(camp_df, "D0_CAC_calc", app_color, "D0 CAC by Campaign"),
            use_container_width=True,
            key=f"cac_camp_bar_cac_{app}",
        )
    with col2:
        st.plotly_chart(
            campaign_bar(camp_df, "CPI_calc", app_color, "CPI by Campaign"),
            use_container_width=True,
            key=f"cac_camp_bar_cpi_{app}",
        )

    st.plotly_chart(
        l3d_group_trend(df, "campaign", "D0_CAC_calc",
                        title="L3D D0 CAC — Top Campaigns",
                        metric_label="D0 CAC", prefix="₹"),
        use_container_width=True,
        key=f"cac_camp_l3d_{app}",
    )

    st.subheader("Campaign Table")
    display_cols = ["campaign", "source", "D0_CAC_calc", "CPI_calc", "conv_rate",
                    "cancel_rate", "CPC", "CPM", "total_cost", "spend_share"]
    rename_map = {
        "campaign": "Campaign", "source": "Source",
        "D0_CAC_calc": "D0 CAC", "CPI_calc": "CPI", "conv_rate": "Conv %",
        "cancel_rate": "Cancel %", "CPC": "CPC", "CPM": "CPM",
        "total_cost": "Spend", "spend_share": "Spend %",
    }
    disp = camp_df[[c for c in display_cols if c in camp_df.columns]].rename(columns=rename_map)
    for num_col in ["D0 CAC", "CPI", "Conv %", "Cancel %", "CPC", "CPM", "Spend %"]:
        if num_col in disp.columns:
            disp[num_col] = disp[num_col].round(2)
    if "Spend" in disp.columns:
        disp["Spend"] = disp["Spend"].round(0)
    st.dataframe(disp, use_container_width=True, hide_index=True)


def cac_adsets(df: pd.DataFrame, app_color: str, app: str = ""):
    all_campaigns = sorted(df["campaign"].dropna().unique().tolist())
    options = ["All"] + all_campaigns
    selected_camp = st.selectbox("Filter by Campaign", options,
                                 key=f"cac_camp_filter_{app}")
    campaign_filter = None if selected_camp == "All" else selected_camp

    ad_df = adset_table(df, campaign_filter=campaign_filter)
    if ad_df.empty:
        st.info("No ad-set data.")
        return

    display_cols = ["ad_set", "campaign", "source", "D0_CAC_calc", "CPI_calc",
                    "conv_rate", "cancel_rate", "CPC", "CPM", "spend_share", "total_cost"]
    rename_map = {
        "ad_set": "Ad Set", "campaign": "Campaign", "source": "Source",
        "D0_CAC_calc": "D0 CAC", "CPI_calc": "CPI", "conv_rate": "Conv %",
        "cancel_rate": "Cancel %", "CPC": "CPC", "CPM": "CPM",
        "spend_share": "Spend %", "total_cost": "Spend",
    }
    disp = ad_df[[c for c in display_cols if c in ad_df.columns]].rename(columns=rename_map)
    for num_col in ["D0 CAC", "CPI", "Conv %", "Cancel %", "CPC", "CPM", "Spend %"]:
        if num_col in disp.columns:
            disp[num_col] = disp[num_col].round(2)
    if "Spend" in disp.columns:
        disp["Spend"] = disp["Spend"].round(0)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    filtered_df = df[df["campaign"] == campaign_filter] if campaign_filter else df
    st.plotly_chart(
        l3d_group_trend(filtered_df, "ad_set", "D0_CAC_calc",
                        title="L3D D0 CAC — Top Ad Sets",
                        metric_label="D0 CAC", prefix="₹"),
        use_container_width=True,
        key=f"cac_adset_l3d_{app}",
    )


def cac_rise(df: pd.DataFrame, app: str = ""):
    c1, c2 = st.columns([1, 2])
    with c1:
        level = st.radio("Group by", ["campaign", "ad_set"], horizontal=True,
                         key=f"cac_rise_level_{app}")
    with c2:
        view = st.radio("View", ["Latest day", "7-day heatmap"], horizontal=True,
                        key=f"cac_rise_view_{app}")

    if view == "Latest day":
        kit_df = kitagawa_cac(df, level=level)
        if kit_df.empty:
            st.info("Need at least 2 days of data for decomposition.")
            return
        d0, d1 = kit_df["d0_date"].iloc[0], kit_df["d1_date"].iloc[0]
        st.caption(f"Comparing **{d0}** (D0) vs **{d1}** (D1)")
        st.plotly_chart(
            kitagawa_waterfall(kit_df, "D0 CAC — Kitagawa Decomposition"),
            use_container_width=True,
            key=f"cac_rise_waterfall_{app}",
        )
        st.subheader("Decomposition Table")
        cols_to_show = ["group", "cac_d0", "cac_d1", "cpi_d0", "cpi_d1",
                        "conv_d0", "conv_d1", "rate_effect", "mix_effect", "contribution"]
        avail = [c for c in cols_to_show if c in kit_df.columns]
        disp = kit_df[avail].copy()
        for c in avail[1:]:
            disp[c] = disp[c].round(3)
        rename = {
            "group": "Group", "cac_d0": "CAC D0", "cac_d1": "CAC D1",
            "cpi_d0": "CPI D0", "cpi_d1": "CPI D1",
            "conv_d0": "Conv D0%", "conv_d1": "Conv D1%",
            "rate_effect": "Rate Effect", "mix_effect": "Mix Effect",
            "contribution": "Contribution",
        }
        disp = disp.rename(columns=rename)
        st.dataframe(disp, use_container_width=True, hide_index=True)

    else:  # 7-day heatmap
        with st.spinner("Computing 7-day decomposition…"):
            pivot, detail = kitagawa_rolling_cac(df, level=level)
        if pivot.empty:
            st.info("Need at least 2 days of data.")
            return
        st.plotly_chart(
            kitagawa_heatmap(pivot, detail, mode="cac",
                             title="D0 CAC — 7-day Kitagawa Heatmap"),
            use_container_width=True,
            key=f"cac_rise_heatmap_{app}",
        )
        st.caption("Red = worsening (CAC rising) · Green = improving · "
                   "Rows sorted by total absolute contribution")


def cac_scatter(df: pd.DataFrame, app_color: str, app: str = ""):
    latest_date = df["date_tz"].max() if not df.empty else None
    if latest_date is None:
        st.info("No data.")
        return
    latest_df = df[df["date_tz"] == latest_date]
    st.plotly_chart(spend_cac_scatter(latest_df, app_color),
                    use_container_width=True, key=f"cac_scatter_{app}")

    st.subheader("Quadrant Analysis")
    quads = spend_cac_quadrants(latest_df)
    for qname, qdf in quads.items():
        with st.expander(f"{qname} ({len(qdf)} ad sets)"):
            if qdf.empty:
                st.write("None")
            else:
                disp = qdf[["ad_set", "source", "spend_share", "cac"]].copy()
                disp.columns = ["Ad Set", "Source", "Spend %", "CAC"]
                disp["Spend %"] = disp["Spend %"].round(2)
                disp["CAC"]     = disp["CAC"].round(2)
                st.dataframe(disp, use_container_width=True, hide_index=True)




# ════════════════════════════════════════════════════════════════════════════
#  Category Mix view
# ════════════════════════════════════════════════════════════════════════════

def category_mix_view():
    """Cross-app creative category breakdown: Category → Campaign, with YD + DBY metrics."""

    # ── date selector (same logic as morning pulse) ──
    # load all apps data to find common date range
    all_dfs = {}
    all_cr  = {}
    for a in APPS:
        d = safe_fetch(a)
        if not d.empty:
            all_dfs[a] = d
        if a in CREATIVE_QUERY_IDS:
            try:
                cr = add_derived_metrics(fetch_creative_data(a))
                if not cr.empty:
                    all_cr[a] = cr
            except Exception:
                pass

    if not all_cr:
        st.warning("No creative data available for any app.")
        return

    # find selectable dates (last 7, must have prior day)
    all_dates_combined = sorted(set().union(*[set(d["date_tz"].unique()) for d in all_dfs.values()]))
    avail_dates = all_dates_combined[-7:]
    selectable  = [d for d in avail_dates if all_dates_combined.index(d) > 0]
    if not selectable:
        st.warning("Need at least 2 days of data.")
        return

    date_key = "catmix_date"
    if date_key not in st.session_state or st.session_state[date_key] not in selectable:
        st.session_state[date_key] = selectable[-1]

    # pill date buttons
    btn_cols = st.columns(len(selectable) + 4)
    for i, d in enumerate(reversed(selectable)):
        label  = "Today" if d == selectable[-1] else str(d)
        is_sel = st.session_state[date_key] == d
        with btn_cols[i]:
            if is_sel:
                st.markdown(
                    f"<div style='background:#1a1a1a;border:1px solid #444;border-radius:20px;"
                    f"padding:5px 0;text-align:center;font-size:0.72rem;color:#ddd;font-weight:700'>{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button(label, key=f"catmix_date_{d}", use_container_width=True):
                    st.session_state[date_key] = d
                    st.rerun()

    sel_date = st.session_state[date_key]
    prior_date = all_dates_combined[all_dates_combined.index(sel_date) - 1]

    st.markdown(
        f"<div style='font-size:0.72rem;color:#444;margin:6px 0 20px'>"
        f"Showing <b style='color:#888'>{sel_date}</b> vs <b style='color:#555'>{prior_date}</b></div>",
        unsafe_allow_html=True,
    )

    def _parse_category(name: str) -> str:
        if not isinstance(name, str):
            return "Unknown"
        seg = name.split("_")[0].strip().lower()
        return seg.title() if seg else "Unknown"

    def _agg(cr_df, date):
        d = cr_df[cr_df["date_tz"] == date] if "date_tz" in cr_df.columns else cr_df
        if d.empty:
            return pd.DataFrame()
        d = d.copy()
        d["category"] = d["ad_creative"].apply(_parse_category)
        g = d.groupby(["category", "campaign"], as_index=False).agg(
            spend=("total_cost", "sum"),
            orders=("D0_paid_users", "sum"),
            uninstalls=("p0_unin_users", "sum"),
        )
        g["cac"]      = g.apply(lambda r: r["spend"] / r["orders"] if r["orders"] > 0 else None, axis=1)
        g["unin_rate"]= g.apply(lambda r: r["uninstalls"] / r["orders"] * 100 if r["orders"] > 0 else None, axis=1)
        return g

    # aggregate across all apps for sel_date and prior_date
    frames_yd, frames_pr = [], []
    for a, cr in all_cr.items():
        yd = _agg(cr, sel_date);   yd["app"] = a if not yd.empty else None
        pr = _agg(cr, prior_date); pr["app"] = a if not pr.empty else None
        if not yd.empty: frames_yd.append(yd)
        if not pr.empty: frames_pr.append(pr)

    if not frames_yd:
        st.info("No creative data for selected date.")
        return

    yd_all = pd.concat(frames_yd, ignore_index=True)
    pr_all = pd.concat(frames_pr, ignore_index=True) if frames_pr else pd.DataFrame()

    # roll up to category → campaign across apps
    yd_grp = yd_all.groupby(["category", "campaign"], as_index=False).agg(
        spend=("spend", "sum"), orders=("orders", "sum"), uninstalls=("uninstalls", "sum"),
    )
    yd_grp["cac"]       = yd_grp.apply(lambda r: r["spend"] / r["orders"]       if r["orders"] > 0 else None, axis=1)
    yd_grp["unin_rate"] = yd_grp.apply(lambda r: r["uninstalls"] / r["orders"] * 100 if r["orders"] > 0 else None, axis=1)

    pr_grp = pd.DataFrame()
    if not pr_all.empty:
        pr_grp = pr_all.groupby(["category", "campaign"], as_index=False).agg(
            spend_pr=("spend", "sum"), orders_pr=("orders", "sum"), uninstalls_pr=("uninstalls", "sum"),
        )
        pr_grp["cac_pr"]       = pr_grp.apply(lambda r: r["spend_pr"] / r["orders_pr"]           if r["orders_pr"] > 0 else None, axis=1)
        pr_grp["unin_rate_pr"] = pr_grp.apply(lambda r: r["uninstalls_pr"] / r["orders_pr"] * 100 if r["orders_pr"] > 0 else None, axis=1)

    # merge yd + prior
    if not pr_grp.empty:
        merged = yd_grp.merge(pr_grp[["category","campaign","spend_pr","orders_pr","cac_pr","unin_rate_pr"]],
                              on=["category","campaign"], how="left")
    else:
        merged = yd_grp.copy()
        for c in ["spend_pr","orders_pr","cac_pr","unin_rate_pr"]:
            merged[c] = None

    # category-level rollup
    cat_totals = merged.groupby("category", as_index=False).agg(
        spend=("spend","sum"), orders=("orders","sum"), uninstalls=("uninstalls","sum"),
        spend_pr=("spend_pr","sum"),
    )
    cat_totals["cac"] = cat_totals.apply(lambda r: r["spend"]/r["orders"] if r["orders"]>0 else None, axis=1)
    cat_totals = cat_totals.sort_values("spend", ascending=False)

    def _delta_html(now, prev, fmt, higher_is_bad=True):
        if prev is None or pd.isna(prev) or prev == 0:
            return ""
        diff = now - prev
        if diff == 0:
            return ""
        is_bad  = (diff > 0 and higher_is_bad) or (diff < 0 and not higher_is_bad)
        col     = "#E24B4A" if is_bad else "#1D9E75"
        arrow   = "▲" if diff > 0 else "▼"
        return (f"<span style='font-size:0.65rem;color:{col};font-weight:700;"
                f"background:rgba({'226,75,74' if is_bad else '29,158,117'},.1);"
                f"border-radius:6px;padding:1px 5px;margin-left:4px'>{arrow}{fmt(abs(diff))}</span>")

    # ── render ──
    cat_open_key = "catmix_open"
    if cat_open_key not in st.session_state:
        st.session_state[cat_open_key] = None

    for _, cat_row in cat_totals.iterrows():
        cat     = cat_row["category"]
        is_open = st.session_state[cat_open_key] == cat
        bg      = "#181824" if is_open else "#111"
        chevron = "▾" if is_open else "›"
        ch_col  = "#ddd" if is_open else "#444"

        # category header
        sp_delta  = _delta_html(cat_row["spend"],  cat_row.get("spend_pr"),  lambda v: f"₹{v:,.0f}", higher_is_bad=False)
        n_camps   = len(merged[merged["category"] == cat])

        ch_left, ch_btn = st.columns([11, 1])
        with ch_left:
            st.markdown(
                f"<div style='background:{bg};border:1px solid {'#333' if is_open else '#1a1a1a'};"
                f"border-left:3px solid #333;border-radius:10px;padding:10px 16px;margin-bottom:3px'>"
                f"<div style='display:flex;align-items:center;justify-content:space-between'>"
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<span style='color:{ch_col};font-size:1rem'>{chevron}</span>"
                f"<span style='font-weight:700;font-size:0.9rem;color:#e0e0e0'>{cat}</span>"
                f"<span style='font-size:0.65rem;color:#444;background:#1a1a1a;border:1px solid #222;"
                f"border-radius:6px;padding:1px 6px'>{n_camps} campaigns</span>"
                f"</div>"
                f"<div style='display:flex;gap:16px;font-size:0.75rem;color:#777'>"
                f"<span>₹{cat_row['spend']:,.0f}{sp_delta}</span>"
                f"<span>{int(cat_row['orders'])} orders</span>"
                f"<span>{'₹'+str(int(cat_row['cac'])) if (cat_row['cac'] and pd.notna(cat_row['cac'])) else '—'} CAC</span>"
                f"</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        with ch_btn:
            if st.button("⋯", key=f"catmix_btn_{cat}", use_container_width=True):
                st.session_state[cat_open_key] = None if is_open else cat
                st.rerun()

        if not is_open:
            continue

        # campaign rows within category
        camp_rows = merged[merged["category"] == cat].sort_values("spend", ascending=False)
        st.markdown("<div style='padding-left:16px;border-left:2px solid #1e1e1e;margin-left:6px;margin-bottom:6px'>", unsafe_allow_html=True)

        for _, row in camp_rows.iterrows():
            cac_now  = row["cac"]
            cac_pr   = row.get("cac_pr")
            unin_now = row["unin_rate"]
            unin_pr  = row.get("unin_rate_pr")

            sp_d   = _delta_html(row["spend"],    row.get("spend_pr"),    lambda v: f"₹{v:,.0f}",  False)
            ord_d  = _delta_html(row["orders"],   row.get("orders_pr"),   lambda v: f"{v:,.0f}",   False)
            cac_d  = _delta_html(cac_now,  cac_pr,  lambda v: f"₹{v:.0f}",  True)  if (cac_now  and pd.notna(cac_now))  else ""
            unin_d = _delta_html(unin_now, unin_pr, lambda v: f"{v:.1f}pp", True)  if (unin_now and pd.notna(unin_now)) else ""

            cac_str  = f"₹{int(cac_now)}"   if (cac_now  and pd.notna(cac_now))  else "—"
            unin_str = f"{unin_now:.1f}%"   if (unin_now and pd.notna(unin_now)) else "—"

            st.markdown(
                f"<div style='background:#0f0f0f;border:1px solid #1a1a1a;border-radius:8px;"
                f"padding:8px 14px;margin-bottom:3px;display:flex;justify-content:space-between;align-items:center'>"
                f"<span style='font-size:0.82rem;color:#ccc;flex:1;min-width:0;white-space:nowrap;"
                f"overflow:hidden;text-overflow:ellipsis'>{row['campaign']}</span>"
                f"<div style='display:flex;gap:14px;font-size:0.72rem;color:#666;flex-shrink:0;margin-left:12px;align-items:center'>"
                f"<span>₹{row['spend']:,.0f}{sp_d}</span>"
                f"<span>{int(row['orders'])} ord{ord_d}</span>"
                f"<span>{cac_str}{cac_d}</span>"
                f"<span>{unin_str}{unin_d}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  main navigation
# ════════════════════════════════════════════════════════════════════════════

def main():
    # ── sidebar navigation ────────────────────────────────────────────────────
    with st.sidebar:
        # ── Logo / title ──
        st.markdown(
            "<div style='padding:2px 0 14px'>"
            "<div style='font-size:0.6rem;color:#2c2c2c;letter-spacing:.18em;"
            "text-transform:uppercase;margin-bottom:5px'>Marketing Analytics</div>"
            "<div style='font-size:1.05rem;font-weight:700;color:#d8d8d8;"
            "letter-spacing:-.02em'>Dashboard</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border-color:#111;margin:0 0 6px'>", unsafe_allow_html=True)

        # ── init session state ──
        if "sb_app"     not in st.session_state:
            st.session_state["sb_app"]     = "Seekho"
        if "sb_section" not in st.session_state:
            st.session_state["sb_section"] = "🌅 Morning Pulse"

        app   = st.session_state.get("sb_app", APPS[0])
        color = APP_COLORS[app]
        hex_col = color.lstrip("#")
        r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)

        # inject hardcoded color into sidebar — CSS vars don't cross sidebar boundary
        st.markdown(f"""<style>
          [data-testid="stSidebar"] .nav-btn-active button {{
              background:rgba({r},{g},{b},0.12) !important;
              color:{color} !important; font-weight:600 !important;
              border:none !important; box-shadow:none !important;
          }}
          [data-testid="stSidebar"] .nav-btn-active button:hover {{
              background:rgba({r},{g},{b},0.18) !important; color:{color} !important;
          }}
        </style>""", unsafe_allow_html=True)

        def _nav_btn(label: str, key: str, state_key: str):
            is_active = st.session_state.get(state_key) == label
            css_class = "nav-btn-active" if is_active else "nav-btn"
            st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
            if st.button(label, key=key, use_container_width=True):
                st.session_state[state_key] = label
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── App picker ──
        st.markdown("<div class='sb-group-label'>App</div>", unsafe_allow_html=True)
        for a in APPS:
            a_color = APP_COLORS[a]
            a_hex = a_color.lstrip("#")
            ar, ag, ab = int(a_hex[0:2], 16), int(a_hex[2:4], 16), int(a_hex[4:6], 16)
            is_active = st.session_state.get("sb_app") == a
            if is_active:
                # render active app with its own color inline
                st.markdown(f"""<style>
                  [data-testid="stSidebar"] .nav-app-{a} button {{
                      background:rgba({ar},{ag},{ab},0.12) !important;
                      color:{a_color} !important; font-weight:600 !important;
                      border:none !important; box-shadow:none !important;
                  }}
                </style>""", unsafe_allow_html=True)
                st.markdown(f"<div class='nav-app-{a}'>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='nav-btn'>", unsafe_allow_html=True)
            if st.button(f"● {a}", key=f"app_{a}", use_container_width=True):
                st.session_state["sb_app"] = a
                st.session_state["sb_section"] = "🌅 Morning Pulse"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Section picker ──
        st.markdown("<div class='sb-group-label'>Section</div>", unsafe_allow_html=True)
        section_options = ["🌅 Morning Pulse", "📊 Category Mix"]
        if st.session_state.get("sb_section") not in section_options:
            st.session_state["sb_section"] = section_options[0]
        for opt in section_options:
            _nav_btn(opt, f"sec_{opt}", "sb_section")
        section = st.session_state["sb_section"]

        # ── Refresh ──
        st.markdown("<hr style='border-color:#111;margin:18px 0 10px'>", unsafe_allow_html=True)
        if st.button(f"↻  Refresh {app}", key="refresh_btn", use_container_width=True):
            with st.spinner("Refreshing…"):
                refresh_app_data(app)
            st.success("Done!")

    # ── main content header ───────────────────────────────────────────────────
    hex_col = color.lstrip("#")
    r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:16px'>"
        f"<div style='display:inline-flex;align-items:center;gap:7px;"
        f"background:rgba({r},{g},{b},0.1);border:1px solid rgba({r},{g},{b},0.2);"
        f"border-radius:20px;padding:4px 12px 4px 8px'>"
        f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;background:{color}'></span>"
        f"<span style='font-size:0.82rem;font-weight:700;color:{color}'>{app}</span>"
        f"</div>"
        f"<span style='color:#222'>/</span>"
        f"<span style='font-size:0.82rem;color:#444'>{section}</span>"
        f"</div>"
        f"<div style='height:1px;background:#141414;margin-bottom:18px'></div>",
        unsafe_allow_html=True,
    )

    if section == "📊 Category Mix":
        category_mix_view()
        return

    df = safe_fetch(app)
    if df.empty:
        st.warning(f"No data loaded for {app}.")
        return

    morning_pulse_view(df, app=app, color=color, mode="uninstall")


if __name__ == "__main__":
    main()
