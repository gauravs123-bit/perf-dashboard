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
    initial_sidebar_state="collapsed",
)

# ── light cream theme ────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  /* ── Base ── */
  html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
  [data-testid="stAppViewContainer"] { background:#F0EBE1; }
  [data-testid="stHeader"]           { background:#F0EBE1; display:none; }
  .block-container { padding-top:1.5rem; padding-bottom:2rem; max-width:1200px; }

  /* scrollbar */
  ::-webkit-scrollbar { width:4px; height:4px; }
  ::-webkit-scrollbar-track { background:#E8E3D9; }
  ::-webkit-scrollbar-thumb { background:#C8C3B8; border-radius:4px; }

  /* ── Streamlit metric cards (used in non-pulse views) ── */
  [data-testid="metric-container"] {
      background:#FFFFFF; border:1px solid #DDD8CE; border-radius:12px; padding:14px 18px;
  }
  [data-testid="stMetricValue"] { font-size:1.35rem; font-weight:700; letter-spacing:-.02em; }
  [data-testid="stMetricDelta"] { font-size:0.75rem; }
  button[data-baseweb="tab"]    { font-size:0.85rem; font-weight:600; }
  [data-testid="stDataFrame"]   { border-radius:10px; overflow:hidden; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background:#EBE6DC !important;
      border-right:1px solid #D0CBC1 !important;
      min-width:220px !important;
  }
  [data-testid="stSidebar"] > div:first-child { padding:1.4rem 1rem 1rem; }

  /* sidebar collapse button (inside open sidebar) */
  [data-testid="stSidebarCollapseButton"] {
      opacity:1 !important; color:#9A958C !important;
  }
  [data-testid="stSidebarCollapseButton"]:hover { color:#5A554D !important; }
  [data-testid="stSidebarCollapseButton"] svg { stroke:#9A958C !important; }

  /* sidebar EXPAND button — shown on left edge when sidebar is collapsed */
  [data-testid="stSidebarCollapsedControl"] {
      background:#DDD8CE !important;
      border:1px solid #C5C0B6 !important;
      border-left:none !important;
      border-radius:0 8px 8px 0 !important;
      width:28px !important;
      opacity:1 !important;
      top:50% !important;
      box-shadow:2px 0 8px rgba(0,0,0,0.08) !important;
  }
  [data-testid="stSidebarCollapsedControl"] button {
      color:#6B665E !important;
  }
  [data-testid="stSidebarCollapsedControl"] svg {
      stroke:#6B665E !important; fill:none !important;
  }
  [data-testid="stSidebarCollapsedControl"]:hover {
      background:#D0CBC1 !important; border-color:#B8B3A9 !important;
  }

  /* hide radio circles */
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display:none !important; }
  [data-testid="stSidebar"] .stRadio > div { gap:2px !important; }
  [data-testid="stSidebar"] .stRadio label {
      font-size:0.83rem; padding:7px 12px !important; border-radius:7px;
      color:#7A756D !important; font-weight:500; transition:background .1s, color .1s;
      cursor:pointer; display:flex !important; align-items:center; gap:7px; width:100%;
  }
  [data-testid="stSidebar"] .stRadio label:hover {
      background:#DDD8CE !important; color:#2A2520 !important;
  }
  [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { margin:0; }
  [data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] { display:none; }
  [data-testid="stSidebar"] hr { border-color:#D8D3C9; margin:10px 0; }

  /* ── nav buttons ── */
  [data-testid="stSidebar"] .nav-btn button,
  [data-testid="stSidebar"] .nav-btn [data-testid="stBaseButton-secondary"] {
      background:transparent !important; border:none !important; box-shadow:none !important;
      color:#7A756D !important; font-size:0.83rem !important;
      font-weight:500 !important; text-align:left !important;
      padding:8px 12px !important; border-radius:8px !important;
      width:100% !important; transition:background .12s, color .12s !important;
      justify-content:flex-start !important;
  }
  [data-testid="stSidebar"] .nav-btn button:hover {
      background:#DDD8CE !important; color:#2A2520 !important;
  }
  [data-testid="stSidebar"] .nav-btn-active button,
  [data-testid="stSidebar"] .nav-btn-active [data-testid="stBaseButton-secondary"] {
      background:var(--app-color-subtle, #E5E0D5) !important;
      color:var(--app-color, #1C1A17) !important;
      font-weight:600 !important; border:none !important; box-shadow:none !important;
  }
  [data-testid="stSidebar"] .nav-btn-active button:hover {
      background:var(--app-color-subtle, #E5E0D5) !important;
      color:var(--app-color, #1C1A17) !important;
  }

  /* sidebar group label */
  .sb-group-label {
      font-size:0.6rem; font-weight:700; letter-spacing:.16em;
      text-transform:uppercase; color:#B0AB9F; margin:20px 0 6px 4px;
  }

  /* sidebar action buttons (refresh etc) */
  [data-testid="stSidebar"] .stButton > button {
      background:#EBE6DC !important; border:1px solid #D5D0C6 !important;
      color:#7A756D !important; border-radius:8px !important;
      font-size:0.79rem !important; font-weight:500 !important;
      padding:8px 14px !important; width:100%; transition:all .15s;
  }
  [data-testid="stSidebar"] .stButton > button:hover {
      background:#DDD8CE !important; color:#2A2520 !important; border-color:#C5C0B6 !important;
  }

  /* ── Morning Pulse KPI cards ── */
  .pulse-card {
      background:#FFFFFF; border:1px solid #E2DDD3; border-radius:12px;
      padding:16px 16px; height:100%; position:relative; overflow:hidden;
      transition: border-color .15s, background .15s;
  }
  .pulse-card:hover { border-color:#D0CBC1; background:#F8F5F0; }
  .pulse-card::after {
      content:''; position:absolute; top:0; left:0; right:0; height:2px;
      border-radius:12px 12px 0 0;
  }
  .pulse-card-red::after   { background:linear-gradient(90deg,#E24B4A,transparent); }
  .pulse-card-green::after { background:linear-gradient(90deg,#1D9E75,transparent); }
  .pulse-card-grey::after  { background:linear-gradient(90deg,#C8C3B8,transparent); }
  .pulse-label { font-size:0.58rem; color:#A8A39A; text-transform:uppercase;
                 letter-spacing:.16em; margin-bottom:10px; font-weight:700; }
  .pulse-value { font-size:1.75rem; font-weight:700; color:#1C1A17;
                 letter-spacing:-.03em; line-height:1; margin-bottom:4px; }
  .pulse-yday  { font-size:0.66rem; color:#B0AB9F; margin-bottom:10px; }
  .pulse-delta-row { display:flex; align-items:center; justify-content:space-between; }
  .pulse-delta-bad  { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      font-weight:700; padding:3px 10px; border-radius:20px;
                      background:rgba(226,75,74,.10); color:#E24B4A;
                      border:1px solid rgba(226,75,74,.20); }
  .pulse-delta-good { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      font-weight:700; padding:3px 10px; border-radius:20px;
                      background:rgba(29,158,117,.10); color:#1D9E75;
                      border:1px solid rgba(29,158,117,.20); }
  .pulse-delta-neu  { display:inline-flex; align-items:center; gap:3px; font-size:0.68rem;
                      padding:3px 10px; border-radius:20px;
                      background:#F0EBE1; color:#A8A39A; border:1px solid #DDD8CE; }
  .pulse-pct { font-size:0.62rem; color:#B0AB9F; }

  /* ── Section header ── */
  .section-hdr { display:flex; align-items:center; gap:10px; margin:28px 0 14px; }
  .section-hdr-line { flex:1; height:1px; background:#E5E0D6; }
  .section-hdr-text { font-size:0.58rem; font-weight:700; letter-spacing:.16em;
                      text-transform:uppercase; color:#B0AB9F; white-space:nowrap; }

  /* ── Alert pills ── */
  .alert-pill { display:inline-flex; align-items:center; gap:5px; padding:5px 13px;
                border-radius:20px; font-size:0.78rem; font-weight:500; margin:0 4px 5px 0; }
  .alert-pill-red    { background:rgba(226,75,74,.08);  color:#C0392B; border:1px solid rgba(226,75,74,.2); }
  .alert-pill-green  { background:rgba(29,158,117,.08); color:#1A7A5E; border:1px solid rgba(29,158,117,.2); }
  .alert-pill-yellow { background:rgba(180,130,0,.07);  color:#8B6914; border:1px solid rgba(180,130,0,.2); }

  /* ── Shared section label ── */
  .section-label { font-size:0.6rem; text-transform:uppercase; letter-spacing:.14em;
                   color:#A8A39A; margin-bottom:12px; margin-top:0; font-weight:700; }

  /* ── Contributor cards ── */
  .contrib-card { background:#FFFFFF; border:1px solid #E5E0D6; border-radius:12px;
                  padding:13px 15px; margin-bottom:6px; }
  .contrib-tag  { display:inline-flex; align-items:center; gap:3px; font-size:0.67rem;
                  background:#F0EBE1; padding:3px 9px; border-radius:10px;
                  border:1px solid #DDD8CE; margin-right:4px; }

  /* ── Campaign table ── */
  .camp-table { width:100%; border-collapse:collapse; }
  .camp-table th {
      font-size:0.58rem; color:#B0AB9F; text-transform:uppercase; letter-spacing:.12em;
      font-weight:700; padding:8px 12px; text-align:right; border-bottom:1px solid #E5E0D6;
      background:#F5F2ED;
  }
  .camp-table th:first-child { text-align:left; }
  .camp-table td {
      padding:9px 12px; font-size:0.78rem; color:#5A554D; border-bottom:1px solid #EDE8DE;
      text-align:right; white-space:nowrap;
  }
  .camp-table td:first-child { text-align:left; }
  .camp-table tr:hover td { background:#F8F5F0; }
  .camp-table tr:last-child td { border-bottom:none; }
  .src-dot { display:inline-block; width:7px; height:7px; border-radius:50%;
             margin-right:6px; flex-shrink:0; }
  .src-badge { font-size:0.6rem; background:#EDE8DE; border:1px solid #DDD8CE;
               border-radius:4px; padding:1px 6px; color:#8A857D; margin-left:5px; }
  .dod-pill-bad  { display:inline-flex; align-items:center; font-size:0.68rem; font-weight:700;
                   padding:2px 8px; border-radius:5px; background:rgba(226,75,74,.10); color:#E24B4A; }
  .dod-pill-good { display:inline-flex; align-items:center; font-size:0.68rem; font-weight:700;
                   padding:2px 8px; border-radius:5px; background:rgba(29,158,117,.10); color:#1D9E75; }
  .dod-pill-neu  { display:inline-flex; align-items:center; font-size:0.68rem;
                   padding:2px 8px; border-radius:5px; background:#EDE8DE; color:#8A857D; }

  /* ── Drill + Trend buttons ─────────────────────────────────────────────── */
  [data-testid="stColumn"] > * > .stHorizontalBlock { gap:2px !important; padding:0 !important; }
  [data-testid="stColumn"] .stHorizontalBlock [data-testid="stElementContainer"],
  [data-testid="stColumn"] .stHorizontalBlock .element-container {
    margin:0 !important; padding:0 !important; min-height:0 !important;
  }
  [data-testid="stColumn"] .stHorizontalBlock button {
    min-height:20px !important; height:20px !important; line-height:20px !important;
    padding:0 5px !important; font-size:0.6rem !important; font-weight:600 !important;
    letter-spacing:0.04em !important; text-transform:uppercase !important;
    border-radius:2px !important; box-shadow:none !important;
    white-space:nowrap !important; width:100% !important;
  }
  /* drill ▸ — first sub-column */
  [data-testid="stColumn"] .stHorizontalBlock [data-testid="stColumn"]:first-child button {
    background:transparent !important; border:1px solid #D0CBC1 !important; color:#8A857D !important;
  }
  [data-testid="stColumn"] .stHorizontalBlock [data-testid="stColumn"]:first-child button:hover {
    border-color:#B8B3A9 !important; color:#4A4540 !important; background:transparent !important;
  }
  /* trend — second (last) sub-column */
  [data-testid="stColumn"] .stHorizontalBlock [data-testid="stColumn"]:last-child button {
    background:#F5F2ED !important; border:1px solid #DDD8CE !important; color:#8A857D !important;
  }
  [data-testid="stColumn"] .stHorizontalBlock [data-testid="stColumn"]:last-child button:hover {
    background:#EDE8DE !important; border-color:rgba(226,75,74,0.3) !important; color:#E24B4A !important;
  }

  /* ── Header strip ── */
  .strip-card { background:#FFFFFF; border:1px solid #E5E0D6; border-radius:10px;
                padding:10px 14px; text-align:center; cursor:pointer;
                transition:border-color .15s; }
  .strip-app-name  { font-size:0.68rem; color:#A8A39A; margin-bottom:2px; font-weight:500; }
  .strip-value     { font-size:1.05rem; font-weight:700; letter-spacing:-.02em; }
  .strip-delta-pos { color:#1D9E75; font-size:0.72rem; }
  .strip-delta-neg { color:#E24B4A; font-size:0.72rem; }

  /* strip switch button — compact pill */
  .strip-click-btn { margin-top:4px; }
  .strip-click-btn button {
      background:#F5F2ED !important; border:1px solid #DDD8CE !important;
      box-shadow:none !important; color:#8A857D !important;
      font-size:0.7rem !important; font-weight:500 !important;
      padding:3px 10px !important; border-radius:20px !important;
      width:auto !important; min-height:0 !important; height:auto !important;
      transition:color .12s, border-color .12s !important;
      display:inline-flex !important;
  }
  .strip-click-btn button:hover {
      color:#2A2520 !important; border-color:#C5C0B6 !important;
      background:#EBE6DC !important;
  }

  /* section pill nav */
  div[data-testid="stHorizontalBlock"] .stRadio [data-testid="stWidgetLabel"] { display:none; }

  /* ── Nav pills (app + section selectors) ──────────────────────────────── */
  [data-baseweb="button-group"] {
    flex-direction: row !important;
    flex-wrap: wrap !important;
    gap: 4px !important;
    padding: 0 !important;
    align-items: center !important;
  }
  [data-baseweb="button-group"] button {
    border-radius: 20px !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 3px 14px !important;
    min-height: 28px !important;
    height: 28px !important;
    line-height: 28px !important;
    background: linear-gradient(180deg, #FDFAF7 0%, #EDE8DE 100%) !important;
    border: 1px solid #C8C3B8 !important;
    color: #6B665E !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.85) !important;
    flex: 0 0 auto !important;
    transition: all .12s !important;
  }
  [data-baseweb="button-group"] button:hover {
    border-color: #B0AB9F !important;
    color: #2A2520 !important;
    background: linear-gradient(180deg, #F5F0E8 0%, #E5DFD4 100%) !important;
    box-shadow: 0 3px 6px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.75) !important;
  }
  [class*="e8vg11g11"],
  [data-baseweb="button-group"] button[aria-pressed="true"],
  [data-baseweb="button-group"] button[aria-checked="true"] {
    font-weight: 700 !important;
  }
  [data-testid="stWidgetLabel"]:has(+ [data-baseweb="button-group"]) {
    display: none !important;
    margin: 0 !important;
    height: 0 !important;
  }
</style>
""", unsafe_allow_html=True)

APPS = list(APP_QUERY_IDS.keys())

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

# ════════════════════════════════════════════════════════════════════════════
#  Trend chart dialog (module-level for @st.dialog)
# ════════════════════════════════════════════════════════════════════════════

def _build_trend_fig(filter_df: pd.DataFrame, label: str, n_days: int = 14,
                     end_date=None):
    if filter_df is None or filter_df.empty or "date_tz" not in filter_df.columns:
        return None, None
    daily = (filter_df.groupby("date_tz")
             .agg(spend=("total_cost", "sum"),
                  orders=("D0_paid_users", "sum"),
                  unin=("p0_unin_users", "sum"))
             .reset_index().sort_values("date_tz"))
    # Reindex to full date range so 0-spend days show as empty bars
    min_date = daily["date_tz"].min()
    max_date = end_date if end_date is not None else daily["date_tz"].max()
    full_range = pd.date_range(min_date, max_date, freq="D").date
    daily = (daily.set_index("date_tz")
                  .reindex(full_range)
                  .reset_index()
                  .rename(columns={"index": "date_tz"}))
    daily["spend"]  = daily["spend"].fillna(0)
    daily["orders"] = daily["orders"].fillna(0)
    daily["unin"]   = daily["unin"].fillna(0)
    daily = daily.tail(n_days)
    daily["cac"]       = daily.apply(
        lambda r: r["spend"] / r["orders"] if r["orders"] > 0 else float("nan"), axis=1)
    daily["unin_rate"] = daily.apply(
        lambda r: r["unin"] / r["orders"] * 100 if r["orders"] > 0 else float("nan"), axis=1)
    fig = go.Figure()
    # Spend bars (y3, right-2)
    fig.add_trace(go.Bar(
        x=daily["date_tz"].astype(str), y=daily["spend"],
        name="Spend ₹", yaxis="y3",
        marker_color="rgba(120,120,120,0.22)",
        hovertemplate="%{x}<br>Spend ₹%{y:,.0f}<extra></extra>"))
    # CAC line (y1, left)
    fig.add_trace(go.Scatter(
        x=daily["date_tz"].astype(str), y=daily["cac"],
        name="CAC ₹", line=dict(color="#E24B4A", width=2.5),
        hovertemplate="%{x}<br>CAC ₹%{y:.0f}<extra></extra>"))
    # Uninstall % line (y2, right)
    fig.add_trace(go.Scatter(
        x=daily["date_tz"].astype(str), y=daily["unin_rate"],
        name="Unin %", line=dict(color="#378ADD", width=2.5, dash="dot"),
        yaxis="y2",
        hovertemplate="%{x}<br>Unin %{y:.1f}%<extra></extra>"))
    fig.update_layout(
        height=340, margin=dict(l=0, r=60, t=24, b=40),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(color="#7A756D", size=11),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        xaxis=dict(showgrid=False, tickfont=dict(size=9), tickangle=-30),
        yaxis=dict(title="CAC ₹", showgrid=True, gridcolor="#E5E0D6",
                   tickfont=dict(size=9), tickprefix="₹"),
        yaxis2=dict(title="Unin %", overlaying="y", side="right",
                    showgrid=False, tickfont=dict(size=9), ticksuffix="%",
                    anchor="x"),
        yaxis3=dict(overlaying="y", side="right", showgrid=False,
                    showticklabels=False, anchor="free", position=1.0),
        barmode="overlay",
    )
    return fig, daily


@st.dialog("📈 CAC, Spend & Uninstall Trend", width="large")
def show_trend_dialog(label: str, filter_df: pd.DataFrame, end_date=None):
    st.markdown(f"<div style='font-size:0.82rem;color:#6B665E;margin-bottom:12px'>{label}</div>",
                unsafe_allow_html=True)
    fig, daily = _build_trend_fig(filter_df, label, end_date=end_date)
    if fig is None:
        st.info("No historical data available for this selection.")
        return
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    if daily is not None and not daily.empty:
        last = daily.iloc[-1]
        prev = daily.iloc[-2] if len(daily) > 1 else last
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spend (YD)", f"₹{last['spend']:,.0f}",
                  f"₹{last['spend']-prev['spend']:+,.0f}")
        c2.metric("CAC (YD)", f"₹{last['cac']:.0f}",
                  f"₹{last['cac']-prev['cac']:+.0f}")
        c3.metric("Unin% (YD)", f"{last['unin_rate']:.1f}%",
                  f"{last['unin_rate']-prev['unin_rate']:+.2f}pp")
        c4.metric("Orders (YD)", f"{int(last['orders']):,}",
                  f"{int(last['orders']-prev['orders']):+,}")


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
        <div style="flex:1;min-width:120px;background:#FFFFFF;border:1px solid #E2DDD3;
                    border-top:2px solid {sc};border-radius:10px;padding:12px 14px">
          <div style="font-size:0.6rem;color:{sc};font-weight:700;letter-spacing:.1em;
                      text-transform:uppercase;margin-bottom:8px">{s}</div>
          <div style="font-size:0.75rem;color:#A8A39A;margin-bottom:2px">Spend</div>
          <div style="font-size:1rem;font-weight:700;color:#1C1A17;margin-bottom:6px">
            ₹{spend:,.0f} <span style="font-size:0.68rem;color:#7A756D">({spct:.0f}%)</span>
          </div>
          <div style="font-size:0.75rem;color:#A8A39A;margin-bottom:2px">{primary_label}</div>
          <div style="font-size:0.95rem;font-weight:600;color:#2A2520;margin-bottom:6px">
            {primary_prefix}{pval:.1f}{primary_suffix}
          </div>
          <div style="font-size:0.75rem;color:#A8A39A;margin-bottom:2px">D0 Orders</div>
          <div style="font-size:0.85rem;color:#5A554D">{paid:,}</div>
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
        bg     = f"rgba({r},{g},{b},0.15)" if is_sel else "#F0EBE1"
        border = color if is_sel else "#D8D3C9"
        fc     = color if is_sel else "#7A756D"
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
        f"<div style='background:#FFFFFF;border:1px solid #E2DDD3;border-radius:20px;"
        f"padding:5px 14px;font-size:0.75rem;color:#7A756D;display:inline-flex;align-items:center;gap:6px'>"
        f"<span style='color:#A8A39A'>📅</span>"
        f"<b style='color:#1C1A17'>{today_lbl} ({yd_date})</b>"
        f"<span style='color:#B0AB9F'>vs</span>"
        f"<span style='color:#6B665E'>{yday_lbl} ({d1_date})</span>"
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
        row_bg  = "#E8E1D6" if is_today else ("#F0EBE3" if is_yday else "transparent")
        date_lbl = f"<b style='color:#1C1A17'>{dt}</b>" if is_today else f"<span style='color:#4A4540'>{dt}</span>"

        def _delta_cell(now, prev, fmt, higher_is_bad=True):
            if prev is None or prev == 0:
                return "<td style='text-align:right;padding:5px 10px;color:#C5C0B6'>—</td>"
            diff = now - prev
            is_bad = (diff > 0 and higher_is_bad) or (diff < 0 and not higher_is_bad)
            col = "#E24B4A" if is_bad else "#1D9E75"
            arrow = "▲" if diff > 0 else "▼"
            return f"<td style='text-align:right;padding:5px 10px;font-size:0.68rem;color:{col}'>{arrow}{fmt(abs(diff))}</td>"

        cac_delta_cell  = _delta_cell(cac,     prev_cac,   lambda v: f"₹{v:.0f}",  True)
        unin_delta_cell = _delta_cell(unin_rt, prev_unin,  lambda v: f"{v:.1f}pp", True)
        spend_delta_cell= _delta_cell(sp,      prev_spend, lambda v: f"₹{v:,.0f}", False)

        rows_html += (
            f"<tr style='background:{row_bg};border-bottom:1px solid #E5E0D6'>"
            f"<td style='padding:5px 10px;font-size:0.75rem;white-space:nowrap'>{date_lbl}</td>"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#2A2520'>₹{sp:,.0f}</td>"
            f"{spend_delta_cell}"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#2A2520'>{orders:,.0f}</td>"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#2A2520'>₹{cac:,.0f}</td>"
            f"{cac_delta_cell}"
            f"<td style='text-align:right;padding:5px 10px;font-size:0.78rem;color:#2A2520'>{unin_rt:.1f}%</td>"
            f"{unin_delta_cell}"
            f"</tr>"
        )
        prev_cac   = cac
        prev_unin  = unin_rt
        prev_spend = sp

    th = "style='text-align:right;padding:5px 10px;font-size:0.65rem;color:#8A857D;font-weight:600;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #E5E0D6'"
    thl = "style='padding:5px 10px;font-size:0.65rem;color:#8A857D;font-weight:600;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #E5E0D6'"
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
              <div style="font-size:0.84rem;font-weight:600;color:#2A2520;margin-bottom:6px;line-height:1.3">{short}</div>
              <div style="display:flex;gap:5px;flex-wrap:wrap">
                <span class="contrib-tag" style="color:{re_col}">Rate&nbsp;{re_arrow}&nbsp;{re_str}</span>
                <span class="contrib-tag" style="color:{me_col}">Mix&nbsp;{me_arrow}&nbsp;{me_str}</span>
              </div>
            </div>
            <div style="text-align:right;flex-shrink:0;min-width:70px">
              <div style="font-size:0.62rem;color:#8A857D;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px">{rate_lbl}</div>
              <div style="font-size:0.88rem;color:#4A4540;margin-bottom:4px">{rate_str}</div>
              <div style="font-size:1.05rem;font-weight:700;color:{c_col};letter-spacing:-.01em">{contrib_str}</div>
            </div>
          </div>
        </div>"""

    def _render_kit_col(kit_df, is_cac):
        if kit_df.empty:
            st.markdown("<div style='color:#8A857D;font-size:0.82rem;padding:8px'>No data</div>", unsafe_allow_html=True)
            return
        worsened = kit_df[kit_df["contribution"] > 0].head(3)
        improved = kit_df[kit_df["contribution"] < 0].tail(2)
        st.markdown("<div style='font-size:0.72rem;color:#E24B4A;font-weight:600;margin-bottom:5px;letter-spacing:.06em;text-transform:uppercase'>↑ Worsened</div>", unsafe_allow_html=True)
        if worsened.empty:
            st.markdown("<div style='color:#C5C0B6;font-size:0.8rem;margin-bottom:8px'>—</div>", unsafe_allow_html=True)
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
    # kit_df used by drill-down level 1 list — use CAC as primary ordering
    kit_df = kit_cac if not kit_cac.empty else kit_unin

    # ── Drill-down ──
    st.markdown(
        "<div class='section-hdr'><div class='section-hdr-line'></div>"
        "<div class='section-hdr-text'>Drill Down — Campaign → Ad Set → Creative</div>"
        "<div class='section-hdr-line'></div></div>",
        unsafe_allow_html=True)

    camp_key  = f"dd_camp_{app}_{mode}"
    adset_key = f"dd_adset_{app}_{mode}"
    if camp_key  not in st.session_state: st.session_state[camp_key]  = None
    if adset_key not in st.session_state: st.session_state[adset_key] = None
    sel_camp  = st.session_state[camp_key]
    sel_adset = st.session_state[adset_key]

    # Kitagawa contribution maps — campaign level
    camp_cac_map  = {r["group"]: r for _, r in kit_cac.iterrows()}  if not kit_cac.empty  else {}
    camp_unin_map = {r["group"]: r for _, r in kit_unin.iterrows()} if not kit_unin.empty else {}

    # Kitagawa contribution maps — ad set level
    kit_adset_cac  = kitagawa_cac(df_sel,       level="ad_set")
    kit_adset_unin = kitagawa_uninstall(df_sel, level="ad_set")
    adset_cac_map  = {r["group"]: r for _, r in kit_adset_cac.iterrows()}  if not kit_adset_cac.empty  else {}
    adset_unin_map = {r["group"]: r for _, r in kit_adset_unin.iterrows()} if not kit_adset_unin.empty else {}

    adset_contrib = diagnose_contribution(df_sel, "ad_set", campaign_filter=sel_camp) if sel_camp else None

    cr_raw = None; cr_sel = None; kit_cr_cac_map = {}; kit_cr_unin_map = {}
    if app in CREATIVE_QUERY_IDS:
        try:
            cr_raw = add_derived_metrics(fetch_creative_data(app))
            cr_sel = cr_raw[cr_raw["date_tz"] <= sel_date] if "date_tz" in cr_raw.columns else cr_raw
            kit_cr_cac  = kitagawa_cac(cr_sel,       level="ad_creative")
            kit_cr_unin = kitagawa_uninstall(cr_sel, level="ad_creative")
            kit_cr_cac_map  = {r["group"]: r for _, r in kit_cr_cac.iterrows()}  if not kit_cr_cac.empty  else {}
            kit_cr_unin_map = {r["group"]: r for _, r in kit_cr_unin.iterrows()} if not kit_cr_unin.empty else {}
        except Exception:
            pass

    if not camps.empty:
        all_camps = camps.sort_values("spend_yd", ascending=False)["campaign"].tolist()
    else:
        all_camps = kit_df["group"].tolist() if not kit_df.empty else []

    camp_source_map: dict[str, str] = {}
    if "campaign" in df_sel.columns and "source" in df_sel.columns:
        for c_name, grp in df_sel.groupby("campaign"):
            yd = grp[grp["date_tz"] == sel_date] if "date_tz" in grp.columns else grp
            srcs = yd.groupby("source")["total_cost"].sum().sort_values(ascending=False)
            camp_source_map[c_name] = str(srcs.index[0]) if not srcs.empty else ""

    camps_metrics = {}
    if not camps.empty:
        for _, crow in camps.iterrows():
            camps_metrics[crow["campaign"]] = crow

    def _fmt_spend(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return "—"
        if v >= 1_00_000: return f"₹{v/1_00_000:.1f}L"
        if v >= 1_000:    return f"₹{v/1_000:.0f}k"
        return f"₹{v:.0f}"

    def _src_dot_label(src):
        s = (src or "").lower()
        if "facebook" in s or "meta" in s: return "#378ADD", "Facebook"
        if "google" in s:                   return "#34A853", "Google"
        if "snap" in s:                     return "#F5A623", "Snapchat"
        return "#555555", "Other"

    def _contrib_pill(val, fmt_fn):
        """Colored pill: positive = red (bad — contributed to rise), negative = green."""
        if val is None or val == 0:
            return "<span style='color:#2a2a2a;font-size:0.72rem'>—</span>"
        is_bad = val > 0
        col = "#E24B4A" if is_bad else "#1D9E75"
        bg  = "rgba(226,75,74,0.14)" if is_bad else "rgba(29,158,117,0.14)"
        arr = "↑" if val > 0 else "↓"
        return (f"<span style='background:{bg};color:{col};font-size:0.72rem;font-weight:700;"
                f"padding:3px 9px;border-radius:6px;white-space:nowrap'>{arr} {fmt_fn(abs(val))}</span>")

    _TH_s = ("font-size:0.62rem;text-transform:uppercase;letter-spacing:0.1em;color:#8A857D;"
             "padding:9px 12px;font-weight:600;border-bottom:1px solid #E5E0D6;background:#F5F2ED;")
    _TD_s = "font-size:0.82rem;color:#2A2520;padding:10px 12px;border-bottom:1px solid #EDE8DE;"

    def _tbl_wrap(headers, inner_rows):
        hdr = "".join(
            f"<th style='{_TH_s}{';text-align:right' if i > 0 else ''}'>{h}</th>"
            for i, h in enumerate(headers))
        return (f"<div style='margin-top:10px;border-radius:8px;overflow:hidden;border:1px solid #E5E0D6'>"
                f"<table style='width:100%;border-collapse:collapse'>"
                f"<thead><tr>{hdr}</tr></thead>"
                f"<tbody>{inner_rows}</tbody></table></div>")

    # ── Breadcrumb + back ──
    if sel_camp:
        bc = (f"<span style='color:#A8A39A'>Campaigns</span>"
              f"<span style='color:#C5C0B6'> › </span>"
              f"<span style='color:#5A554D'>{sel_camp[:50]}</span>")
        if sel_adset:
            bc += (f"<span style='color:#C5C0B6'> › </span>"
                   f"<span style='color:#5A554D'>{sel_adset[:50]}</span>")
        st.markdown(f"<div style='font-size:0.72rem;margin-bottom:6px'>{bc}</div>",
                    unsafe_allow_html=True)
        bc1, _ = st.columns([1, 9])
        with bc1:
            if st.button("← Back", key=f"bc_back_{app}_{mode}", use_container_width=True):
                if sel_adset: st.session_state[adset_key] = None
                else:
                    st.session_state[camp_key] = None
                    st.session_state[adset_key] = None
                st.rerun()

    # col widths: name | spend | cac | uninst | cac_contrib | unin_contrib | [drill+trend]
    _CW = [4.2, 1.0, 1.0, 1.0, 1.5, 1.5, 1.3]

    def _cell(txt, align="right", color="#2A2520", bold=False):
        fw = "600" if bold else "400"
        return (f"<div style='font-size:0.8rem;color:{color};padding:9px 4px;"
                f"border-bottom:1px solid #EDE8DE;text-align:{align};"
                f"font-weight:{fw};white-space:nowrap'>{txt}</div>")

    def _contrib_cell(val, fmt_fn):
        if val is None or (isinstance(val, float) and pd.isna(val)) or val == 0:
            return _cell("—", color="#C5C0B6")
        is_bad = val > 0
        col = "#E24B4A" if is_bad else "#1D9E75"
        bg  = "rgba(226,75,74,0.12)" if is_bad else "rgba(29,158,117,0.12)"
        arr = "↑" if val > 0 else "↓"
        return (f"<div style='padding:9px 4px;border-bottom:1px solid #EDE8DE;text-align:right'>"
                f"<span style='background:{bg};color:{col};font-size:0.7rem;font-weight:700;"
                f"padding:2px 7px;border-radius:5px'>{arr} {fmt_fn(abs(val))}</span></div>")

    def _tbl_header(labels):
        cols = st.columns(_CW)
        for i, (col, lbl) in enumerate(zip(cols, labels)):
            with col:
                st.markdown(
                    f"<div style='font-size:0.58rem;text-transform:uppercase;letter-spacing:0.1em;"
                    f"color:#A8A39A;padding:7px 4px;border-bottom:1px solid #E5E0D6;"
                    f"background:#F5F2ED;text-align:{'left' if i==0 else 'right'}'>{lbl}</div>",
                    unsafe_allow_html=True)

    # Max date from full dataset — used to extend trend charts past last-spend date
    _df_max_date = df["date_tz"].max() if not df.empty and "date_tz" in df.columns else None
    _cr_max_date = (cr_raw["date_tz"].max()
                    if cr_raw is not None and not cr_raw.empty and "date_tz" in cr_raw.columns
                    else _df_max_date)

    # ══════════════════════════════════════════════════════════
    #  LEVEL 1 — CAMPAIGNS
    # ══════════════════════════════════════════════════════════
    if not sel_camp:
        srch_c, _ = st.columns([3, 6])
        with srch_c:
            camp_search = st.text_input("", placeholder="Search campaigns…",
                                        key=f"camp_search_{app}_{mode}",
                                        label_visibility="collapsed")
        filtered_camps = ([c for c in all_camps if camp_search.lower() in c.lower()]
                          if camp_search else all_camps)

        hdr_l, hdr_r = st.columns([7, 3])
        with hdr_l:
            st.markdown(
                "<div style='font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
                "color:#333;margin-bottom:2px'>DRILLDOWN</div>"
                "<div style='font-size:1.05rem;font-weight:700;color:#1C1A17'>Top campaigns</div>",
                unsafe_allow_html=True)
        with hdr_r:
            st.markdown(
                f"<div style='font-size:0.72rem;color:#3a3a3a;text-align:right;margin-top:16px'>"
                f"Sorted by spend · {len(filtered_camps)} active</div>",
                unsafe_allow_html=True)

        # ── Source-level summary bar ──────────────────────────────────────
        src_summary = source_split(df_sel, "p0_uninstall_rate") if not df_sel.empty and "source" in df_sel.columns else pd.DataFrame()
        if not src_summary.empty:
            _SRC_COLORS = {"Facebook": "#378ADD", "Google": "#34A853", "Other": "#666"}
            cards_html = "<div style='display:flex;gap:8px;margin:10px 0 14px;flex-wrap:wrap'>"
            for _, srow in src_summary.sort_values("total_cost", ascending=False).iterrows():
                sg  = srow["source_group"]
                sc  = _SRC_COLORS.get(sg, "#666")
                sp  = srow["total_cost"]
                cac = srow["D0_CAC_calc"]
                unin= srow["p0_uninstall_rate"]
                spct= srow.get("spend_share", 0)
                sp_s = _fmt_spend(sp) if sp else "—"
                cac_s = f"₹{cac:,.0f}" if cac else "—"
                unin_s = f"{unin:.1f}%" if unin else "—"
                cards_html += (
                    f"<div style='background:#FFFFFF;border:1px solid #E2DDD3;border-left:3px solid {sc};"
                    f"border-radius:6px;padding:7px 12px;display:flex;align-items:center;gap:16px'>"
                    f"<span style='font-size:0.7rem;font-weight:700;color:{sc};letter-spacing:0.06em;"
                    f"text-transform:uppercase;min-width:54px'>{sg}</span>"
                    f"<span style='font-size:0.62rem;color:#A8A39A;margin-right:-8px'>spend</span>"
                    f"<span style='font-size:0.82rem;font-weight:600;color:#1C1A17'>{sp_s}"
                    f"<span style='font-size:0.62rem;color:#8A857D;margin-left:3px'>{spct:.0f}%</span></span>"
                    f"<span style='font-size:0.62rem;color:#A8A39A;margin-right:-8px'>cac</span>"
                    f"<span style='font-size:0.82rem;font-weight:600;color:#1C1A17'>{cac_s}</span>"
                    f"<span style='font-size:0.62rem;color:#A8A39A;margin-right:-8px'>unin</span>"
                    f"<span style='font-size:0.82rem;font-weight:600;color:#1C1A17'>{unin_s}</span>"
                    f"</div>"
                )
            cards_html += "</div>"
            st.markdown(cards_html, unsafe_allow_html=True)

        _tbl_header(["Campaign", "Spend", "CAC ₹", "Uninst%", "CAC contrib ₹", "Unin contrib pp", ""])

        for ci, camp_name in enumerate(filtered_camps):
            cm        = camps_metrics.get(camp_name)
            spend_val = cm.get("spend_yd")     if cm is not None else None
            cac_val   = cm.get("cac_yd")       if cm is not None else None
            unin_val  = cm.get("unin_rate_yd") if cm is not None else None
            spend_str = _fmt_spend(spend_val)
            cac_str   = f"₹{cac_val:,.0f}"  if cac_val  is not None and pd.notna(cac_val)  else "—"
            unin_str  = f"{unin_val:.1f}%"   if unin_val is not None and pd.notna(unin_val) else "—"
            cac_col   = "#E24B4A" if cac_val  is not None and pd.notna(cac_val)  and cac_val  > 500 else "#4A4540"
            unin_col  = "#E24B4A" if unin_val is not None and pd.notna(unin_val) and unin_val > 25  else "#4A4540"
            src       = camp_source_map.get(camp_name, "")
            dot_col, src_label = _src_dot_label(src)
            cac_cv    = camp_cac_map.get(camp_name,  {}).get("contribution")
            unin_cv   = camp_unin_map.get(camp_name, {}).get("contribution")
            camp_df_s = df[df["campaign"] == camp_name] if "campaign" in df.columns else pd.DataFrame()
            disp_name = (camp_name[:48] + "…") if len(camp_name) > 49 else camp_name

            c0, c1, c2, c3, c4, c5, c6 = st.columns(_CW)
            with c0:
                st.markdown(
                    f"<div style='padding:10px 4px;border-bottom:1px solid #E5E0D6;"
                    f"display:flex;align-items:center;gap:7px'>"
                    f"<span style='width:6px;height:6px;border-radius:50%;background:{dot_col};"
                    f"flex-shrink:0;display:inline-block'></span>"
                    f"<span style='font-size:0.8rem;color:#1C1A17;font-weight:500;min-width:0;"
                    f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{disp_name}</span>"
                    f"<span style='font-size:0.65rem;color:#333;flex-shrink:0'>{src_label}</span>"
                    f"</div>", unsafe_allow_html=True)
            with c1: st.markdown(_cell(spend_str, bold=True, color="#1C1A17"), unsafe_allow_html=True)
            with c2: st.markdown(_cell(cac_str, color=cac_col), unsafe_allow_html=True)
            with c3: st.markdown(_cell(unin_str, color=unin_col), unsafe_allow_html=True)
            with c4: st.markdown(_contrib_cell(cac_cv,  lambda v: f"₹{v:.0f}"), unsafe_allow_html=True)
            with c5: st.markdown(_contrib_cell(unin_cv, lambda v: f"{v:.2f}pp"), unsafe_allow_html=True)
            with c6:
                ca, cb = st.columns(2, gap="small")
                with ca:
                    if st.button("▸", key=f"drill_c1_{app}_{mode}_{ci}",
                                 use_container_width=True, help="Drill into ad sets"):
                        st.session_state[camp_key]  = camp_name
                        st.session_state[adset_key] = None
                        st.rerun()
                with cb:
                    if st.button("trend", key=f"chart_c1_{app}_{mode}_{ci}",
                                 use_container_width=True, help="7-day trend"):
                        show_trend_dialog(camp_name, camp_df_s, end_date=_df_max_date)

    # ══════════════════════════════════════════════════════════
    #  LEVEL 2 — AD SETS
    # ══════════════════════════════════════════════════════════
    elif sel_camp and not sel_adset:
        n_adsets = len(adset_contrib) if adset_contrib is not None else 0
        hdr_l, hdr_r = st.columns([7, 3])
        with hdr_l:
            st.markdown(
                "<div style='font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
                "color:#333;margin-bottom:2px'>DRILLDOWN</div>"
                f"<div style='font-size:1.05rem;font-weight:700;color:#1C1A17'>Ad sets</div>",
                unsafe_allow_html=True)
        with hdr_r:
            st.markdown(
                f"<div style='font-size:0.72rem;color:#3a3a3a;text-align:right;margin-top:16px'>"
                f"Sorted by spend · {n_adsets} active</div>",
                unsafe_allow_html=True)

        if adset_contrib is None or adset_contrib.empty:
            st.markdown("<div style='color:#444;font-size:0.82rem;padding:16px 0'>No ad set data.</div>",
                        unsafe_allow_html=True)
        else:
            _tbl_header(["Ad Set", "Spend%", "CAC ₹", "Uninst%", "CAC contrib ₹", "Unin contrib pp", ""])

            for ai, (_, arow) in enumerate(adset_contrib.iterrows()):
                aname    = arow["ad_set"]
                sig      = arow["signal"]
                b_col    = "#E24B4A" if sig == "🔴 High Risk" else ("#1D9E75" if sig == "🟢 Efficient" else "#444")
                cac_abs  = arow["spend"] / arow["orders"] if arow.get("orders", 0) > 0 else None
                unin_abs = arow["unin"]  / arow["orders"] * 100 if arow.get("orders", 0) > 0 else None
                cac_cv   = adset_cac_map.get(aname,  {}).get("contribution")
                unin_cv  = adset_unin_map.get(aname, {}).get("contribution")
                _sp      = f"{arow['spend_pct']:.1f}%" if pd.notna(arow.get("spend_pct")) else "—"
                cac_str  = f"₹{cac_abs:,.0f}"   if cac_abs  is not None else "—"
                unin_str = f"{unin_abs:.1f}%"    if unin_abs is not None else "—"
                cac_col  = "#E24B4A" if cac_abs  is not None and cac_abs  > 500 else "#4A4540"
                unin_col = "#E24B4A" if unin_abs is not None and unin_abs > 25  else "#4A4540"
                adset_df_s = (df[(df["campaign"] == sel_camp) & (df["ad_set"] == aname)]
                              if "ad_set" in df.columns else pd.DataFrame())
                disp_name = (aname[:48] + "…") if len(aname) > 49 else aname

                c0, c1, c2, c3, c4, c5, c6 = st.columns(_CW)
                with c0:
                    st.markdown(
                        f"<div style='padding:10px 4px 10px 10px;border-bottom:1px solid #E5E0D6;"
                        f"border-left:2px solid {b_col};display:flex;align-items:center;gap:7px'>"
                        f"<span style='font-size:0.62rem;padding:1px 5px;border-radius:3px;"
                        f"background:{b_col}20;color:{b_col};flex-shrink:0'>{sig.split()[0]}</span>"
                        f"<span style='font-size:0.8rem;color:#1C1A17;min-width:0;overflow:hidden;"
                        f"text-overflow:ellipsis;white-space:nowrap'>{disp_name}</span>"
                        f"</div>", unsafe_allow_html=True)
                with c1: st.markdown(_cell(_sp), unsafe_allow_html=True)
                with c2: st.markdown(_cell(cac_str, color=cac_col), unsafe_allow_html=True)
                with c3: st.markdown(_cell(unin_str, color=unin_col), unsafe_allow_html=True)
                with c4: st.markdown(_contrib_cell(cac_cv,  lambda v: f"₹{v:.0f}"), unsafe_allow_html=True)
                with c5: st.markdown(_contrib_cell(unin_cv, lambda v: f"{v:.2f}pp"), unsafe_allow_html=True)
                with c6:
                    if app in CREATIVE_QUERY_IDS:
                        ca, cb = st.columns(2, gap="small")
                        with ca:
                            if st.button("▸", key=f"drill_a2_{app}_{mode}_{ai}",
                                         use_container_width=True, help="Drill into creatives"):
                                st.session_state[adset_key] = aname
                                st.rerun()
                        with cb:
                            if st.button("trend", key=f"chart_a2_{app}_{mode}_{ai}",
                                         use_container_width=True, help="7-day trend"):
                                show_trend_dialog(aname, adset_df_s, end_date=_df_max_date)
                    else:
                        if st.button("trend", key=f"chart_a2_{app}_{mode}_{ai}",
                                     use_container_width=True, help="7-day trend"):
                            show_trend_dialog(aname, adset_df_s, end_date=_df_max_date)

    # ══════════════════════════════════════════════════════════
    #  LEVEL 3 — CREATIVES
    # ══════════════════════════════════════════════════════════
    elif sel_camp and sel_adset and cr_sel is not None:
        cr_abs = creative_yd_contribution(cr_sel, campaign_filter=sel_camp, adset_filter=sel_adset)
        hdr_l, hdr_r = st.columns([7, 3])
        with hdr_l:
            st.markdown(
                "<div style='font-size:0.6rem;text-transform:uppercase;letter-spacing:0.12em;"
                "color:#333;margin-bottom:2px'>DRILLDOWN</div>"
                f"<div style='font-size:1.05rem;font-weight:700;color:#1C1A17'>Creatives</div>",
                unsafe_allow_html=True)
        with hdr_r:
            st.markdown(
                f"<div style='font-size:0.72rem;color:#3a3a3a;text-align:right;margin-top:16px'>"
                f"{len(cr_abs)} creatives</div>",
                unsafe_allow_html=True)

        if cr_abs.empty:
            st.markdown("<div style='color:#444;font-size:0.82rem;padding:16px 0'>No creative data.</div>",
                        unsafe_allow_html=True)
        else:
            _tbl_header(["Creative", "Spend%", "CAC ₹", "Uninst%", "CAC contrib ₹", "Unin contrib pp", ""])

            for ri, (_, crow) in enumerate(cr_abs.iterrows()):
                cr_name = crow["ad_creative"]
                if crow["orders_pct"] < crow["spend_pct"] and crow["unin_pct"] > crow["spend_pct"]:
                    cr_col = "#E24B4A"
                elif crow["orders_pct"] > crow["spend_pct"] and crow["unin_pct"] < crow["spend_pct"]:
                    cr_col = "#1D9E75"
                else:
                    cr_col = "#444"
                cr_cac       = crow["spend"] / crow["orders"] if crow["orders"] > 0 else None
                cr_unin_rate = crow["unin"]  / crow["orders"] * 100 if crow["orders"] > 0 else None
                cac_str  = f"₹{cr_cac:,.0f}"     if cr_cac       is not None else "—"
                unin_str = f"{cr_unin_rate:.1f}%" if cr_unin_rate is not None else "—"
                cac_col  = "#E24B4A" if cr_cac       is not None and cr_cac       > 500 else "#4A4540"
                unin_col = "#E24B4A" if cr_unin_rate is not None and cr_unin_rate > 30  else "#4A4540"
                cac_cv   = kit_cr_cac_map.get(cr_name,  {}).get("contribution")
                unin_cv  = kit_cr_unin_map.get(cr_name, {}).get("contribution")
                _sp      = f"{crow['spend_pct']:.1f}%"
                cr_df_t  = cr_raw[cr_raw["ad_creative"] == cr_name] if cr_raw is not None else pd.DataFrame()
                disp_name = (cr_name[:52] + "…") if len(cr_name) > 53 else cr_name

                c0, c1, c2, c3, c4, c5, c6 = st.columns(_CW)
                with c0:
                    st.markdown(
                        f"<div style='padding:10px 4px 10px 10px;border-bottom:1px solid #E5E0D6;"
                        f"border-left:2px solid {cr_col};font-size:0.8rem;color:#1C1A17;font-weight:500;"
                        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis' title='{cr_name}'>"
                        f"{disp_name}</div>", unsafe_allow_html=True)
                with c1: st.markdown(_cell(_sp), unsafe_allow_html=True)
                with c2: st.markdown(_cell(cac_str, color=cac_col), unsafe_allow_html=True)
                with c3: st.markdown(_cell(unin_str, color=unin_col), unsafe_allow_html=True)
                with c4: st.markdown(_contrib_cell(cac_cv,  lambda v: f"₹{v:.0f}"), unsafe_allow_html=True)
                with c5: st.markdown(_contrib_cell(unin_cv, lambda v: f"{v:.2f}pp"), unsafe_allow_html=True)
                with c6:
                    if st.button("trend", key=f"chart_cr_{app}_{mode}_{ri}",
                                 use_container_width=True, help="7-day trend"):
                        show_trend_dialog(cr_name, cr_df_t, end_date=_cr_max_date)



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

def category_mix_view(app: str = "Seekho"):
    """Category → Meta/Google campaign drill-down: 7-day trend + creative/adset analysis."""

    SOUTH_LANGS = {"tamil", "telugu", "kannada", "malayalam"}
    app_color = APP_COLORS.get(app, "#B8944A")

    # Prefixes that are app/language identifiers — skip and use next segment as category
    _APP_PREFIXES = {
        "seekho", "nerchuko", "arivu", "vidhya", "kali",
        # compound seekho+language (no underscore in creative name)
        "seekhotelugu", "seekhotamil", "seekhokannada", "seekhomalayalam",
        "seekhohindi", "seekhobengali", "seekhomarathi", "seekhopunjabi",
    }
    # Abbreviation → full display name
    _EXPAND = {
        "eng": "English", "hin": "Hindi", "kan": "Kannada", "tel": "Telugu",
        "tam": "Tamil",   "mal": "Malayalam", "ben": "Bengali", "mar": "Marathi",
        "pun": "Punjabi", "biz": "Business",  "fin": "Finance", "astro": "Astrology",
        "insta": "Instagram", "ret": "Retention", "acq": "Acquisition",
        "sub": "Subscription", "p0": "P0", "p1": "P1",
    }
    # Values that mean "no category identified" → bucket under Google
    _NULL_VALS = {"null", "none", "unknown", "nan", ""}

    def _parse_cat(name: str) -> str:
        if not isinstance(name, str):
            return "__google__"
        cleaned = name.strip().lower()
        if cleaned in _NULL_VALS:
            return "__google__"
        parts = [p for p in cleaned.split("_") if p]
        if not parts:
            return "__google__"
        seg = parts[0]
        # If first segment is an app/language prefix, move to next
        if seg in _APP_PREFIXES and len(parts) >= 2:
            seg = parts[1]
            # seekho + south-lang_underscore case: seekho_telugu_<cat>
            if seg in SOUTH_LANGS and len(parts) >= 3:
                seg = parts[2]
        return _EXPAND.get(seg, seg.replace("-", " ").title())

    def _fmt_spend(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        if v >= 1e7: return f"₹{v/1e7:.1f}Cr"
        if v >= 1e5: return f"₹{v/1e5:.1f}L"
        if v >= 1e3: return f"₹{v/1e3:.0f}k"
        return f"₹{int(v)}"

    def _base_fig(h: int = 190, legend: bool = False) -> go.Figure:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FAFAF8",
            font=dict(family="Inter,sans-serif", color="#5A554D", size=10),
            height=h, margin=dict(l=4, r=4, t=28, b=4),
            showlegend=legend,
            legend=dict(orientation="h", y=1.18, x=0, font=dict(size=9)) if legend else {},
            xaxis=dict(
                showgrid=False, zeroline=False,
                type="date", tickformat="%b %d",
                tickfont=dict(size=9, color="#8A857D"),
            ),
        )
        return fig

    def _section_label(text: str, dot_color: str):
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:7px;margin:10px 0 6px'>"
            f"<span style='width:8px;height:8px;border-radius:50%;background:{dot_color};"
            f"display:inline-block;flex-shrink:0'></span>"
            f"<span style='font-size:0.62rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:.12em;color:{dot_color}'>{text}</span></div>",
            unsafe_allow_html=True,
        )

    def _chart_label(text: str):
        st.markdown(
            f"<div style='font-size:0.6rem;color:#A8A39A;text-transform:uppercase;"
            f"letter-spacing:.1em;margin-bottom:2px'>{text}</div>",
            unsafe_allow_html=True,
        )

    # ── helpers for top-80% count ──
    def _top80_creatives(grp: pd.DataFrame) -> int:
        s = grp.sort_values("total_cost", ascending=False)
        tot = s["total_cost"].sum()
        if tot == 0: return 0
        cum = s["total_cost"].cumsum()
        return int((cum <= tot * 0.8).sum()) + 1

    def _top80_adsets(grp: pd.DataFrame) -> int:
        s = grp.groupby("ad_set")["total_cost"].sum().sort_values(ascending=False)
        tot = s.sum()
        if tot == 0: return 0
        cum = s.cumsum()
        return int((cum <= tot * 0.8).sum()) + 1

    # ── load data ──
    df = safe_fetch(app)
    if df.empty:
        st.warning(f"No data for {app}.")
        return

    cr_df = pd.DataFrame()
    if app in CREATIVE_QUERY_IDS:
        try:
            cr_df = add_derived_metrics(fetch_creative_data(app))
        except Exception:
            pass

    # ── 14-day window ──
    all_dates = sorted(df["date_tz"].unique())
    last7 = set(all_dates[-14:])
    df7 = df[df["date_tz"].isin(last7)].copy()

    cr7 = pd.DataFrame()
    if not cr_df.empty and "date_tz" in cr_df.columns:
        cr_dates = sorted(cr_df["date_tz"].unique())
        cr7 = cr_df[cr_df["date_tz"].isin(set(cr_dates[-14:]))].copy()

    # ── assign categories ──
    # Creative names are the source of truth for categories.
    # For Meta: each campaign is assigned the category of its most-spent creative.
    # For Google (no creative data): fall back to campaign name parsing.
    if not cr7.empty and "ad_creative" in cr7.columns:
        cr7["category"] = cr7["ad_creative"].apply(_parse_cat)
        # build campaign → dominant_category map from creative data
        camp_cat_map = (cr7.groupby(["campaign", "category"])["total_cost"]
                        .sum().reset_index()
                        .sort_values("total_cost", ascending=False)
                        .drop_duplicates("campaign")
                        .set_index("campaign")["category"]
                        .to_dict())
    else:
        camp_cat_map = {}

    def _assign_cat(row) -> str:
        # Use creative-derived category if available, else parse from campaign name
        return camp_cat_map.get(row["campaign"], _parse_cat(row["campaign"]))

    df7["category"] = df7.apply(_assign_cat, axis=1)

    # ── category totals ──
    # Meta spend/orders/unin from creative data (source of truth for Meta categories).
    # Google spend from df7 filtered by source=google.
    meta_stats = pd.DataFrame()
    if not cr7.empty:
        meta_stats = (cr7.groupby("category")
                      .agg(spend=("total_cost", "sum"),
                           orders=("D0_paid_users", "sum"),
                           unin=("p0_unin_users", "sum"))
                      .reset_index())

    goog_stats = pd.DataFrame()
    if "source" in df7.columns:
        goog_df7 = df7[df7["source"].str.lower() == "google"]
        if not goog_df7.empty:
            goog_stats = (goog_df7.groupby("category")
                          .agg(spend=("total_cost", "sum"),
                               orders=("D0_paid_users", "sum"),
                               unin=("p0_unin_users", "sum"))
                          .reset_index())

    cat_stats = pd.concat([meta_stats, goog_stats], ignore_index=True)
    if cat_stats.empty:
        st.info("No data available.")
        return
    cat_stats = (cat_stats.groupby("category")
                 .agg(spend=("spend", "sum"),
                      orders=("orders", "sum"),
                      unin=("unin", "sum"))
                 .reset_index())
    cat_stats["cac"] = cat_stats.apply(
        lambda r: r["spend"] / r["orders"] if r["orders"] > 0 else None, axis=1)
    cat_stats["unin_rate"] = cat_stats.apply(
        lambda r: r["unin"] / r["orders"] * 100 if r["orders"] > 0 else None, axis=1)
    # Sort by spend descending, but keep __google__ (uncategorised) last
    cat_stats["_sort"] = cat_stats["category"].apply(lambda c: 1 if c == "__google__" else 0)
    cat_stats = cat_stats.sort_values(["_sort", "spend"], ascending=[True, False]).drop(columns="_sort")

    # ── panel renderers ──

    def _render_trend(camp_df: pd.DataFrame, src_color: str):
        """7-day Spend bars + CAC line + Uninstall% line."""
        daily = (camp_df.groupby("date_tz")
                 .agg(spend=("total_cost", "sum"),
                      orders=("D0_paid_users", "sum"),
                      unin=("p0_unin_users", "sum"))
                 .reset_index().sort_values("date_tz"))
        daily["cac"] = daily.apply(
            lambda r: r["spend"] / r["orders"] if r["orders"] > 0 else None, axis=1)
        daily["unin_rate"] = daily.apply(
            lambda r: r["unin"] / r["orders"] * 100 if r["orders"] > 0 else None, axis=1)
        daily["ds"] = daily["date_tz"].astype(str)
        rc, gc, bc = _hex_to_rgb(src_color)

        fig = _base_fig(h=200, legend=True)
        fig.add_trace(go.Bar(
            x=daily["ds"], y=daily["spend"], name="Spend",
            marker_color=f"rgba({rc},{gc},{bc},0.22)", yaxis="y3",
            hovertemplate="₹%{y:,.0f}<extra>Spend</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["ds"], y=daily["cac"], name="CAC ₹",
            mode="lines+markers",
            line=dict(color="#E24B4A", width=2),
            marker=dict(size=5, color="#E24B4A"),
            hovertemplate="₹%{y:,.0f}<extra>CAC</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["ds"], y=daily["unin_rate"], name="Unin%",
            mode="lines+markers",
            line=dict(color="#D4537E", width=2, dash="dot"),
            marker=dict(size=5, color="#D4537E"),
            yaxis="y2",
            hovertemplate="%{y:.1f}%<extra>Unin</extra>",
        ))
        fig.update_layout(
            yaxis=dict(title="CAC ₹", gridcolor="#F0EBE1", tickprefix="₹",
                       tickfont=dict(size=9), zeroline=False),
            yaxis2=dict(title="Unin%", overlaying="y", side="right",
                        ticksuffix="%", tickfont=dict(size=9), zeroline=False, showgrid=False),
            yaxis3=dict(overlaying="y", side="right", showticklabels=False, showgrid=False, zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    def _render_saturation(camp_cr: pd.DataFrame) -> bool:
        """Combined chart: Spend bars + CAC line + # Creatives line, with saturation annotation.
        Returns True if chart was rendered, False if not enough data (caller should fall back)."""
        daily = (camp_cr.groupby("date_tz")
                 .agg(spend=("total_cost", "sum"),
                      orders=("D0_paid_users", "sum"),
                      n_creatives=("ad_creative", "nunique"))
                 .reset_index().sort_values("date_tz"))
        daily["cac"] = daily.apply(
            lambda r: r["spend"] / r["orders"] if r["orders"] > 0 else None, axis=1)
        daily["ds"] = daily["date_tz"].astype(str)

        if daily["cac"].dropna().empty:
            return False

        # Saturation point = day with lowest CAC (best efficiency)
        best_idx  = daily["cac"].idxmin()
        best_date = daily.loc[best_idx, "ds"]
        best_cac  = daily.loc[best_idx, "cac"]
        best_ncr  = daily.loc[best_idx, "n_creatives"]
        curr_ncr  = daily["n_creatives"].iloc[-1]
        curr_cac  = daily["cac"].dropna().iloc[-1]

        # Signal: compare current creative count to optimal
        delta_cr   = curr_ncr - best_ncr
        delta_cac  = curr_cac - best_cac if pd.notna(curr_cac) else 0
        if delta_cr > 2 and delta_cac > 50:
            signal = ("⚠ Possible dilution", "#E24B4A",
                      f"Running {curr_ncr} creatives now vs {best_ncr} at best CAC. "
                      f"CAC up ₹{abs(delta_cac):.0f} since saturation point.")
        elif delta_cr < -2 and delta_cac > 50:
            signal = ("↓ Under-diversified", "#D85A30",
                      f"Only {curr_ncr} creatives running vs {best_ncr} at best CAC. "
                      f"Consider adding creatives.")
        else:
            signal = ("✓ Creative count healthy", "#1D9E75",
                      f"Current {curr_ncr} creatives near optimal ({best_ncr} at best CAC ₹{best_cac:.0f}).")

        rc, gc, bc = _hex_to_rgb("#378ADD")
        fig = _base_fig(h=220, legend=True)
        fig.add_trace(go.Bar(
            x=daily["ds"], y=daily["spend"], name="Spend",
            marker_color=f"rgba({rc},{gc},{bc},0.18)", yaxis="y3",
            hovertemplate="₹%{y:,.0f}<extra>Spend</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["ds"], y=daily["cac"], name="CAC ₹",
            mode="lines+markers",
            line=dict(color="#E24B4A", width=2),
            marker=dict(size=5, color="#E24B4A"),
            hovertemplate="₹%{y:,.0f}<extra>CAC</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["ds"], y=daily["n_creatives"], name="# Creatives",
            mode="lines+markers",
            line=dict(color="#378ADD", width=2, dash="dot"),
            marker=dict(size=5, color="#378ADD"),
            yaxis="y2",
            hovertemplate="%{y} creatives<extra></extra>",
        ))
        # Saturation point annotation
        fig.add_annotation(
            x=best_date, y=best_cac,
            text=f"Best CAC<br>({best_ncr} cr)",
            showarrow=True, arrowhead=2, arrowcolor="#1D9E75",
            font=dict(size=9, color="#1D9E75"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#1D9E75", borderwidth=1,
            ax=0, ay=-36,
        )
        fig.update_layout(
            yaxis=dict(title="CAC ₹", gridcolor="#F0EBE1", tickprefix="₹",
                       tickfont=dict(size=9), zeroline=False),
            yaxis2=dict(title="# Creatives", overlaying="y", side="right",
                        tickfont=dict(size=9), zeroline=False, showgrid=False),
            yaxis3=dict(overlaying="y", side="right", showticklabels=False, showgrid=False, zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Insight pill
        sig_label, sig_col, sig_msg = signal
        st.markdown(
            f"<div style='background:rgba({','.join(str(x) for x in _hex_to_rgb(sig_col))},0.08);"
            f"border:1px solid {sig_col};border-radius:8px;padding:8px 14px;margin-top:-6px;"
            f"display:flex;align-items:flex-start;gap:10px'>"
            f"<span style='font-size:0.72rem;font-weight:700;color:{sig_col};white-space:nowrap'>{sig_label}</span>"
            f"<span style='font-size:0.72rem;color:#4A4540'>{sig_msg}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return True

    def _render_sparklines_meta(camp_cr: pd.DataFrame):
        """Creatives running (daily) + creatives at 80% spend (daily)."""
        cr_daily = (camp_cr.groupby("date_tz")
                    .agg(n_creatives=("ad_creative", "nunique"))
                    .reset_index().sort_values("date_tz"))
        cr_daily["ds"] = cr_daily["date_tz"].astype(str)

        top80_s = (camp_cr.groupby("date_tz")
                   .apply(_top80_creatives)
                   .reset_index().rename(columns={0: "n_top80"})
                   .sort_values("date_tz"))
        top80_s["ds"] = top80_s["date_tz"].astype(str)

        c1, c2 = st.columns(2)
        with c1:
            _chart_label("Creatives Running · Meta")
            fig = _base_fig(h=120)
            fig.add_trace(go.Scatter(
                x=cr_daily["ds"], y=cr_daily["n_creatives"], mode="lines+markers",
                line=dict(color="#378ADD", width=2),
                fill="tozeroy", fillcolor="rgba(55,138,221,0.08)",
                hovertemplate="%{y} creatives<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            _chart_label("Creatives at 80% Spend · Meta")
            fig = _base_fig(h=120)
            fig.add_trace(go.Scatter(
                x=top80_s["ds"], y=top80_s["n_top80"], mode="lines+markers",
                line=dict(color="#B8944A", width=2),
                fill="tozeroy", fillcolor="rgba(184,148,74,0.08)",
                hovertemplate="%{y} creatives<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)

    def _render_sparklines_google(camp_goog: pd.DataFrame):
        """Ad sets running (daily) + ad sets at 80% spend (daily)."""
        if "ad_set" not in camp_goog.columns:
            st.info("No ad set data.")
            return
        as_daily = (camp_goog.groupby("date_tz")
                    .agg(n_adsets=("ad_set", "nunique"))
                    .reset_index().sort_values("date_tz"))
        as_daily["ds"] = as_daily["date_tz"].astype(str)

        top80_s = (camp_goog.groupby("date_tz")
                   .apply(_top80_adsets)
                   .reset_index().rename(columns={0: "n_top80"})
                   .sort_values("date_tz"))
        top80_s["ds"] = top80_s["date_tz"].astype(str)

        c1, c2 = st.columns(2)
        with c1:
            _chart_label("Ad Sets Running · Google")
            fig = _base_fig(h=120)
            fig.add_trace(go.Scatter(
                x=as_daily["ds"], y=as_daily["n_adsets"], mode="lines+markers",
                line=dict(color="#34A853", width=2),
                fill="tozeroy", fillcolor="rgba(52,168,83,0.08)",
                hovertemplate="%{y} ad sets<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            _chart_label("Ad Sets at 80% Spend · Google")
            fig = _base_fig(h=120)
            fig.add_trace(go.Scatter(
                x=top80_s["ds"], y=top80_s["n_top80"], mode="lines+markers",
                line=dict(color="#B8944A", width=2),
                fill="tozeroy", fillcolor="rgba(184,148,74,0.08)",
                hovertemplate="%{y} ad sets<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)

    def _render_spend_dist(data_df: pd.DataFrame, unit_col: str, unit_label: str, color: str):
        """Avg spend per unit/day + 80th‑%ile unit spend/day (both line charts)."""
        daily_agg = (data_df.groupby("date_tz")
                     .agg(total_spend=("total_cost", "sum"),
                          n_units=(unit_col, "nunique"))
                     .reset_index().sort_values("date_tz"))
        daily_agg["avg"] = daily_agg["total_spend"] / daily_agg["n_units"]
        daily_agg["ds"]  = daily_agg["date_tz"].astype(str)

        def _p80(grp):
            per_unit = grp.groupby(unit_col)["total_cost"].sum()
            return float(per_unit.quantile(0.8)) if not per_unit.empty else None

        p80_s = (data_df.groupby("date_tz")
                 .apply(_p80)
                 .reset_index().rename(columns={0: "p80"})
                 .sort_values("date_tz"))
        p80_s["ds"] = p80_s["date_tz"].astype(str)

        rc, gc, bc = _hex_to_rgb(color)
        c1, c2 = st.columns(2)
        with c1:
            _chart_label(f"Avg Spend / {unit_label}")
            fig = _base_fig(h=140)
            fig.add_trace(go.Scatter(
                x=daily_agg["ds"], y=daily_agg["avg"], mode="lines+markers",
                line=dict(color=color, width=2),
                fill="tozeroy", fillcolor=f"rgba({rc},{gc},{bc},0.08)",
                hovertemplate="₹%{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickprefix="₹",
                                         tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            _chart_label(f"80th %ile {unit_label} Spend")
            fig = _base_fig(h=140)
            fig.add_trace(go.Scatter(
                x=p80_s["ds"], y=p80_s["p80"], mode="lines+markers",
                line=dict(color="#D85A30", width=2),
                fill="tozeroy", fillcolor="rgba(216,90,48,0.08)",
                hovertemplate="₹%{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(yaxis=dict(gridcolor="#F0EBE1", tickprefix="₹",
                                         tickfont=dict(size=9), zeroline=False))
            st.plotly_chart(fig, use_container_width=True)

    # ── per-category render ──
    for _, cat_row in cat_stats.iterrows():
        cat       = cat_row["category"]
        disp_cat  = "Google (Uncategorised)" if cat == "__google__" else cat
        cac_str   = f"₹{int(cat_row['cac'])}"      if (cat_row["cac"]      and pd.notna(cat_row["cac"]))      else "—"
        unin_str  = f"{cat_row['unin_rate']:.1f}%"  if (cat_row["unin_rate"] and pd.notna(cat_row["unin_rate"])) else "—"
        n_camps   = df7[df7["category"] == cat]["campaign"].nunique()

        with st.expander(
            f"{disp_cat}  ·  {_fmt_spend(cat_row['spend'])}  ·  CAC {cac_str}  ·  Unin {unin_str}  ·  {n_camps} campaigns",
            expanded=False,
        ):
            cat_df = df7[df7["category"] == cat]

            has_src = "source" in cat_df.columns
            cat_meta_df = cat_df[cat_df["source"].str.lower() == "facebook"] if has_src else pd.DataFrame()
            cat_goog_df = cat_df[cat_df["source"].str.lower() == "google"]   if has_src else pd.DataFrame()

            # ════ META ════
            cat_cr_df = cr7[cr7["category"] == cat] if not cr7.empty else pd.DataFrame()
            if not cat_cr_df.empty:
                _section_label("Meta", "#378ADD")

                # Campaign list and spend from creative data (consistent source)
                meta_camps = (cat_cr_df.groupby("campaign")["total_cost"]
                              .sum().sort_values(ascending=False).index.tolist())
                sel_meta = st.selectbox(
                    "Meta Campaign", meta_camps,
                    key=f"cm_meta_{app}_{cat}",
                    label_visibility="collapsed",
                )
                meta_camp_df = cat_meta_df[cat_meta_df["campaign"] == sel_meta] if has_src else pd.DataFrame()
                meta_camp_cr = cat_cr_df[cat_cr_df["campaign"] == sel_meta]

                if not meta_camp_cr.empty:
                    # Use creative data for ALL Meta panels — keeps spend consistent
                    if not _render_saturation(meta_camp_cr):
                        # No paid conversions (e.g. retention campaign) — fall back to trend
                        _render_trend(meta_camp_cr, "#378ADD")
                    _render_sparklines_meta(meta_camp_cr)
                    _render_spend_dist(meta_camp_cr, "ad_creative", "Creative", "#378ADD")
                else:
                    # Fall back to APP_QUERY_IDS for trend only
                    _render_trend(meta_camp_df, "#378ADD")
                    st.markdown(
                        "<div style='background:#F8F5F0;border-radius:8px;padding:10px 14px;"
                        "font-size:0.78rem;color:#8A857D;text-align:center;margin:4px 0'>"
                        "No Meta creative data for this campaign</div>",
                        unsafe_allow_html=True,
                    )

            # ════ GOOGLE ════
            if not cat_goog_df.empty:
                if not cat_meta_df.empty:
                    st.markdown("<div style='height:1px;background:#EDE8DE;margin:14px 0 4px'></div>",
                                unsafe_allow_html=True)
                _section_label("Google", "#34A853")

                goog_camps = (cat_goog_df.groupby("campaign")["total_cost"]
                              .sum().sort_values(ascending=False).index.tolist())
                sel_goog = st.selectbox(
                    "Google Campaign", goog_camps,
                    key=f"cm_goog_{app}_{cat}",
                    label_visibility="collapsed",
                )
                goog_camp_df = cat_goog_df[cat_goog_df["campaign"] == sel_goog]

                _render_trend(goog_camp_df, "#34A853")
                _render_sparklines_google(goog_camp_df)
                if "ad_set" in goog_camp_df.columns:
                    _render_spend_dist(goog_camp_df, "ad_set", "Ad Set", "#34A853")

            if cat_meta_df.empty and cat_goog_df.empty:
                st.info("No campaign data found for this category.")


# ════════════════════════════════════════════════════════════════════════════
#  Daily Adviser — prioritised budget action recommendations
# ════════════════════════════════════════════════════════════════════════════

CAC_TARGET   = 500.0
UNIN_TARGET  = 15.0   # percent

# Spend floors to filter noise
_MIN_SPEND_CREATIVE  = 2_000
_MIN_SPEND_ADSET     = 5_000
_MIN_SPEND_CAMPAIGN  = 10_000

def _adviser_score(cac, unin, spend=0, cac_target=CAC_TARGET, unin_target=UNIN_TARGET):
    """Return (action, urgency, reason_parts) for a single entity."""
    try:
        cac  = float(cac)
        unin = float(unin)
    except (TypeError, ValueError):
        return "WATCH", "neutral", ["Insufficient data"]
    if pd.isna(cac) or pd.isna(unin):
        return "WATCH", "neutral", ["Insufficient data"]
    cac_ratio  = cac  / cac_target  if cac_target  else 0
    unin_ratio = unin / unin_target if unin_target else 0

    if cac_ratio >= 1.4 and unin_ratio >= 1.5:
        return "PAUSE", "urgent", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target)", f"Uninstall {unin:.1f}% ({unin_ratio:.1f}x target)"]
    if cac_ratio >= 2.0:
        return "PAUSE", "urgent", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target) — extremely high"]
    if unin_ratio >= 2.5:
        return "PAUSE", "urgent", [f"Uninstall {unin:.1f}% ({unin_ratio:.1f}x target) — very high churn"]
    if cac_ratio >= 1.2 and unin_ratio >= 1.2:
        return "DECREASE BUDGET", "warn", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target)", f"Uninstall {unin:.1f}% ({unin_ratio:.1f}x target)"]
    if cac_ratio >= 1.2:
        return "DECREASE BUDGET", "warn", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target)", f"Uninstall {unin:.1f}% (ok)"]
    if unin_ratio >= 1.5:
        return "DECREASE BUDGET", "warn", [f"Uninstall {unin:.1f}% ({unin_ratio:.1f}x target)", f"CAC ₹{cac:,.0f} (ok)"]
    if cac_ratio <= 0.8 and unin_ratio <= 0.85:
        return "SCALE", "good", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target) — efficient", f"Uninstall {unin:.1f}% — low churn"]
    if cac_ratio <= 0.9 and unin_ratio <= 1.0:
        return "INCREASE BUDGET", "good", [f"CAC ₹{cac:,.0f} — below target", f"Uninstall {unin:.1f}% — within target"]
    return "WATCH", "neutral", [f"CAC ₹{cac:,.0f} ({cac_ratio:.1f}x target)", f"Uninstall {unin:.1f}% ({unin_ratio:.1f}x target)"]


def _agg_3day(df: pd.DataFrame, group_col: str, days: int = 3) -> pd.DataFrame:
    """Aggregate last N days cumulatively by group_col."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame()
    cutoff = sorted(df["date_tz"].unique())[-days] if len(df["date_tz"].unique()) >= days else df["date_tz"].min()
    sub = df[df["date_tz"] >= cutoff]
    agg = (sub.groupby(group_col)
              .agg(spend=("total_cost", "sum"),
                   paid=("D0_paid_users", "sum"),
                   unin=("p0_unin_users", "sum"))
              .reset_index())
    agg["cac"]  = agg["spend"] / agg["paid"].clip(lower=1)
    agg["unin_rate"] = (agg["unin"] / agg["paid"].clip(lower=1) * 100)
    return agg


def _action_card(name: str, level: str, action: str, urgency: str,
                 reasons: list, spend: float, paid: int, color: str) -> str:
    _ACTION_COLORS = {
        "PAUSE":           ("#E24B4A", "🛑"),
        "DECREASE BUDGET": ("#E8883A", "📉"),
        "SCALE":           ("#1D9E75", "🚀"),
        "INCREASE BUDGET": ("#378ADD", "📈"),
        "SHIFT BUDGET":    ("#9B59B6", "🔀"),
        "WATCH":           ("#555",    "👀"),
    }
    ac, icon = _ACTION_COLORS.get(action, ("#555", "•"))
    urgency_badge = {"urgent": f"<span style='background:#E24B4A22;color:#E24B4A;font-size:0.6rem;padding:1px 6px;border-radius:3px;font-weight:700'>URGENT</span>",
                     "warn":   f"<span style='background:#E8883A22;color:#E8883A;font-size:0.6rem;padding:1px 6px;border-radius:3px;font-weight:700'>REVIEW</span>",
                     "good":   f"<span style='background:#1D9E7522;color:#1D9E75;font-size:0.6rem;padding:1px 6px;border-radius:3px;font-weight:700'>OPPORTUNITY</span>",
                     "neutral":f"<span style='background:#8A857D22;color:#8A857D;font-size:0.6rem;padding:1px 6px;border-radius:3px;font-weight:700'>MONITOR</span>",
    }.get(urgency, "")
    level_badge = f"<span style='font-size:0.58rem;color:#8A857D;text-transform:uppercase;letter-spacing:.06em'>{level}</span>"
    reason_html = "".join(f"<div style='font-size:0.72rem;color:#7A756D;margin-top:2px'>· {r}</div>" for r in reasons)
    spend_str = f"₹{spend/1000:.0f}k" if spend >= 1000 else f"₹{spend:.0f}"
    meta = f"<div style='font-size:0.7rem;color:#8A857D;margin-top:4px'>Spend {spend_str} · {paid} paid users (3d)</div>"
    disp = (name[:55] + "…") if len(name) > 56 else name
    return f"""
<div style='border-left:3px solid {ac};padding:10px 14px;margin:6px 0;background:#F8F5F0;border-radius:0 6px 6px 0'>
  <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px'>
    <span style='font-size:1rem'>{icon}</span>
    <span style='font-size:0.88rem;font-weight:700;color:{ac}'>{action}</span>
    {urgency_badge}
    {level_badge}
  </div>
  <div style='font-size:0.8rem;color:#2A2520;font-weight:500'>{disp}</div>
  {reason_html}
  {meta}
</div>"""


def adviser_view(df: pd.DataFrame, cr_raw, app: str, color: str):
    """Daily budget action adviser — campaign / adset / creative level."""
    st.markdown(
        "<div style='font-size:0.6rem;text-transform:uppercase;letter-spacing:.12em;color:#333;margin-bottom:2px'>DAILY ADVISER</div>"
        f"<div style='font-size:1.1rem;font-weight:700;color:#1C1A17;margin-bottom:2px'>Budget Actions</div>"
        f"<div style='font-size:0.72rem;color:#444;margin-bottom:16px'>Target CAC ₹{CAC_TARGET:,.0f} · Uninstall {UNIN_TARGET:.0f}% · Based on last 3 days</div>",
        unsafe_allow_html=True)

    cards = []  # list of (urgency_rank, html)
    urgency_rank = {"urgent": 0, "warn": 1, "good": 2, "neutral": 3}

    # ── Campaign level ────────────────────────────────────────────────────
    camp_agg = _agg_3day(df, "campaign")
    for _, row in camp_agg.iterrows():
        if row["spend"] < _MIN_SPEND_CAMPAIGN: continue
        if row["paid"] < 3: continue
        action, urgency, reasons = _adviser_score(row["cac"], row["unin_rate"])
        if action == "WATCH": continue
        reasons.append(f"Campaign-level signal")
        html = _action_card(row["campaign"], "Campaign", action, urgency,
                            reasons, row["spend"], int(row["paid"]), color)
        cards.append((urgency_rank[urgency], html))

    # ── Ad set level ──────────────────────────────────────────────────────
    if "ad_set" in df.columns:
        adset_agg = _agg_3day(df, "ad_set")
        for _, row in adset_agg.iterrows():
            if row["spend"] < _MIN_SPEND_ADSET: continue
            if row["paid"] < 2: continue
            action, urgency, reasons = _adviser_score(row["cac"], row["unin_rate"])
            if action == "WATCH": continue
            html = _action_card(row["ad_set"], "Ad Set", action, urgency,
                                reasons, row["spend"], int(row["paid"]), color)
            cards.append((urgency_rank[urgency], html))

    # ── Creative level ────────────────────────────────────────────────────
    if cr_raw is not None and not cr_raw.empty and "ad_creative" in cr_raw.columns:
        cr_agg = _agg_3day(cr_raw, "ad_creative")
        for _, row in cr_agg.iterrows():
            if row["spend"] < _MIN_SPEND_CREATIVE: continue
            if row["paid"] < 2: continue
            action, urgency, reasons = _adviser_score(row["cac"], row["unin_rate"])
            if action == "WATCH": continue
            html = _action_card(row["ad_creative"], "Creative", action, urgency,
                                reasons, row["spend"], int(row["paid"]), color)
            cards.append((urgency_rank[urgency], html))

    # ── Shift budget signals ───────────────────────────────────────────────
    # Find campaigns that have both good and bad adsets
    if "ad_set" in df.columns and "campaign" in df.columns:
        cutoff = sorted(df["date_tz"].unique())[-3] if len(df["date_tz"].unique()) >= 3 else df["date_tz"].min()
        sub = df[df["date_tz"] >= cutoff]
        camp_adset = (sub.groupby(["campaign", "ad_set"])
                        .agg(spend=("total_cost", "sum"),
                             paid=("D0_paid_users", "sum"),
                             unin=("p0_unin_users", "sum"))
                        .reset_index())
        camp_adset["cac"] = camp_adset["spend"] / camp_adset["paid"].clip(lower=1)
        camp_adset["unin_rate"] = camp_adset["unin"] / camp_adset["paid"].clip(lower=1) * 100
        camp_adset = camp_adset[camp_adset["spend"] >= _MIN_SPEND_ADSET]
        for camp, grp in camp_adset.groupby("campaign"):
            good = grp[grp["cac"] <= CAC_TARGET * 0.85]
            bad  = grp[grp["cac"] >= CAC_TARGET * 1.3]
            if good.empty or bad.empty: continue
            best  = good.sort_values("cac").iloc[0]
            worst = bad.sort_values("cac", ascending=False).iloc[0]
            reasons = [
                f"Move budget from '{worst['ad_set'][:40]}' (CAC ₹{worst['cac']:,.0f})",
                f"To '{best['ad_set'][:40]}' (CAC ₹{best['cac']:,.0f})",
            ]
            html = _action_card(camp, "Campaign", "SHIFT BUDGET", "warn",
                                reasons, grp["spend"].sum(), int(grp["paid"].sum()), color)
            cards.append((1, html))

    # ── Render ────────────────────────────────────────────────────────────
    if not cards:
        st.markdown(
            "<div style='padding:32px;text-align:center;color:#333;font-size:0.85rem'>"
            "✅ All campaigns within target — no actions needed today.</div>",
            unsafe_allow_html=True)
        return

    cards.sort(key=lambda x: x[0])

    # Summary bar
    counts = {"urgent": 0, "warn": 0, "good": 0}
    all_camp  = _agg_3day(df, "campaign")
    for _, row in all_camp.iterrows():
        if row["spend"] < _MIN_SPEND_CAMPAIGN: continue
        _, urg, _ = _adviser_score(row["cac"], row["unin_rate"])
        if urg in counts: counts[urg] += 1

    summary_html = (
        "<div style='display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap'>"
        f"<div style='background:#E24B4A22;border:1px solid #E24B4A44;border-radius:6px;padding:8px 14px'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:#E24B4A'>{sum(1 for r,_ in cards if r==0)}</div>"
        f"<div style='font-size:0.65rem;color:#E24B4A;text-transform:uppercase'>Urgent</div></div>"
        f"<div style='background:#E8883A22;border:1px solid #E8883A44;border-radius:6px;padding:8px 14px'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:#E8883A'>{sum(1 for r,_ in cards if r==1)}</div>"
        f"<div style='font-size:0.65rem;color:#E8883A;text-transform:uppercase'>Review</div></div>"
        f"<div style='background:#1D9E7522;border:1px solid #1D9E7544;border-radius:6px;padding:8px 14px'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:#1D9E75'>{sum(1 for r,_ in cards if r==2)}</div>"
        f"<div style='font-size:0.65rem;color:#1D9E75;text-transform:uppercase'>Opportunity</div></div>"
        "</div>"
    )
    st.markdown(summary_html, unsafe_allow_html=True)

    # Filter tabs
    filter_col, _ = st.columns([4, 6])
    with filter_col:
        level_filter = st.pills("Show", ["All", "Campaign", "Ad Set", "Creative"],
                                default="All", key=f"adv_filter_{app}")

    for rank, html in cards:
        level_in_html = ("Campaign" if "Campaign-level" in html or ">Campaign<" in html
                         else "Ad Set" if ">Ad Set<" in html
                         else "Creative")
        # parse level from badge
        if ">Campaign<" in html: lev = "Campaign"
        elif ">Ad Set<" in html: lev = "Ad Set"
        elif ">Creative<" in html: lev = "Creative"
        else: lev = "Campaign"
        if level_filter != "All" and level_filter != lev:
            continue
        st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  Ad Set Analysis — source → ad set, 7-day cumulative
# ════════════════════════════════════════════════════════════════════════════

def adset_analysis_view(df: pd.DataFrame, app: str, color: str):
    """Source → ad set breakdown over last 7 days (cumulative)."""
    if df.empty or "ad_set" not in df.columns:
        st.markdown("<div style='color:#444;padding:24px 0'>No ad set data available.</div>",
                    unsafe_allow_html=True)
        return

    # ── 14-day window ──────────────────────────────────────────────────────────
    latest = df["date_tz"].max()
    all_dates = sorted(df["date_tz"].unique())
    window_dates = all_dates[-14:]
    df7 = df[df["date_tz"].isin(window_dates)].copy()

    if df7.empty:
        st.markdown("<div style='color:#444;padding:24px 0'>No data in last 14 days.</div>",
                    unsafe_allow_html=True)
        return

    # ── source grouping ───────────────────────────────────────────────────────
    src_lower = df7["source"].str.lower() if "source" in df7.columns else pd.Series("", index=df7.index)
    df7["_src"] = np.where(
        src_lower.str.contains("facebook|meta", na=False), "Facebook",
        np.where(src_lower.str.contains("google|goog", na=False), "Google", "Other")
    )

    # ── aggregate per source + ad_set over 7 days ────────────────────────────
    grp = df7.groupby(["_src", "ad_set"], as_index=False).agg(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        unin=("p0_unin_users", "sum"),
    )
    grp["cac"]  = (grp["spend"] / grp["orders"].replace(0, np.nan)).fillna(0)
    grp["unin_rate"] = (grp["unin"] / grp["orders"].replace(0, np.nan) * 100).fillna(0)

    # overall 7d averages for signal comparison
    total_spend = grp["spend"].sum() or 1
    total_orders = grp["orders"].sum() or 1
    total_unin   = grp["unin"].sum()
    avg_cac  = total_spend / total_orders
    avg_unin = total_unin  / total_orders * 100
    grp["spend_pct"] = grp["spend"] / total_spend * 100

    _SRC_COLORS = {"Facebook": "#378ADD", "Google": "#34A853", "Other": "#666"}

    def _signal(row):
        """Returns (label, color) for the focus signal."""
        high_cac  = row["cac"]       > avg_cac  * 1.25
        high_unin = row["unin_rate"] > avg_unin * 1.25
        low_vol   = row["spend_pct"] < 1.0
        if high_cac and high_unin: return "⚠ Both High",   "#E24B4A"
        if high_cac:               return "↑ CAC",         "#E07B39"
        if high_unin:              return "↑ Uninstall",   "#E07B39"
        if not high_cac and not high_unin and not low_vol: return "✓ Efficient", "#1D9E75"
        return "", "#444"

    def _fmt_spend(v):
        if v >= 1_000_000: return f"₹{v/1_000_000:.1f}M"
        if v >= 1_000:     return f"₹{v/1_000:.0f}k"
        return f"₹{v:.0f}"

    # ── date range label ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:0.72rem;color:#444;margin-bottom:18px'>"
        f"7-day window · {window_dates[0]} → {window_dates[-1]} · "
        f"avg CAC <span style='color:#4A4540;font-weight:600'>₹{avg_cac:,.0f}</span> · "
        f"avg uninstall <span style='color:#4A4540;font-weight:600'>{avg_unin:.1f}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    open_key = f"adset_analysis_open_{app}"
    if open_key not in st.session_state:
        st.session_state[open_key] = None

    # ── render per source ─────────────────────────────────────────────────────
    for src_name in ["Facebook", "Google", "Other"]:
        src_df = grp[grp["_src"] == src_name].sort_values("spend", ascending=False)
        if src_df.empty:
            continue

        sc = _SRC_COLORS[src_name]
        src_spend = src_df["spend"].sum()
        src_orders = src_df["orders"].sum()
        src_cac   = src_spend / src_orders if src_orders else 0
        src_unin_rate = src_df["unin"].sum() / src_orders * 100 if src_orders else 0
        src_spct  = src_spend / total_spend * 100
        n_adsets  = len(src_df)

        # Source header card
        st.markdown(
            f"<div style='background:#FFFFFF;border:1px solid #E2DDD3;border-left:3px solid {sc};"
            f"border-radius:8px;padding:10px 16px;margin-bottom:6px;"
            f"display:flex;align-items:center;gap:24px'>"
            f"<span style='font-size:0.82rem;font-weight:700;color:{sc};min-width:70px;"
            f"text-transform:uppercase;letter-spacing:0.07em'>{src_name}</span>"
            f"<span style='font-size:0.68rem;color:#8A857D'>{n_adsets} ad sets</span>"
            f"<span style='font-size:0.68rem;color:#A8A39A'>spend</span>"
            f"<span style='font-size:0.9rem;font-weight:700;color:#1C1A17'>{_fmt_spend(src_spend)}"
            f"<span style='font-size:0.65rem;color:#8A857D;margin-left:4px'>{src_spct:.0f}%</span></span>"
            f"<span style='font-size:0.68rem;color:#A8A39A'>cac</span>"
            f"<span style='font-size:0.9rem;font-weight:700;color:#1C1A17'>₹{src_cac:,.0f}</span>"
            f"<span style='font-size:0.68rem;color:#A8A39A'>unin</span>"
            f"<span style='font-size:0.9rem;font-weight:700;color:#1C1A17'>{src_unin_rate:.1f}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Ad set rows
        for _, row in src_df.iterrows():
            aname = row["ad_set"]
            sig_label, sig_col = _signal(row)
            cac_col  = "#E24B4A" if row["cac"]       > avg_cac  * 1.25 else "#5A554D"
            unin_col = "#E24B4A" if row["unin_rate"] > avg_unin * 1.25 else "#4A4540"
            disp = (aname[:60] + "…") if len(aname) > 61 else aname

            signal_html = (
                f"<span style='font-size:0.6rem;font-weight:700;padding:1px 6px;"
                f"border-radius:3px;background:{sig_col}20;color:{sig_col}'>{sig_label}</span>"
            ) if sig_label else ""

            st.markdown(
                f"<div style='display:flex;align-items:center;gap:16px;padding:7px 12px 7px 20px;"
                f"border-bottom:1px solid #E5E0D6'>"
                f"<span style='font-size:0.78rem;color:#1C1A17;flex:1;min-width:0;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{disp}</span>"
                f"{signal_html}"
                f"<span style='font-size:0.65rem;color:#444;flex-shrink:0'>spend</span>"
                f"<span style='font-size:0.82rem;font-weight:600;color:#1C1A17;flex-shrink:0'>"
                f"{_fmt_spend(row['spend'])}"
                f"<span style='font-size:0.62rem;color:#8A857D;margin-left:3px'>{row['spend_pct']:.1f}%</span>"
                f"</span>"
                f"<span style='font-size:0.65rem;color:#444;flex-shrink:0'>cac</span>"
                f"<span style='font-size:0.82rem;font-weight:600;color:{cac_col};flex-shrink:0'>"
                f"₹{row['cac']:,.0f}</span>"
                f"<span style='font-size:0.65rem;color:#444;flex-shrink:0'>unin</span>"
                f"<span style='font-size:0.82rem;font-weight:600;color:{unin_col};flex-shrink:0'>"
                f"{row['unin_rate']:.1f}%</span>"
                f"<span style='font-size:0.75rem;color:#2a2a2a;flex-shrink:0'>{row['orders']:,.0f} users</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  main navigation
# ════════════════════════════════════════════════════════════════════════════

def main():
    # ── init session state ──────────────────────────────────────────────────
    if "sb_app"     not in st.session_state: st.session_state["sb_app"]     = "Seekho"
    if "sb_section" not in st.session_state: st.session_state["sb_section"] = "Morning Pulse"

    app     = st.session_state.get("sb_app", APPS[0])
    color   = APP_COLORS[app]
    hex_col = color.lstrip("#")
    r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
    section_options = ["Morning Pulse", "Category Mix", "Ad Set Analysis", "Adviser"]
    if st.session_state.get("sb_section") not in section_options:
        st.session_state["sb_section"] = section_options[0]
    section = st.session_state["sb_section"]

    # ── top nav ──────────────────────────────────────────────────────────────
    # Inject dynamic CSS: selected pill uses current app's color
    _r, _g, _b = _hex_to_rgb(APP_COLORS[app])
    _c = APP_COLORS[app]
    st.markdown(f"""<style>
      [class*="e8vg11g11"],
      [data-baseweb="button-group"] button[aria-pressed="true"],
      [data-baseweb="button-group"] button[aria-checked="true"] {{
        background: linear-gradient(180deg, rgba({_r},{_g},{_b},0.18) 0%, rgba({_r},{_g},{_b},0.28) 100%) !important;
        border-color: {_c} !important;
        color: {_c} !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba({_r},{_g},{_b},0.25), inset 0 1px 0 rgba(255,255,255,0.6) !important;
      }}
    </style>""", unsafe_allow_html=True)

    nav_app, nav_sec, nav_right = st.columns([5.5, 3.2, 1.5])
    with nav_app:
        sel_app = st.pills("App", list(APPS),
                           default=st.session_state["sb_app"],
                           key="pills_app", label_visibility="collapsed")
        if sel_app and sel_app != st.session_state["sb_app"]:
            st.session_state["sb_app"]     = sel_app
            st.session_state["sb_section"] = "Morning Pulse"
            st.rerun()
    with nav_sec:
        sel_sec = st.pills("Section", section_options,
                           default=st.session_state["sb_section"],
                           key="pills_sec", label_visibility="collapsed")
        if sel_sec and sel_sec != st.session_state["sb_section"]:
            st.session_state["sb_section"] = sel_sec
            st.rerun()
    with nav_right:
        if st.button(f"↻  Refresh {app}", key="tnav_refresh", use_container_width=True):
            with st.spinner("Refreshing…"):
                refresh_app_data(app)
            st.success("Done!")

    app     = st.session_state.get("sb_app", APPS[0])
    color   = APP_COLORS[app]
    section = st.session_state.get("sb_section", "Morning Pulse")

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
        f"<div style='height:1px;background:#E5E0D6;margin-bottom:18px'></div>",
        unsafe_allow_html=True,
    )

    if section == "Category Mix":
        category_mix_view(app=app)
        return

    df = safe_fetch(app)
    if df.empty:
        st.warning(f"No data loaded for {app}.")
        return

    if section == "Ad Set Analysis":
        adset_analysis_view(df, app=app, color=color)
        return

    if section == "Adviser":
        cr_raw = None
        if app in CREATIVE_QUERY_IDS:
            try:
                cr_raw = add_derived_metrics(fetch_creative_data(app))
            except Exception:
                pass
        adviser_view(df, cr_raw, app=app, color=color)
        return

    # Debug: show what app_name values are in the fetched data
    if "app_name" in df.columns:
        apps_in_data = df["app_name"].unique().tolist()
        if len(apps_in_data) > 1 or (len(apps_in_data) == 1 and apps_in_data[0] != app):
            st.warning(f"⚠️ Data mismatch: fetched for **{app}** but data contains app_name={apps_in_data}. "
                       f"Check Redash query {__import__('utils.fetcher', fromlist=['APP_QUERY_IDS']).APP_QUERY_IDS.get(app)}.")

    morning_pulse_view(df, app=app, color=color, mode="uninstall")


if __name__ == "__main__":
    main()
