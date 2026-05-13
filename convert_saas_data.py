"""
convert_saas_data.py
────────────────────
Converts the Kaggle "Customer Subscription Data" dataset (gsagar12/dspp1)
into a KPI-ready CSV compatible with the Smart KPI Dashboard.

USAGE
─────
1. Download all 4 files from https://www.kaggle.com/datasets/gsagar12/dspp1
2. Place them in a folder (e.g. KPI_Dashboard/data/saas_raw/)
3. Run:
       python convert_saas_data.py
4. Output → data/kpi_ready.csv  (upload this to the dashboard)

INPUT FILES EXPECTED
────────────────────
  saas_raw/customer_product.csv  — sign-up / cancellation dates + product + price
  saas_raw/customer_info.csv     — customer demographics + region
  saas_raw/customer_cases.csv    — call center case volume
  saas_raw/product_info.csv      — product name / type mapping
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_DIR    = Path(__file__).parent / "data" / "saas_raw"
OUTPUT_CSV = Path(__file__).parent / "data" / "kpi_ready.csv"


# ── Helpers ───────────────────────────────────────────────────────────────────
def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return first matching column name (case-insensitive) or None."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def load(filename: str) -> pd.DataFrame:
    path = RAW_DIR / filename
    if not path.exists():
        print(f"⚠️  Missing file: {path}")
        print(f"   Download from https://www.kaggle.com/datasets/gsagar12/dspp1")
        sys.exit(1)
    df = pd.read_csv(path, low_memory=False)
    print(f"✅ Loaded {filename}: {len(df):,} rows | Columns: {list(df.columns)}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load raw files
# ══════════════════════════════════════════════════════════════════════════════
print("\n📂 Loading raw files...")
cp = load("customer_product.csv")   # sign-up / cancellation / revenue
ci = load("customer_info.csv")      # demographics / region
cc = load("customer_cases.csv")     # call center cases
pi = load("product_info.csv")       # product names


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Detect key columns flexibly
# ══════════════════════════════════════════════════════════════════════════════
print("\n🔍 Detecting columns...")

# customer_product.csv
cp_id      = find_col(cp, ["customer_id", "customerid", "cust_id", "id"])
cp_prod    = find_col(cp, ["product_id", "productid", "product", "prod_id", "plan"])
cp_start   = find_col(cp, ["start_date", "startdate", "signup_date", "purchase_date", "date"])
cp_end     = find_col(cp, ["end_date", "enddate", "cancel_date", "cancellation_date", "churn_date"])
cp_price   = find_col(cp, ["price", "revenue", "amount", "mrr", "arr", "total", "value"])

# customer_info.csv
ci_id      = find_col(ci, ["customer_id", "customerid", "cust_id", "id"])
ci_region  = find_col(ci, ["region", "state", "area", "territory", "geo", "geography", "location"])

# customer_cases.csv
cc_date    = find_col(cc, ["date", "case_date", "created_date", "call_date", "datetime"])
cc_vol     = find_col(cc, ["volume", "cases", "count", "calls", "tickets", "case_count", "call_count"])
cc_id      = find_col(cc, ["customer_id", "customerid", "cust_id", "id"])

# product_info.csv
pi_id      = find_col(pi, ["product_id", "productid", "id", "prod_id"])
pi_name    = find_col(pi, ["product_name", "name", "product", "type", "plan_name", "plan"])

print(f"  customer_product: id={cp_id}, product={cp_prod}, start={cp_start}, end={cp_end}, price={cp_price}")
print(f"  customer_info:    id={ci_id}, region={ci_region}")
print(f"  customer_cases:   date={cc_date}, volume={cc_vol}")
print(f"  product_info:     id={pi_id}, name={pi_name}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Parse dates and join
# ══════════════════════════════════════════════════════════════════════════════
print("\n🔗 Joining and parsing dates...")

cp[cp_start] = pd.to_datetime(cp[cp_start], errors="coerce", infer_datetime_format=True)
if cp_end:
    cp[cp_end] = pd.to_datetime(cp[cp_end], errors="coerce", infer_datetime_format=True)

# Join product names if available
if pi_id and pi_name:
    cp = cp.merge(pi[[pi_id, pi_name]].drop_duplicates(), left_on=cp_prod, right_on=pi_id, how="left")
    product_col = pi_name
else:
    product_col = cp_prod

# Join region from customer_info
if ci_id and ci_region:
    cp = cp.merge(ci[[ci_id, ci_region]].drop_duplicates(subset=[ci_id]),
                  left_on=cp_id, right_on=ci_id, how="left")
    region_col = ci_region
else:
    print("⚠️  No region column found — using 'Unknown' as region")
    cp["region"] = "Unknown"
    region_col = "region"

# Drop rows with no start date
cp = cp.dropna(subset=[cp_start])
cp["month"] = cp[cp_start].dt.to_period("M")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Compute price per customer per month
# ══════════════════════════════════════════════════════════════════════════════
if cp_price:
    cp[cp_price] = pd.to_numeric(cp[cp_price], errors="coerce").fillna(0)
else:
    print("⚠️  No price/revenue column found — using $100 per customer as proxy")
    cp["price_proxy"] = 100.0
    cp_price = "price_proxy"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Normalise region and product
# ══════════════════════════════════════════════════════════════════════════════
# Map to 4 clean regions if needed
region_map = {
    "northeast": "North", "north": "North", "n": "North", "new england": "North",
    "south": "South",     "se": "South",    "s": "South", "southeast": "South",
    "west": "West",       "w": "West",      "pacific": "West", "northwest": "West",
    "east": "East",       "e": "East",      "midwest": "East", "mid-west": "East",
}
cp[region_col] = (
    cp[region_col]
    .astype(str).str.strip().str.lower()
    .map(lambda x: region_map.get(x, x.title()))
)

# Take top-4 regions if there are more
top_regions = cp[region_col].value_counts().nlargest(4).index.tolist()
cp = cp[cp[region_col].isin(top_regions)]

# Normalise product line to max 3 values
if product_col and product_col in cp.columns:
    top_products = cp[product_col].astype(str).value_counts().nlargest(3).index.tolist()
    cp[product_col] = cp[product_col].astype(str).apply(
        lambda x: x if x in top_products else top_products[0]
    )
else:
    cp["product_line"] = "Standard"
    product_col = "product_line"


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Monthly aggregation per region × product
# ══════════════════════════════════════════════════════════════════════════════
print("\n📊 Aggregating KPIs by month × region × product...")

def agg_monthly(df):
    grp = df.groupby(["month", region_col, product_col])

    # Revenue = sum of prices of active subscriptions
    revenue = grp[cp_price].sum().rename("revenue")

    # New customers = count of sign-ups in that month
    new_cust = grp[cp_id].count().rename("new_customers")

    result = pd.concat([revenue, new_cust], axis=1).reset_index()
    result.columns = ["month", "region", "product_line", "revenue", "new_customers"]
    return result

monthly = agg_monthly(cp)

# Churn: customers whose end_date falls in this month
if cp_end and cp_end in cp.columns:
    cp["churn_month"] = cp[cp_end].dt.to_period("M")
    churn = (
        cp.dropna(subset=[cp_end])
        .groupby(["churn_month", region_col, product_col])[cp_id]
        .count()
        .reset_index()
    )
    churn.columns = ["month", "region", "product_line", "churned"]
    monthly = monthly.merge(churn, on=["month", "region", "product_line"], how="left")
    monthly["churned"] = monthly["churned"].fillna(0)
else:
    print("⚠️  No cancellation date column — estimating churn at 4% per month")
    monthly["churned"] = (monthly["new_customers"] * 0.04).round()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Derive rate KPIs
# ══════════════════════════════════════════════════════════════════════════════
monthly["churn_rate"] = (
    (monthly["churned"] / monthly["new_customers"].replace(0, np.nan)) * 100
).clip(0, 50).round(2).fillna(4.0)

monthly["customer_retention"] = (100 - monthly["churn_rate"]).round(2)

# Conversion rate: proxy = new customers / (new customers + churned) * 100
monthly["conversion_rate"] = (
    (monthly["new_customers"] / (monthly["new_customers"] + monthly["churned"] + 1)) * 100
).clip(5, 50).round(2)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Merge call center / support tickets
# ══════════════════════════════════════════════════════════════════════════════
if cc_date and cc_date in cc.columns:
    cc[cc_date] = pd.to_datetime(cc[cc_date], errors="coerce", infer_datetime_format=True)
    cc = cc.dropna(subset=[cc_date])
    cc["month"] = cc[cc_date].dt.to_period("M")

    if cc_vol and cc_vol in cc.columns:
        cc[cc_vol] = pd.to_numeric(cc[cc_vol], errors="coerce").fillna(1)
        monthly_cases = cc.groupby("month")[cc_vol].sum().reset_index()
        monthly_cases.columns = ["month", "total_cases"]
    else:
        monthly_cases = cc.groupby("month").size().reset_index(name="total_cases")

    # Distribute proportionally across region × product combos per month
    combo_counts = monthly.groupby("month")["region"].transform("count")
    monthly_cases_map = monthly_cases.set_index("month")["total_cases"].to_dict()
    monthly["support_tickets"] = (
        monthly["month"].map(monthly_cases_map).fillna(200) / combo_counts
    ).round().astype(int)
else:
    print("⚠️  No case date column — estimating support tickets from new customers")
    monthly["support_tickets"] = (monthly["new_customers"] * 0.4).round().astype(int)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — Final cleanup and output
# ══════════════════════════════════════════════════════════════════════════════
monthly["month"] = monthly["month"].astype(str)
monthly["revenue"] = monthly["revenue"].round(2)
monthly["new_customers"] = monthly["new_customers"].astype(int)
monthly["support_tickets"] = monthly["support_tickets"].astype(int)

# Sort by month
monthly = monthly.sort_values("month").reset_index(drop=True)

# Keep only needed columns
output_cols = [
    "month", "region", "product_line", "revenue",
    "conversion_rate", "churn_rate", "new_customers",
    "customer_retention", "support_tickets"
]
monthly = monthly[[c for c in output_cols if c in monthly.columns]]

# Filter to months with meaningful data
monthly = monthly[monthly["new_customers"] > 0]

print(f"\n✅ Conversion complete!")
print(f"   Rows: {len(monthly):,}")
print(f"   Date range: {monthly['month'].min()} → {monthly['month'].max()}")
print(f"   Regions: {sorted(monthly['region'].unique())}")
print(f"   Products: {sorted(monthly['product_line'].unique())}")
print(f"\n📋 Sample output:")
print(monthly.head(8).to_string(index=False))

monthly.to_csv(OUTPUT_CSV, index=False)
print(f"\n💾 Saved to: {OUTPUT_CSV}")
print(f"   ✅ Upload this file to the Smart KPI Dashboard!")
