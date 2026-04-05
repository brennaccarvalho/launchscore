"""Geracao de PDF executivo do LaunchScore."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import PDF_RODAPE
from modules.data_orchestrator import FONTES_DE_DADOS
from modules.termos_de_uso import AUTORA, LINKEDIN


AZUL = colors.Color(0.106, 0.165, 0.290)
DOURADO = colors.Color(0.910, 0.627, 0.125)
CREME = colors.Color(0.980, 0.973, 0.961)
BRANCO = colors.white
CINZA = colors.Color(0.420, 0.443, 0.502)
CINZA_CLARO = colors.HexColor("#D6D3D1")
VERDE_SUAVE = colors.HexColor("#DCFCE7")
AMARELO_SUAVE = colors.HexColor("#FEF3C7")
LARANJA_SUAVE = colors.HexColor("#FFEDD5")
VERMELHO_SUAVE = colors.HexColor("#FEE2E2")
AZUL_SUAVE = colors.HexColor("#EFF6FF")

MAPA_VARIAVEIS = {
    "idh": "Ambiente socioeconomico local",
    "renda_media": "Renda media do municipio",
    "faixa_etaria": "Faixa etaria predominante",
    "escolaridade": "Escolaridade da populacao",
    "densidade": "Densidade urbana",
    "proporcao_alugados": "Proporcao de domicilios alugados",
    "crescimento_pop": "Crescimento populacional",
    "concorrencia": "Concorrencia direta",
    "localizacao": "Percepcao de localizacao",
    "inovacao": "Diferenciacao do produto",
    "tracao": "Sinais de demanda",
    "funcionalidades": "Pacote de atributos e lazer",
    "conexao_luxo": "Aderencia aspiracional do produto",
}

CORES_CLASSIFICACAO = {
    "verde": (VERDE_SUAVE, colors.HexColor("#16A34A")),
    "amarelo": (AMARELO_SUAVE, colors.HexColor("#CA8A04")),
    "laranja": (LARANJA_SUAVE, colors.HexColor("#EA580C")),
    "vermelho": (VERMELHO_SUAVE, colors.HexColor("#DC2626")),
}


def _moeda(valor: float | None) -> str:
    if valor is None:
        return "Indisponivel"
    return f"R$ {valor:,.0f}".replace(",", ".")


def _pct(valor: float | None) -> str:
    if valor is None:
        return "Indisponivel"
    return f"{valor * 100:.1f}%".replace(".", ",")


def _roas(valor: float | None) -> str:
    if valor is None:
        return "Indisponivel"
    return f"{valor:.1f}:1".replace(".", ",")


def _numero(valor: float | int | None, *, casas: int = 1, sufixo: str = "") -> str:
    if valor is None:
        return "Indisponivel"
    if casas == 0:
        corpo = f"{valor:,.0f}"
    else:
        corpo = f"{valor:,.{casas}f}"
    corpo = corpo.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{corpo}{sufixo}"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="LaunchKicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=DOURADO, spaceAfter=6))
    styles.add(ParagraphStyle(name="LaunchTitulo", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=AZUL, spaceAfter=4))
    styles.add(ParagraphStyle(name="LaunchSubtitulo", fontName="Helvetica", fontSize=10, leading=14, textColor=CINZA))
    styles.add(ParagraphStyle(name="LaunchH2", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=AZUL, spaceAfter=8, spaceBefore=2))
    styles.add(ParagraphStyle(name="LaunchH3", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=AZUL, spaceAfter=4))
    styles.add(ParagraphStyle(name="LaunchBody", fontName="Helvetica", fontSize=9.3, leading=13.6, textColor=AZUL))
    styles.add(ParagraphStyle(name="LaunchSmall", fontName="Helvetica", fontSize=8, leading=11, textColor=CINZA))
    styles.add(ParagraphStyle(name="LaunchTableHead", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=BRANCO))
    styles.add(ParagraphStyle(name="LaunchCardLabel", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=CINZA))
    styles.add(ParagraphStyle(name="LaunchBig", fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=AZUL))
    styles.add(ParagraphStyle(name="LaunchQuote", fontName="Helvetica-Bold", fontSize=11.2, leading=15.2, textColor=AZUL))
    return styles


def _p(texto: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(texto).replace("\n", "<br/>"), style)


def _card(
    conteudo: list,
    largura: float,
    *,
    background=BRANCO,
    border_color=CINZA_CLARO,
    top_border_color=None,
    padding: int = 12,
) -> Table:
    tabela = Table([[item] for item in conteudo], colWidths=[largura])
    comandos = [
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, border_color),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if top_border_color is not None:
        comandos.append(("LINEABOVE", (0, 0), (-1, 0), 2, top_border_color))
    tabela.setStyle(TableStyle(comandos))
    return tabela


def _metric_card(titulo: str, valor: str, detalhe: str, largura: float, styles, *, background=BRANCO, border_color=CINZA_CLARO) -> Table:
    return _card(
        [
            _p(titulo, styles["LaunchCardLabel"]),
            _p(valor, styles["LaunchBig"]),
            _p(detalhe, styles["LaunchSmall"]),
        ],
        largura,
        background=background,
        border_color=border_color,
        top_border_color=DOURADO,
    )


def _info_card(titulo: str, texto: str, largura: float, styles, *, background=CREME, border_color=CINZA_CLARO) -> Table:
    return _card(
        [
            _p(titulo, styles["LaunchH3"]),
            _p(texto, styles["LaunchBody"]),
        ],
        largura,
        background=background,
        border_color=border_color,
    )


def _table_style(header_bg=DOURADO, body_bg=BRANCO):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
            ("GRID", (0, 0), (-1, -1), 0.5, CINZA_CLARO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [body_bg, CREME]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _paragraph_table(data: list[list[str]], col_widths: list[float], styles, *, header_bg=DOURADO) -> Table:
    table_data = []
    for row_idx, row in enumerate(data):
        if row_idx == 0:
            table_data.append([_p(str(cell), styles["LaunchTableHead"]) for cell in row])
        else:
            table_data.append([_p(str(cell), styles["LaunchBody"]) for cell in row])
    tabela = Table(table_data, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(_table_style(header_bg=header_bg))
    return tabela


def _rodape(canvas, doc, nome_empreendimento: str):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(AZUL)
        canvas.rect(doc.leftMargin, A4[1] - 1.45 * cm, doc.width, 0.65 * cm, fill=1, stroke=0)
        canvas.setFillColor(BRANCO)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(doc.leftMargin + 10, A4[1] - 1.08 * cm, "LaunchScore")
        canvas.drawRightString(doc.leftMargin + doc.width - 10, A4[1] - 1.08 * cm, nome_empreendimento)
        canvas.setStrokeColor(DOURADO)
        canvas.setLineWidth(2)
        canvas.line(doc.leftMargin, A4[1] - 1.48 * cm, doc.leftMargin + doc.width, A4[1] - 1.48 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(CINZA)
    canvas.drawString(doc.leftMargin, 0.8 * cm, PDF_RODAPE)
    canvas.drawRightString(doc.leftMargin + doc.width, 0.8 * cm, f"Pagina {doc.page}")
    canvas.drawString(doc.leftMargin, 0.45 * cm, f"© 2026 {AUTORA} | LaunchScore | Uso orientativo conforme Termos de Uso.")
    canvas.restoreState()


def _gauge_drawing(score: float, classificacao: str) -> Drawing:
    drawing = Drawing(450, 130)
    drawing.add(Rect(0, 0, 450, 130, fillColor=CREME, strokeColor=None))
    faixas = [
        (0, 30, VERDE_SUAVE),
        (30, 50, AMARELO_SUAVE),
        (50, 70, LARANJA_SUAVE),
        (70, 100, VERMELHO_SUAVE),
    ]
    x = 35
    largura_total = 360
    for inicio, fim, cor in faixas:
        largura = largura_total * ((fim - inicio) / 100)
        drawing.add(Rect(x, 60, largura, 22, fillColor=cor, strokeColor=None))
        x += largura
    marcador_x = 35 + largura_total * (score / 100)
    drawing.add(Line(marcador_x, 52, marcador_x, 92, strokeColor=AZUL, strokeWidth=3))
    drawing.add(String(35, 100, "Leitura do score de dificuldade de venda", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
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
    drawing.add(String(40, 190, "Comparativo entre verba, leads e vendas estimadas", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
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
    drawing.add(String(20, 190, "Distribuicao do mix de midia do cenario base", fontName="Helvetica-Bold", fontSize=11, fillColor=AZUL))
    return drawing


def _texto_localizacao(localizacao: dict) -> str:
    partes = [f"{localizacao['municipio']} - {localizacao['uf']}"]
    bairro = (localizacao.get("bairro") or "").strip()
    if bairro:
        partes.append(f"Bairro {bairro}")
    return " | ".join(partes)


def _resumo_executivo(score: dict, base: dict, empreendimento: dict, localizacao: dict, styles) -> Table:
    texto = (
        f"O empreendimento <b>{empreendimento['nome']}</b>, em <b>{_texto_localizacao(localizacao)}</b>, "
        f"recebeu score <b>{score['score_final']}/100</b>, classificado como <b>{score['classificacao']}</b>. "
        f"A recomendacao inicial e abrir a operacao pelo <b>cenario base</b>, com investimento estimado de "
        f"<b>{_moeda(base['verba_r$'])}</b> ({_pct(base['percentual'])} do VGV), equilibrando presenca comercial, velocidade e margem."
    )
    return _card(
        [
            _p("Resumo executivo", styles["LaunchH3"]),
            _p(texto, styles["LaunchBody"]),
        ],
        16.2 * cm,
        background=BRANCO,
        border_color=CINZA_CLARO,
        top_border_color=DOURADO,
    )


def _fatores_criticos(score: dict, styles) -> Table:
    linhas = [["Fator", "Leitura para o cliente", "Peso na pressao"]]
    ordenados = sorted(score["breakdown"].items(), key=lambda item: item[1]["contribuicao"], reverse=True)[:4]
    for nome, dados in ordenados:
        linhas.append(
            [
                MAPA_VARIAVEIS.get(nome, nome),
                nome.replace("_", " "),
                f"{dados['contribuicao']:.3f}",
            ]
        )
    return _paragraph_table(linhas, [5.2 * cm, 7.8 * cm, 2.4 * cm], styles, header_bg=DOURADO)


def _fontes_ativas_relatorio(styles) -> Table:
    fontes = []
    for fonte in FONTES_DE_DADOS:
        if "Ativa" not in fonte.get("status_integracao", ""):
            continue
        fontes.append([fonte["fonte"], fonte["uso_no_relatorio"]])
    linhas = [["Fonte publica", "Como entra nesta apresentacao"]] + fontes
    return _paragraph_table(linhas, [4.8 * cm, 11.4 * cm], styles, header_bg=AZUL)


def _contexto_cards(dados_publicos: dict, styles) -> Table:
    dados_bcb = dados_publicos["bcb"]
    dados_ipea = dados_publicos["ipea"]
    dados_trends = dados_publicos["trends"]

    macro = _info_card(
        "Macroeconomia",
        (
            f"Selic em <b>{_numero(dados_bcb.get('selic', {}).get('valor'), sufixo='%')}</b>. "
            f"Juros imobiliario em <b>{_numero(dados_bcb.get('juros_imobiliario', {}).get('valor'), sufixo='%')}</b> "
            f"e INCC em <b>{_numero(dados_bcb.get('incc', {}).get('valor'), sufixo='%')}</b> ajudam a calibrar o apetite de compra."
        ),
        5.0 * cm,
        styles,
        background=AZUL_SUAVE,
    )
    local = _info_card(
        "Mercado local",
        (
            f"PIB per capita em <b>{_moeda(dados_ipea.get('pib_percapita', {}).get('valor'))}</b>. "
            f"Desemprego em <b>{_numero(dados_ipea.get('desemprego', {}).get('valor'), sufixo='%')}</b> "
            f"e Gini em <b>{_numero(dados_ipea.get('gini', {}).get('valor'), casas=2)}</b> sinalizam ambiente de absorcao."
        ),
        5.0 * cm,
        styles,
        background=CREME,
    )
    termos = ", ".join(dados_trends.get("termos", [])[:2]) or "Sem leitura detalhada"
    digital = _info_card(
        "Demanda digital",
        (
            f"Interesse medio em <b>{_numero(dados_trends.get('score_interesse'), casas=0)}/100</b> "
            f"com tendencia <b>{dados_trends.get('tendencia_recente', 'indisponivel')}</b>. "
            f"Termos monitorados: <b>{termos}</b>."
        ),
        5.0 * cm,
        styles,
        background=AMARELO_SUAVE,
    )
    tabela = Table([[macro, local, digital]], colWidths=[5.2 * cm, 5.2 * cm, 5.2 * cm])
    tabela.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return tabela


def _publico_insights(publico: dict, styles) -> Table:
    texto = (
        f"<b>Motivacoes:</b> {', '.join(publico['motivacoes_compra'])}.<br/>"
        f"<b>Objecoes:</b> {', '.join(publico['objecoes_tipicas'])}.<br/>"
        f"<b>Mensagem-chave:</b> {publico['mensagem_chave']}"
    )
    return _card(
        [
            _p("Narrativa comercial recomendada", styles["LaunchH3"]),
            _p(texto, styles["LaunchBody"]),
        ],
        16.2 * cm,
        background=AMARELO_SUAVE,
        border_color=DOURADO,
    )


def gerar_pdf(dados_completos: dict) -> bytes:
    """Gera um PDF executivo com visual de apresentacao para cliente."""

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
    publico = dados_completos["perfil_publico"]
    dados_publicos = dados_completos["dados_publicos"]

    score_bg, score_border = CORES_CLASSIFICACAO.get(score.get("cor"), (CREME, DOURADO))
    logo_path = Path("assets/logo.png")
    if logo_path.exists():
        story.append(Image(str(logo_path), width=2.4 * cm, height=2.4 * cm))
        story.append(Spacer(1, 0.18 * cm))

    story.append(_p("APRESENTACAO EXECUTIVA", styles["LaunchKicker"]))
    story.append(_p(empreendimento["nome"], styles["LaunchTitulo"]))
    story.append(
        _p(
            f"{_texto_localizacao(localizacao)} | {empreendimento['tipologia']} | {date.today().strftime('%d/%m/%Y')}",
            styles["LaunchSubtitulo"],
        )
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(
        _card(
            [
                _p("Recomendacao inicial", styles["LaunchH3"]),
                _p(
                    f"Para esta leitura, o melhor ponto de partida comercial e o <b>cenario base</b>, "
                    f"com investimento estimado de <b>{_moeda(base['verba_r$'])}</b> "
                    f"e expectativa de <b>{base['leads_estimados']:.0f} leads</b> ao longo da operacao.",
                    styles["LaunchQuote"],
                ),
            ],
            16.2 * cm,
            background=CREME,
            border_color=DOURADO,
            top_border_color=DOURADO,
        )
    )
    story.append(Spacer(1, 0.28 * cm))

    cards_capa = Table(
        [
            [
                _metric_card("Score de venda", f"{score['score_final']}/100", "Nivel de friccao comercial previsto", 4.95 * cm, styles, background=score_bg, border_color=score_border),
                _metric_card("Classificacao", score["classificacao"], "Leitura consolidada para decisao", 4.95 * cm, styles, background=BRANCO),
                _metric_card("Verba inicial", _moeda(base["verba_r$"]), f"{_pct(base['percentual'])} do VGV recomendado", 4.95 * cm, styles, background=BRANCO),
            ]
        ],
        colWidths=[5.2 * cm, 5.2 * cm, 5.2 * cm],
    )
    cards_capa.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(cards_capa)
    story.append(Spacer(1, 0.3 * cm))
    story.append(_resumo_executivo(score, base, empreendimento, localizacao, styles))
    story.append(Spacer(1, 0.28 * cm))
    story.append(
        _card(
            [
                _p("O que esta apresentacao entrega", styles["LaunchH3"]),
                _p(
                    "1. Diagnostico comercial do lancamento.<br/>"
                    "2. Intensidade de investimento recomendada.<br/>"
                    "3. Plano de ativacao por canais.<br/>"
                    "4. Publico-alvo e narrativa comercial.<br/>"
                    "5. Sinais de mercado e fontes usadas na leitura.",
                    styles["LaunchBody"],
                ),
            ],
            16.2 * cm,
            background=BRANCO,
            border_color=CINZA_CLARO,
        )
    )
    story.append(Spacer(1, 3.0 * cm))
    story.append(_p(f"Criado por {AUTORA} | {LINKEDIN}", styles["LaunchSmall"]))
    story.append(PageBreak())

    story.append(_p("1. Diagnostico comercial", styles["LaunchH2"]))
    story.append(_p("Leitura visual para explicar o grau de pressao comercial do lancamento.", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.08 * cm))
    story.append(_gauge_drawing(score["score_final"], score["classificacao"]))
    story.append(Spacer(1, 0.22 * cm))
    story.append(_p("Fatores que mais sustentam o score", styles["LaunchH3"]))
    story.append(_fatores_criticos(score, styles))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        _card(
            [
                _p("Leitura recomendada para a reuniao com o cliente", styles["LaunchH3"]),
                _p(dados_completos["recomendacoes_estrategicas"], styles["LaunchBody"]),
            ],
            16.2 * cm,
            background=CREME,
            border_color=CINZA_CLARO,
            top_border_color=DOURADO,
        )
    )
    story.append(PageBreak())

    story.append(_p("2. Estrategia de investimento", styles["LaunchH2"]))
    story.append(_p("Comparativo simples para defender intensidade de verba, volume de leads e retorno esperado.", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.08 * cm))
    cenarios_data = [["Cenario", "% do VGV", "Verba", "Custo/unid.", "Leads", "CPL", "ROAS"]]
    for nome, dados in verba["cenarios"].items():
        cenarios_data.append(
            [
                nome.capitalize(),
                _pct(dados["percentual"]),
                _moeda(dados["verba_r$"]),
                _moeda(dados["custo_unidade"]),
                f"{dados['leads_estimados']:.0f}",
                _moeda(dados["cpl_estimado"]),
                _roas(dados["roas"]),
            ]
        )
    story.append(_paragraph_table(cenarios_data, [2.7 * cm, 2.1 * cm, 2.7 * cm, 2.5 * cm, 1.5 * cm, 2.1 * cm, 1.7 * cm], styles, header_bg=AZUL))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_bar_drawing(verba["cenarios"]))
    story.append(Spacer(1, 0.22 * cm))
    story.append(
        Table(
            [[
                _info_card(
                    "Por que comecar pelo cenario base",
                    "Ele concentra o equilibrio entre presenca de mercado, ritmo comercial e protecao de margem, evitando subinvestimento na largada.",
                    7.8 * cm,
                    styles,
                    background=CREME,
                ),
                _info_card(
                    "Leitura financeira",
                    f"O cenario base representa <b>{base['benchmark_comparacao'].lower()}</b> em relacao ao benchmark e projeta ROAS de <b>{_roas(base['roas'])}</b>.",
                    7.8 * cm,
                    styles,
                    background=AZUL_SUAVE,
                ),
            ]],
            colWidths=[8.1 * cm, 8.1 * cm],
        )
    )
    story.append(PageBreak())

    story.append(_p("3. Plano de ativacao", styles["LaunchH2"]))
    story.append(_p("Distribuicao recomendada da verba base para acelerar demanda com coerencia de canais.", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.08 * cm))
    story.append(_pie_drawing(mix_base))
    story.append(Spacer(1, 0.18 * cm))
    mix_table = [["Canal", "Budget", "Leads", "Taticas prioritarias"]]
    for canal, dados in mix_base["canais"].items():
        mix_table.append(
            [
                canal,
                _moeda(dados["budget_r$"]),
                f"{dados['leads_estimados']:.0f}",
                "<br/>".join(dados["taticas"][:2]),
            ]
        )
    story.append(_paragraph_table(mix_table, [4.7 * cm, 2.7 * cm, 2.0 * cm, 6.8 * cm], styles, header_bg=DOURADO))
    story.append(Spacer(1, 0.24 * cm))
    prioridades = sorted(mix_base["canais"].items(), key=lambda item: item[1]["budget_r$"], reverse=True)[:3]
    cards_prioridade = []
    for canal, dados in prioridades:
        cards_prioridade.append(
            _info_card(
                canal,
                f"Priorize: <b>{dados['taticas'][0]}</b>.<br/>Budget sugerido: <b>{_moeda(dados['budget_r$'])}</b>.",
                4.95 * cm,
                styles,
                background=BRANCO,
            )
        )
    story.append(Table([cards_prioridade], colWidths=[5.2 * cm, 5.2 * cm, 5.2 * cm]))
    story.append(PageBreak())

    story.append(_p("4. Publico e narrativa comercial", styles["LaunchH2"]))
    story.append(_p("Leitura sintetica para orientar criativo, discurso de vendas e prova de valor.", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.08 * cm))
    publico_table = _paragraph_table(
        [
            ["Dimensao", "Leitura recomendada"],
            ["Faixa etaria primaria", publico["faixa_etaria_primaria"]],
            ["Faixa etaria secundaria", publico["faixa_etaria_secundaria"]],
            ["Renda familiar estimada", publico["renda_familiar_estimada"]],
            ["Escolaridade", publico["escolaridade"]],
            ["Motivacoes", ", ".join(publico["motivacoes_compra"])],
            ["Objecoes tipicas", ", ".join(publico["objecoes_tipicas"])],
        ],
        [5.0 * cm, 11.2 * cm],
        styles,
        header_bg=AZUL,
    )
    story.append(publico_table)
    story.append(Spacer(1, 0.26 * cm))
    story.append(_publico_insights(publico, styles))
    story.append(Spacer(1, 0.22 * cm))
    story.append(
        _card(
            [
                _p("Como usar na pratica", styles["LaunchH3"]),
                _p(
                    "Leve esta pagina para alinhar criativos, argumento de vendas, prova social e abordagem de atendimento. "
                    "Quanto mais esse perfil conversar com as objecoes reais do CRM, melhor a performance comercial.",
                    styles["LaunchBody"],
                ),
            ],
            16.2 * cm,
            background=CREME,
            border_color=CINZA_CLARO,
        )
    )
    story.append(PageBreak())

    story.append(_p("5. Contexto de mercado e inteligencia usada", styles["LaunchH2"]))
    story.append(_p("Panorama dos sinais externos considerados para deixar a recomendacao mais aderente ao momento do mercado.", styles["LaunchSubtitulo"]))
    story.append(Spacer(1, 0.1 * cm))
    story.append(_contexto_cards(dados_publicos, styles))
    story.append(Spacer(1, 0.24 * cm))
    story.append(
        _card(
            [
                _p("Como o score foi construido", styles["LaunchH3"]),
                _p(
                    "O LaunchScore combina sinais publicos de territorio, macroeconomia, mercado local e demanda digital "
                    "com os atributos comerciais do produto. O objetivo nao e produzir um relatorio tecnico, e sim traduzir "
                    "complexidade em uma decisao de investimento mais clara e defensavel.",
                    styles["LaunchBody"],
                ),
            ],
            16.2 * cm,
            background=BRANCO,
            border_color=CINZA_CLARO,
            top_border_color=DOURADO,
        )
    )
    story.append(Spacer(1, 0.24 * cm))
    story.append(_p("Fontes consideradas nesta leitura", styles["LaunchH3"]))
    story.append(_fontes_ativas_relatorio(styles))
    story.append(Spacer(1, 0.24 * cm))
    story.append(
        _card(
            [
                _p("Nota de uso", styles["LaunchH3"]),
                _p(
                    "Esta apresentacao apoia reunioes com clientes, calibragem de verba e alinhamento comercial. "
                    "Os resultados possuem carater orientativo e devem ser lidos em conjunto com validacao local, estrategia de vendas e contexto do negocio.",
                    styles["LaunchBody"],
                ),
            ],
            16.2 * cm,
            background=CREME,
            border_color=CINZA_CLARO,
        )
    )

    doc.build(
        story,
        onFirstPage=lambda canvas, document: _rodape(canvas, document, empreendimento["nome"]),
        onLaterPages=lambda canvas, document: _rodape(canvas, document, empreendimento["nome"]),
    )
    return buffer.getvalue()
