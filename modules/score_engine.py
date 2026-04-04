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

    score_ajustado = min(100, max(0, score_base + ajuste))
    return {
        "score_ajustado": round(score_ajustado, 1),
        "ajuste_macro": round(ajuste, 1),
        "justificativa_macro": justificativa,
    }


def _ajuste_mercado_local(dados_ipea: dict | None, dados_trends: dict | None) -> tuple[float, list[str]]:
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

    return ajuste, justificativas


def calcular_score(
    dados_normalizados: dict,
    atributos_usuario: dict,
    dados_bcb: dict | None = None,
    dados_ipea: dict | None = None,
    dados_trends: dict | None = None,
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
    ajuste_macro_info = ajuste_macro(score_base, dados_bcb or {})
    ajuste_local, justificativas_locais = _ajuste_mercado_local(dados_ipea, dados_trends)
    score_final = round(min(100, max(0, ajuste_macro_info["score_ajustado"] + ajuste_local)), 1)
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

    return {
        "score_final": score_final,
        "score_base": score_base,
        "classificacao": classificacao,
        "cor": cor,
        "breakdown": breakdown,
        "top3_fatores_criticos": top3_fatores_criticos,
        "justificativa_texto": justificativa,
        "ajuste_macro": ajuste_macro_info["ajuste_macro"],
        "ajuste_mercado_local": round(ajuste_local, 1),
        "justificativa_macro": ajuste_macro_info["justificativa_macro"],
        "justificativa_mercado_local": justificativas_locais,
    }
