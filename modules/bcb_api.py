# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.
# Use of this service is subject to proprietary restrictions. Reverse engineering, scraping, or competitive usage is strictly prohibited.

"""Integracao com series do Banco Central (BCB/SGS)."""

from __future__ import annotations

import requests
import streamlit as st

BCB_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados/ultimos/1?formato=json"
BCB_ODATA_BASE = "https://olinda.bcb.gov.br/olinda/servico/MercadoImobiliario/versao/v1/odata/mercadoimobiliario"
TIMEOUT = 6

SERIES_BCB = {
    "selic": {"codigo": 432, "label": "Taxa Selic (% a.a.)", "formato": "pct"},
    "juros_imobiliario": {"codigo": 20772, "label": "Juros Financiamento Imobiliario", "formato": "pct"},
    "concessoes_credito": {"codigo": 20704, "label": "Concessoes Credito Imobiliario", "formato": "bilhoes"},
    "ivg_r": {"codigo": 21340, "label": "Indice Valorizacao Imoveis (IVG-R)", "formato": "indice"},
    "incc": {"codigo": 192, "label": "INCC-DI (Custo Construcao)", "formato": "pct"},
    "unidades_financiadas": {"codigo": 20698, "label": "Unidades Financiadas SBPE (mensal)", "formato": "unidades"},
    "ticket_medio_financiado": {"codigo": 20703, "label": "Valor Medio Financiado por Unidade", "formato": "reais"},
    "inadimplencia_imobiliaria": {"codigo": 21082, "label": "Inadimplencia Credito Imobiliario", "formato": "pct"},
    "ipca_12m": {"codigo": 13522, "label": "IPCA acumulado 12 meses", "formato": "pct"},
    "igpm_12m": {"codigo": 189, "label": "IGP-M acumulado 12 meses", "formato": "pct"},
}


def _resultado_indisponivel(label: str, formato: str, fonte: str = "indisponivel") -> dict:
    return {
        "valor": None,
        "data": None,
        "label": label,
        "formato": formato,
        "fonte": fonte,
    }


def _buscar_serie_sgs(config: dict) -> dict:
    try:
        resp = requests.get(BCB_BASE.format(config["codigo"]), timeout=TIMEOUT)
        resp.raise_for_status()
        dados = resp.json()
        ultimo = dados[-1]
        valor = float(str(ultimo["valor"]).replace(",", "."))
        if config["formato"] == "bilhoes":
            valor /= 1_000
        return {
            "valor": valor,
            "data": ultimo.get("data"),
            "label": config["label"],
            "formato": config["formato"],
            "fonte": "BCB/SGS",
        }
    except Exception:
        return _resultado_indisponivel(config["label"], config["formato"])


def _buscar_odata_info(info: str) -> dict | None:
    filtro = f"$filter=Info eq '{info}'&$orderby=Data desc&$top=1"
    resp = requests.get(f"{BCB_ODATA_BASE}?{filtro}", timeout=TIMEOUT)
    resp.raise_for_status()
    dados = resp.json().get("value", [])
    return dados[0] if dados else None


def _buscar_mercado_imobiliario_uf(uf: str | None) -> dict:
    if not uf:
        return {
            "disponivel": False,
            "motivo": "UF nao informada para benchmark estadual.",
            "fonte": "BCB / Mercado Imobiliario por UF",
        }

    uf = uf.lower()
    info_map = {
        "valor_sfh": f"credito_contratacao_contratado_pf_sfh_{uf}",
        "valor_fgts": f"credito_contratacao_contratado_pf_fgts_{uf}",
        "ltv_sfh": f"credito_contratacao_ltv_pf_sfh_{uf}",
        "ltv_fgts": f"credito_contratacao_ltv_pf_fgts_{uf}",
        "imoveis_apartamento": f"imoveis_tipo_apartamento_{uf}",
        "imoveis_casa": f"imoveis_tipo_casa_{uf}",
        "valor_compra": f"imoveis_valor_compra_{uf}",
    }
    try:
        dados = {chave: _buscar_odata_info(info) for chave, info in info_map.items()}
        valor_sfh = float(dados["valor_sfh"]["Valor"]) if dados["valor_sfh"] else 0.0
        valor_fgts = float(dados["valor_fgts"]["Valor"]) if dados["valor_fgts"] else 0.0
        total_valor = valor_sfh + valor_fgts
        unidades = int(float(dados["imoveis_apartamento"]["Valor"])) + int(float(dados["imoveis_casa"]["Valor"])) if dados["imoveis_apartamento"] and dados["imoveis_casa"] else None
        ticket = (total_valor / unidades) if unidades else None
        ltv_pesado = None
        if total_valor > 0:
            ltv_sfh = float(dados["ltv_sfh"]["Valor"]) if dados["ltv_sfh"] else 0.0
            ltv_fgts = float(dados["ltv_fgts"]["Valor"]) if dados["ltv_fgts"] else 0.0
            ltv_pesado = ((valor_sfh * ltv_sfh) + (valor_fgts * ltv_fgts)) / total_valor

        referencias = [item["Data"] for item in dados.values() if item and item.get("Data")]
        return {
            "disponivel": any(item is not None for item in dados.values()),
            "uf": uf.upper(),
            "data_referencia": max(referencias) if referencias else None,
            "unidades_financiadas": unidades,
            "valor_financiado": total_valor if total_valor > 0 else None,
            "ticket_medio_financiado": ticket,
            "ltv_medio": ltv_pesado,
            "valor_compra_medio": float(dados["valor_compra"]["Valor"]) if dados["valor_compra"] else None,
            "fonte": "BCB / Mercado Imobiliario por UF",
            "detalhe": "Benchmark estadual composto por contratacoes PF SFH/FGTS e tipologias de imoveis financiados.",
        }
    except Exception as exc:
        return {
            "disponivel": False,
            "uf": uf.upper(),
            "motivo": f"Falha ao consultar benchmark estadual: {exc}",
            "fonte": "BCB / Mercado Imobiliario por UF",
        }


@st.cache_data(ttl=3600)
def get_dados_bcb(uf: str | None = None) -> dict:
    """Busca a leitura mais recente das series BCB/SGS e benchmark estadual."""

    resultados: dict[str, dict] = {}
    for chave, config in SERIES_BCB.items():
        resultados[chave] = _buscar_serie_sgs(config)
    resultados["mercado_imobiliario_uf"] = _buscar_mercado_imobiliario_uf(uf)
    return resultados
