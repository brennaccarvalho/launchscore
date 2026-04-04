"""Integracao com series do Banco Central (BCB/SGS)."""

from __future__ import annotations

import requests
import streamlit as st

BCB_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados/ultimos/1?formato=json"
TIMEOUT = 6

SERIES_BCB = {
    "selic": {"codigo": 432, "label": "Taxa Selic (% a.a.)", "formato": "pct"},
    "juros_imobiliario": {"codigo": 20772, "label": "Juros Financiamento Imobiliario", "formato": "pct"},
    "concessoes_credito": {"codigo": 20704, "label": "Concessoes Credito Imobiliario", "formato": "bilhoes"},
    "ivg_r": {"codigo": 21340, "label": "Indice Valorizacao Imoveis (IVG-R)", "formato": "indice"},
    "incc": {"codigo": 192, "label": "INCC-DI (Custo Construcao)", "formato": "pct"},
}


@st.cache_data(ttl=3600)
def get_dados_bcb() -> dict:
    """Busca a leitura mais recente das series BCB/SGS."""

    resultados: dict[str, dict] = {}
    for chave, config in SERIES_BCB.items():
        try:
            resp = requests.get(BCB_BASE.format(config["codigo"]), timeout=TIMEOUT)
            resp.raise_for_status()
            dados = resp.json()
            ultimo = dados[-1]
            valor = float(str(ultimo["valor"]).replace(",", "."))
            if config["formato"] == "bilhoes":
                valor /= 1_000
            resultados[chave] = {
                "valor": valor,
                "data": ultimo.get("data"),
                "label": config["label"],
                "formato": config["formato"],
                "fonte": "BCB/SGS",
            }
        except Exception:
            resultados[chave] = {
                "valor": None,
                "data": None,
                "label": config["label"],
                "formato": config["formato"],
                "fonte": "indisponivel",
            }
    return resultados
