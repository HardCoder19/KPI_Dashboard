"""
forecaster.py
Linear regression forecast for next-quarter revenue projection.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_revenue(monthly: pd.DataFrame, periods: int = 3) -> dict:
    """
    Fit LinearRegression on last 6 months of revenue, forecast next `periods` months.
    Returns dict with forecast values, months, and pct change vs current.
    """
    if len(monthly) < 3:
        return {"forecast_values": [], "forecast_months": [], "forecast_pct": 0.0}

    series = monthly[["month", "revenue"]].dropna().tail(6).reset_index(drop=True)
    X = np.arange(len(series)).reshape(-1, 1)
    y = series["revenue"].values

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(len(series), len(series) + periods).reshape(-1, 1)
    future_y = model.predict(future_X)

    last_month = series["month"].iloc[-1]
    future_months = [
        (last_month + pd.DateOffset(months=i + 1)).strftime("%b %Y")
        for i in range(periods)
    ]

    current_rev = series["revenue"].iloc[-1]
    end_forecast = future_y[-1]
    pct_change = ((end_forecast - current_rev) / current_rev) * 100 if current_rev else 0

    return {
        "forecast_values": [round(v, 0) for v in future_y],
        "forecast_months": future_months,
        "forecast_pct": round(pct_change, 1),
        "end_forecast": round(end_forecast, 0),
        "r2_score": round(model.score(X, y), 3)
    }
