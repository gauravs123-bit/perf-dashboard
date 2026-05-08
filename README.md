# Performance Marketing Dashboard

A daily performance marketing dashboard for monitoring D0 CAC and uninstall rates across apps — built with Streamlit, powered by Redash.

## Apps Covered

| App | Color |
|---|---|
| Seekho | #F5A623 |
| Arivu | #7F77DD |
| Kali | #1D9E75 |
| Vidhya | #D85A30 |
| Nerchuko | #D4537E |

---

## What It Does

### Morning Pulse (main view)
- **KPI cards** — Today vs yesterday: Spend, D0 Orders, D0 CAC, Uninstall Rate, Cancel Rate with absolute deltas
- **7-day daily table** — Spend, Orders, CAC, Uninstall % for each of the last 7 days with day-over-day deltas
- **Date selector** — Switch the entire view to any of the last 7 days (not just today)
- **Kitagawa contributors** — Which campaigns drove CAC rise / uninstall rise, decomposed into rate effect + mix effect
- **Drill-down** — Campaign → Ad Set → Creative, each level showing contribution pills (how much they explain the overall app-level delta)

### Key Metrics

| Metric | Definition |
|---|---|
| D0 CAC | `total_spend / D0_paid_users` |
| P0 Uninstall Rate | `p0_unin_users / D0_paid_users × 100` |
| Kitagawa contribution | Rate effect + mix effect decomposition of day-over-day delta |

---

## Setup

### Local

```bash
git clone https://github.com/gauravs123-bit/perf-dashboard
cd perf-dashboard
pip install -r requirements.txt
```

Create a `.env` file:
```
REDASH_BASE_URL=https://your-redash-instance.com
REDASH_API_KEY=your_api_key_here
```

Run:
```bash
streamlit run app.py
```

### Streamlit Cloud

1. Fork / connect this repo at [share.streamlit.io](https://share.streamlit.io)
2. Set secrets in Advanced settings:
```toml
REDASH_BASE_URL = "https://your-redash-instance.com"
REDASH_API_KEY  = "your_api_key_here"
```

---

## Data Sources (Redash Query IDs)

| App | Adset Query | Creative Query |
|---|---|---|
| Seekho | 97452 | 97486 |
| Arivu | 89268 | 86447 |
| Vidhya | 89172 | 86002 |
| Kali | 89171 | 86001 |
| Nerchuko | 96035 | 86364 |

---

## Stack

- **Frontend** — Streamlit
- **Charts** — Plotly
- **Data** — Redash API (cached per session)
- **Analytics** — Kitagawa decomposition (rate effect + mix effect)
