# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.
# Use of this service is subject to proprietary restrictions. Reverse engineering, scraping, or competitive usage is strictly prohibited.

"""Integracao com Ipeadata."""

from __future__ import annotations

import requests
import streamlit as st

IPEA_BASE = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{serie}')/Valores"
TIMEOUT = 8
SERIES_IPEA = {
    "pib_percapita": "PIB_PERCAP",
    "gini": "GINI_MUNC",
    "rendimento": "PNAD_RMTOT",
    "desemprego": "PNAD12_DESOC",
}


@st.cache_data(ttl=86400)
def get_dados_ipea(codigo_ibge: str) -> dict:
    """Busca a observacao mais recente disponivel no IPEA para o municipio."""

    resultados: dict[str, dict] = {}
    for chave, codigo_serie in SERIES_IPEA.items():
        try:
            params = {
                "$filter": f"TERCODIGO eq '{codigo_ibge}'",
                "$orderby": "VALDATA desc",
                "$top": 1,
            }
            resp = requests.get(IPEA_BASE.format(serie=codigo_serie), params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            dados = resp.json().get("value", [])
            if dados:
                resultados[chave] = {
                    "valor": dados[0].get("VALVALOR"),
                    "data": dados[0].get("VALDATA"),
                    "fonte": "Ipeadata/IPEA",
                }
            else:
                resultados[chave] = {"valor": None, "data": None, "fonte": "nao disponivel para municipio"}
        except Exception:
            resultados[chave] = {"valor": None, "data": None, "fonte": "erro na requisicao"}
    return resultados
