# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

"""Orquestracao das fontes publicas do LaunchScore."""

from __future__ import annotations

import concurrent.futures

from modules.atlas_brasil import get_idhm
from modules.bcb_api import get_dados_bcb
from modules.fipezap_api import get_dados_fipezap
from modules.google_trends_api import get_tendencia_busca
from modules.ibge_api import get_dados_ibge
from modules.ipea_api import get_dados_ipea
from modules.rib_api import get_dados_rib

FONTES_DE_DADOS = [
    {
        "fonte": "IBGE SIDRA",
        "dados": "Renda, faixa etaria, escolaridade, densidade, domicilios",
        "granularidade": "Municipal",
        "frequencia": "Censo / PNAD anual",
        "url": "https://sidra.ibge.gov.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Base demografica e socioeconomica do municipio",
    },
    {
        "fonte": "BrasilAPI",
        "dados": "Geocodificacao por CEP, codigo IBGE do municipio e fallback de endereco",
        "granularidade": "CEP / Municipal",
        "frequencia": "Tempo real",
        "url": "https://brasilapi.com.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Identificacao do municipio e enrich de localizacao",
    },
    {
        "fonte": "ViaCEP",
        "dados": "Validacao de bairro e logradouro por CEP",
        "granularidade": "CEP",
        "frequencia": "Tempo real",
        "url": "https://viacep.com.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Refino do bairro identificado e validacao do endereco de entrada",
    },
    {
        "fonte": "Banco Central (BCB/SGS)",
        "dados": "Selic, juros imobiliario, concessoes de credito, IVG-R, INCC",
        "granularidade": "Nacional",
        "frequencia": "Mensal",
        "url": "https://dadosabertos.bcb.gov.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Contexto macroeconomico e ajuste contextual do score",
    },
    {
        "fonte": "Ipeadata",
        "dados": "PIB per capita, Gini, rendimento do trabalho, desemprego regional",
        "granularidade": "Municipal / Estadual",
        "frequencia": "Anual",
        "url": "http://www.ipeadata.gov.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Contexto economico local e favorabilidade de demanda",
    },
    {
        "fonte": "Atlas Brasil (PNUD/IPEA/FJP)",
        "dados": "IDHM e subindices (renda, longevidade, educacao)",
        "granularidade": "Municipal",
        "frequencia": "Decenal (Censo)",
        "url": "http://www.atlasbrasil.org.br",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa com fallback local",
        "uso_no_relatorio": "Substitui o IDH generico por leitura municipal mais precisa",
    },
    {
        "fonte": "Portal Transparencia (MCMV)",
        "dados": "Contratos Minha Casa Minha Vida por municipio",
        "granularidade": "Municipal",
        "frequencia": "Mensal",
        "url": "https://portaldatransparencia.gov.br",
        "gratuita": True,
        "requer_key": True,
        "status_integracao": "Opcional",
        "uso_no_relatorio": "Leitura de dominancia do mercado popular e subsidios",
    },
    {
        "fonte": "Google Trends (pytrends)",
        "dados": "Interesse de busca por imoveis na cidade",
        "granularidade": "Cidade",
        "frequencia": "Semanal",
        "url": "https://trends.google.com",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Ativa",
        "uso_no_relatorio": "Demanda digital e tendencia recente de interesse",
    },
    {
        "fonte": "Indice FipeZAP",
        "dados": "Preco anunciado de venda e locacao por cidade e m2",
        "granularidade": "Cidade",
        "frequencia": "Mensal",
        "url": "https://www.fipe.org.br/pt-br/indices/fipezap/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Benchmark de preco por m2, locacao e rental yield",
    },
    {
        "fonte": "Indicadores Abrainc/Fipe",
        "dados": "Lancamentos, vendas, entregas, oferta e distratos",
        "granularidade": "Nacional / Segmento",
        "frequencia": "Mensal",
        "url": "https://www.fipe.org.br/pt-br/indices/abrainc/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Benchmark de aquecimento do mercado primario e ciclo de oferta",
    },
    {
        "fonte": "Radar Abrainc/Fipe",
        "dados": "Leitura executiva trimestral do mercado imobiliario",
        "granularidade": "Nacional",
        "frequencia": "Trimestral",
        "url": "https://www.fipe.org.br/pt-br/indices/radar-abrainc/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Narrativa executiva sobre fase do ciclo imobiliario",
    },
    {
        "fonte": "Indicadores do Registro Imobiliario",
        "dados": "Transferencias e estatisticas de atividade imobiliaria",
        "granularidade": "Capital / Municipio",
        "frequencia": "Mensal",
        "url": "https://www.fipe.org.br/pt-br/indices/indicadores-do-registro-imobiliario/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Proxy de liquidez real do mercado, alem do anuncio",
    },
    {
        "fonte": "Indicador Antecedente do Mercado Imobiliario",
        "dados": "Alvaras e sinais preliminares de nova oferta",
        "granularidade": "Municipal",
        "frequencia": "Trimestral",
        "url": "https://www.fipe.org.br/pt-br/indices/indicador-antecedente-do-mercado-imobiliario/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Antecipacao de concorrencia futura e pressao de oferta",
    },
    {
        "fonte": "OLX API",
        "dados": "Publicacao de anuncios, leads e integracao com CRM",
        "granularidade": "Conta / Anuncio",
        "frequencia": "Tempo real",
        "url": "https://developers.olx.com.br/",
        "gratuita": False,
        "requer_key": True,
        "status_integracao": "Depende de homologacao",
        "uso_no_relatorio": "Benchmark operacional de portal, SLA e qualidade de lead",
    },
    {
        "fonte": "Google Ads API",
        "dados": "Cliques, CPC, CPL, conversoes e qualidade de campanha",
        "granularidade": "Campanha / Grupo / Criativo",
        "frequencia": "Tempo real",
        "url": "https://developers.google.com/google-ads/api",
        "gratuita": True,
        "requer_key": True,
        "status_integracao": "Depende de conta",
        "uso_no_relatorio": "Benchmark real de performance por canal e tipologia",
    },
    {
        "fonte": "Meta Lead Ads + Conversions API",
        "dados": "Leads, eventos online/offline e performance de campanhas",
        "granularidade": "Campanha / Conjunto / Formulario",
        "frequencia": "Tempo real",
        "url": "https://www.facebook.com/business/help/AboutConversionsAPI",
        "gratuita": True,
        "requer_key": True,
        "status_integracao": "Depende de conta",
        "uso_no_relatorio": "Qualidade de lead, atribuicao e funil de vendas",
    },
    {
        "fonte": "CNES / DataSUS",
        "dados": "Estabelecimentos de saude por municipio",
        "granularidade": "Municipal / Bairro",
        "frequencia": "Mensal",
        "url": "https://cnes.saude.gov.br/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Infraestrutura urbana e conveniencia para familias",
    },
    {
        "fonte": "INEP Censo Escolar",
        "dados": "Escolas, matriculas e estrutura educacional",
        "granularidade": "Municipal / Escola",
        "frequencia": "Anual",
        "url": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Leitura de perfil familiar e maturidade do entorno",
    },
    {
        "fonte": "Anatel Banda Larga Fixa",
        "dados": "Acessos e densidade de banda larga por municipio",
        "granularidade": "Municipal",
        "frequencia": "Mensal",
        "url": "https://www.anatel.gov.br/dadosabertos/PDA/Acessos/SCM/",
        "gratuita": True,
        "requer_key": False,
        "status_integracao": "Planejada",
        "uso_no_relatorio": "Proxy de infraestrutura digital e madurez urbana",
    },
]


def _resultado_seguro(futuro: concurrent.futures.Future, fallback: dict) -> dict:
    try:
        resultado = futuro.result()
        return resultado if isinstance(resultado, dict) else fallback
    except Exception:
        return fallback


def coletar_todos_dados(codigo_ibge: str, cidade: str, uf: str, tipologia: str) -> dict:
    """Coleta dados de todas as fontes em paralelo com fallbacks isolados."""

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        fut_ibge = executor.submit(get_dados_ibge, codigo_ibge)
        fut_bcb = executor.submit(get_dados_bcb, uf)
        fut_ipea = executor.submit(get_dados_ipea, codigo_ibge)
        fut_idhm = executor.submit(get_idhm, codigo_ibge)
        fut_trends = executor.submit(get_tendencia_busca, cidade, tipologia)
        fut_fipezap = executor.submit(get_dados_fipezap, cidade, uf)
        fut_rib = executor.submit(get_dados_rib, cidade, uf)

        dados_ibge = _resultado_seguro(fut_ibge, {"codigo_ibge": codigo_ibge})
        dados_bcb = _resultado_seguro(fut_bcb, {})
        dados_ipea = _resultado_seguro(fut_ipea, {})
        dados_idhm = _resultado_seguro(fut_idhm, {})
        dados_trends = _resultado_seguro(fut_trends, {})
        dados_fipezap = _resultado_seguro(fut_fipezap, {"disponivel": False})
        dados_rib = _resultado_seguro(fut_rib, {"disponivel": False})

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
            dados_fipezap.get("disponivel", False),
            dados_rib.get("disponivel", False),
        ]
    )
    qualidade_geral = fontes_ok / 7

    return {
        "ibge": dados_ibge,
        "bcb": dados_bcb,
        "ipea": dados_ipea,
        "idhm": dados_idhm,
        "trends": dados_trends,
        "fipezap": dados_fipezap,
        "rib": dados_rib,
        "qualidade_geral": qualidade_geral,
        "fontes_ativas": fontes_ok,
    }


def calcular_favorabilidade_mercado(
    dados_bcb: dict,
    dados_ipea: dict,
    dados_trends: dict,
    dados_fipezap: dict | None = None,
    dados_rib: dict | None = None,
) -> dict:
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

    dados_fipezap = dados_fipezap or {}
    if dados_fipezap.get("disponivel"):
        variacao_12m = dados_fipezap.get("variacao_12m", 0)
        if variacao_12m > 8:
            score += 1.0
        elif variacao_12m < 0:
            score -= 1.0

    dados_rib = dados_rib or {}
    if dados_rib.get("disponivel"):
        variacao_anual = dados_rib.get("variacao_anual_pct", 0)
        if variacao_anual > 10:
            score += 1.0
        elif variacao_anual < -5:
            score -= 1.0

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
