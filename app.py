"""
app.py — Smart KPI Dashboard
Main Streamlit application entry point.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import (
    load_csv, validate_schema, apply_filters,
    aggregate_monthly, compute_mom, get_regional_breakdown,
    get_product_breakdown, build_ai_metrics
)
from utils.anomaly_detector import detect_anomalies, get_anomaly_summary
from utils.forecaster import forecast_revenue
from utils.prompt_builder import (
    build_revenue_prompt, build_conversion_prompt,
    build_churn_prompt, build_customers_prompt,
    build_executive_summary_prompt
)
from utils.gemini_client import generate_all_commentary, clear_cache
from utils.pdf_exporter import generate_pdf

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ────────────────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 4rem !important; padding-bottom: 1rem !important; }

/* ── Header Banner ─────────────────────────────────────────────────────── */
.header-banner {
    background: linear-gradient(135deg, rgba(79,142,247,0.07) 0%, rgba(139,92,246,0.07) 100%);
    border: 1px solid rgba(79,142,247,0.15);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    backdrop-filter: blur(12px);
}
.header-title {
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4f8ef7, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.02em;
}
.header-subtitle {
    color: #8b949e;
    font-size: 0.85rem;
    margin: 6px 0 0 0;
    font-weight: 400;
}
.header-meta {
    color: #6e7681;
    font-size: 0.75rem;
    margin: 0;
    text-align: right;
}

/* ── KPI Metric Cards ─────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(22, 27, 34, 0.6);
    border: 1px solid rgba(48, 54, 61, 0.8);
    border-radius: 14px;
    padding: 18px 22px !important;
    backdrop-filter: blur(16px);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(79, 142, 247, 0.12);
    border-color: rgba(79, 142, 247, 0.4);
}
[data-testid="stMetricLabel"] {
    color: #8b949e !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

/* ── AI Commentary ─────────────────────────────────────────────────────── */
.ai-box {
    background: rgba(22, 27, 34, 0.5);
    border: 1px solid rgba(48, 54, 61, 0.6);
    border-left: 3px solid #4f8ef7;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    color: #c9d1d9;
    font-size: 0.9rem;
    line-height: 1.7;
    backdrop-filter: blur(8px);
}
.ai-box-exec {
    background: linear-gradient(135deg, rgba(79,142,247,0.06), rgba(139,92,246,0.06));
    border: 1px solid rgba(79,142,247,0.2);
    border-left: 3px solid #8b5cf6;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    color: #c9d1d9;
    font-size: 0.92rem;
    line-height: 1.75;
    backdrop-filter: blur(8px);
}
.ai-box ul, .ai-box-exec ul {
    margin: 0;
    padding-left: 20px;
}
.ai-box li, .ai-box-exec li {
    margin-bottom: 8px;
}
.ai-box li:last-child, .ai-box-exec li:last-child {
    margin-bottom: 0;
}
.ai-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4f8ef7;
    margin-bottom: 6px;
}
.ai-label-exec {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8b5cf6;
    margin-bottom: 6px;
}

/* ── Anomaly Alert ─────────────────────────────────────────────────────── */
.anomaly-box {
    background: rgba(239, 68, 68, 0.06);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-left: 3px solid #ef4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: #fca5a5;
    font-size: 0.88rem;
    line-height: 1.6;
}
.anomaly-card {
    background: rgba(22, 27, 34, 0.6);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-top: 3px solid #ef4444;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    backdrop-filter: blur(12px);
}
.anomaly-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.anomaly-card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #e6edf3;
    margin: 0;
}
.anomaly-card-stat {
    font-size: 1.8rem;
    font-weight: 700;
    color: #fca5a5;
    margin: 0 0 8px 0;
}
.anomaly-card-desc {
    font-size: 0.9rem;
    color: #c9d1d9;
    line-height: 1.5;
    margin: 0;
}

/* ── Welcome Screen ────────────────────────────────────────────────────── */
.welcome-screen {
    max-width: 800px;
    margin: 60px auto;
    text-align: center;
}
.welcome-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4f8ef7, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
    letter-spacing: -0.02em;
}
.welcome-subtitle {
    font-size: 1.1rem;
    color: #8b949e;
    margin-bottom: 40px;
}
.welcome-card {
    background: rgba(22, 27, 34, 0.6);
    border: 1px solid rgba(48, 54, 61, 0.8);
    border-radius: 16px;
    padding: 32px;
    text-align: left;
    backdrop-filter: blur(16px);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
}
.welcome-card:hover {
    transform: translateY(-4px);
    border-color: rgba(79, 142, 247, 0.4);
    box-shadow: 0 12px 32px rgba(79, 142, 247, 0.12);
}
.welcome-card h3 {
    margin-top: 0;
    color: #e6edf3;
    font-size: 1.25rem;
}
.welcome-card p {
    color: #8b949e;
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 24px;
}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: rgba(13, 17, 23, 0.5);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8b949e;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 8px 20px;
    letter-spacing: 0.01em;
}
.stTabs [aria-selected="true"] {
    background: rgba(79, 142, 247, 0.12) !important;
    color: #e6edf3 !important;
    font-weight: 600;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── Sidebar ───────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .stMarkdown hr {
    border-color: #21262d;
    margin: 12px 0;
}
.sidebar-section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6e7681;
    margin: 16px 0 8px 0;
}

/* ── Expander ──────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.88rem;
    font-weight: 600;
    color: #c9d1d9;
}

/* ── Download button ───────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    box-shadow: 0 4px 16px rgba(46, 160, 67, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* ── Misc ──────────────────────────────────────────────────────────────── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.pill-green { background: rgba(16,185,129,0.15); color: #34d399; }
.pill-red { background: rgba(239,68,68,0.15); color: #f87171; }
.pill-blue { background: rgba(79,142,247,0.15); color: #79b8ff; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark chart layout ──────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#8b949e", size=11),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#21262d",
                borderwidth=1, font=dict(color="#c9d1d9", size=10)),
    xaxis=dict(gridcolor="#161b22", linecolor="#21262d",
               tickfont=dict(color="#6e7681")),
    yaxis=dict(gridcolor="#161b22", linecolor="#21262d",
               tickfont=dict(color="#6e7681")),
    hoverlabel=dict(bgcolor="#161b22", bordercolor="#4f8ef7",
                    font=dict(color="#e6edf3", family="Inter")),
)
COLORS = ["#4f8ef7", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4"]


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
if "df_raw" not in st.session_state:
    st.session_state["df_raw"] = None
if "ai_commentary" not in st.session_state:
    st.session_state["ai_commentary"] = {}
if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "filter_key" not in st.session_state:
    st.session_state["filter_key"] = 0


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & WELCOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("df_raw") is None:
    welcome_container = st.empty()
    with welcome_container.container():
        st.markdown("""
        <div class="welcome-screen">
            <h1 class="welcome-title">Smart KPI Dashboard</h1>
            <p class="welcome-subtitle">Connect your data to instantly generate AI-powered business insights.</p>
        </div>
        """, unsafe_allow_html=True)
    
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="welcome-card">
                <h3>📂 Upload CSV</h3>
                <p>Upload your monthly KPI data. The file must include metrics for revenue, conversion_rate, churn_rate, and new_customers.</p>
            </div>
            """, unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed", key=f"welcome_uploader_{st.session_state['uploader_key']}")
            if uploaded_file:
                st.session_state["df_raw"] = load_csv(uploaded_file)
                st.session_state["filter_key"] += 1
                st.session_state["ai_commentary"] = {}
                welcome_container.empty()
                st.rerun()
                
        with col2:
            st.markdown("""
            <div class="welcome-card" style="opacity: 0.7;">
                <h3>🔌 Connect Database</h3>
                <p>Securely connect to PostgreSQL, Snowflake, or BigQuery to pull live metrics.</p>
                <div style="margin-top: 16px;">
                    <span class="status-pill pill-blue">Coming Soon</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Hidden fallback for testing: load default sample if no upload
        if st.button("Load Sample Data (DataPulse)", type="tertiary"):
            from pathlib import Path
            st.session_state["df_raw"] = load_csv(str(Path("data/datapulse_kpi_data.csv")))
            st.session_state["filter_key"] += 1
            st.session_state["ai_commentary"] = {}
            welcome_container.empty()
            st.rerun()
            
    st.stop()

# If we reached here, df_raw is loaded
df_raw = st.session_state["df_raw"]

# Validate
errors = validate_schema(df_raw)
if errors:
    st.error("**Data Validation Failed:**\n" + "\n".join(f"- {e}" for e in errors))
    if st.button("Start Over"):
        st.session_state["df_raw"] = None
        st.session_state["uploader_key"] += 1
        st.session_state["filter_key"] += 1
        st.session_state["ai_commentary"] = {}
        st.rerun()
    st.stop()

# ── Dynamically populate filters from loaded data ──
region_options = sorted(df_raw["region"].unique().tolist())
product_options = sorted(df_raw["product_line"].unique().tolist())

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("#### 📊 Smart KPI Dashboard")
    st.markdown("---")

    # ── Data Source ──
    st.markdown('<p class="sidebar-section-label">Data Source</p>', unsafe_allow_html=True)
    new_upload = st.file_uploader("Upload new CSV", type=["csv"], label_visibility="collapsed", key=f"sidebar_uploader_{st.session_state['uploader_key']}")
    
    if new_upload and getattr(st.session_state, "last_uploaded_file_id", None) != new_upload.file_id:
        st.session_state["df_raw"] = load_csv(new_upload)
        st.session_state["last_uploaded_file_id"] = new_upload.file_id
        st.session_state["filter_key"] += 1
        st.session_state["ai_commentary"] = {}
        st.session_state["pdf_bytes"] = None
        st.rerun()
        
    if st.button("Start Over", type="tertiary", width="stretch"):
        st.session_state["df_raw"] = None
        st.session_state["last_uploaded_file_id"] = None
        st.session_state["uploader_key"] += 1
        st.session_state["filter_key"] += 1
        st.session_state["ai_commentary"] = {}
        st.rerun()

    st.markdown("---")

    # ── Filters ──
    st.markdown('<p class="sidebar-section-label">Filters</p>', unsafe_allow_html=True)
    selected_regions = st.multiselect("Region", region_options, default=region_options, key=f"filter_region_{st.session_state['filter_key']}")
    selected_products = st.multiselect("Product Line", product_options, default=product_options, key=f"filter_product_{st.session_state['filter_key']}")

    st.markdown("---")

    # ── AI & Export ──
    st.markdown('<p class="sidebar-section-label">AI Insights</p>', unsafe_allow_html=True)
    regen = st.button("🔄 Refresh Insights", width="stretch")
    if regen:
        clear_cache()
        st.session_state["ai_commentary"] = {}
        st.session_state["pdf_bytes"] = None
        st.toast("Cache cleared — insights will regenerate.", icon="✅")
        st.rerun()

    st.markdown("---")

    # ── PDF Export (in sidebar) ──
    st.markdown('<p class="sidebar-section-label">Export</p>', unsafe_allow_html=True)
    pdf_gen_btn = st.button("📄 Generate PDF Report", width="stretch")

    if st.session_state.get("pdf_bytes"):
        st.download_button(
            label="⬇️ Download PDF",
            data=st.session_state["pdf_bytes"],
            file_name="KPI_Report.pdf",
            mime="application/pdf",
            width="stretch"
        )

    st.markdown("---")
    st.caption("Built with Streamlit · Pandas · Plotly · Gemini")

# Apply filters
df = apply_filters(df_raw, selected_regions, selected_products)
if df.empty:
    st.warning("No data matches the current filters. Adjust your selections in the sidebar.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# COMPUTE METRICS
# ══════════════════════════════════════════════════════════════════════════════
monthly    = aggregate_monthly(df)
monthly    = detect_anomalies(monthly)
mom        = compute_mom(monthly)
anomalies  = get_anomaly_summary(monthly)
forecast   = forecast_revenue(monthly)
ai_metrics = build_ai_metrics(df, monthly, mom, anomalies, forecast)
latest_month = monthly["month"].max().strftime("%B %Y")


# ── Handle PDF generation (after metrics are computed) ────────────────────────
if pdf_gen_btn:
    with st.spinner("Building PDF report..."):
        pdf_bytes = generate_pdf(mom, st.session_state.get("ai_commentary", {}), latest_month)
        st.session_state["pdf_bytes"] = pdf_bytes
    st.toast("PDF report ready! Download from the sidebar.", icon="📄")
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
h_left, h_right = st.columns([3, 1])
with h_left:
    st.markdown(f"""
    <div class="header-banner">
      <p class="header-title">Smart KPI Dashboard</p>
      <p class="header-subtitle">AI-powered business intelligence · Reporting period: <strong style="color:#e6edf3">{latest_month}</strong></p>
    </div>
    """, unsafe_allow_html=True)
with h_right:
    st.markdown(f"""
    <div class="header-banner" style="text-align:right;">
      <p class="header-meta">Regions: {', '.join(selected_regions)}</p>
      <p class="header-meta" style="margin-top:4px">Products: {', '.join(selected_products)}</p>
      <p class="header-meta" style="margin-top:4px">Data points: {len(monthly)} months</p>
    </div>
    """, unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
if mom:
    rev = mom["revenue"]
    cvr = mom["conversion_rate"]
    churn = mom["churn_rate"]
    cust = mom["new_customers"]
    ret = mom.get("customer_retention", {})
    tix = mom.get("support_tickets", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue", f"${rev['current']:,.0f}", f"{rev['mom_pct']:+.1f}% MoM")
    c2.metric("Conversion", f"{cvr['current']:.1f}%", f"{cvr['mom_pct']:+.1f}% MoM")
    c3.metric("Churn Rate", f"{churn['current']:.1f}%",
              f"{churn['mom_pct']:+.1f}% MoM", delta_color="inverse")
    c4.metric("New Customers", f"{int(cust['current']):,}", f"{cust['mom_pct']:+.1f}% MoM")
    if ret:
        c5.metric("Retention", f"{ret['current']:.1f}%", f"{ret['mom_pct']:+.1f}% MoM")

    # Second row — forecast + support
    c6, c7, c8, c9, c10 = st.columns(5)
    if tix:
        c6.metric("Support Tickets", f"{int(tix['current']):,}",
                   f"{tix['mom_pct']:+.1f}% MoM", delta_color="inverse")
    if forecast.get("forecast_values"):
        c7.metric("Q+1 Forecast",
                   f"${forecast['forecast_values'][0]:,.0f}",
                   f"{forecast['forecast_pct']:+.1f}% projected")
    c8.metric("Data Span", f"{len(monthly)} months", "in dataset")


# ══════════════════════════════════════════════════════════════════════════════
# TABBED CONTENT
# ══════════════════════════════════════════════════════════════════════════════
tab_trends, tab_breakdown = st.tabs(["📈 Trends", "🗺️ Breakdown"])


# ── Tab 1: Trends ─────────────────────────────────────────────────────────────
with tab_trends:
    col_l, col_r = st.columns(2)

    with col_l:
        # Revenue area chart + forecast overlay
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["revenue"],
            fill="tozeroy", name="Revenue",
            line=dict(color="#4f8ef7", width=2.5),
            fillcolor="rgba(79,142,247,0.08)",
            hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: $%{y:,.0f}<extra></extra>"
        ))
        # Anomaly markers
        anom_rows = monthly[monthly["is_anomaly"]].copy() if "is_anomaly" in monthly.columns else pd.DataFrame()
        if not anom_rows.empty:
            import textwrap
            hover_texts = []
            for _, row in anom_rows.iterrows():
                m_str = row["month"].strftime("%B %Y")
                exps = [d["explanation"] for d in anomalies.get("details", []) if d["month"] == m_str]
                if exps:
                    wrapped_exps = ["<br>".join(textwrap.wrap(exp, width=50)) for exp in exps]
                    hover_texts.append("<br><br>".join(wrapped_exps))
                else:
                    hover_texts.append("Anomaly Detected")
            anom_rows["hover_text"] = hover_texts

            fig_rev.add_trace(go.Scatter(
                x=anom_rows["month"], y=anom_rows["revenue"],
                mode="markers", name="Anomaly",
                marker=dict(color="#ef4444", size=10, symbol="x"),
                customdata=anom_rows["hover_text"],
                hovertemplate="<b>⚠️ Anomaly</b><br>%{x|%b %Y}<br>$%{y:,.0f}<br><br><i>%{customdata}</i><extra></extra>"
            ))
        # Forecast
        if forecast.get("forecast_values"):
            last = monthly["month"].max()
            fcast_months = pd.date_range(
                start=last, periods=len(forecast["forecast_values"]) + 1, freq="MS"
            )[1:]
            fig_rev.add_trace(go.Scatter(
                x=fcast_months, y=forecast["forecast_values"],
                name="Forecast", line=dict(color="#8b5cf6", width=2, dash="dash"),
                hovertemplate="<b>Forecast</b><br>%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>"
            ))
        fig_rev.update_layout(title="Revenue Trend & Forecast",
                              height=380, **CHART_LAYOUT)
        st.plotly_chart(fig_rev, key="rev_chart")

    with col_r:
        # Churn vs Retention dual line
        fig_churn = go.Figure()
        fig_churn.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["churn_rate"],
            name="Churn Rate", line=dict(color="#ef4444", width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>Churn: %{y:.1f}%<extra></extra>"
        ))
        fig_churn.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["customer_retention"],
            name="Retention Rate", line=dict(color="#10b981", width=2.5),
            yaxis="y2",
            hovertemplate="<b>%{x|%b %Y}</b><br>Retention: %{y:.1f}%<extra></extra>"
        ))
        fig_churn.update_layout(
            title="Churn vs. Retention",
            height=380,
            yaxis2=dict(overlaying="y", side="right",
                        gridcolor="#161b22", tickfont=dict(color="#10b981")),
            **CHART_LAYOUT
        )
        st.plotly_chart(fig_churn, key="churn_chart")


# ── Tab 2: Breakdown ──────────────────────────────────────────────────────────
with tab_breakdown:
    col_l2, col_r2 = st.columns(2)

    with col_l2:
        regional = get_regional_breakdown(df)
        fig_cvr = px.bar(
            regional, x="region", y="conversion_rate",
            color="region", color_discrete_sequence=COLORS,
            labels={"conversion_rate": "Conversion Rate (%)", "region": "Region"},
            title="Conversion Rate by Region"
        )
        fig_cvr.update_layout(height=380, showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig_cvr, key="cvr_chart")

    with col_r2:
        product = get_product_breakdown(df)
        fig_cust = px.bar(
            product, x="product_line", y="new_customers",
            color="product_line", color_discrete_sequence=COLORS,
            labels={"new_customers": "New Customers", "product_line": "Product Line"},
            title="New Customers by Product Line"
        )
        fig_cust.update_layout(height=380, showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig_cust, key="cust_chart")

    # Regional revenue trend
    with st.expander("📊 Regional Revenue Over Time", expanded=False):
        region_monthly = df.groupby(["month", "region"])["revenue"].sum().reset_index()
        fig_heat = px.line(
            region_monthly, x="month", y="revenue", color="region",
            color_discrete_sequence=COLORS,
            labels={"revenue": "Revenue ($)", "month": "Month"},
            title="Revenue Trend by Region"
        )
        fig_heat.update_layout(height=350, **CHART_LAYOUT)
        st.plotly_chart(fig_heat, key="region_chart")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 🤖 AI Business Insights")

if not st.session_state["ai_commentary"]:
    prompts = {
        "revenue":          build_revenue_prompt(ai_metrics),
        "conversion_rate":  build_conversion_prompt(ai_metrics),
        "churn_rate":       build_churn_prompt(ai_metrics),
        "new_customers":    build_customers_prompt(ai_metrics),
    }
    with st.spinner("Gemini is analyzing your KPI data..."):
        commentary = generate_all_commentary(prompts)
        exec_prompt = build_executive_summary_prompt(ai_metrics, commentary)
        commentary["executive_summary"] = generate_all_commentary(
            {"executive_summary": exec_prompt}
        )["executive_summary"]
        
        # Convert bullet points to HTML unordered lists and parse markdown bold
        import re
        for key, text in commentary.items():
            text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
            if "•" in text:
                items = [item.strip() for item in text.split("•") if item.strip()]
                text = "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"
            commentary[key] = text
                
        st.session_state["ai_commentary"] = commentary

commentary = st.session_state["ai_commentary"]

# Executive Overview
if "executive_summary" in commentary:
    st.markdown(f"""
    <div class="ai-label-exec">🏆 Executive Overview — {latest_month}</div>
    <div class="ai-box-exec">{commentary['executive_summary']}</div>
    """, unsafe_allow_html=True)

# Per-KPI commentary
kpi_items = [
    ("revenue",         "💰 Revenue Trends"),
    ("conversion_rate", "🎯 Conversion Efficiency"),
    ("churn_rate",      "📉 Churn & Retention"),
    ("new_customers",   "👥 Customer Acquisition"),
]
col_a, col_b = st.columns(2)
for i, (key, label) in enumerate(kpi_items):
    target_col = col_a if i % 2 == 0 else col_b
    with target_col:
        text = commentary.get(key, "")
        if text:
            st.markdown(f"""
            <div class="ai-label">📌 {label}</div>
            <div class="ai-box">{text}</div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.caption("Smart KPI Dashboard · Powered by Google Gemini · Built with Streamlit + Pandas + Plotly + scikit-learn")
