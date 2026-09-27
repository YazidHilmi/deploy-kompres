"""Pembuatan laporan PDF dari hasil prediksi yang tersimpan."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_prediction_pdf(record: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="Laporan Prediksi Produksi Padi",
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Laporan Prediksi Produksi Padi", styles["Title"]), Spacer(1, 0.4 * cm),
        Paragraph("Estimasi produksi bulanan berdasarkan indeks vegetasi satelit dan model TabPFN.", styles["BodyText"]),
        Spacer(1, 0.5 * cm),
    ]
    created_at = record.get("created_at")
    summary = [
        ["ID hasil", record["id"]], ["Kabupaten", record["kabupaten"]],
        ["Bulan target", str(record["target_period"])[:7]],
        ["Estimasi produksi", f'{record["estimated_production_ton"]:,.2f} ton'],
        ["Model", record["model_version"]], ["Sumber indeks", record["index_source"]],
        ["Status data", record["quality_status"]],
        ["Waktu pemrosesan", f'{record.get("processing_seconds") or 0:.2f} detik'],
        ["Dibuat", str(created_at) if created_at else "-"],
    ]
    story.append(_styled_table(summary, [4.5 * cm, 11.5 * cm]))
    story.extend([Spacer(1, 0.7 * cm), Paragraph("Fitur model", styles["Heading2"])])
    feature_rows = [["Fitur", "Nilai"]]
    feature_rows.extend([key, f"{float(value):.6f}"] for key, value in record["input_features"].items())
    story.append(_styled_table(feature_rows, [9 * cm, 7 * cm], header=True))
    story.extend([
        Spacer(1, 0.6 * cm),
        Paragraph("Catatan: hasil ini merupakan estimasi model berdasarkan data indeks yang tersedia pada bulan target.", styles["Italic"]),
    ])
    document.build(story)
    return buffer.getvalue()


def _styled_table(rows, widths, header=False):
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C4B8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2E8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E6B3E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(commands))
    return table
