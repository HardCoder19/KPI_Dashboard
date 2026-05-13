"""
pdf_exporter.py
Generates a downloadable PDF KPI report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ── Color Palette (light, printable theme) ───────────────────────────────────
PRIMARY    = colors.HexColor("#4f8ef7")
PRIMARY_DK = colors.HexColor("#3b6fd4")
ACCENT     = colors.HexColor("#8b5cf6")
SUCCESS    = colors.HexColor("#059669")
DANGER     = colors.HexColor("#dc2626")
TEXT_DARK  = colors.HexColor("#1f2937")
TEXT_MID   = colors.HexColor("#4b5563")
TEXT_LIGHT = colors.HexColor("#6b7280")
BG_LIGHT   = colors.HexColor("#f9fafb")
BG_ROW_ALT = colors.HexColor("#f3f4f6")
BORDER     = colors.HexColor("#e5e7eb")
WHITE      = colors.white


def _styles():
    return {
        "title": ParagraphStyle(
            "title", fontSize=24, textColor=PRIMARY_DK,
            fontName="Helvetica-Bold", spaceAfter=12,
            alignment=TA_CENTER, leading=30
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=12, textColor=TEXT_LIGHT,
            fontName="Helvetica", spaceAfter=14,
            alignment=TA_CENTER, leading=16
        ),
        "section": ParagraphStyle(
            "section", fontSize=13, textColor=PRIMARY_DK,
            fontName="Helvetica-Bold", spaceBefore=18,
            spaceAfter=8
        ),
        "body": ParagraphStyle(
            "body", fontSize=10, textColor=TEXT_MID,
            fontName="Helvetica", leading=15,
            spaceAfter=8, alignment=TA_JUSTIFY
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", fontSize=9, textColor=TEXT_LIGHT,
            fontName="Helvetica-Bold"
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", fontSize=14, textColor=TEXT_DARK,
            fontName="Helvetica-Bold"
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=8, textColor=TEXT_LIGHT,
            fontName="Helvetica", alignment=TA_CENTER,
            spaceBefore=16
        ),
    }


def generate_pdf(mom: dict, commentaries: dict, report_month: str) -> bytes:
    """
    Build and return a PDF report as bytes for st.download_button.

    Args:
        mom: MoM metrics dict from data_loader.compute_mom()
        commentaries: dict of {kpi_name: commentary_text} (can be empty)
        report_month: string like "December 2024"
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Smart KPI Dashboard", styles["title"]))
    story.append(Paragraph(
        f"Executive Performance Report — {report_month}", styles["subtitle"]
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        styles["subtitle"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=PRIMARY, spaceAfter=16
    ))

    # ── KPI Summary Table ─────────────────────────────────────────────────────
    story.append(Paragraph("KPI Summary", styles["section"]))

    def fmt_val(key, val):
        if key == "revenue":
            return f"${val:,.0f}"
        elif key in ("conversion_rate", "churn_rate", "customer_retention"):
            return f"{val:.1f}%"
        else:
            return f"{int(val):,}"

    def fmt_mom(pct, inverse=False):
        if inverse:
            color_hex = "#059669" if pct < 0 else "#dc2626"
        else:
            color_hex = "#059669" if pct >= 0 else "#dc2626"
        arrow = "▲" if pct >= 0 else "▼"
        return f'<font color="{color_hex}"><b>{arrow} {abs(pct):.1f}%</b></font>'

    kpi_display = [
        ("Revenue", "revenue", False),
        ("Conversion Rate", "conversion_rate", False),
        ("Churn Rate", "churn_rate", True),
        ("New Customers", "new_customers", False),
        ("Customer Retention", "customer_retention", False),
    ]

    header_style = ParagraphStyle(
        "tbl_header", fontSize=9, textColor=WHITE,
        fontName="Helvetica-Bold"
    )
    table_data = [[
        Paragraph("KPI", header_style),
        Paragraph("Current", header_style),
        Paragraph("Previous", header_style),
        Paragraph("MoM Change", header_style),
    ]]

    for label, key, inverse in kpi_display:
        if key in mom:
            d = mom[key]
            table_data.append([
                Paragraph(label, styles["kpi_label"]),
                Paragraph(fmt_val(key, d["current"]), styles["kpi_value"]),
                Paragraph(fmt_val(key, d["previous"]), styles["body"]),
                Paragraph(fmt_mom(d["mom_pct"], inverse), styles["body"]),
            ])

    kpi_table = Table(table_data, colWidths=[4.5*cm, 4*cm, 4*cm, 4*cm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, BG_ROW_ALT]),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(kpi_table)

    # ── AI Commentary (optional) ──────────────────────────────────────────────
    has_commentary = commentaries and any(
        v and not v.startswith("⚠️") for v in commentaries.values()
    )

    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER, spaceAfter=8
    ))

    if has_commentary:
        story.append(Paragraph("AI-Generated Insights", styles["section"]))

        kpi_order = [
            ("executive_summary", "Executive Overview"),
            ("revenue", "Revenue Analysis"),
            ("conversion_rate", "Conversion Rate Analysis"),
            ("churn_rate", "Churn & Retention Analysis"),
            ("new_customers", "New Customer Acquisition"),
        ]

        for key, label in kpi_order:
            if key in commentaries and commentaries[key]:
                text = commentaries[key]
                if text.startswith("⚠️"):
                    continue
                story.append(Paragraph(f"● {label}", styles["kpi_label"]))
                story.append(Paragraph(text, styles["body"]))
                story.append(Spacer(1, 0.15*cm))
    else:
        story.append(Paragraph(
            "AI commentary was not generated for this report. "
            "Generate AI Insights in the dashboard to include narrative analysis.",
            styles["body"]
        ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER, spaceBefore=16
    ))
    story.append(Paragraph(
        "This report was automatically generated by the Smart KPI Dashboard. "
        "AI commentary powered by Google Gemini. Data analysis via Pandas & scikit-learn.",
        styles["footer"]
    ))

    doc.build(story)
    return buffer.getvalue()
