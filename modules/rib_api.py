# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.
# Use of this service is subject to proprietary restrictions. Reverse engineering, scraping, or competitive usage is strictly prohibited.

"""Leitura local do histórico do Portal Estatístico Registral."""

from __future__ import annotations

from pathlib import Path
import unicodedata

import pandas as pd
import streamlit as st


RIB_CSV_PATH = Path("data/rib_transacoes.csv")


def _normalizar_texto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").strip().lower())
    return "".join(char for char in texto if not unicodedata.combining(char))


def _carregar_csv_rib() -> pd.DataFrame:
    if not RIB_CSV_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(RIB_CSV_PATH)
    except Exception:
        return pd.DataFrame()
    if "municipio" in df.columns:
        df["municipio_normalizado"] = df["municipio"].map(_normalizar_texto)
    if "ano_mes" in df.columns:
        df["ano_mes"] = pd.to_datetime(df["ano_mes"], errors="coerce")
    for coluna in ("compra_venda", "incorporacoes", "loteamentos"):
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)
    return df.dropna(subset=["municipio", "ano_mes"]).copy()


@st.cache_data(ttl=86400)
def get_dados_rib(municipio: str, uf: str | None = None) -> dict:
    df = _carregar_csv_rib()
    resultado_padrao = {
        "disponivel": False,
        "motivo": "Município não coberto pela base local do Portal Estatístico Registral.",
        "fonte": "RIB — Portal Estatístico Registral",
        "url": "https://www.registrodeimoveis.org.br/portal-estatistico-registral",
    }

    if df.empty:
        return {**resultado_padrao, "motivo": "Arquivo local do RIB indisponível ou inválido."}

    municipio_norm = _normalizar_texto(municipio)
    df_mun = df[df["municipio_normalizado"] == municipio_norm].copy()
    if uf and "uf" in df_mun.columns:
        df_mun = df_mun[df_mun["uf"].astype(str).str.upper() == uf.upper()]
    if df_mun.empty:
        return resultado_padrao

    df_mun = df_mun.sort_values("ano_mes")
    ultimo = df_mun.iloc[-1]
    anterior_12m = df_mun.iloc[-13] if len(df_mun) >= 13 else df_mun.iloc[0]
    compra_venda_atual = int(ultimo.get("compra_venda", 0))
    compra_venda_12m_ant = int(anterior_12m.get("compra_venda", 0))
    variacao = ((compra_venda_atual - compra_venda_12m_ant) / max(compra_venda_12m_ant, 1)) * 100
    media_12m = float(df_mun.tail(12)["compra_venda"].mean()) if not df_mun.empty else 0.0
    tendencia = "alta" if variacao > 5 else "queda" if variacao < -5 else "estavel"
    return {
        "disponivel": True,
        "municipio": ultimo["municipio"],
        "uf": ultimo.get("uf"),
        "data_referencia": ultimo["ano_mes"].strftime("%Y-%m"),
        "compra_venda_mensal": compra_venda_atual,
        "media_mensal_12m": round(media_12m, 0),
        "variacao_anual_pct": round(variacao, 1),
        "tendencia": tendencia,
        "incorporacoes": int(ultimo.get("incorporacoes", 0)),
        "loteamentos": int(ultimo.get("loteamentos", 0)),
        "fonte": "RIB — Portal Estatístico Registral",
        "url": "https://www.registrodeimoveis.org.br/portal-estatistico-registral",
    }
