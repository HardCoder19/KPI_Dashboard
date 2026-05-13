"""
data_loader.py
Handles CSV ingestion, validation, metric aggregation, and MoM calculations.
"""

import pandas as pd
import numpy as np
from pathlib import Path

REQUIRED_COLUMNS = {
    "month", "region", "product_line", "revenue",
    "conversion_rate", "churn_rate", "new_customers",
    "customer_retention", "support_tickets"
}

NUMERIC_COLS = ["revenue", "conversion_rate", "churn_rate",
                "new_customers", "customer_retention", "support_tickets"]

SAMPLE_DATA_PATH = Path(__file__).parent.parent / "data" / "sample_kpi_data.csv"


def load_csv(file=None) -> pd.DataFrame:
    """Load CSV from uploaded file object or fall back to sample dataset."""
    if file is not None:
        df = pd.read_csv(file)
    else:
        df = pd.read_csv(SAMPLE_DATA_PATH)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def validate_schema(df: pd.DataFrame) -> list[str]:
    """Return list of validation errors; empty list means valid."""
    errors = []
    missing = REQUIRED_COLUMNS - set(df.columns.str.lower())
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
    if df.empty:
        errors.append("Dataset is empty.")
    for col in NUMERIC_COLS:
        if col in df.columns and df[col].isna().all():
            errors.append(f"Column '{col}' has no valid numeric values.")
    return errors


def apply_filters(df: pd.DataFrame, regions: list, products: list,
                  start_month=None, end_month=None) -> pd.DataFrame:
    """Apply sidebar filters to the dataframe."""
    if regions:
        df = df[df["region"].isin(regions)]
    if products:
        df = df[df["product_line"].isin(products)]
    if start_month:
        df = df[df["month"] >= pd.to_datetime(start_month)]
    if end_month:
        df = df[df["month"] <= pd.to_datetime(end_month)]
    return df


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate all regions/products by month for trend charts."""
    monthly = df.groupby("month").agg(
        revenue=("revenue", "sum"),
        conversion_rate=("conversion_rate", "mean"),
        churn_rate=("churn_rate", "mean"),
        new_customers=("new_customers", "sum"),
        customer_retention=("customer_retention", "mean"),
        support_tickets=("support_tickets", "sum")
    ).reset_index().sort_values("month")
    return monthly


def compute_mom(monthly: pd.DataFrame) -> dict:
    """
    Compute Month-over-Month % change for the latest month vs previous.
    Returns dict of {metric: (current_value, mom_pct, prev_value)}
    """
    if len(monthly) < 2:
        return {}

    latest = monthly.iloc[-1]
    previous = monthly.iloc[-2]
    metrics = {}

    for col in ["revenue", "conversion_rate", "churn_rate",
                "new_customers", "customer_retention", "support_tickets"]:
        cur = latest[col]
        prev = previous[col]
        if prev and prev != 0:
            pct = ((cur - prev) / abs(prev)) * 100
        else:
            pct = 0.0
        metrics[col] = {
            "current": cur,
            "previous": prev,
            "mom_pct": round(pct, 1),
            "month": latest["month"].strftime("%B %Y")
        }
    return metrics


def get_regional_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the latest month's data by region."""
    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]
    regional = latest.groupby("region").agg(
        revenue=("revenue", "sum"),
        conversion_rate=("conversion_rate", "mean"),
        churn_rate=("churn_rate", "mean"),
        new_customers=("new_customers", "sum"),
    ).reset_index()
    return regional


def get_product_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the latest month's data by product line."""
    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]
    product = latest.groupby("product_line").agg(
        revenue=("revenue", "sum"),
        conversion_rate=("conversion_rate", "mean"),
        churn_rate=("churn_rate", "mean"),
        new_customers=("new_customers", "sum"),
    ).reset_index()
    return product


def get_trend_direction(series: pd.Series, window: int = 3) -> str:
    """Determine if a metric is improving, declining, or stable over last N months."""
    if len(series) < 2:
        return "stable"
    recent = series.iloc[-window:] if len(series) >= window else series
    slope = np.polyfit(range(len(recent)), recent.values, 1)[0]
    relative = abs(slope) / (abs(series.mean()) + 1e-9)
    if relative < 0.005:
        return "stable"
    return "improving" if slope > 0 else "declining"


def build_ai_metrics(df: pd.DataFrame, monthly: pd.DataFrame,
                     mom: dict, anomalies: dict, forecast: dict) -> dict:
    """
    Build a unified metrics dict for prompt construction.
    Combines MoM, regional breakdown, trends, anomalies, and forecasts.
    """
    regional = get_regional_breakdown(df)
    top_region = regional.loc[regional["revenue"].idxmax(), "region"]
    bottom_region = regional.loc[regional["revenue"].idxmin(), "region"]
    top_region_rev = regional["revenue"].max()
    bottom_region_rev = regional["revenue"].min()

    metrics = {
        "month": mom.get("revenue", {}).get("month", "Latest Month"),
        "top_region": top_region,
        "bottom_region": bottom_region,
        "top_region_rev": top_region_rev,
        "bottom_region_rev": bottom_region_rev,
    }

    for key, data in mom.items():
        metrics[key] = data["current"]
        metrics[f"{key}_mom_pct"] = data["mom_pct"]
        metrics[f"{key}_prev"] = data["previous"]

    for key in ["revenue", "conversion_rate", "churn_rate", "new_customers"]:
        if key in monthly.columns:
            metrics[f"{key}_trend"] = get_trend_direction(monthly[key])

    metrics["anomalies"] = anomalies
    metrics["forecast"] = forecast
    return metrics
