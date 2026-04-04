"""Geracao de PDF consolidado com ReportLab."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import CORES_RELATORIO


def _hex_color(chave: str) -> colors.HexColor:
    return colors.HexColor(CORES_RELATORIO[chave])


def _moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _hex_color("azul")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _hex_color("cinza")]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]
    )


def gerar_pdf(dados_completos: dict) -> bytes:
    """Gera um PDF completo do relatorio."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TituloAzul",
            parent=styles["Heading1"],
            textColor=_hex_color("azul"),
            fontName="Helvetica-Bold",
        )
    )
    styles.add(ParagraphStyle(name="TextoBase", parent=styles["BodyText"], leading=16, spaceAfter=8))

    story = []
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        story.append(Image(str(logo_path), width=4 * cm, height=4 * cm))

    story.append(Paragraph("Score Marketing Imobiliario", styles["TituloAzul"]))
    story.append(
        Paragraph(
            f"{dados_completos['empreendimento']['nome']}<br/>"
            f"{dados_completos['localizacao']['municipio']} - {dados_completos['localizacao']['uf']}<br/>"
            f"{date.today().strftime('%d/%m/%Y')}",
            styles["TextoBase"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    score = dados_completos["resultado_score"]
    verba = dados_completos["resultado_verba"]
    resumo = [
        ["Indicador", "Valor"],
        ["Score de Dificuldade", f"{score['score_final']}/100 - {score['classificacao']}"],
        ["VGV", _moeda(verba["vgv"])],
        ["Verba Recomendada", _moeda(verba["verba_total_r$"])],
    ]
    tabela_resumo = Table(resumo, colWidths=[6 * cm, 9 * cm])
    tabela_resumo.setStyle(_table_style())
    story.append(Paragraph("Resumo Executivo", styles["Heading2"]))
    story.append(tabela_resumo)
    story.append(Spacer(1, 0.4 * cm))

    breakdown_data = [["Variavel", "Peso", "Valor Norm.", "Contribuicao"]]
    for variavel, dados in score["breakdown"].items():
        breakdown_data.append([variavel, f"{dados['peso']:.0%}", f"{dados['valor_norm']:.2f}", f"{dados['contribuicao']:.4f}"])
    tabela_breakdown = Table(breakdown_data, colWidths=[5 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm])
    tabela_breakdown.setStyle(_table_style())
    story.append(Paragraph("Score Detalhado", styles["Heading2"]))
    story.append(tabela_breakdown)
    story.append(PageBreak())

    cenarios_data = [["Cenario", "Percentual", "Verba", "Custo por Unidade"]]
    for nome, dados in verba["cenarios"].items():
        cenarios_data.append([nome.capitalize(), f"{dados['percentual']:.2%}", _moeda(dados["verba_r$"]), _moeda(dados["custo_unidade"])])
    tabela_cenarios = Table(cenarios_data, colWidths=[4 * cm, 3 * cm, 4 * cm, 4 * cm])
    tabela_cenarios.setStyle(_table_style())
    story.append(Paragraph("Projecao de Verba", styles["Heading2"]))
    story.append(tabela_cenarios)
    story.append(Spacer(1, 0.4 * cm))

    mix = dados_completos["mix_midias"]
    mix_data = [["Canal", "%", "Budget"]]
    for canal, dados in mix["canais"].items():
        mix_data.append([canal, f"{dados['percentual']:.2f}%", _moeda(dados["budget_r$"])])
    tabela_mix = Table(mix_data, colWidths=[8 * cm, 2 * cm, 4 * cm])
    tabela_mix.setStyle(_table_style())
    story.append(Paragraph("Mix de Midia", styles["Heading2"]))
    story.append(tabela_mix)
    story.append(Spacer(1, 0.4 * cm))

    publico = dados_completos["perfil_publico"]
    story.append(Paragraph("Perfil de Publico", styles["Heading2"]))
    for chave, valor in publico.items():
        texto = ", ".join(valor) if isinstance(valor, list) else str(valor)
        story.append(Paragraph(f"<b>{chave.replace('_', ' ').title()}:</b> {texto}", styles["TextoBase"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Recomendacoes Estrategicas", styles["Heading2"]))
    story.append(Paragraph(dados_completos["recomendacoes_estrategicas"], styles["TextoBase"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            "Gerado por Score Marketing Imobiliario",
            ParagraphStyle(name="Rodape", parent=styles["BodyText"], textColor=_hex_color("dourado"), alignment=1),
        )
    )

    doc.build(story)
    return buffer.getvalue()
