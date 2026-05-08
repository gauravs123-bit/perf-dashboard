# Perf Marketing Dashboard — Context Brief

## What This Is
A multi-page Streamlit dashboard at `localhost:8501` connected to Redash Cloud for performance marketing analytics across 4 apps: **Arivu, Kali, Vidhya, Nerchuko**.

## How to Run
```bash
cd /Users/gauravsharma/Claude/perf_dashboard
python3 -m streamlit run app.py
```

---

## Project Structure

```
perf_dashboard/
├── app.py                  # Main Streamlit entrypoint (801 lines)
├── utils/
│   ├── fetcher.py          # Redash API fetch + caching
│   ├── metrics.py          # All metric calculations (696 lines)
│   └── charts.py           # All Plotly chart builders (623 lines)
├── .env                    # REDASH_API_KEY, REDASH_BASE_URL
├── requirements.txt        # streamlit, pandas, requests, plotly, python-dotenv
└── no_track_creatives.xlsx # Export of creatives missing track# (see below)
```

---

## Redash Query IDs

| App      | Main Query | Creative Query (Meta only) |
|----------|------------|---------------------------|
| Arivu    | 89268      | 86447                     |
| Vidhya   | 89172      | 86002                     |
| Kali     | 89171      | 86001                     |
| Nerchuko | 57757      | 86364                     |

---

## App Colors

| App      | Hex     |
|----------|---------|
| Arivu    | #7F77DD |
| Kali     | #1D9E75 |
| Vidhya   | #D85A30 |
| Nerchuko | #D4537E |

---

## Dashboard Structure

Two dashboards toggled via top radio:

### Uninstall Dashboard
Per-app tabs → sub-tabs:
1. **Overview** — KPIs, trend bar, source donut, source metrics table
2. **Campaigns** — campaign bar + L3D trend, drilldown to ad sets
3. **Ad Sets** — adset table + L3D trend
4. **Rise Analysis** — Kitagawa waterfall (YD vs D-1) + 7-day rolling heatmap
5. **Creatives (Meta)** — *(apps with creative query only)* creative table + L3D trend + Dimension Insights

### CAC Dashboard
Per-app tabs → sub-tabs:
1. **Overview** — KPIs, trend bar, source donut, source metrics table
2. **Campaigns** — campaign bar + L3D trend, drilldown to ad sets
3. **Ad Sets** — adset table + L3D trend
4. **Rise Analysis** — Kitagawa waterfall + 7-day rolling heatmap
5. **Spend vs CAC** — scatter quadrant (spend vs CAC per ad set)
6. **Creatives (Meta)** — *(apps with creative query only)* creative table + L3D trend + Dimension Insights

---

## Key Metric Definitions

- **D0 CAC** = `total_cost / D0_paid_users` (spend divided by same-day paying users)
- **P0 Rate** = `p0_unin_users / D0_paid_users * 100` (day-0 uninstall rate)
- **CPI** = `total_cost / installs`
- **Conv%** = `D0_paid_users / installs * 100`
- CAC is `NaN` (blank) when `D0_paid_users = 0` — do not fill with 0

---

## Kitagawa Decomposition

Decomposes delta between two dates into rate effect + mix effect:

```
rate_effect_i = (rate_d0 - rate_d1) × share_d1
mix_effect_i  = (share_d0 - share_d1) × (rate_d1 - overall_rate_d1)   ← deviation from mean
contribution_i = rate_effect_i + mix_effect_i
```

**Uninstall**: group = campaign or source, rate = p0_uninstall_rate, share = spend share
**CAC**: group = campaign or source, rate = D0_CAC, share = **D0_paid_users share** (not spend share), filter rows where D0_paid_users > 0

Sum of contributions equals actual delta exactly.

---

## Creative Table (`creative_table()` in metrics.py)

Returns one row per creative with YD / L3D / L7D metrics, sorted by L7D spend descending.

### Column windows
For each window (yd, l3d, l7d):
- `spend_{w}` — total spend
- `orders_{w}` — D0_paid_users sum
- `CAC_{w}` — spend/orders (NaN if orders=0)
- `unin_{w}` — p0_unin_users sum
- `p0_rate_{w}` — unin/orders*100 (NaN if orders=0)
- `CPI_{w}`, `conv_{w}`, `CTR_{w}`, `CPC_{w}`, `CPM_{w}`

Plus: `campaign`, `ad_set` (mode of most common mapping), `spend_share_l7d`

Plus parsed dimensions (see below).

### Display columns
**CAC tab**: Creative, Ad Set, Campaign, Spend YD → D0 Orders YD → D0 CAC YD → Spend L3D → D0 Orders L3D → D0 CAC L3D → Spend L7D → Spend % → D0 Orders L7D → D0 CAC L7D

**Uninstall tab**: same structure but adds Unin YD/L3D/L7D and P0 Rate YD/L3D/L7D instead of (only) CAC

---

## Creative Name Parser (`parse_creative_name()` in metrics.py)

Creative names follow the convention:
```
[category]_[hook_xwords]_[audience_xwords]_[type]_[production]_track[N]_[team]_[date]
```
`x` = word separator within segment, `_` = segment separator

### Extracted dimensions

| Dimension      | Logic                                              | Example values                        |
|----------------|----------------------------------------------------|---------------------------------------|
| `category`     | First `_` segment                                  | Astro, Business, Career, English, Finance |
| `gender`       | `female`/`male` keyword                            | Male, Female, Unknown                 |
| `creative_type`| Keywords: microdrama > repte > repex > exp > rep > ugc | Explainer, Repurposed, Microdrama |
| `production`   | Keywords: actor > ai vo > _ai_                     | AI, Actor, AI Voice-Over, Other       |
| `track`        | `track\d+` → `trackN`; fallback `iteration N`, `hook N`, standalone number `batch N` | Track 255, Batch 1, N/A |
| `team`         | `_wdm_` / `_sling_`                                | WDM, Sling, Other                     |
| `launch_month` | `\d{2}(jan\|feb\|...)` at end                      | Apr, Mar, Unknown                     |

### Known N/A track creatives
25 creatives across Arivu (18) and Nerchuko (7) have no parseable track number — exported to `no_track_creatives.xlsx`. These are older/external productions (mythmedia_dubbed, adlive, freeform names) predating the structured naming convention.

---

## Dimension Insights (in Creatives tab)

Below the creative table, an expander "Dimension Insights" shows:
- Radio: Category | Gender | Creative Type | Production | Track | Team | Launch Month
- `pivot_bar_chart()`: dual chart — Spend L7D bars (app color) + Avg D0 CAC line (red) per group
- Summary table: group | # Creatives | Spend L7D | Spend % | D0 Orders | Avg D0 CAC | Avg P0 Rate %

`creative_pivot(cr_df, dimension)` in metrics.py aggregates by summing raw totals then deriving CAC/p0 — not averaging per-creative rates.

---

## Common Bug Patterns (solved)

| Bug | Fix |
|-----|-----|
| CPC/CPM inflated (₹898 vs ₹5) | Always re-derive from raw clicks/impressions after any groupby, never sum pre-computed ratios |
| Kitagawa mix effect near-zero | Use deviation-from-mean: `(share_d0 - share_d1) × (rate_d1 - overall_rate_d1)` |
| CAC Kitagawa sum mismatch | Weight by D0_paid_users share, not spend share; filter D0_paid > 0 |
| `ValueError: cannot reindex` in creative_table | Groups only by `ad_creative`; use `_suffix()` rename before merge, not after |
| `StreamlitDuplicateElementKey` | All widget keys namespaced: `key=f"widget_{app}_{context}"` |
| `StreamlitDuplicateElementId` | All `st.plotly_chart` calls have explicit `key=` |
| stale pyc cache | `find . -name "*.pyc" -delete` then restart |

---

## Pending / Possible Next Steps

- Tag the 25 N/A-track creatives with a proper track/batch identifier retroactively
- Add creative-level trend charts per parsed dimension (e.g. CAC over time by creative type)
- Add a "pause candidates" view: high spend + high CAC creatives highlighted in red
- Cross-app creative comparison (same creative type / category across Arivu vs Kali)
- Auto-refresh cron (currently manual refresh button per app)
