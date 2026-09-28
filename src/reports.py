"""Pembuatan laporan PDF dari hasil prediksi yang tersimpan."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_prediction_pdf(record: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="Laporan Prediksi Produksi Padi",
    )
    styles = getSampleStyleSheet()
    green, ink, muted, pale = colors.HexColor("#1F6B45"), colors.HexColor("#17211B"), colors.HexColor("#637168"), colors.HexColor("#EAF3ED")
    styles.add(ParagraphStyle(name="Brand", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=green, spaceAfter=8))
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=ink, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="ReportSub", parent=styles["Normal"], fontSize=10, leading=15, textColor=muted, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="BigNumber", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=green, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=ink, spaceBefore=8, spaceAfter=8))

    from src.ui import format_period, format_ton

    period_label = format_period(record["target_period"])
    created_at = record.get("created_at")
    created_label = created_at.strftime("%d-%m-%Y") if hasattr(created_at, "strftime") else "-"
    story = [
        Paragraph("PADI CASTING", styles["Brand"]),
        Paragraph("Laporan Prediksi Produksi Padi", styles["ReportTitle"]),
        Paragraph(f'{record["kabupaten"]} &nbsp;&middot;&nbsp; {period_label}', styles["ReportSub"]),
        Spacer(1, 0.6 * cm),
    ]

    hero = Table([
        [Paragraph("PREDIKSI PRODUKSI", styles["ReportSub"])],
        [Paragraph(format_ton(record["estimated_production_ton"], 2), styles["BigNumber"])],
        [Paragraph(f'Estimasi produksi padi {record["kabupaten"]} untuk {period_label}.', styles["ReportSub"])],
    ], colWidths=[16 * cm])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale), ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BDD5C5")),
        ("TOPPADDING", (0, 0), (-1, 0), 14), ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([hero, Spacer(1, 0.6 * cm), Paragraph("Ringkasan laporan", styles["Section"])])
    summary = [
        ["Kabupaten", record["kabupaten"]], ["Periode", period_label],
        ["Prediksi produksi", format_ton(record["estimated_production_ton"], 2)],
        ["Status data", "Data lengkap dan berhasil diproses"], ["Tanggal laporan", created_label],
    ]
    story.append(_styled_table(summary, [5 * cm, 11 * cm]))

    index_history = record.get("index_history")
    if index_history is not None and len(index_history):
        story.extend([Spacer(1, 0.5 * cm), Paragraph("Data pendukung dari citra satelit", styles["Section"])])
        story.append(Paragraph(
            "Tabel berikut berisi observasi indeks vegetasi Sentinel-2 yang digunakan sebagai data pendukung prediksi.",
            styles["BodyText"],
        ))
        story.append(Spacer(1, 0.2 * cm))
        rows = [["Periode", "NDVI", "EVI", "SAVI"]]
        for _, item in index_history.sort_values("Period").iterrows():
            rows.append([
                format_period(item["Period"]), f'{float(item["NDVI_mean"]):.3f}',
                f'{float(item["EVI_mean"]):.3f}', f'{float(item["SAVI_mean"]):.3f}',
            ])
        story.append(_styled_table(rows, [5.2 * cm, 3.6 * cm, 3.6 * cm, 3.6 * cm], header=True))

    story.extend([
        Spacer(1, 0.6 * cm), Paragraph("Tentang prediksi", styles["Section"]),
        Paragraph(
            "Prediksi dihitung menggunakan data indeks vegetasi dari citra Sentinel-2 dan pola produksi padi historis. "
            "Laporan ini disusun sebagai informasi pendukung pemantauan produksi padi.",
            styles["BodyText"],
        ),
        Spacer(1, 0.8 * cm),
        Paragraph("Padi Casting &nbsp;&middot;&nbsp; Platform Prediksi dan Pemantauan Produksi Padi", styles["ReportSub"]),
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
