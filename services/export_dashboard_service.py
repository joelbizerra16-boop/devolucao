"""Exportação da listagem operacional (Excel / PDF) com filtros aplicados."""

from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from typing import Any

import pandas as pd

from core.utils import sidebar_logo_path
from services.dashboard_service import preparar_listview_dashboard


def nome_arquivo_exportacao(extensao: str, mes_label: str, ano: int) -> str:
    mes_slug = (
        mes_label.strip()
        .lower()
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("é", "e")
        .replace(" ", "_")
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return f"listagem_devolucoes_{mes_slug}_{ano}_{ts}.{extensao}"


def export_listagem_excel_bytes(rows: list) -> bytes:
    df = preparar_listview_dashboard(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Listagem")
        ws = writer.sheets["Listagem"]
        for col in ws.columns:
            max_len = 0
            letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[letter].width = min(max_len + 2, 48)
    buffer.seek(0)
    return buffer.getvalue()


def export_listagem_pdf_bytes(
    rows: list,
    *,
    mes: str,
    ano: int,
    busca: str = "",
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    df = preparar_listview_dashboard(rows)
    total = len(df)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    busca_txt = escape((busca or "").strip() or "—")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ExportTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1f6feb"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "ExportMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=4,
    )

    story: list[Any] = []
    logo = sidebar_logo_path()
    if logo and logo.exists() and logo.stat().st_size < 400_000:
        try:
            img = Image(str(logo), width=2.4 * cm, height=0.85 * cm, kind="proportional")
            img.hAlign = "LEFT"
            story.append(img)
            story.append(Spacer(1, 0.2 * cm))
        except Exception:
            pass

    story.append(Paragraph("Listagem operacional — Devoluções", title_style))
    story.append(
        Paragraph(
            f"Período: <b>{mes}/{ano}</b> &nbsp;|&nbsp; Busca: <b>{busca_txt}</b> "
            f"&nbsp;|&nbsp; Exportado em: <b>{agora}</b> &nbsp;|&nbsp; Total: <b>{total}</b>",
            meta_style,
        )
    )
    story.append(Spacer(1, 0.35 * cm))

    if df.empty:
        story.append(Paragraph("Nenhum registro para os filtros selecionados.", styles["Normal"]))
    else:
        headers = [list(df.columns)]
        data = [[str(v) for v in row] for row in df.values.tolist()]
        table = Table(headers + data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
