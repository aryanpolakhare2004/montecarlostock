"""Renders a stored run record (mcstock/web/db.py) as a downloadable PDF report."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_run_pdf(record: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=f"mcstock {record['run_type']} report")
    styles = getSampleStyleSheet()

    story = [
        Paragraph(f"{record['run_type'].replace('_', ' ').title()} report &mdash; {record['ticker']}", styles["Title"]),
        Paragraph(f"Run #{record['id']} &middot; {record['created_at']}", styles["Normal"]),
        Spacer(1, 0.2 * inch),
    ]

    if record.get("params"):
        story.append(Paragraph("Parameters", styles["Heading2"]))
        story.append(_dict_table(record["params"]))
        story.append(Spacer(1, 0.15 * inch))

    if record.get("summary"):
        story.append(Paragraph("Summary", styles["Heading2"]))
        story.append(_dict_table(record["summary"]))
        story.append(Spacer(1, 0.2 * inch))

    if record.get("chart_png"):
        story.append(Image(BytesIO(record["chart_png"]), width=6.5 * inch, height=3.9 * inch))

    doc.build(story)
    return buf.getvalue()


def _dict_table(data: dict) -> Table:
    rows = [["Field", "Value"]] + [[str(k), _fmt(v)] for k, v in data.items()]
    table = Table(rows, colWidths=[220, 260])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#171a21")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dde1e7")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f8")]),
    ]))
    return table


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
