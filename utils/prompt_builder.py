"""
prompt_builder.py
Constructs rich, structured prompts for Gemini AI commentary per KPI.
Outputs are formatted as concise bullet points in clear business language.
"""


def build_revenue_prompt(m: dict) -> str:
    anomaly_text = (
        f"Yes — {m['anomalies']['anomaly_note']} (Severity: {m['anomalies']['severity']})"
        if m["anomalies"].get("has_anomaly") else "No anomalies detected"
    )
    forecast = m.get("forecast", {})
    forecast_text = (
        f"${forecast.get('end_forecast', 0):,.0f} in {forecast.get('forecast_months', ['Q+3'])[-1]} "
        f"({forecast.get('forecast_pct', 0):+.1f}% vs current)"
        if forecast.get("forecast_values") else "Forecast unavailable"
    )
    return f"""You are a senior business analyst providing a KPI briefing for a non-technical executive audience.

DATA CONTEXT — Revenue:
- Reporting Period: {m['month']}
- Total Revenue: ${m['revenue']:,.0f}
- Month-over-Month Change: {m['revenue_mom_pct']:+.1f}%
- Previous Month Revenue: ${m['revenue_prev']:,.0f}
- Best Performing Region: {m['top_region']} (${m['top_region_rev']:,.0f})
- Worst Performing Region: {m['bottom_region']} (${m['bottom_region_rev']:,.0f})
- 3-Month Trend: {m.get('revenue_trend', 'stable')}
- Anomaly Detected: {anomaly_text}
- Next Quarter Forecast: {forecast_text}

INSTRUCTIONS:
Write exactly 4-5 bullet points. Each bullet must:
- Start with a clear, bold key finding (e.g., "Revenue grew 5% to $1.67M")
- Follow with a one-sentence business explanation of WHY it matters or WHAT's driving it
- Use plain, jargon-free business language a CEO would immediately understand
- Highlight trends ("third consecutive month of growth", "reversing last quarter's decline")
- If an anomaly exists, one bullet must explain what happened and what it means for the business

Format each bullet as: • <bold finding>. <explanation>.
Do NOT use markdown. Do NOT use headers. Do NOT use numbered lists. Just bullet points with the • character."""


def build_conversion_prompt(m: dict) -> str:
    anomaly_text = (
        f"Yes — {m['anomalies']['anomaly_note']}"
        if m["anomalies"].get("has_anomaly") else "No anomalies detected"
    )
    return f"""You are a senior business analyst providing a KPI briefing for a non-technical executive audience.

DATA CONTEXT — Conversion Rate:
- Reporting Period: {m['month']}
- Conversion Rate: {m['conversion_rate']:.1f}%
- Month-over-Month Change: {m['conversion_rate_mom_pct']:+.1f}%
- Previous Month Rate: {m['conversion_rate_prev']:.1f}%
- Best Region: {m['top_region']}
- 3-Month Trend: {m.get('conversion_rate_trend', 'stable')}
- Anomaly Detected: {anomaly_text}

INSTRUCTIONS:
Write exactly 3-4 bullet points. Each bullet must:
- Start with a clear, bold key finding about the conversion rate
- Explain in plain language what this means for the sales pipeline and bottom line
- Highlight the trend direction ("improving steadily", "plateauing", "declining for the second month")
- Include one actionable recommendation the business can act on

Format each bullet as: • <bold finding>. <explanation>.
Do NOT use markdown. Do NOT use headers. Do NOT use numbered lists. Just bullet points with the • character."""


def build_churn_prompt(m: dict) -> str:
    anomaly_text = (
        f"Yes — {m['anomalies']['anomaly_note']}"
        if m["anomalies"].get("has_anomaly") else "No anomalies detected"
    )
    churn_direction = "increased" if m['churn_rate_mom_pct'] > 0 else "decreased"
    retention = m.get('customer_retention', 100 - m['churn_rate'])
    return f"""You are a senior business analyst providing a KPI briefing for a non-technical executive audience.

DATA CONTEXT — Churn & Retention:
- Reporting Period: {m['month']}
- Churn Rate: {m['churn_rate']:.1f}% ({churn_direction} by {abs(m['churn_rate_mom_pct']):.1f}% MoM)
- Customer Retention Rate: {retention:.1f}%
- Previous Month Churn: {m['churn_rate_prev']:.1f}%
- 3-Month Trend: {m.get('churn_rate_trend', 'stable')}
- Anomaly Detected: {anomaly_text}

INSTRUCTIONS:
Write exactly 3-4 bullet points. Each bullet must:
- Start with a clear, bold key finding about churn or retention
- Translate the numbers into business impact (e.g., "losing X% of customers means $Y at risk")
- Explain the trend in human terms ("customers are staying longer", "we're bleeding accounts faster")
- Include one concrete retention action the business should consider

Format each bullet as: • <bold finding>. <explanation>.
Do NOT use markdown. Do NOT use headers. Do NOT use numbered lists. Just bullet points with the • character."""


def build_customers_prompt(m: dict) -> str:
    anomaly_text = (
        f"Yes — {m['anomalies']['anomaly_note']}"
        if m["anomalies"].get("has_anomaly") else "No anomalies detected"
    )
    return f"""You are a senior business analyst providing a KPI briefing for a non-technical executive audience.

DATA CONTEXT — New Customer Acquisition:
- Reporting Period: {m['month']}
- New Customers Acquired: {int(m['new_customers']):,}
- Month-over-Month Change: {m['new_customers_mom_pct']:+.1f}%
- Previous Month New Customers: {int(m['new_customers_prev']):,}
- Best Region for Acquisition: {m['top_region']}
- 3-Month Trend: {m.get('new_customers_trend', 'stable')}
- Anomaly Detected: {anomaly_text}

INSTRUCTIONS:
Write exactly 3-4 bullet points. Each bullet must:
- Start with a clear, bold key finding about customer acquisition
- Connect the numbers to business growth (e.g., "pipeline is expanding", "growth engine is stalling")
- Highlight regional winners and what's working there
- Link acquisition trends to revenue outlook

Format each bullet as: • <bold finding>. <explanation>.
Do NOT use markdown. Do NOT use headers. Do NOT use numbered lists. Just bullet points with the • character."""


def build_executive_summary_prompt(m: dict, commentaries: dict) -> str:
    return f"""You are a Chief Analytics Officer writing a board-level executive summary.

PERIOD: {m['month']}

KEY METRICS AT A GLANCE:
- Revenue: ${m['revenue']:,.0f} ({m['revenue_mom_pct']:+.1f}% MoM) — Trend: {m.get('revenue_trend', 'stable')}
- Conversion Rate: {m['conversion_rate']:.1f}% ({m['conversion_rate_mom_pct']:+.1f}% MoM)
- Churn Rate: {m['churn_rate']:.1f}% ({m['churn_rate_mom_pct']:+.1f}% MoM)
- New Customers: {int(m['new_customers']):,} ({m['new_customers_mom_pct']:+.1f}% MoM)
- Anomalies: {"Yes — " + m['anomalies']['anomaly_note'] if m['anomalies'].get('has_anomaly') else "None"}
- Best Region: {m['top_region']} | Needs Attention: {m['bottom_region']}

INSTRUCTIONS:
Write exactly 5-6 bullet points that tell the story of the business this period:
- First bullet: Overall verdict — is the business healthy, growing, or under pressure?
- Next 2 bullets: The biggest wins this period and what's driving them
- Next 1-2 bullets: The risks or warning signs leadership must watch
- Final bullet: What to expect next quarter and what action to take now

Use plain, confident business language. Think "board meeting talking points" — every bullet should be something a CEO would highlight in a quarterly earnings call.

Format each bullet as: • <bold finding>. <explanation>.
Do NOT use markdown. Do NOT use headers. Do NOT use numbered lists. Just bullet points with the • character."""
