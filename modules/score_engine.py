# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

"""Motor de calculo do score de dificuldade de venda."""

from __future__ import annotations

from config import PESOS_SCORE


def _escala_usuario(valor: int, invertido: bool = False) -> float:
    base = ((valor - 1) / 4) * 10
    return round(10 - base, 2) if invertido else round(base, 2)


def classificar_score(score: float) -> tuple[str, str]:
    if score <= 30:
        return "Baixa Dificuldade", "verde"
    if score <= 50:
        return "Dificuldade Moderada", "amarelo"
    if score <= 70:
        return "Alta Dificuldade", "laranja"
    return "Dificuldade Critica", "vermelho"


def ajuste_macro(score_base: float, dados_bcb: dict) -> dict:
    """Aplica ajuste contextual macroeconomico ao score."""

    ajuste = 0.0
    justificativa = []

    selic = dados_bcb.get("selic", {}).get("valor")
    if selic is not None and selic > 12.0:
        ajuste += 3.0
        justificativa.append(f"Selic em {selic:.1f}% — credito imobiliario mais restrito (+3 pts)")
    elif selic is not None and selic < 8.0:
        ajuste -= 2.0
        justificativa.append(f"Selic em {selic:.1f}% — credito favoravel para compradores (-2 pts)")

    juros_imob = dados_bcb.get("juros_imobiliario", {}).get("valor")
    if juros_imob is not None and juros_imob > 10.0:
        ajuste += 2.0
        justificativa.append(f"Juros do financiamento imobiliario em {juros_imob:.1f}% a.a. (+2 pts)")

    return {
        "ajuste": round(ajuste, 1),
        "ajuste_macro": round(ajuste, 1),
        "justificativa": justificativa,
        "justificativa_macro": justificativa,
    }


def ajuste_mercado_local(score_base: float, dados_ipea: dict | None, dados_trends: dict | None) -> dict:
    ajuste = 0.0
    justificativas = []

    if dados_ipea:
        gini = dados_ipea.get("gini", {}).get("valor")
        if gini is not None and gini > 0.55:
            ajuste += 1.5
            justificativas.append(f"Gini municipal elevado ({gini:.2f}) indica mercado mais polarizado (+1,5 pt)")

        desemprego = dados_ipea.get("desemprego", {}).get("valor")
        if desemprego is not None and desemprego > 12:
            ajuste += 2.0
            justificativas.append(f"Desemprego regional em {desemprego:.1f}% pressiona a demanda (+2 pts)")

        pib = dados_ipea.get("pib_percapita", {}).get("valor")
        if pib is not None and pib > 45000:
            ajuste -= 1.5
            justificativas.append(f"PIB per capita local acima da media favorece absorcao (-1,5 pt)")

    if dados_trends:
        tendencia = dados_trends.get("tendencia_recente")
        interesse = dados_trends.get("score_interesse", 50)
        if tendencia == "crescendo" and interesse >= 55:
            ajuste -= 1.0
            justificativas.append("Busca por imoveis em alta no Google Trends reduz friccao comercial (-1 pt)")
        elif tendencia == "caindo" and interesse <= 45:
            ajuste += 1.0
            justificativas.append("Busca por imoveis em retracao recente aumenta cautela comercial (+1 pt)")

    return {
        "ajuste": round(ajuste, 1),
        "justificativa": justificativas,
    }


def ajuste_fipezap(score_base: float, dados_fipezap: dict | None, valor_unidade: float | None) -> dict:
    dados_fipezap = dados_fipezap or {}
    if not dados_fipezap.get("disponivel"):
        return {"ajuste": 0.0, "justificativa": ["FipeZap: dados nao disponiveis para esta cidade."]}

    ajuste = 0.0
    justificativas: list[str] = []
    variacao_12m = float(dados_fipezap.get("variacao_12m") or 0.0)
    preco_m2_local = float(dados_fipezap.get("preco_medio_m2") or 0.0)

    if variacao_12m > 10:
        ajuste -= 2.0
        justificativas.append(
            f"Precos residenciais em {dados_fipezap['cidade_fipezap']} sobem {variacao_12m:.1f}% em 12 meses, reduzindo a resistencia de compra (-2 pts)"
        )
    elif variacao_12m > 5:
        ajuste -= 1.0
        justificativas.append(f"Valorizacao de {variacao_12m:.1f}% em 12 meses sugere mercado positivo (-1 pt)")
    elif variacao_12m < 0:
        ajuste += 2.0
        justificativas.append(f"Preco medio recuou {abs(variacao_12m):.1f}% em 12 meses e pode estimular espera do comprador (+2 pts)")

    if valor_unidade and preco_m2_local > 0:
        preco_estimado_m2 = valor_unidade / 60
        if preco_estimado_m2 > preco_m2_local * 1.3:
            ajuste += 2.0
            justificativas.append(
                f"Ticket estimado por m2 fica acima da media local de R$ {preco_m2_local:,.0f}/m2 (+2 pts)"
            )
        elif preco_estimado_m2 < preco_m2_local * 0.85:
            ajuste -= 1.5
            justificativas.append("Ticket fica abaixo da media local e reforca competitividade de preco (-1,5 pt)")

    return {"ajuste": round(ajuste, 1), "justificativa": justificativas}


def ajuste_rib(score_base: float, dados_rib: dict | None) -> dict:
    dados_rib = dados_rib or {}
    if not dados_rib.get("disponivel"):
        return {"ajuste": 0.0, "justificativa": ["RIB: dados de transacoes registradas nao disponiveis para este municipio."]}

    ajuste = 0.0
    justificativas: list[str] = []
    variacao = float(dados_rib.get("variacao_anual_pct") or 0.0)
    tendencia = dados_rib.get("tendencia")

    if tendencia == "alta" and variacao > 10:
        ajuste -= 2.0
        justificativas.append(f"Transacoes registradas sobem {variacao:.1f}% a/a, sinalizando mercado mais ativo (-2 pts)")
    elif tendencia == "alta":
        ajuste -= 1.0
        justificativas.append(f"Registros imobiliarios crescem {variacao:.1f}% a/a e ajudam a absorcao (-1 pt)")
    elif tendencia == "queda":
        ajuste += 2.0
        justificativas.append(f"Volume de transacoes recua {abs(variacao):.1f}% a/a e indica mercado retraido (+2 pts)")

    incorporacoes = int(dados_rib.get("incorporacoes") or 0)
    if incorporacoes > 10:
        ajuste += 1.0
        justificativas.append(f"{incorporacoes} incorporacoes recentes ampliam a oferta local (+1 pt)")

    return {"ajuste": round(ajuste, 1), "justificativa": justificativas}


def ajuste_macro_expandido(score_base: float, dados_bcb: dict, valor_unidade: float | None = None) -> dict:
    ajuste = 0.0
    justificativas: list[str] = []

    inadimplencia = dados_bcb.get("inadimplencia_imobiliaria", {}).get("valor")
    if inadimplencia is not None and inadimplencia > 3.0:
        ajuste += 1.5
        justificativas.append(
            f"Inadimplencia do credito imobiliario em {inadimplencia:.1f}% sinaliza maior restricao de credito (+1,5 pt)"
        )

    ticket_medio = dados_bcb.get("ticket_medio_financiado", {}).get("valor")
    if ticket_medio is not None and valor_unidade and valor_unidade > ticket_medio * 1.5:
        ajuste += 1.0
        justificativas.append(
            f"Ticket da unidade supera em mais de 50% o valor medio financiado no mercado (+1 pt)"
        )

    ipca = dados_bcb.get("ipca_12m", {}).get("valor")
    if ipca is not None and ipca > 6.0:
        ajuste += 1.0
        justificativas.append(f"IPCA em {ipca:.1f}% pressiona o poder de compra (+1 pt)")

    return {"ajuste": round(ajuste, 1), "justificativa": justificativas}


def calcular_score(
    dados_normalizados: dict,
    atributos_usuario: dict,
    dados_bcb: dict | None = None,
    dados_ipea: dict | None = None,
    dados_trends: dict | None = None,
    dados_fipezap: dict | None = None,
    dados_rib: dict | None = None,
    valor_unidade: float | None = None,
) -> dict:
    """Combina dados externos e atributos do produto em score final."""

    valores = {
        "idh": dados_normalizados["idh"],
        "renda_media": dados_normalizados["renda_media"],
        "faixa_etaria": dados_normalizados["faixa_etaria"],
        "escolaridade": dados_normalizados["escolaridade"],
        "densidade": dados_normalizados["densidade"],
        "proporcao_alugados": dados_normalizados["proporcao_alugados"],
        "crescimento_pop": dados_normalizados["crescimento_pop"],
        "concorrencia": _escala_usuario(atributos_usuario["concorrencia"]),
        "localizacao": _escala_usuario(atributos_usuario["localizacao"]),
        "inovacao": _escala_usuario(atributos_usuario["inovacao"], invertido=True),
        "tracao": _escala_usuario(atributos_usuario["tracao"], invertido=True),
        "funcionalidades": _escala_usuario(atributos_usuario["funcionalidades"], invertido=True),
        "conexao_luxo": _escala_usuario(atributos_usuario["conexao_luxo"], invertido=True),
    }

    breakdown = {}
    score_bruto = 0.0
    for chave, peso in PESOS_SCORE.items():
        contribuicao = valores[chave] * peso
        score_bruto += contribuicao
        breakdown[chave] = {
            "peso": peso,
            "valor_norm": round(valores[chave], 2),
            "contribuicao": round(contribuicao, 4),
        }

    score_base = round(score_bruto * 10, 1)
    aj_macro = ajuste_macro(score_base, dados_bcb or {})
    aj_local = ajuste_mercado_local(score_base, dados_ipea, dados_trends)
    aj_fipezap = ajuste_fipezap(score_base, dados_fipezap, valor_unidade)
    aj_rib = ajuste_rib(score_base, dados_rib)
    aj_macro_expand = ajuste_macro_expandido(score_base, dados_bcb or {}, valor_unidade)
    ajuste_total = (
        aj_macro["ajuste"]
        + aj_local["ajuste"]
        + aj_fipezap["ajuste"]
        + aj_rib["ajuste"]
        + aj_macro_expand["ajuste"]
    )
    ajuste_total = max(-10, min(10, ajuste_total))
    score_final = round(min(100, max(0, score_base + ajuste_total)), 1)
    classificacao, cor = classificar_score(score_final)
    top3 = sorted(breakdown.items(), key=lambda item: item[1]["contribuicao"], reverse=True)[:3]
    top3_fatores_criticos = [nome for nome, _ in top3]
    justificativa = (
        "Os principais fatores de pressao sobre a venda sao "
        + ", ".join(top3_fatores_criticos[:-1])
        + (" e " if len(top3_fatores_criticos) > 1 else "")
        + top3_fatores_criticos[-1]
        + ", pois concentram a maior contribuicao ponderada no score final."
    )

    justificativas_contextuais = (
        aj_macro["justificativa"]
        + aj_local["justificativa"]
        + aj_fipezap["justificativa"]
        + aj_rib["justificativa"]
        + aj_macro_expand["justificativa"]
    )

    return {
        "score_final": score_final,
        "score_base": score_base,
        "classificacao": classificacao,
        "cor": cor,
        "breakdown": breakdown,
        "top3_fatores_criticos": top3_fatores_criticos,
        "justificativa_texto": justificativa,
        "ajuste_macro": aj_macro["ajuste"],
        "ajuste_mercado_local": aj_local["ajuste"],
        "ajuste_fipezap": aj_fipezap["ajuste"],
        "ajuste_rib": aj_rib["ajuste"],
        "ajuste_macro_expandido": aj_macro_expand["ajuste"],
        "ajuste_total": round(ajuste_total, 1),
        "justificativa_macro": aj_macro["justificativa"],
        "justificativa_mercado_local": aj_local["justificativa"],
        "justificativa_fipezap": aj_fipezap["justificativa"],
        "justificativa_rib": aj_rib["justificativa"],
        "justificativa_macro_expandido": aj_macro_expand["justificativa"],
        "justificativas_contextuais": justificativas_contextuais,
        "ajustes_contextuais": {
            "macro": aj_macro,
            "mercado_local": aj_local,
            "fipezap": aj_fipezap,
            "rib": aj_rib,
            "macro_expandido": aj_macro_expand,
        },
    }
