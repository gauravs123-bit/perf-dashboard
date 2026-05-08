import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from utils.metrics import APP_COLORS, SOURCE_COLORS


# ── sparkline ───────────────────────────────────────────────────────────────
def _hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def sparkline(series: list[float], color: str = "#7F77DD") -> go.Figure:
    fill_color = (
        color.replace(")", f",0.15)").replace("rgb(", "rgba(")
        if color.startswith("rgb(") else _hex_to_rgba(color)
    )
    fig = go.Figure(go.Scatter(
        y=series, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=fill_color,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=40, width=120,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ── KPI card (returns a dict for st.metric) ─────────────────────────────────
def kpi_values(latest: float, prev: float, fmt: str = ".1f") -> tuple[str, str]:
    val_str   = f"{latest:{fmt}}"
    delta     = latest - prev
    delta_str = f"{delta:+{fmt}}"
    return val_str, delta_str


# ── 7-day trend bar chart ────────────────────────────────────────────────────
def trend_bar(trend_df: pd.DataFrame, metric_col: str,
              color: str = "#7F77DD", title: str = "") -> go.Figure:
    trend_df = trend_df.sort_values("date_tz")
    fig = go.Figure(go.Bar(
        x=trend_df["date_tz"].astype(str),
        y=trend_df[metric_col],
        marker_color=color,
        text=trend_df[metric_col].round(2),
        textposition="outside",
    ))
    fig.update_layout(
        title=title, height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        font=dict(color="#e0e0e0"),
    )
    return fig


# ── source split donut ───────────────────────────────────────────────────────
def source_donut(src_df: pd.DataFrame, metric_col: str, title: str = "") -> go.Figure:
    colors = [SOURCE_COLORS.get(s.lower(), "#888888") for s in src_df["source_group"]]
    fig = go.Figure(go.Pie(
        labels=src_df["source_group"],
        values=src_df[metric_col],
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
    ))
    fig.update_layout(
        title=title, height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        showlegend=False,
    )
    return fig


# ── campaign / ad-set bar chart (inline bar in table) ───────────────────────
def inline_bar_col(values: pd.Series, color: str = "#7F77DD") -> go.Figure:
    """Horizontal bars for embedding inside a table column visual."""
    fig = go.Figure(go.Bar(
        x=values,
        y=[str(i) for i in range(len(values))],
        orientation="h",
        marker_color=color,
    ))
    fig.update_layout(
        height=max(200, len(values) * 30),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ── horizontal grouped bar for campaign table ────────────────────────────────
def campaign_bar(camp_df: pd.DataFrame, metric_col: str, color: str,
                 title: str = "") -> go.Figure:
    camp_df = camp_df.sort_values(metric_col, ascending=True).tail(15)
    src_lower = camp_df["source"].str.lower()
    bar_colors = [
        SOURCE_COLORS.get("facebook", "#378ADD") if "facebook" in s or "meta" in s
        else SOURCE_COLORS.get("google", "#E24B4A") if "google" in s else color
        for s in src_lower
    ]
    fig = go.Figure(go.Bar(
        x=camp_df[metric_col],
        y=camp_df["campaign"].str[:40],
        orientation="h",
        marker_color=bar_colors,
        text=camp_df[metric_col].round(2),
        textposition="outside",
    ))
    fig.update_layout(
        title=title, height=max(300, len(camp_df) * 30),
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        yaxis=dict(showgrid=False),
        font=dict(color="#e0e0e0"),
    )
    return fig


# ── Kitagawa waterfall chart ─────────────────────────────────────────────────
def kitagawa_waterfall(kit_df: pd.DataFrame, title: str = "Kitagawa Decomposition") -> go.Figure:
    if kit_df.empty:
        return go.Figure()

    kit_df = kit_df.head(12)
    groups = kit_df["group"].str[:30].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Rate Effect",
        x=groups, y=kit_df["rate_effect"],
        marker_color="#7F77DD",
    ))
    fig.add_trace(go.Bar(
        name="Mix Effect",
        x=groups, y=kit_df["mix_effect"],
        marker_color="#D85A30",
    ))
    fig.add_trace(go.Scatter(
        name="Total Contribution",
        x=groups, y=kit_df["contribution"],
        mode="markers+lines",
        marker=dict(color="#ffffff", size=8, line=dict(color="#7F77DD", width=2)),
        line=dict(color="#ffffff", width=1, dash="dot"),
    ))
    fig.update_layout(
        title=title,
        barmode="relative",
        height=400,
        margin=dict(l=10, r=10, t=50, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-30, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        font=dict(color="#e0e0e0"),
        legend=dict(orientation="h", y=1.12),
    )
    return fig


# ── cross-app L7D trend ──────────────────────────────────────────────────────
def l7d_trend(app_series: dict[str, dict], metric_label: str,
              prefix: str = "", suffix: str = "") -> go.Figure:
    """
    app_series: {app_name: {"dates": [...], "values": [...]}}
    Renders a multi-line chart with one line per app over the last 7 days,
    plus a dashed average line per app.
    """
    fig = go.Figure()
    for app_name, data in app_series.items():
        color = APP_COLORS.get(app_name, "#888888")
        dates  = [str(d) for d in data["dates"]]
        values = data["values"]
        if not values:
            continue

        # main line
        fig.add_trace(go.Scatter(
            x=dates, y=values,
            name=app_name,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{app_name}</b><br>%{{x}}<br>{metric_label}: {prefix}%{{y:.2f}}{suffix}<extra></extra>",
        ))

        # L7D average reference line
        avg = np.mean(values)
        fig.add_trace(go.Scatter(
            x=[dates[0], dates[-1]], y=[avg, avg],
            name=f"{app_name} L7D avg",
            mode="lines",
            line=dict(color=color, width=1, dash="dot"),
            opacity=0.5,
            showlegend=False,
            hovertemplate=f"{app_name} L7D avg: {prefix}{avg:.2f}{suffix}<extra></extra>",
        ))

    fig.update_layout(
        title=f"L7D {metric_label} — All Apps",
        height=320,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-20),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a",
                   tickprefix=prefix, ticksuffix=suffix),
        font=dict(color="#e0e0e0"),
        legend=dict(orientation="h", y=1.12, x=0),
        hovermode="x unified",
    )
    return fig


# ── L3D multi-line trend (campaign / ad-set level) ───────────────────────────
def l3d_group_trend(df: "pd.DataFrame", group_col: str, metric_col: str,
                    title: str = "", top_n: int = 10,
                    metric_label: str = "", prefix: str = "",
                    suffix: str = "") -> "go.Figure":
    """
    Line chart: last 3 days, one line per group (campaign or ad_set).
    Only the top_n groups by latest-day metric are shown to keep it readable.
    metric_col must already be derived (e.g. p0_uninstall_rate, D0_CAC_calc).
    """
    import numpy as np

    if df.empty:
        return go.Figure()

    dates = sorted(df["date_tz"].unique())[-3:]
    if len(dates) < 2:
        return go.Figure()

    # aggregate per group × date
    records = []
    for d in dates:
        day_df = df[df["date_tz"] == d]
        grp = day_df.groupby(group_col, as_index=False).apply(
            lambda g: pd.Series({
                "date_tz": d,
                group_col: g[group_col].iloc[0],
                "_val": _derive(g, metric_col),
            })
        )
        records.append(grp)

    long = pd.concat(records, ignore_index=True)
    # force plain YYYY-MM-DD strings so Plotly treats as categories not datetimes
    long["date_str"] = pd.to_datetime(long["date_tz"]).dt.strftime("%Y-%m-%d")

    # pick top_n by latest day value
    latest = long[long["date_tz"] == dates[-1]].nlargest(top_n, "_val")
    top_groups = latest[group_col].tolist()
    long = long[long[group_col].isin(top_groups)]

    fig = go.Figure()
    palette = px.colors.qualitative.Plotly
    for i, grp_name in enumerate(top_groups):
        grp_df = long[long[group_col] == grp_name].sort_values("date_tz")
        color = palette[i % len(palette)]
        short_name = str(grp_name)[:40]
        fig.add_trace(go.Scatter(
            x=grp_df["date_str"],
            y=grp_df["_val"],
            name=short_name,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=7),
            hovertemplate=(
                f"<b>{short_name}</b><br>%{{x}}<br>"
                f"{metric_label or metric_col}: {prefix}%{{y:.2f}}{suffix}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=title or f"L3D {metric_label or metric_col} Trend",
        height=340,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, type="category"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a",
                   tickprefix=prefix, ticksuffix=suffix),
        font=dict(color="#e0e0e0"),
        legend=dict(orientation="v", x=1.01, y=1, font=dict(size=10)),
        hovermode="x unified",
    )
    return fig


def _derive(g: "pd.DataFrame", metric_col: str) -> float:
    """Re-derive ratio metrics from raw columns for a group slice."""
    import numpy as np
    if metric_col == "p0_uninstall_rate":
        d = g["D0_paid_users"].sum()
        return g["p0_unin_users"].sum() / d * 100 if d else 0
    if metric_col in ("D0_CAC_calc", "D0_CAC"):
        d = g["D0_paid_users"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col == "CPI_calc":
        d = g["installs"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col == "conv_rate":
        d = g["installs"].sum()
        return g["D0_paid_users"].sum() / d * 100 if d else 0
    if metric_col in ("CPC",):
        d = g["clicks"].sum()
        return g["total_cost"].sum() / d if d else 0
    if metric_col in ("CPM",):
        d = g["impressions"].sum()
        return g["total_cost"].sum() / d * 1000 if d else 0
    return g[metric_col].sum() if metric_col in g.columns else 0


# ── creative L3D trend ───────────────────────────────────────────────────────
def creative_trend(long_df: "pd.DataFrame", metric_label: str,
                   prefix: str = "", suffix: str = "",
                   top_n: int = 10) -> "go.Figure":
    """Multi-line L3D chart, one line per creative."""
    if long_df.empty:
        return go.Figure()

    # pick top_n by latest day value
    latest = long_df.groupby("ad_creative")["_val"].last().nlargest(top_n)
    top = latest.index.tolist()
    df = long_df[long_df["ad_creative"].isin(top)]

    palette = px.colors.qualitative.Plotly
    fig = go.Figure()
    for i, creative in enumerate(top):
        cdf = df[df["ad_creative"] == creative].sort_values("date_tz")
        short = str(creative)[:35]
        fig.add_trace(go.Scatter(
            x=cdf["date_tz"].astype(str),
            y=cdf["_val"],
            name=short,
            mode="lines+markers",
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=6),
            hovertemplate=(
                f"<b>{short}</b><br>%{{x}}<br>"
                f"{metric_label}: {prefix}%{{y:.2f}}{suffix}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=f"L3D {metric_label} — Top Creatives (Meta)",
        height=340,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a",
                   tickprefix=prefix, ticksuffix=suffix),
        font=dict(color="#e0e0e0"),
        legend=dict(orientation="v", x=1.01, y=1, font=dict(size=10)),
        hovermode="x unified",
    )
    return fig


# ── Kitagawa 7-day heatmap ───────────────────────────────────────────────────
def kitagawa_heatmap(
    pivot: pd.DataFrame,
    detail: dict,
    mode: str = "uninstall",   # 'uninstall' or 'cac'
    title: str = "7-day Kitagawa Heatmap",
) -> go.Figure:
    """
    pivot   : rows = groups, cols = transition labels, values = contribution
    detail  : {transition_label: full kit_df}
    mode    : controls tooltip field names and formatting
    """
    if pivot.empty:
        return go.Figure()

    groups      = pivot.index.tolist()
    transitions = pivot.columns.tolist()
    z_matrix    = pivot.values.tolist()

    # ── build customdata matrix for rich tooltips ─────────────────────────
    # shape: (n_groups, n_transitions, n_fields)
    n_g, n_t = len(groups), len(transitions)
    custom = [[[""] * 8 for _ in range(n_t)] for _ in range(n_g)]

    for tj, trans in enumerate(transitions):
        kit = detail.get(trans, None)
        if kit is None or kit.empty:
            continue
        kit_idx = kit.set_index("group")
        for gi, grp in enumerate(groups):
            if grp not in kit_idx.index:
                continue
            row = kit_idx.loc[grp]
            if mode == "uninstall":
                custom[gi][tj] = [
                    f"{row.get('rate_d1', 0):.2f}%",      # 0 rate D-1
                    f"{row.get('rate_d0', 0):.2f}%",      # 1 rate D0
                    f"{row.get('rate_effect', 0):+.3f}",   # 2 rate effect
                    f"{row.get('mix_effect', 0):+.3f}",    # 3 mix effect
                    f"{int(row.get('D0_paid_d1', 0))}",    # 4 paid D-1
                    f"{int(row.get('D0_paid_d0', 0))}",    # 5 paid D0
                    "",                                     # 6 unused
                    "",                                     # 7 unused
                ]
            else:  # cac
                custom[gi][tj] = [
                    f"₹{row.get('cac_d1', 0):.2f}",        # 0 CAC D-1
                    f"₹{row.get('cac_d0', 0):.2f}",        # 1 CAC D0
                    f"{row.get('rate_effect', 0):+.2f}",    # 2 rate effect
                    f"{row.get('mix_effect', 0):+.2f}",     # 3 mix effect
                    f"₹{row.get('spend_d1', 0):,.0f}",      # 4 spend D-1
                    f"₹{row.get('spend_d0', 0):,.0f}",      # 5 spend D0
                    f"₹{row.get('cpi_d1', 0):.2f}",         # 6 CPI D-1
                    f"₹{row.get('cpi_d0', 0):.2f}",         # 7 CPI D0
                ]

    # ── cell text (contribution value) ────────────────────────────────────
    if mode == "uninstall":
        cell_text = [
            [f"{v:+.2f}pp" if v != 0 else "" for v in row]
            for row in z_matrix
        ]
        hover_template = (
            "<b>%{y}</b> | %{x}<br>"
            "Rate D-1: %{customdata[0]}  →  Rate D0: %{customdata[1]}<br>"
            "Rate Effect: %{customdata[2]}pp  |  Mix Effect: %{customdata[3]}pp<br>"
            "Paid D-1: %{customdata[4]}  →  Paid D0: %{customdata[5]}<br>"
            "<b>Contribution: %{z:+.3f}pp</b>"
            "<extra></extra>"
        )
    else:
        cell_text = [
            [f"{v:+.0f}₹" if v != 0 else "" for v in row]
            for row in z_matrix
        ]
        hover_template = (
            "<b>%{y}</b> | %{x}<br>"
            "CAC D-1: %{customdata[0]}  →  CAC D0: %{customdata[1]}<br>"
            "Rate Effect: %{customdata[2]}  |  Mix Effect: %{customdata[3]}<br>"
            "Spend D-1: %{customdata[4]}  →  Spend D0: %{customdata[5]}<br>"
            "CPI D-1: %{customdata[6]}  →  CPI D0: %{customdata[7]}<br>"
            "<b>Contribution: %{z:+.2f}</b>"
            "<extra></extra>"
        )

    # ── diverging colorscale: red = worsening, green = improving ─────────
    colorscale = [
        [0.0, "#1D9E75"],   # strong green (most negative / best)
        [0.4, "#a8d5c2"],   # light green
        [0.5, "#ffffff"],   # white = zero
        [0.6, "#f2a79e"],   # light red
        [1.0, "#E24B4A"],   # strong red (most positive / worst)
    ]

    abs_max = max(abs(pivot.values.min()), abs(pivot.values.max()), 0.001)

    fig = go.Figure(go.Heatmap(
        z=z_matrix,
        x=transitions,
        y=[str(g)[:45] for g in groups],
        customdata=custom,
        colorscale=colorscale,
        zmid=0,
        zmin=-abs_max,
        zmax=abs_max,
        text=cell_text,
        texttemplate="%{text}",
        textfont=dict(size=10, color="#111111"),
        hovertemplate=hover_template,
        colorbar=dict(
            title=dict(text="Contribution", font=dict(color="#e0e0e0")),
            tickfont=dict(color="#e0e0e0"),
        ),
    ))

    row_height = max(20, min(40, 600 // max(len(groups), 1)))
    fig.update_layout(
        title=title,
        height=max(300, len(groups) * row_height + 120),
        margin=dict(l=10, r=10, t=50, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis=dict(tickangle=-30, side="bottom"),
        yaxis=dict(autorange="reversed"),   # biggest mover at top
    )
    return fig


# ── Spend vs CAC scatter ──────────────────────────────────────────────────────
def spend_cac_scatter(adset_df: pd.DataFrame, app_color: str = "#7F77DD") -> go.Figure:
    if adset_df.empty:
        return go.Figure()

    df = adset_df.copy()
    total_spend = df["total_cost"].sum() or np.nan
    df["spend_share"] = df["total_cost"] / total_spend * 100
    df["cac"] = np.where(df["D0_paid_users"] > 0,
                         df["total_cost"] / df["D0_paid_users"], 0)
    df = df[df["cac"] > 0]

    # source colouring
    src_lower = df["source"].str.lower()
    df["src_group"] = np.where(
        src_lower.str.contains("facebook|meta"), "Facebook",
        np.where(src_lower.str.contains("google|goog"), "Google", "Other")
    )

    color_map = {"Facebook": SOURCE_COLORS["facebook"],
                 "Google":   SOURCE_COLORS["google"],
                 "Other":    "#888888"}

    fig = px.scatter(
        df, x="spend_share", y="cac",
        size="spend_share", color="src_group",
        color_discrete_map=color_map,
        hover_name="ad_set",
        hover_data={"campaign": True, "spend_share": ":.1f", "cac": ":.2f"},
        labels={"spend_share": "Spend Share (%)", "cac": "D0 CAC"},
        title="Spend Share vs D0 CAC",
    )

    # weighted-avg CAC reference line
    total_paid = df["D0_paid_users"].sum()
    wav_cac = df["total_cost"].sum() / total_paid if total_paid else 0
    fig.add_hline(
        y=wav_cac, line_dash="dash", line_color="#ffffff",
        annotation_text=f"Wtd Avg CAC: {wav_cac:.2f}",
        annotation_font_color="#ffffff",
    )

    fig.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a"),
        legend=dict(title="Source"),
    )
    return fig


# ── overview dual-axis trend chart ───────────────────────────────────────────
def overview_trend_chart(
    trend_df: pd.DataFrame,
    primary_col: str,
    secondary_col: str,
    primary_label: str = "",
    secondary_label: str = "",
    primary_prefix: str = "",
    primary_suffix: str = "",
    secondary_prefix: str = "",
    color: str = "#7F77DD",
) -> go.Figure:
    """
    Dual-axis line chart: primary metric (left y) + secondary metric bars (right y).
    trend_df must have date_tz + both metric columns.
    """
    if trend_df.empty:
        return go.Figure()

    df = trend_df.sort_values("date_tz")
    dates = df["date_tz"].astype(str).tolist()
    fill_color = _hex_to_rgba(color, 0.12)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # secondary: spend bars (right axis)
    fig.add_trace(go.Bar(
        x=dates,
        y=df[secondary_col],
        name=secondary_label or secondary_col,
        marker_color=_hex_to_rgba("#ffffff", 0.05),
        marker_line_color=_hex_to_rgba("#ffffff", 0.1),
        marker_line_width=1,
        hovertemplate=(
            f"{secondary_label}: {secondary_prefix}%{{y:,.0f}}<extra></extra>"
        ),
    ), secondary_y=True)

    # primary: rate line (left axis)
    fig.add_trace(go.Scatter(
        x=dates,
        y=df[primary_col],
        name=primary_label or primary_col,
        mode="lines+markers",
        line=dict(color=color, width=2.5),
        marker=dict(color=color, size=7, line=dict(color="#0d0d0d", width=2)),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate=(
            f"{primary_label}: {primary_prefix}%{{y:.2f}}{primary_suffix}<extra></extra>"
        ),
    ), secondary_y=False)

    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=11),
        xaxis=dict(showgrid=False, tickangle=-20, tickfont=dict(size=10, color="#555")),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        bargap=0.25,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#1e1e1e",
        tickprefix=primary_prefix, ticksuffix=primary_suffix,
        tickfont=dict(color="#555", size=10),
        secondary_y=False, title_text="",
    )
    fig.update_yaxes(
        showgrid=False,
        tickprefix=secondary_prefix,
        tickfont=dict(color="#333", size=10),
        secondary_y=True, title_text="",
    )
    return fig


# ── creative pivot bar chart ─────────────────────────────────────────────────
def pivot_bar_chart(pivot_df: pd.DataFrame, dimension: str,
                    color: str = "#1D9E75") -> go.Figure:
    """
    Dual-bar chart: Total Spend (left y) + Avg D0 CAC (right y) per dimension group.
    Sorted by spend descending (pivot_df already sorted).
    """
    if pivot_df.empty:
        return go.Figure()

    labels = pivot_df[dimension].tolist()
    spend  = pivot_df["total_spend"].tolist()
    cac    = pivot_df["avg_cac"].tolist()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        name="Spend L7D",
        x=labels,
        y=spend,
        marker_color=_hex_to_rgba(color, 0.8),
        text=[f"₹{v:,.0f}" for v in spend],
        textposition="outside",
        textfont=dict(size=11),
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        name="Avg D0 CAC",
        x=labels,
        y=cac,
        mode="markers+lines+text",
        marker=dict(color="#E24B4A", size=10),
        line=dict(color="#E24B4A", width=2, dash="dot"),
        text=[f"₹{v:,.0f}" for v in cac],
        textposition="top center",
        textfont=dict(size=11, color="#E24B4A"),
    ), secondary_y=True)

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis=dict(showgrid=False, tickangle=-20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        bargap=0.3,
    )
    fig.update_yaxes(
        title_text="Spend L7D (₹)", secondary_y=False,
        showgrid=True, gridcolor="#2a2a2a",
    )
    fig.update_yaxes(
        title_text="Avg D0 CAC (₹)", secondary_y=True,
        showgrid=False,
    )
    return fig
