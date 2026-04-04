"""Orquestracao das fontes publicas do LaunchScore."""

from __future__ import annotations

import concurrent.futures

from modules.atlas_brasil import get_idhm
from modules.bcb_api import get_dados_bcb
from modules.google_trends_api import get_tendencia_busca
from modules.ibge_api import get_dados_ibge
from modules.ipea_api import get_dados_ipea

FONTES_DE_DADOS = [
    {
        "fonte": "IBGE SIDRA",
        "dados": "Renda, faixa etaria, escolaridade, densidade, domicilios",
        "granularidade": "Municipal",
        "frequencia": "Censo / PNAD anual",
        "url": "https://sidra.ibge.gov.br",
        "gratuita": True,
        "requer_key": False,
    },
    {
        "fonte": "BrasilAPI",
        "dados": "Geocodificacao por CEP, codigo IBGE do municipio",
        "granularidade": "CEP / Municipal",
        "frequencia": "Tempo real",
        "url": "https://brasilapi.com.br",
        "gratuita": True,
        "requer_key": False,
    },
    {
        "fonte": "Banco Central (BCB/SGS)",
        "dados": "Selic, juros imobiliario, concessoes de credito, IVG-R, INCC",
        "granularidade": "Nacional",
        "frequencia": "Mensal",
        "url": "https://dadosabertos.bcb.gov.br",
        "gratuita": True,
        "requer_key": False,
    },
    {
        "fonte": "Ipeadata",
        "dados": "PIB per capita, Gini, rendimento do trabalho, desemprego regional",
        "granularidade": "Municipal / Estadual",
        "frequencia": "Anual",
        "url": "http://www.ipeadata.gov.br",
        "gratuita": True,
        "requer_key": False,
    },
    {
        "fonte": "Atlas Brasil (PNUD/IPEA/FJP)",
        "dados": "IDHM e subindices (renda, longevidade, educacao)",
        "granularidade": "Municipal",
        "frequencia": "Decenal (Censo)",
        "url": "http://www.atlasbrasil.org.br",
        "gratuita": True,
        "requer_key": False,
    },
    {
        "fonte": "Portal Transparencia (MCMV)",
        "dados": "Contratos Minha Casa Minha Vida por municipio",
        "granularidade": "Municipal",
        "frequencia": "Mensal",
        "url": "https://portaldatransparencia.gov.br",
        "gratuita": True,
        "requer_key": True,
    },
    {
        "fonte": "Google Trends (pytrends)",
        "dados": "Interesse de busca por imoveis na cidade",
        "granularidade": "Cidade",
        "frequencia": "Semanal",
        "url": "https://trends.google.com",
        "gratuita": True,
        "requer_key": False,
    },
]


def coletar_todos_dados(codigo_ibge: str, cidade: str, tipologia: str) -> dict:
    """Coleta dados de todas as fontes em paralelo com fallbacks isolados."""

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        fut_ibge = executor.submit(get_dados_ibge, codigo_ibge)
        fut_bcb = executor.submit(get_dados_bcb)
        fut_ipea = executor.submit(get_dados_ipea, codigo_ibge)
        fut_idhm = executor.submit(get_idhm, codigo_ibge)
        fut_trends = executor.submit(get_tendencia_busca, cidade, tipologia)

        dados_ibge = fut_ibge.result()
        dados_bcb = fut_bcb.result()
        dados_ipea = fut_ipea.result()
        dados_idhm = fut_idhm.result()
        dados_trends = fut_trends.result()

    if dados_idhm.get("idhm") is not None and "idh" in dados_ibge:
        dados_ibge["idh"]["valor"] = dados_idhm["idhm"]
        dados_ibge["idh"]["fonte"] = "atlas"
        dados_ibge["idh"]["fonte_nome"] = dados_idhm.get("fonte", "Atlas Brasil")
        dados_ibge["idh"]["fonte_detalhe"] = "Atlas Brasil — PNUD/IPEA/FJP (Censo 2010)"

    qualidade_ibge = _qualidade_ibge(dados_ibge)
    fontes_ok = sum(
        [
            qualidade_ibge > 0.5,
            dados_bcb.get("selic", {}).get("valor") is not None,
            dados_ipea.get("pib_percapita", {}).get("valor") is not None,
            dados_idhm.get("idhm") is not None,
            bool(dados_trends.get("serie_interesse")),
        ]
    )
    qualidade_geral = fontes_ok / 5

    return {
        "ibge": dados_ibge,
        "bcb": dados_bcb,
        "ipea": dados_ipea,
        "idhm": dados_idhm,
        "trends": dados_trends,
        "qualidade_geral": qualidade_geral,
        "fontes_ativas": fontes_ok,
    }


def calcular_favorabilidade_mercado(dados_bcb: dict, dados_ipea: dict, dados_trends: dict) -> dict:
    """Calcula um indice simples de favorabilidade para lancamento."""

    score = 5.0

    selic = dados_bcb.get("selic", {}).get("valor", 10.75)
    if selic < 8:
        score += 1.5
    elif selic < 11:
        score += 0.5
    elif selic > 13:
        score -= 1.5

    desemprego = dados_ipea.get("desemprego", {}).get("valor", 9.0)
    if desemprego is not None:
        if desemprego < 7:
            score += 1.0
        elif desemprego > 12:
            score -= 1.0

    tendencia = dados_trends.get("tendencia_recente", "estavel")
    if tendencia == "crescendo":
        score += 1.0
    elif tendencia == "caindo":
        score -= 0.5

    score = round(min(10, max(0, score)), 1)
    return {
        "score": score,
        "classificacao": "🟢 Favoravel" if score >= 7 else "🟡 Neutro" if score >= 4 else "🔴 Desafiador",
    }


def _qualidade_ibge(dados_ibge: dict) -> float:
    variaveis = [valor for chave, valor in dados_ibge.items() if chave != "codigo_ibge"]
    total = len(variaveis) or 1
    reais = sum(1 for valor in variaveis if valor.get("fonte") in {"api", "atlas"})
    return reais / total
