"""
generate_alt_data.py
Generates a realistic alternate sample CSV for the KPI Dashboard.

Grounded in real Kaggle dataset benchmarks:
- IBM Telco Churn: MonthlyCharges $18-$118, ~26.5% churn rate, tenure 1-72 months
- Kaggle SaaS Business Metrics: 3 plan tiers (Basic/Pro/Enterprise), MRR $29-$299
- Kaggle E-Commerce 2021-2024: Regional revenue splits (Americas ~38%, EMEA ~31%, APAC ~31%)
- Kaggle Customer Churn Prediction: SupportTicketsPerMonth 0-9, subscription types

This script creates a scenario simulating a B2B SaaS analytics platform ("DataPulse")
with real-world patterns:
- Seasonal dip in Q3 (summer slowdown), Q4 budget-flush spike
- Enterprise segment grows steadily; SMB is volatile; Consumer has high churn
- APAC is the fastest-growing region; EMEA is mature and stable
- A deliberate anomaly in Aug 2023 (pricing migration causing churn spike)
"""

import csv
import random
import math
from pathlib import Path

random.seed(42)

# ── Configuration ─────────────────────────────────────────────────────────────
MONTHS = [f"2023-{m:02d}" for m in range(1, 13)] + [f"2024-{m:02d}" for m in range(1, 13)]
REGIONS = ["Americas", "EMEA", "APAC", "LATAM"]
PRODUCT_LINES = ["Enterprise", "SMB", "Consumer"]

# Base revenue per region×product (grounded in Kaggle SaaS MRR data scaled to segment)
# Enterprise: avg $249/seat × ~800 seats; SMB: avg $79/seat × ~600 seats; Consumer: avg $19/seat × ~2000 seats
BASE_REVENUE = {
    ("Americas", "Enterprise"):  199000,
    ("Americas", "SMB"):         118000,
    ("Americas", "Consumer"):     76000,
    ("EMEA", "Enterprise"):      172000,
    ("EMEA", "SMB"):             102000,
    ("EMEA", "Consumer"):         58000,
    ("APAC", "Enterprise"):      138000,
    ("APAC", "SMB"):              82000,
    ("APAC", "Consumer"):         48000,
    ("LATAM", "Enterprise"):      92000,
    ("LATAM", "SMB"):             56000,
    ("LATAM", "Consumer"):        32000,
}

# Monthly growth rates (annualized: Enterprise ~18%, SMB ~12%, Consumer ~8%)
GROWTH_RATE = {"Enterprise": 0.014, "SMB": 0.009, "Consumer": 0.006}

# Regional growth multipliers (APAC growing fastest, LATAM emerging)
REGION_GROWTH = {"Americas": 1.0, "EMEA": 0.9, "APAC": 1.4, "LATAM": 1.2}

# Seasonality factors (indexed by month 1-12)
# Q1: budget flush carryover, Q2: steady, Q3: summer dip, Q4: year-end spike
SEASONALITY = {
    1: 1.02, 2: 1.01, 3: 1.03,   # Q1: solid
    4: 1.00, 5: 0.99, 6: 0.98,   # Q2: plateaus
    7: 0.94, 8: 0.92, 9: 0.96,   # Q3: summer dip
    10: 1.01, 11: 1.04, 12: 1.08  # Q4: year-end spike
}

# Conversion rate baselines (from Kaggle Telco data: ~26.5% to ~3.5% depending on funnel)
# Enterprise: high-touch → higher conversion; Consumer: self-serve → lower
BASE_CONVERSION = {"Enterprise": 18.5, "SMB": 12.8, "Consumer": 7.2}

# Churn rate baselines (from Kaggle Telco: ~26.5% annual → ~2.5% monthly for high-churn)
# Enterprise: sticky contracts; Consumer: month-to-month like Telco basic
BASE_CHURN = {"Enterprise": 1.8, "SMB": 3.4, "Consumer": 5.8}

# New customers baseline
BASE_NEW_CUST = {
    ("Americas", "Enterprise"): 42, ("Americas", "SMB"): 68, ("Americas", "Consumer"): 156,
    ("EMEA", "Enterprise"): 35, ("EMEA", "SMB"): 58, ("EMEA", "Consumer"): 128,
    ("APAC", "Enterprise"): 28, ("APAC", "SMB"): 48, ("APAC", "Consumer"): 108,
    ("LATAM", "Enterprise"): 18, ("LATAM", "SMB"): 32, ("LATAM", "Consumer"): 72,
}

# Support tickets per 100 customers (from Kaggle: SupportTicketsPerMonth 0-9 range)
TICKET_RATE = {"Enterprise": 1.8, "SMB": 2.5, "Consumer": 3.8}


def generate_row(month_str: str, month_idx: int, region: str, product: str) -> dict:
    """Generate a single row with realistic, correlated metrics."""
    m = int(month_str.split("-")[1])
    season = SEASONALITY[m]
    growth = (1 + GROWTH_RATE[product] * REGION_GROWTH[region]) ** month_idx

    # ── Revenue ──
    base_rev = BASE_REVENUE[(region, product)]
    revenue = base_rev * growth * season
    # Add noise (±3%)
    revenue *= random.uniform(0.97, 1.03)

    # ── Anomaly: Aug 2023 pricing migration causes disruption ──
    is_anomaly_month = month_str == "2023-08"
    if is_anomaly_month:
        if product == "Consumer":
            revenue *= 0.78  # Consumer segment hit hardest
        elif product == "SMB":
            revenue *= 0.88

    revenue = round(revenue, -2)  # Round to nearest 100

    # ── Conversion Rate ──
    conv = BASE_CONVERSION[product]
    # Gradual improvement over time (product improvements)
    conv += month_idx * 0.08
    conv *= season
    # APAC slightly lower conversion (market maturity)
    if region == "APAC":
        conv *= 0.92
    elif region == "LATAM":
        conv *= 0.88
    conv += random.uniform(-0.6, 0.6)
    conv = round(max(3.0, min(35.0, conv)), 1)

    # ── Churn Rate ──
    churn = BASE_CHURN[product]
    # Gradually improving churn (better product, customer success)
    churn -= month_idx * 0.04
    # Higher churn in Q3 (summer, less engagement)
    if m in (7, 8, 9):
        churn += 0.5
    # Anomaly: Aug 2023 pricing migration spike
    if is_anomaly_month:
        churn += 2.8 if product == "Consumer" else 1.5 if product == "SMB" else 0.6
    churn += random.uniform(-0.3, 0.3)
    churn = round(max(0.5, min(12.0, churn)), 1)

    # ── Retention (inversely correlated with churn, but not exactly 100-churn) ──
    retention = 100 - churn - random.uniform(-0.2, 0.2)
    retention = round(max(88.0, min(99.5, retention)), 1)

    # ── New Customers ──
    base_cust = BASE_NEW_CUST[(region, product)]
    new_cust = base_cust * growth * season
    if is_anomaly_month and product in ("Consumer", "SMB"):
        new_cust *= 0.72  # Pricing change deters signups
    new_cust += random.uniform(-8, 8)
    new_cust = max(5, round(new_cust))

    # ── Support Tickets (correlated with customer base size and churn) ──
    # Higher churn → more tickets; anomaly months → spike
    cust_base = base_cust * growth * 8  # Rough total customer estimate
    tickets = cust_base * TICKET_RATE[product] / 100
    tickets *= (1 + (churn - BASE_CHURN[product]) * 0.15)  # Churn correlation
    if is_anomaly_month:
        tickets *= 1.6  # Support flood during pricing migration
    tickets += random.uniform(-10, 10)
    tickets = max(10, round(tickets))

    return {
        "month": month_str,
        "region": region,
        "product_line": product,
        "revenue": int(revenue),
        "conversion_rate": conv,
        "churn_rate": churn,
        "new_customers": new_cust,
        "customer_retention": retention,
        "support_tickets": tickets,
    }


def main():
    rows = []
    for month_idx, month_str in enumerate(MONTHS):
        for region in REGIONS:
            for product in PRODUCT_LINES:
                rows.append(generate_row(month_str, month_idx, region, product))

    output_path = Path(__file__).parent / "data" / "datapulse_kpi_data.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "month", "region", "product_line", "revenue",
            "conversion_rate", "churn_rate", "new_customers",
            "customer_retention", "support_tickets"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows -> {output_path}")
    print(f"  Months: {MONTHS[0]} to {MONTHS[-1]}")
    print(f"  Regions: {', '.join(REGIONS)}")
    print(f"  Products: {', '.join(PRODUCT_LINES)}")
    print(f"  File size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
