"""
anomaly_detector.py
Uses scikit-learn IsolationForest to detect anomalous KPI values.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def detect_anomalies(monthly: pd.DataFrame, contamination: float = 0.1) -> pd.DataFrame:
    """Run IsolationForest on monthly KPI data. Adds is_anomaly and anomaly_score columns."""
    feature_cols = ["revenue", "conversion_rate", "churn_rate",
                    "new_customers", "customer_retention"]
    available = [c for c in feature_cols if c in monthly.columns]

    if len(monthly) < 4 or not available:
        monthly["is_anomaly"] = False
        monthly["anomaly_score"] = 0.0
        return monthly

    scaler = StandardScaler()
    X = scaler.fit_transform(monthly[available].fillna(0))

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(X)

    monthly = monthly.copy()
    monthly["anomaly_score"] = model.score_samples(X)
    monthly["is_anomaly"] = model.predict(X) == -1
    return monthly


def get_anomaly_summary(monthly: pd.DataFrame) -> dict:
    """Return a structured summary of detected anomalies with per-anomaly details."""
    if "is_anomaly" not in monthly.columns:
        return {
            "has_anomaly": False, "anomaly_months": [],
            "anomaly_note": "", "severity": "None", "details": []
        }

    anomaly_rows = monthly[monthly["is_anomaly"]]
    if anomaly_rows.empty:
        return {
            "has_anomaly": False, "anomaly_months": [],
            "anomaly_note": "", "severity": "None", "details": []
        }

    months_flagged = anomaly_rows["month"].dt.strftime("%B %Y").tolist()

    metric_cols = ["revenue", "conversion_rate", "churn_rate", "new_customers"]
    metric_labels = {
        "revenue": "Revenue",
        "conversion_rate": "Conversion Rate",
        "churn_rate": "Churn Rate",
        "new_customers": "New Customers",
    }
    available = [c for c in metric_cols if c in monthly.columns]

    notes = []
    details = []  # Structured anomaly details for cards
    for col in available:
        col_mean = monthly[col].mean()
        col_std = monthly[col].std()
        for _, row in anomaly_rows.iterrows():
            z = (row[col] - col_mean) / (col_std + 1e-9)
            if abs(z) > 1.5:
                direction = "spike" if z > 0 else "drop"
                month_str = row['month'].strftime('%B %Y')
                label = metric_labels.get(col, col.replace('_', ' ').title())

                # Build plain-English explanation
                if col == "revenue":
                    val_fmt = f"${row[col]:,.0f}"
                    avg_fmt = f"${col_mean:,.0f}"
                elif col in ("conversion_rate", "churn_rate"):
                    val_fmt = f"{row[col]:.1f}%"
                    avg_fmt = f"{col_mean:.1f}%"
                else:
                    val_fmt = f"{int(row[col]):,}"
                    avg_fmt = f"{int(col_mean):,}"

                if direction == "spike":
                    explanation = f"{label} reached {val_fmt} in {month_str}, significantly above the average of {avg_fmt}. This {abs(z):.1f}σ deviation suggests an unusual surge that may warrant investigation."
                else:
                    explanation = f"{label} fell to {val_fmt} in {month_str}, well below the average of {avg_fmt}. This {abs(z):.1f}σ deviation signals a potential issue that needs attention."

                notes.append(
                    f"{label} {direction} in {month_str} (z={z:.1f}σ)"
                )
                details.append({
                    "metric": label,
                    "month": month_str,
                    "direction": direction,
                    "z_score": round(z, 1),
                    "value": val_fmt,
                    "average": avg_fmt,
                    "explanation": explanation,
                    "severity": "High" if abs(z) > 2.0 else "Medium",
                })

    severity = "High" if len(months_flagged) >= 2 else "Medium" if notes else "Low"
    note = "; ".join(notes[:3]) if notes else f"Unusual pattern in {', '.join(months_flagged)}"

    return {
        "has_anomaly": True,
        "anomaly_months": months_flagged,
        "anomaly_note": note,
        "severity": severity,
        "details": details[:6],  # Cap at 6 cards max
    }
