import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def _secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, fall back to env var."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

REDASH_BASE_URL = _secret("REDASH_BASE_URL", "https://analytics.seekho.in")
REDASH_API_KEY  = _secret("REDASH_API_KEY", "")

APP_QUERY_IDS = {
    "Arivu": 89268,
    "Vidhya": 89172,
    "Kali": 89171,
    "Nerchuko": 96035,
    "Seekho": 97452,
}

# Creative-level query IDs (Meta only).
CREATIVE_QUERY_IDS = {
    "Kali":     86001,
    "Vidhya":   86002,
    "Nerchuko": 86364,
    "Arivu":    86447,
    "Seekho":   97486,
}

NUMERIC_COLS = [
    "active_users", "D0_paid_users", "p0_unin_users", "p0_cancel_users",
    "p0_exit_users", "p0_watched_users", "p0_time_total", "p1_watched_users",
    "P1_paid_users", "total_cost", "installs", "clicks", "impressions",
    "D0_CAC", "CPP1", "CPS", "CPI", "CPC", "CPM", "D0_Conversion",
    "p0_uninstalls", "p0_cancellation", "p0_exit", "p0_time_spent", "p1_retention",
]


@st.cache_data(ttl=3600)
def fetch_app_data(app_name: str) -> pd.DataFrame:
    query_id = APP_QUERY_IDS[app_name]
    url = f"{REDASH_BASE_URL}/api/queries/{query_id}/results.json"
    params = {"api_key": REDASH_API_KEY}

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    payload = resp.json()
    rows = payload["query_result"]["data"]["rows"]
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    if "date_tz" in df.columns:
        df["date_tz"] = pd.to_datetime(df["date_tz"]).dt.date

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # exclude installer rows — data is unreliable
    for col in ("campaign", "ad_set", "ad_creative", "source"):
        if col in df.columns:
            mask = df[col].str.contains("install", case=False, na=False)
            df = df[~mask]

    return df


def refresh_app_data(app_name: str) -> pd.DataFrame:
    fetch_app_data.clear(app_name)
    return fetch_app_data(app_name)


@st.cache_data(ttl=3600)
def fetch_creative_data(app_name: str) -> pd.DataFrame:
    if app_name not in CREATIVE_QUERY_IDS:
        return pd.DataFrame()
    query_id = CREATIVE_QUERY_IDS[app_name]
    url = f"{REDASH_BASE_URL}/api/queries/{query_id}/results.json"
    resp = requests.get(url, params={"api_key": REDASH_API_KEY}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()["query_result"]["data"]["rows"]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if "date_tz" in df.columns:
        df["date_tz"] = pd.to_datetime(df["date_tz"]).dt.date
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # exclude installer rows — data is unreliable
    for col in ("campaign", "ad_set", "ad_creative", "source"):
        if col in df.columns:
            mask = df[col].str.contains("install", case=False, na=False)
            df = df[~mask]

    return df
