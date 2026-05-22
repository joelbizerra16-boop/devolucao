"""Exportação da listagem operacional (Excel / PDF executivo)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape
from io import BytesIO
from typing import Any

import pandas as pd

from core.utils import sidebar_logo_path
from services.dashboard_service import preparar_listview_dashboard
from services.devolucao_service import (
    _formatar_data,
    _formatar_valor_br,
    _nome_responsavel_exibicao,
    _texto_celula,
)

# Paleta alinhada ao sistema (PDF em fundo claro premium)
C_PRIMARY = "#1f6feb"
C_PRIMARY_DARK = "#1558c9"
C_TEXT = "#0f172a"
C_TEXT_MUTED = "#64748b"
C_BORDER = "#e2e8f0"
C_ROW_ALT = "#f8fafc"
C_SUCCESS = "#16a34a"
C_SUCCESS_BG = "#ecfdf5"
C_CARD_BG = "#ffffff"
C_ACCENT_LINE = "#2F80ED"

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


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


def _kpis_filtrados(rows: list) -> dict[str, str]:
    total = len(rows)
    impacto = 0.0
    motivos: Counter[str] = Counter()
    clientes: set[str] = set()

    for r in rows:
        try:
            if r.valor_nf is not None:
                impacto += float(r.valor_nf)
        except (TypeError, ValueError):
            pass
        m = _texto_celula(getattr(r, "motivo_devolucao", None))
        if m != "—":
            motivos[m] += 1
        cod = _texto_celula(getattr(r, "cod_cliente", None))
        if cod not in ("—", "N/C", "N/C."):
            clientes.add(cod)

    principal = motivos.most_common(1)[0][0] if motivos else "N/A"

    return {
        "total_devolucoes": str(total),
        "impacto_financeiro": _formatar_valor_br(impacto),
        "principal_motivo": principal,
        "qtd_clientes": str(len(clientes)),
    }


def _linhas_tabela_pdf(rows: list) -> list[list[str]]:
    linhas = []
    for r in rows:
        linhas.append(
            [
                _formatar_data(r.data_devolucao),
                _nome_responsavel_exibicao(r),
                _texto_celula(r.motivo_devolucao),
                _texto_celula(r.nf_nfd),
                _formatar_valor_br(r.valor_nf),
                _texto_celula(r.cod_cliente),
                _texto_celula(r.vendedor),
            ]
        )
    return linhas


def export_listagem_pdf_bytes(
    rows: list,
    *,
    mes: str,
    ano: int,
    busca: str = "",
    usuario_exportador: str = "Sistema",
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        Image,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    agora = datetime.now()
    agora_txt = agora.strftime("%d/%m/%Y %H:%M")
    busca_txt = (busca or "").strip() or "—"
    kpis = _kpis_filtrados(rows)
    linhas = _linhas_tabela_pdf(rows)
    usuario_txt = escape((usuario_exportador or "Sistema").strip())

    page_size = landscape(A4)
    page_w, page_h = page_size
    margin_l = 1.35 * cm
    margin_r = 1.35 * cm
    margin_t = 1.15 * cm
    margin_b = 1.45 * cm

    meta = {
        "mes": escape(mes),
        "ano": ano,
        "busca": escape(busca_txt),
        "agora": agora_txt,
        "usuario": usuario_txt,
        "kpis": kpis,
    }

    buffer = BytesIO()

    def _on_page(canv: canvas.Canvas, doc: BaseDocTemplate) -> None:
        canv.saveState()
        # Faixa superior corporativa
        canv.setFillColor(colors.HexColor(C_PRIMARY))
        canv.rect(0, page_h - 0.42 * cm, page_w, 0.42 * cm, fill=1, stroke=0)
        # Rodapé executivo
        canv.setStrokeColor(colors.HexColor(C_BORDER))
        canv.setLineWidth(0.5)
        canv.line(margin_l, margin_b - 0.35 * cm, page_w - margin_r, margin_b - 0.35 * cm)
        canv.setFont(FONT_REGULAR, 7)
        canv.setFillColor(colors.HexColor(C_TEXT_MUTED))
        esq = (
            f"Devolução WMS · Relatório operacional · Exportado em {meta['agora']}"
        )
        dir_txt = f"Página {canv.getPageNumber()}"
        canv.drawString(margin_l, 0.55 * cm, esq)
        canv.drawRightString(page_w - margin_r, 0.55 * cm, dir_txt)
        canv.restoreState()

    doc = BaseDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin_l,
        rightMargin=margin_r,
        topMargin=margin_t + 0.25 * cm,
        bottomMargin=margin_b,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="content",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_on_page)])

    styles = {
        "title": ParagraphStyle(
            "ExecTitle",
            fontName=FONT_BOLD,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor(C_TEXT),
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "ExecSubtitle",
            fontName=FONT_REGULAR,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(C_TEXT_MUTED),
        ),
        "kpi_label": ParagraphStyle(
            "KpiLabel",
            fontName=FONT_REGULAR,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor(C_TEXT_MUTED),
            alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "KpiValue",
            fontName=FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor(C_PRIMARY_DARK),
            alignment=TA_LEFT,
        ),
        "kpi_value_green": ParagraphStyle(
            "KpiValueGreen",
            fontName=FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor(C_SUCCESS),
            alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "Cell",
            fontName=FONT_REGULAR,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor(C_TEXT),
            alignment=TA_LEFT,
        ),
        "cell_right": ParagraphStyle(
            "CellRight",
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor(C_SUCCESS),
            alignment=TA_RIGHT,
        ),
        "cell_center": ParagraphStyle(
            "CellCenter",
            fontName=FONT_REGULAR,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor(C_TEXT),
            alignment=TA_CENTER,
        ),
        "th": ParagraphStyle(
            "TH",
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
    }

    story: list[Any] = []

    # --- Cabeçalho executivo (logo + título + metadados) ---
    logo = sidebar_logo_path()
    logo_flow: Any = ""
    if logo and logo.exists() and logo.stat().st_size < 400_000:
        try:
            logo_flow = Image(str(logo), width=2.8 * cm, height=1.0 * cm, kind="proportional")
        except Exception:
            logo_flow = ""

    titulo_block = [
        Paragraph("Relatório Operacional de Devoluções", styles["title"]),
        Paragraph(
            f"Período: <font color='{C_PRIMARY}'><b>{meta['mes']} / {meta['ano']}</b></font>"
            f" &nbsp;·&nbsp; Busca: <b>{meta['busca']}</b>",
            styles["subtitle"],
        ),
        Paragraph(
            f"Exportado em <b>{meta['agora']}</b> &nbsp;·&nbsp; "
            f"Responsável: <b>{meta['usuario']}</b> &nbsp;·&nbsp; "
            f"Registros: <b>{kpis['total_devolucoes']}</b>",
            styles["subtitle"],
        ),
    ]

    if logo_flow:
        header_tbl = Table(
            [[logo_flow, titulo_block]],
            colWidths=[3.2 * cm, doc.width - 3.2 * cm],
        )
        header_tbl.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(header_tbl)
    else:
        for p in titulo_block:
            story.append(p)

    story.append(Spacer(1, 0.45 * cm))

    # --- KPI cards ---
    kpi_data = [
        [
            Paragraph("Total de devoluções", styles["kpi_label"]),
            Paragraph("Impacto financeiro", styles["kpi_label"]),
            Paragraph("Principal motivo", styles["kpi_label"]),
            Paragraph("Clientes distintos", styles["kpi_label"]),
        ],
        [
            Paragraph(kpis["total_devolucoes"], styles["kpi_value"]),
            Paragraph(kpis["impacto_financeiro"], styles["kpi_value_green"]),
            Paragraph(escape(kpis["principal_motivo"][:42]), styles["kpi_value"]),
            Paragraph(kpis["qtd_clientes"], styles["kpi_value"]),
        ],
    ]
    kpi_w = doc.width / 4
    kpi_table = Table(kpi_data, colWidths=[kpi_w] * 4, rowHeights=[0.55 * cm, 0.85 * cm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(C_CARD_BG)),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(C_BORDER)),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor(C_BORDER)),
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor(C_PRIMARY)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 0.5 * cm))

    # --- Tabela de dados ---
    if not linhas:
        story.append(
            Paragraph(
                "<i>Nenhum registro encontrado para os filtros selecionados.</i>",
                styles["subtitle"],
            )
        )
    else:
        headers = [
            "DATA",
            "USUÁRIO",
            "MOTIVO",
            "NF/NFD",
            "VALOR",
            "CÓD. CLIENTE",
            "VENDEDOR",
        ]
        col_widths = [
            2.0 * cm,
            2.6 * cm,
            5.8 * cm,
            2.1 * cm,
            2.6 * cm,
            2.4 * cm,
            doc.width - (2.0 + 2.6 + 5.8 + 2.1 + 2.6 + 2.4) * cm,
        ]

        header_row = [Paragraph(f"<b>{h}</b>", styles["th"]) for h in headers]
        body_rows = []
        for row in linhas:
            body_rows.append(
                [
                    Paragraph(escape(row[0]), styles["cell"]),
                    Paragraph(escape(row[1]), styles["cell"]),
                    Paragraph(escape(row[2]), styles["cell"]),
                    Paragraph(escape(row[3]), styles["cell_center"]),
                    Paragraph(escape(row[4]), styles["cell_right"]),
                    Paragraph(escape(row[5]), styles["cell_center"]),
                    Paragraph(escape(row[6]), styles["cell"]),
                ]
            )

        data_table = Table(
            [header_row] + body_rows,
            colWidths=col_widths,
            repeatRows=1,
        )
        data_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(C_PRIMARY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
                    ("TOPPADDING", (0, 0), (-1, 0), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(C_ROW_ALT)]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(C_BORDER)),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 1), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),
                    ("ALIGN", (5, 1), (5, -1), "CENTER"),
                ]
            )
        )
        story.append(data_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
