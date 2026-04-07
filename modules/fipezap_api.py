# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.
# Use of this service is subject to proprietary restrictions. Reverse engineering, scraping, or competitive usage is strictly prohibited.

"""Integra o Excel oficial de series historicas do FipeZap."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import unicodedata

import pandas as pd
import requests
import streamlit as st


FIPEZAP_EXCEL_URL = "https://downloads.fipe.org.br/indices/fipezap/fipezap-serieshistoricas.xlsx"
FIPEZAP_CACHE_PATH = Path("data/fipezap_cache.parquet")
FIPEZAP_CIDADES_PATH = Path("data/fipezap_cidades.json")
TIMEOUT = 30
META_SHEETS = {"Resumo", "Aux", "Índice FipeZAP"}


def _normalizar_texto(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").strip().lower())
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.replace(" - ", " ")
    return " ".join(texto.split())


def _coluna_equivale(coluna: tuple, alvo: tuple[str, ...]) -> bool:
    atual = tuple(_normalizar_texto(parte) for parte in coluna)
    esperado = tuple(_normalizar_texto(parte) for parte in alvo)
    return atual == esperado


def _achar_coluna(df: pd.DataFrame, alvo: tuple[str, ...]) -> tuple | None:
    for coluna in df.columns:
        if isinstance(coluna, tuple) and _coluna_equivale(coluna, alvo):
            return coluna
    return None


@st.cache_data(ttl=604800)
def carregar_mapeamento_fipezap() -> list[dict]:
    if not FIPEZAP_CIDADES_PATH.exists():
        return []
    try:
        return json.loads(FIPEZAP_CIDADES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _nome_fipezap_por_cidade(cidade: str, uf: str | None = None) -> dict | None:
    cidade_norm = _normalizar_texto(cidade)
    uf_norm = (uf or "").strip().upper()
    for item in carregar_mapeamento_fipezap():
        if item.get("cidade_normalizada") != cidade_norm:
            continue
        if uf_norm and item.get("uf") != uf_norm:
            continue
        return item
    return None


def _carregar_cache_local() -> pd.DataFrame:
    if not FIPEZAP_CACHE_PATH.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(FIPEZAP_CACHE_PATH)
    except Exception:
        return pd.DataFrame()


def _parsear_planilha_fipezap(conteudo: bytes) -> pd.DataFrame:
    excel = pd.ExcelFile(BytesIO(conteudo))
    frames: list[pd.DataFrame] = []
    for nome_sheet in excel.sheet_names:
        if nome_sheet in META_SHEETS:
            continue
        df_sheet = pd.read_excel(BytesIO(conteudo), sheet_name=nome_sheet, header=[0, 1, 2, 3])
        coluna_data = _achar_coluna(
            df_sheet,
            ("", nome_sheet, "", "Data"),
        ) or _achar_coluna(df_sheet, ("Unnamed: 0_level_0", nome_sheet, "Unnamed: 1_level_2", "Data"))
        coluna_preco = _achar_coluna(df_sheet, ("Imóveis residenciais", "Venda", "Preço médio (R$/m²)", "Total"))
        coluna_var_mensal = _achar_coluna(df_sheet, ("Imóveis residenciais", "Venda", "Var. mensal (%)", "Total"))
        coluna_var_12m = _achar_coluna(df_sheet, ("Imóveis residenciais", "Venda", "Var. em 12 meses (%)", "Total"))

        if not coluna_data or not coluna_preco:
            continue

        df_cidade = pd.DataFrame(
            {
                "data": pd.to_datetime(df_sheet[coluna_data], errors="coerce"),
                "cidade": nome_sheet,
                "preco_m2": pd.to_numeric(df_sheet[coluna_preco], errors="coerce"),
                "variacao_mensal": pd.to_numeric(df_sheet[coluna_var_mensal], errors="coerce") if coluna_var_mensal else None,
                "variacao_12m": pd.to_numeric(df_sheet[coluna_var_12m], errors="coerce") if coluna_var_12m else None,
            }
        )
        df_cidade = df_cidade.dropna(subset=["data", "preco_m2"]).copy()
        if df_cidade.empty:
            continue
        df_cidade["cidade_normalizada"] = _normalizar_texto(nome_sheet)
        frames.append(df_cidade)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["cidade", "data"]).reset_index(drop=True)
    if df["variacao_mensal"].isna().all():
        df["variacao_mensal"] = df.groupby("cidade")["preco_m2"].pct_change() * 100
    if df["variacao_12m"].isna().all():
        df["variacao_12m"] = df.groupby("cidade")["preco_m2"].pct_change(12) * 100
    return df


@st.cache_data(ttl=604800)
def baixar_e_parsear_fipezap() -> pd.DataFrame:
    try:
        resposta = requests.get(FIPEZAP_EXCEL_URL, timeout=TIMEOUT)
        resposta.raise_for_status()
        df = _parsear_planilha_fipezap(resposta.content)
        if not df.empty:
            FIPEZAP_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(FIPEZAP_CACHE_PATH, index=False)
            return df
    except Exception:
        pass
    return _carregar_cache_local()


@st.cache_data(ttl=604800)
def get_dados_fipezap(cidade: str, uf: str | None = None) -> dict:
    registro = _nome_fipezap_por_cidade(cidade, uf)
    resultado_padrao = {
        "disponivel": False,
        "cidade_cobertura": False,
        "motivo": "Cidade não coberta pelo FipeZap para venda residencial.",
        "fonte": "FipeZap / FIPE",
        "url": "https://www.fipe.org.br/pt-br/indices/fipezap/",
    }

    if not registro:
        return resultado_padrao

    df = baixar_e_parsear_fipezap()
    if df.empty:
        return {
            **resultado_padrao,
            "cidade_cobertura": True,
            "motivo": "Falha ao carregar a série histórica do FipeZap.",
        }

    df_cidade = df[df["cidade_normalizada"] == registro["cidade_normalizada"]].sort_values("data")
    if df_cidade.empty:
        return {
            **resultado_padrao,
            "cidade_cobertura": True,
            "motivo": "Cidade mapeada, mas sem série recente disponível.",
        }

    ultimo = df_cidade.iloc[-1]
    penultimo = df_cidade.iloc[-2] if len(df_cidade) > 1 else ultimo
    variacao_mensal = float(ultimo.get("variacao_mensal") or 0.0)
    variacao_12m = float(ultimo.get("variacao_12m") or 0.0)
    return {
        "disponivel": True,
        "cidade_cobertura": True,
        "cidade_fipezap": registro["cidade_fipezap"],
        "cidade_normalizada": registro["cidade_normalizada"],
        "ibge": registro.get("codigo_ibge"),
        "uf": registro.get("uf"),
        "data_referencia": ultimo["data"].strftime("%m/%Y"),
        "preco_medio_m2": round(float(ultimo["preco_m2"]), 2),
        "variacao_mensal": round(variacao_mensal, 2),
        "variacao_12m": round(variacao_12m, 2),
        "tendencia": "alta" if variacao_mensal >= 0 else "queda",
        "acelerando": variacao_mensal > float(penultimo.get("variacao_mensal") or 0.0),
        "fonte": "FipeZap / FIPE — Série histórica residencial",
        "url": "https://www.fipe.org.br/pt-br/indices/fipezap/",
    }
