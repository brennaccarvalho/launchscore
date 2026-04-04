"""Geracao de PDF executivo do LaunchScore."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import PDF_RODAPE, PESOS_SCORE, TERMOS_USO_RESUMIDOS


AZUL = colors.Color(0.106, 0.165, 0.290)
DOURADO = colors.Color(0.910, 0.627, 0.125)
CREME = colors.Color(0.980, 0.973, 0.961)
BRANCO = colors.white
CINZA = colors.Color(0.420, 0.443, 0.502)


def _moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def _pct(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def _roas(valor: float) -> str:
    return f"{valor:.1f}:1".replace(".", ",")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="LaunchTitulo", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=AZUL))
    styles.add(ParagraphStyle(name="LaunchSubtitulo", fontName="Helvetica", fontSize=10, leading=14, textColor=CINZA))
    styles.add(ParagraphStyle(name="LaunchH2", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=AZUL, spaceAfter=8))
    styles.add(ParagraphStyle(name="LaunchBody", fontName="Helvetica", fontSize=9.5, leading=14, textColor=AZUL))
    styles.add(ParagraphStyle(name="LaunchSmall", fontName="Helvetica", fontSize=8, leading=11, textColor=CINZA))
    styles.add(ParagraphStyle(name="LaunchBadge", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=BRANCO, alignment=1))
    return styles


def _table_style(header_bg=DOURADO, body_bg=BRANCO):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6D3D1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [body_bg, CREME]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]
    )


def _rodape(canvas, doc, nome_empreendimento: str):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(AZUL)
        canvas.rect(doc.leftMargin, A4[1] - 1.5 * cm, doc.width, 0.7 * cm, fill=1, stroke=0)
        canvas.setFillColor(BRANCO)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(doc.leftMargin + 10, A4[1] - 1.1 * cm, "LaunchScore")
        canvas.drawRightString(doc.leftMargin + doc.width - 10, A4[1] - 1.1 * cm, nome_empreendimento)
        canvas.setStrokeColor(DOURADO)
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, A4[1] - 1.55 * cm, doc.leftMargin + doc.width, A4[1] - 1.55 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA)
    canvas.drawString(doc.leftMargin, 0.8 * cm, PDF_RODAPE)
    canvas.drawRightString(doc.leftMargin + doc.width, 0.8 * cm, f"Pagina {doc.page}")
    canvas.drawString(
        doc.leftMargin,
        0.45 * cm,
        "© Brenna Carvalho — LaunchScore. Metodologia proprietaria. Uso restrito conforme Termos de Uso.",
    )
    canvas.restoreState()


def _gauge_drawing(score: float, classificacao: str) -> Drawing:
    drawing = Drawing(450, 130)
    drawing.add(Rect(0, 0, 450, 130, fillColor=CREME, strokeColor=None))
    faixas = [(0, 30, colors.HexColor("#DCFCE7")), (30, 50, colors.HexColor("#FEF3C7")), (50, 70, colors.HexColor("#FFEDD5")), (70, 100, colors.HexColor("#FEE2E2"))]
    x = 35
    largura_total = 360
    for inicio, fim, cor in faixas:
        largura = largura_total * ((fim - inicio) / 100)
        drawing.add(Rect(x, 60, largura, 22, fillColor=cor, strokeColor=None))
        x += largura
    marcador_x = 35 + largura_total * (score / 100)
    drawing.add(Line(marcador_x, 52, marcador_x, 92, strokeColor=AZUL, strokeWidth=3))
    drawing.add(String(35, 100, "Gauge de dificuldade de venda", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
    drawing.add(String(35, 28, f"Score {score:.1f}/100", fontName="Helvetica-Bold", fontSize=18, fillColor=AZUL))
    drawing.add(String(35, 12, classificacao, fontName="Helvetica", fontSize=10, fillColor=CINZA))
    return drawing


def _bar_drawing(cenarios: dict) -> Drawing:
    drawing = Drawing(470, 220)
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 40
    chart.height = 140
    chart.width = 380
    chart.data = [
        [cenarios["conservador"]["verba_r$"], cenarios["base"]["verba_r$"], cenarios["agressivo"]["verba_r$"]],
        [cenarios["conservador"]["leads_estimados"], cenarios["base"]["leads_estimados"], cenarios["agressivo"]["leads_estimados"]],
        [cenarios["conservador"]["vendas_estimadas"], cenarios["base"]["vendas_estimadas"], cenarios["agressivo"]["vendas_estimadas"]],
    ]
    chart.categoryAxis.categoryNames = ["Conservador", "Base", "Agressivo"]
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = AZUL
    chart.bars[1].fillColor = DOURADO
    chart.bars[2].fillColor = colors.HexColor("#16A34A")
    drawing.add(chart)
    drawing.add(String(40, 190, "Verba x Leads x Vendas estimadas", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
    return drawing


def _pie_drawing(mix: dict) -> Drawing:
    drawing = Drawing(460, 220)
    pie = Pie()
    pie.x = 90
    pie.y = 20
    pie.width = 150
    pie.height = 150
    pie.data = [dados["percentual"] for dados in mix["canais"].values()]
    pie.labels = [canal[:18] for canal in mix["canais"].keys()]
    cores = [colors.HexColor(dados["cor"]) for dados in mix["canais"].values()]
    for idx, cor in enumerate(cores):
        pie.slices[idx].fillColor = cor
    drawing.add(pie)
    drawing.add(String(20, 190, "Distribuicao do mix de midia - cenario base", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
    return drawing


def gerar_pdf(dados_completos: dict) -> bytes:
    """Gera um PDF executivo em 6 paginas."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = _styles()
    story = []

    empreendimento = dados_completos["empreendimento"]
    localizacao = dados_completos["localizacao"]
    score = dados_completos["resultado_score"]
    verba = dados_completos["resultado_verba"]
    base = verba["cenarios"]["base"]
    mix_base = dados_completos["mix_midias"]["base"]

    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        story.append(Image(str(logo_path), width=3 * cm, height=3 * cm))
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("LaunchScore", styles["LaunchTitulo"]))
    story.append(Paragraph("Score Marketing Imobiliario", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(empreendimento["nome"], styles["LaunchTitulo"]))
    story.append(
        Paragraph(
            f"{localizacao['municipio']} - {localizacao['uf']} | {empreendimento['tipologia']} | {date.today().strftime('%d/%m/%Y')}",
            styles["LaunchSubtitulo"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    kpis = Table(
        [
            ["Score", "VGV", "Verba Recomendada"],
            [f"{score['score_final']}/100", _moeda(verba["vgv"]), _moeda(base["verba_r$"])],
        ],
        colWidths=[4.5 * cm, 5.5 * cm, 6 * cm],
    )
    kpis.setStyle(_table_style(header_bg=AZUL, body_bg=BRANCO))
    story.append(kpis)
    story.append(Spacer(1, 0.3 * cm))
    badge = Table([[score["classificacao"]]], colWidths=[16 * cm])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DOURADO), ("TEXTCOLOR", (0, 0), (-1, -1), AZUL), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(badge)
    story.append(Spacer(1, 11 * cm))
    story.append(Paragraph("Criado por Brenna Carvalho | LaunchScore", styles["LaunchSubtitulo"]))
    story.append(PageBreak())

    story.append(Paragraph("Score e Diagnostico", styles["LaunchH2"]))
    story.append(_gauge_drawing(score["score_final"], score["classificacao"]))
    story.append(Spacer(1, 0.2 * cm))
    top5 = [["Fator", "Contribuicao"]]
    ordenados = sorted(score["breakdown"].items(), key=lambda item: item[1]["contribuicao"], reverse=True)[:5]
    for nome, dados in ordenados:
        top5.append([nome, f"{dados['contribuicao']:.3f}"])
    tabela_top5 = Table(top5, colWidths=[10 * cm, 5 * cm])
    tabela_top5.setStyle(_table_style(header_bg=DOURADO))
    story.append(tabela_top5)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("O que isso significa para a sua campanha", styles["LaunchH2"]))
    story.append(Paragraph(dados_completos["recomendacoes_estrategicas"], styles["LaunchBody"]))
    story.append(PageBreak())

    story.append(Paragraph("Projecao Financeira", styles["LaunchH2"]))
    cenarios_data = [["Cenario", "% VGV", "Verba", "Custo/Unid.", "Leads", "CPL", "ROAS"]]
    for nome, dados in verba["cenarios"].items():
        cenarios_data.append([
            nome.capitalize(),
            _pct(dados["percentual"]),
            _moeda(dados["verba_r$"]),
            _moeda(dados["custo_unidade"]),
            f"{dados['leads_estimados']:.0f}",
            _moeda(dados["cpl_estimado"]),
            _roas(dados["roas"]),
        ])
    tabela_cenarios = Table(cenarios_data, colWidths=[2.7 * cm, 2 * cm, 2.7 * cm, 2.5 * cm, 1.7 * cm, 2.2 * cm, 1.7 * cm])
    tabela_cenarios.setStyle(_table_style(header_bg=AZUL))
    story.append(tabela_cenarios)
    story.append(Spacer(1, 0.4 * cm))
    story.append(_bar_drawing(verba["cenarios"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "Recomendacao: adotar o cenario base, pois combina intensidade comercial competitiva com equilibrio financeiro para a maioria dos lancamentos.",
            styles["LaunchBody"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Mix de Midia - Cenario Base", styles["LaunchH2"]))
    story.append(_pie_drawing(mix_base))
    story.append(Spacer(1, 0.2 * cm))
    mix_table = [["Canal", "Budget", "Leads", "Taticas"]]
    for canal, dados in mix_base["canais"].items():
        mix_table.append([
            canal,
            _moeda(dados["budget_r$"]),
            f"{dados['leads_estimados']:.0f}",
            " | ".join(dados["taticas"][:2]),
        ])
    tabela_mix = Table(mix_table, colWidths=[5.5 * cm, 2.8 * cm, 2 * cm, 6 * cm])
    tabela_mix.setStyle(_table_style(header_bg=DOURADO))
    story.append(tabela_mix)
    story.append(Spacer(1, 0.3 * cm))
    prioridades = list(mix_base["canais"].items())[:3]
    story.append(Paragraph("Prioridades estrategicas", styles["LaunchH2"]))
    for canal, dados in prioridades:
        story.append(Paragraph(f"<b>{canal}:</b> {dados['taticas'][0]}", styles["LaunchBody"]))
    story.append(PageBreak())

    story.append(Paragraph("Perfil de Publico", styles["LaunchH2"]))
    publico = dados_completos["perfil_publico"]
    publico_table = Table(
        [
            ["Faixa etaria primaria", publico["faixa_etaria_primaria"]],
            ["Faixa etaria secundaria", publico["faixa_etaria_secundaria"]],
            ["Renda familiar estimada", publico["renda_familiar_estimada"]],
            ["Escolaridade", publico["escolaridade"]],
            ["Motivacoes", ", ".join(publico["motivacoes_compra"])],
            ["Objecoes", ", ".join(publico["objecoes_tipicas"])],
        ],
        colWidths=[5 * cm, 11 * cm],
    )
    publico_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D6D3D1")), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRANCO, CREME]), ("FONTSIZE", (0, 0), (-1, -1), 8.5)]))
    story.append(publico_table)
    story.append(Spacer(1, 0.3 * cm))
    destaque = Table([[publico["mensagem_chave"]]], colWidths=[16 * cm])
    destaque.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")), ("BOX", (0, 0), (-1, -1), 1, DOURADO), ("TEXTCOLOR", (0, 0), (-1, -1), AZUL), ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story.append(destaque)
    story.append(PageBreak())

    story.append(Paragraph("Metodologia e Termos", styles["LaunchH2"]))
    story.append(Paragraph("O score combina indicadores publicos locais e atributos estrategicos do empreendimento para estimar a dificuldade de venda em uma escala de 0 a 100.", styles["LaunchBody"]))
    story.append(Spacer(1, 0.2 * cm))
    pesos_data = [["Variavel", "Peso"]]
    for chave, peso in PESOS_SCORE.items():
        pesos_data.append([chave, f"{peso:.0%}"])
    tabela_pesos = Table(pesos_data, colWidths=[11 * cm, 3 * cm])
    tabela_pesos.setStyle(_table_style(header_bg=AZUL))
    story.append(tabela_pesos)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Aviso legal: este relatorio tem carater orientativo e nao representa garantia de performance comercial ou financeira.", styles["LaunchBody"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(TERMOS_USO_RESUMIDOS.replace("\n", "<br/>"), styles["LaunchSmall"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("© Brenna Carvalho - LaunchScore. Todos os direitos reservados.", styles["LaunchSubtitulo"]))

    doc.build(
        story,
        onFirstPage=lambda canvas, document: _rodape(canvas, document, empreendimento["nome"]),
        onLaterPages=lambda canvas, document: _rodape(canvas, document, empreendimento["nome"]),
    )
    return buffer.getvalue()
