"""
CACPredictor — per-campaign Ridge regression for CAC prediction.

Features (daily, per campaign):
  spend          — total_cost
  uninstalls     — p0_unin_users
  cancellations  — p0_cancel_users (0 if column absent)
  num_creatives  — distinct ad_creative count per day (1 if creative df absent)

Target: daily CAC = total_cost / D0_paid_users

With only ~7–30 training points Ridge regression is preferred over OLS to
avoid overfitting when features correlate (spend and uninstalls often move
together).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

FEATURE_NAMES = ["spend", "uninstalls", "cancellations", "num_creatives"]
FEATURE_LABELS = {
    "spend":         "Daily Spend ₹",
    "uninstalls":    "Daily Uninstalls",
    "cancellations": "Daily Cancellations",
    "num_creatives": "Active Creatives",
}


# ── data builder ──────────────────────────────────────────────────────────────

def build_daily(
    df_camp: pd.DataFrame,
    cr_df: Optional[pd.DataFrame] = None,
    window_days: int = 14,
) -> pd.DataFrame:
    """
    Aggregate campaign-level df to daily rows with model features + target CAC.

    window_days: only use the most recent N days for training (default 14).
    cr_df: creative-level dataframe with columns [date_tz, campaign, ad_creative]
           used to count distinct creatives per campaign per day.
    """
    if df_camp.empty:
        return pd.DataFrame()

    # restrict to L{window_days} window
    all_dates = sorted(df_camp["date_tz"].unique())
    if len(all_dates) >= window_days:
        cutoff = all_dates[-window_days]
        df_camp = df_camp[df_camp["date_tz"] >= cutoff]

    agg_spec: dict = dict(
        spend=("total_cost", "sum"),
        orders=("D0_paid_users", "sum"),
        uninstalls=("p0_unin_users", "sum"),
    )
    if "p0_cancel_users" in df_camp.columns:
        agg_spec["cancellations"] = ("p0_cancel_users", "sum")

    daily = df_camp.groupby(["campaign", "date_tz"], as_index=False).agg(**agg_spec)

    if "cancellations" not in daily.columns:
        daily["cancellations"] = 0.0

    # target
    daily["cac"] = np.where(
        daily["orders"] > 0, daily["spend"] / daily["orders"], np.nan)
    daily = daily.dropna(subset=["cac"])
    daily = daily[daily["orders"] >= 1].reset_index(drop=True)

    # creative count from creative-level dataframe
    if (cr_df is not None and not cr_df.empty
            and "ad_creative" in cr_df.columns
            and "campaign" in cr_df.columns
            and "date_tz" in cr_df.columns):
        cr_count = (
            cr_df.groupby(["campaign", "date_tz"])["ad_creative"]
            .nunique()
            .reset_index()
            .rename(columns={"ad_creative": "num_creatives"})
        )
        daily = daily.merge(cr_count, on=["campaign", "date_tz"], how="left")
    else:
        daily["num_creatives"] = np.nan

    daily["num_creatives"] = daily["num_creatives"].fillna(1.0)

    return daily


# ── Ridge regression (numpy-only, no sklearn) ─────────────────────────────────

def _ridge_fit(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float = 10.0,
) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """
    Returns (weights, intercept, feature_mean, feature_std).

    Solves the standardised Ridge problem:
        min  ||y - Xs·w - b||² + alpha·||w||²
    The intercept b is not regularised.
    """
    mean = X.mean(axis=0)
    std  = X.std(axis=0)
    std[std == 0] = 1.0          # constant feature → don't divide by zero

    Xs = (X - mean) / std
    Xb = np.column_stack([Xs, np.ones(len(Xs))])

    reg = np.eye(Xb.shape[1]) * alpha
    reg[-1, -1] = 0.0            # don't penalise intercept

    w = np.linalg.solve(Xb.T @ Xb + reg, Xb.T @ y)
    return w[:-1], float(w[-1]), mean, std


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


# ── public API ────────────────────────────────────────────────────────────────

def train_models(
    df_camp: pd.DataFrame,
    cr_df: Optional[pd.DataFrame] = None,
    alpha: float = 10.0,
    min_samples: int = 3,
    window_days: int = 14,
) -> Dict[str, Any]:
    """
    Train one Ridge model per campaign.

    Returns
    -------
    {
      campaign_name: {
        "weights":       np.ndarray,   # one weight per feature (in standardised space)
        "intercept":     float,
        "scaler_mean":   np.ndarray,
        "scaler_std":    np.ndarray,
        "r2":            float,        # in-sample R²
        "rmse":          float,        # in-sample RMSE (₹)
        "n_samples":     int,
        "feature_names": list[str],
        "feature_means": dict,         # raw-space mean — used as simulation defaults
        "feature_mins":  dict,
        "feature_maxs":  dict,
        "coef_display":  dict,         # {feature: signed impact per +1 unit (raw scale)}
      }
    }
    """
    daily = build_daily(df_camp, cr_df, window_days=window_days)
    if daily.empty:
        return {}

    models: Dict[str, Any] = {}

    for camp, sub in daily.groupby("campaign"):
        if len(sub) < min_samples:
            continue

        X = sub[FEATURE_NAMES].values.astype(float)
        y = sub["cac"].values.astype(float)

        w, b, m, s = _ridge_fit(X, y, alpha=alpha)

        Xs    = (X - m) / s
        y_hat = Xs @ w + b

        r2   = _r2(y, y_hat)
        rmse = float(np.sqrt(np.mean((y - y_hat) ** 2)))

        # de-standardised coefficient: effect of +1 raw-unit on CAC
        coef_raw = w / s

        models[str(camp)] = {
            "weights":       w,
            "intercept":     b,
            "scaler_mean":   m,
            "scaler_std":    s,
            "r2":            r2,
            "rmse":          rmse,
            "n_samples":     int(len(sub)),
            "feature_names": FEATURE_NAMES,
            "feature_means": dict(zip(FEATURE_NAMES, X.mean(axis=0))),
            "feature_mins":  dict(zip(FEATURE_NAMES, X.min(axis=0))),
            "feature_maxs":  dict(zip(FEATURE_NAMES, X.max(axis=0))),
            "coef_display":  dict(zip(FEATURE_NAMES, coef_raw)),
        }

    return models


def predict_cac(
    model: dict,
    spend: float,
    uninstalls: Optional[float] = None,
    cancellations: Optional[float] = None,
    num_creatives: Optional[float] = None,
) -> float:
    """
    Predict CAC for a single campaign model.

    Any feature left as None defaults to that campaign's historical mean,
    so the user only has to specify spend if they don't want to control the rest.
    """
    means = model["feature_means"]
    x = np.array([
        spend,
        uninstalls    if uninstalls    is not None else means["uninstalls"],
        cancellations if cancellations is not None else means["cancellations"],
        num_creatives if num_creatives is not None else means["num_creatives"],
    ], dtype=float)

    xs   = (x - model["scaler_mean"]) / model["scaler_std"]
    pred = float(xs @ model["weights"] + model["intercept"])
    return max(pred, 0.0)
