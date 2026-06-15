# Performance Marketing Dashboard

Streamlit dashboard for daily monitoring, diagnosis, and budget decisions across TTMK apps (Arivu, Vidhya, Kali, Nerchuko) and Seekho.

**Stack:** Streamlit · Pandas · Plotly · Redash API · numpy Ridge regression
**Repo:** `gauravs123-bit/perf-dashboard`
**Run:** `streamlit run app.py`

---

## File Structure

```
app.py                    # 4,000-line main app — all views and UI
utils/
  fetcher.py              # Redash API calls + caching
  metrics.py              # All aggregation and decomposition logic
  charts.py               # Plotly chart builders
  allocator.py            # Budget allocation engine
  predictor.py            # Per-campaign Ridge regression (CAC prediction)
data/
  campaign_config.csv     # 617 campaigns → type + owner + app
  targets.csv             # Group-level CAC and uninstall targets
.streamlit/
  secrets.toml            # REDASH_BASE_URL + REDASH_API_KEY
```

---

## Data Sources

All data comes from **Redash** queries, fetched via REST API and cached 1 hour in Streamlit session state.

| App | App Query ID | Creative Query ID |
|---|---|---|
| Arivu | 89268 | 86447 |
| Vidhya | 89172 | 86002 |
| Kali | 89171 | 86001 |
| Nerchuko | 96035 | 86364 |
| Seekho | 97452 | 97486 |

**App-level query columns (key ones):**

| Column | Meaning |
|---|---|
| `date_tz` | Date |
| `campaign` / `ad_set` / `ad_creative` | Hierarchy |
| `source` | Meta / Google / etc. |
| `total_cost` | Spend |
| `D0_paid_users` | Paid conversions (used as "orders" for CAC) |
| `p0_unin_users` | Day-0 uninstalls |
| `p0_cancel_users` | Day-0 cancellations |
| `active_users` | DAU |
| `installs` | Install count |

Creative-level data adds `ad_creative` dimension — used for creative analysis tab and creative count in the predictor.

---

## Navigation

The app has a **per-app selector** (pill selector at top) and a **section selector** within each app:

```
Morning Pulse | Overview | Category Mix | Ad Set Analysis | Adviser | Budget
```

The **Budget** tab is app-independent (TTMK-wide). All other tabs are per-app.

---

## Sections

### 1. Morning Pulse
Daily health snapshot — designed to be the first thing checked each morning.

- **KPI strip:** Spend / CAC / Uninst% / Canc% for Yesterday vs Day-before-yesterday
- **Source cards:** Meta vs Google breakdown for each metric
- **Trend sparklines:** 14-day spend + CAC trend per source
- **Campaign Contributors:** Kitagawa decomposition of what drove CAC/Uninst/Canc change YD vs D-2
  - Each campaign card shows: rate effect + mix effect = total contribution in ₹ or pp
  - Three columns: CAC Rise · Uninstall Rise · Cancel Rise

### 2. Overview
Cross-app summary view — no per-app filter needed.

**TABLE 1 — Per-app L3D**

| Column | Calculation |
|---|---|
| Spend | Sum of `total_cost` L3D |
| CAC | `spend / D0_paid_users` L3D |
| Uninst% | `p0_unin_users / D0_paid_users * 100` L3D |
| Canc% | `p0_cancel_users / D0_paid_users * 100` L3D |
| Delta CAC | YD CAC vs D-2 CAC |

**TABLE 2 — by Group**
- **TTMK** = Arivu + Vidhya + Kali + Nerchuko aggregated
- **Seekho** = standalone
- Shows blended CAC, Uninst%, Canc% for each group

**TABLE 3 — L7D TTMK Blended**
- 7-row daily trend table for TTMK combined
- Columns: date, spend, orders, CAC, Uninst%, Canc%

**TABLE 4 — TTMK Apps L7D Aggregate**
- One row per app, aggregated over L7D

### 3. Category Mix
Seekho-specific — breaks down performance by content category.

- Pivot table: category × metric (spend, CAC, uninst%) for L7D
- Bar charts by category
- Creative analysis within category

### 4. Ad Set Analysis
Drill-down from campaign → ad set → creative level.

- Campaign table with YD/L3D/L7D metrics
- Ad set table filtered by selected campaign
- Creative table with creative-type tagging (parsed from naming convention)
- Kitagawa waterfall charts for CAC and Uninst% contribution
- Spend × CAC scatter quadrant chart

### 5. Adviser
Automated recommendations per campaign based on L3D performance.

- Scores each campaign: `(cac_ratio × unin_ratio)` where ratio = actual / target
- Actions: Scale Up / Maintain / Pause / Watch
- Cards grouped by urgency

### 6. Budget
TTMK-wide budget allocation + ML predictor. See full detail in [Budget System](#budget-system) below.

---

## Key Metric Calculations

### CAC
```
CAC = total_cost / D0_paid_users
```

### Uninstall Rate
```
uninst% = p0_unin_users / D0_paid_users * 100
```

### Cancel Rate
```
canc% = p0_cancel_users / D0_paid_users * 100
```

### Kitagawa Decomposition (contribution analysis)
Decomposes a metric change (YD vs D-2) into two effects per campaign:

```
rate_effect = (rate_today - rate_yesterday) × share_yesterday
mix_effect  = (share_today - share_yesterday) × rate_yesterday
contribution = rate_effect + mix_effect
```

Applied to CAC (in ₹), Uninst% (in pp), and Canc% (in pp). A campaign with
high contribution means it was the primary driver of the overall metric movement.

---

## Budget System

### `data/campaign_config.csv`
617 campaigns mapped to type, owner, and app:

```csv
campaign_name,type,owner,app
top sub campaign - cbo,Scaling,Piyush,Seekho
...
```

Types: `Scaling` · `CTF` · `Experiment` · `Other`

### `data/targets.csv`
```csv
group,cac_target,unin_target,ctf_daily_cap,experiment_daily_cap
TTMK,500,15.0,5000,3000
Seekho,500,15.0,5000,3000
```

### Allocation Logic (`utils/allocator.py`)

**Step 1 — L3D aggregation per campaign**
Looks at the last 3 days of data: sums spend, orders, uninstalls, cancellations.

**Step 2 — Scaling campaigns**

| Condition | Status |
|---|---|
| Both CAC ≤ 0.85× target AND Uninst ≤ 0.85× target | SCALE_UP |
| CAC and Uninst within target | MAINTAIN |
| CAC > 1.2× target OR Uninst > 1.5× target OR both above | DEMOTE |
| Fewer than 3 orders in L3D | INSUFFICIENT_DATA |

Budget split (only SCALE_UP + MAINTAIN receive budget):
```
eff_score = 1 / (cac_ratio × unin_ratio)   # higher = more efficient
weight    = eff_score × multiplier          # SCALE_UP: 1.3×, MAINTAIN: 1.0×
budget    = (weight / total_weight) × daily_envelope
```
Rounded to nearest ₹100.

**Step 3 — Experiment campaigns**

| Condition | Verdict |
|---|---|
| CAC ≤ ₹450 AND Uninst ≤ 15% | GRADUATE → Scaling |
| CAC > ₹750 after 5+ days | KILL |
| Uninst > 30% after 5+ days | KILL |
| Otherwise | CONTINUE |

Fixed daily cap: ₹3,000 (configurable).

**Step 4 — CTF campaigns**
Fixed daily cap: ₹5,000. No decision made — creative testing framework.

**Step 5 — Other / Untagged**
Flagged as needing categorisation. No budget recommended.

---

## CAC Predictor (`utils/predictor.py`)

Per-campaign **Ridge regression** model that learns how CAC responds to 4 daily inputs.

### Features

| Feature | Source column |
|---|---|
| `spend` | `total_cost` |
| `uninstalls` | `p0_unin_users` |
| `cancellations` | `p0_cancel_users` |
| `num_creatives` | distinct `ad_creative` per campaign per day |

### Why Ridge and not OLS
With only 7–30 training points and correlated features (spend and uninstalls move together), ordinary least squares overfits. Ridge adds an L2 penalty `alpha × ||w||²` that shrinks coefficients and keeps predictions stable.

### Training
```python
# Standardise each feature
Xs = (X - mean) / std

# Ridge normal equation (intercept not penalised)
w = solve((Xs.T @ Xs + alpha·I), Xs.T @ y)
```

One model per campaign. Requires ≥ 3 training days.

### Prediction
Any feature not specified by the user defaults to that campaign's historical daily mean, so the minimum input is just a spend value:
```python
predict_cac(model, spend=60_000)
# → uses mean uninstalls, mean cancellations, mean creatives
```

### UI in Budget Tab

1. **Spend → CAC Curves** — L7D scatter + polynomial fit line per campaign. Simulator reads off the curve at a given spend.
2. **CAC Predictor** — 4 sliders (defaulting to each campaign's historical average). Output card shows:
   - Predicted CAC (green/red vs target)
   - Delta vs all-features-at-mean baseline
   - Model R², RMSE, training days inline

---

## Refresh Flow

The nav bar has a **Refresh** button per app:
1. POSTs to Redash with `max_age=0` to force re-execution of both app and creative queries
2. Clears Streamlit's 1-hour cache
3. Re-fetches fresh data

---

## Setup

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Set credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in REDASH_BASE_URL and REDASH_API_KEY

# 3. Run
streamlit run app.py
```

### Environment variables (alternative to secrets.toml)
```
REDASH_BASE_URL=https://analytics.seekho.in
REDASH_API_KEY=your_key_here
```

---

## Adding a New Campaign

Edit `data/campaign_config.csv`:
```csv
my_new_campaign,Scaling,OwnerName,Arivu
```

Types: `Scaling` · `CTF` · `Experiment` · `Other`

The Budget tab picks this up automatically on next load.

---

## Adding a New App

1. Add query IDs to `utils/fetcher.py`: `APP_QUERY_IDS` and optionally `CREATIVE_QUERY_IDS`
2. Add colour to `APP_COLORS` in `utils/metrics.py`
3. Add to `TTMK_APPS` in `utils/allocator.py` if it belongs to the TTMK group
