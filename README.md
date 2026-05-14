# Smart KPI Dashboard

> **AI-powered business intelligence dashboard** that automatically ingests structured business data, renders interactive KPI visualizations, and generates executive-level narrative insights using Google Gemini.

Built for: RP-Sanjiv Goenka / Firstsource Take-Home Assessment | Pro-Code Track

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/KPI_Dashboard.git
cd KPI_Dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here
# Get a free key at: https://aistudio.google.com

# 4. Run the dashboard
streamlit run app.py
```

The app opens at **http://localhost:8501**. You will be greeted by the **Welcome Screen**. From there, you can either **Upload a CSV** or click the **Load Sample Data** button at the bottom to instantly populate the dashboard and trigger AI generation.

---

## 📁 Project Structure

```
KPI_Dashboard/
├── app.py                      # Main Streamlit application with UI/UX logic
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .streamlit/
│   └── config.toml             # Dark theme configuration
├── data/
│   ├── sample_kpi_data.csv     # Original 12-month synthetic operations dataset
│   └── datapulse_kpi_data.csv  # Alternative Kaggle-based sample dataset
├── utils/
│   ├── data_loader.py          # Pandas ingestion, aggregation, and MoM calculations
│   ├── anomaly_detector.py     # scikit-learn IsolationForest anomaly detection
│   ├── forecaster.py           # scikit-learn LinearRegression revenue forecast
│   ├── prompt_builder.py       # Gemini prompt construction (creates bullet-point insights)
│   ├── gemini_client.py        # Gemini API wrapper with Streamlit caching
│   └── pdf_exporter.py         # ReportLab PDF report generation
├── convert_saas_data.py        # Utility script for legacy data conversion
└── generate_alt_data.py        # Utility script to generate the alternate Kaggle-based data
```

---

## 📊 Data Ingestion Flow

```
CSV File (upload via Welcome Screen)
        │
        ▼
pandas.read_csv()
        │
        ▼
validate_schema()          ← checks required columns exist
        │
        ▼
apply_filters()            ← region, product line filtering
        │
        ▼
aggregate_monthly()        ← group by month, sum/mean per KPI
        │
   ┌────┴────────────────┐
   ▼                     ▼
compute_mom()        detect_anomalies()     forecast_revenue()
(MoM % change)       (IsolationForest)      (LinearRegression)
        │
        ▼
build_ai_metrics()         ← unified context dict for prompts
        │
        ▼
Plotly Charts + Gemini AI Commentary + PDF Export
```

**Required CSV columns:**
| Column | Type | Description |
|--------|------|-------------|
| `month` | YYYY-MM | Reporting month |
| `region` | string | Geographic region |
| `product_line` | string | Product segment |
| `revenue` | float | Monthly revenue |
| `conversion_rate` | float | Lead-to-customer % |
| `churn_rate` | float | Monthly churn % |
| `new_customers` | int | New customer count |
| `customer_retention` | float | Retention % |
| `support_tickets` | int | Support ticket volume |

---

## 🤖 AI Commentary Logic

### Prompt Design Philosophy

Each KPI receives a **structured, context-rich prompt** that injects:
- Current metric value + MoM % change
- Regional top/bottom performers
- 3-month trend direction (improving / declining / stable)
- Anomaly detection result (IsolationForest flag + severity)
- Revenue forecast (Linear Regression, next 3 months)

**Lucid Business Language:**
The prompts instruct Gemini to output **3 to 5 concise bullet points** using clear, board-level business language. It highlights the "why" behind the trends and offers actionable strategic recommendations rather than dense paragraphs.

### Example: Revenue Prompt → Output

**Prompt sent to Gemini:**
```
You are a senior business analyst writing an executive KPI briefing for leadership.

DATA CONTEXT — Revenue:
- Reporting Period: December 2024
- Total Revenue: $1,901,000
- Month-over-Month Change: +3.9%
...
- Next Quarter Forecast: $2,043,000 (+7.5% vs current)

INSTRUCTIONS:
Write 3 to 5 concise bullet points.
Format: **[Bold Finding]:** [Brief explanation].
Use lucid, executive-level business language...
```

**Sample Gemini Output:**
- **Robust Q4 Finish:** December revenue reached $1.9M, a 3.9% month-over-month increase that solidifies our strong Q4 trajectory.
- **Enterprise Growth Drives North Region:** The North region led all geographies at $903K, propelled by higher-than-average Enterprise product adoption.
- **South Region Requires Intervention:** Trailing at $811K, the South region presents an immediate opportunity for targeted Q1 sales enablement and marketing spend.
- **Clean Trend Signal:** Our anomaly detection models flagged zero irregularities, indicating stable, predictable revenue growth.
- **Positive Q1 Outlook:** Linear regression modeling projects revenue to hit $2.04M by Q1 2025, representing a 7.5% uplift and our strongest anticipated quarter to date.

---

## 🔬 Anomaly Detection

Uses **scikit-learn `IsolationForest`** on monthly aggregated KPI data:
- Trains on 5 features: revenue, conversion rate, churn, new customers, retention
- `contamination=0.10` (flags ~10% of months as potential anomalies)
- Anomalous months are shown as **red ✕ markers** on the Revenue chart.
- **Anomaly Cards:** When an anomaly is detected, dedicated glassmorphism cards appear at the top of the dashboard breaking down exactly what happened, the severity, and a plain-English explanation.
- Anomaly context is injected into AI prompts for narrative explanation.

---

## 📈 Revenue Forecasting

Uses **scikit-learn `LinearRegression`** on the last 6 months:
- Fits a linear trend to recent revenue history
- Projects 3 months forward
- Forecast is overlaid as a **dashed purple line** on the Revenue chart
- Forecast values are included in the Revenue and Executive AI prompts for forward-looking analysis.

---

## 🛠️ Tech Stack

| Component | Library | Version |
|-----------|---------|---------|
| Dashboard Framework | Streamlit | ≥1.35 |
| Data Analysis | Pandas | ≥2.0 |
| Visualization | Plotly | ≥5.18 |
| AI Commentary | Google Gemini (`gemini-1.5-flash`) | ≥0.5 |
| Anomaly Detection | scikit-learn `IsolationForest` | ≥1.4 |
| Forecasting | scikit-learn `LinearRegression` | ≥1.4 |
| PDF Export | ReportLab | ≥4.1 |

---

## ⚠️ Limitations & Assumptions

- **Synthetic dataset**: Sample data is algorithmically generated for demonstration; real-world data will vary.
- **Gemini limits**: `gemini-1.5-flash` has rate limits (~15 RPM on free tier). If you hit limits while regenerating insights, wait 60 seconds and retry.
- **Linear forecast**: Revenue forecasting uses simple linear regression — it assumes trend continuity and does not model complex seasonality.
- **No authentication**: This is a prototype dashboard meant to run locally or in a private network; add proper auth before public deployment.

---

## 📬 Submission

Demo: [Streamlit Cloud link — add after deployment]  
Repository: https://github.com/HardCoder19/KPI_Dashboard/  
Author: Manav Mishra


