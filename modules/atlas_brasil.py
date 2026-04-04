"""Acesso ao IDHM via cache local e tabela estatica."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ATLAS_CACHE = Path("data/atlas_brasil.parquet")
ATLAS_STATIC = Path("data/idhm_municipios.csv")
FALLBACK_IDHM = 0.699


@st.cache_data(ttl=604800)
def get_idhm(codigo_ibge: str) -> dict:
    """Retorna IDHM e subindices para o municipio."""

    df = _carregar_cache_atlas()
    if df.empty:
        df = _carregar_tabela_estatica_idhm()

    if df.empty:
        return {"idhm": FALLBACK_IDHM, "fonte": "mediana_nacional"}

    municipio = df[df["codmun7"] == int(codigo_ibge)]
    if municipio.empty:
        return {"idhm": FALLBACK_IDHM, "fonte": "mediana_nacional"}

    row = municipio.iloc[0]
    ranking = row.get("ranking")
    return {
        "idhm": float(row.get("IDHM", FALLBACK_IDHM)),
        "idhm_renda": float(row.get("IDHM_Renda", 0.0)),
        "idhm_long": float(row.get("IDHM_Long", 0.0)),
        "idhm_educ": float(row.get("IDHM_E", 0.0)),
        "ranking_nacional": int(ranking) if pd.notna(ranking) else 0,
        "municipio": row.get("municipio", ""),
        "uf": row.get("uf", ""),
        "fonte": "Atlas Brasil — PNUD/IPEA/FJP (Censo 2010)",
    }


def _carregar_cache_atlas() -> pd.DataFrame:
    if not ATLAS_CACHE.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(ATLAS_CACHE)
    except Exception:
        return pd.DataFrame()


def _carregar_tabela_estatica_idhm() -> pd.DataFrame:
    """Carrega a tabela estatica versionada no repositorio."""

    if not ATLAS_STATIC.exists():
        return pd.DataFrame(columns=["codmun7", "municipio", "uf", "IDHM", "IDHM_Renda", "IDHM_Long", "IDHM_E"])
    try:
        df = pd.read_csv(ATLAS_STATIC)
    except Exception:
        return pd.DataFrame(columns=["codmun7", "municipio", "uf", "IDHM", "IDHM_Renda", "IDHM_Long", "IDHM_E"])
    if "codmun7" in df.columns:
        df["codmun7"] = pd.to_numeric(df["codmun7"], errors="coerce").astype("Int64")
    return df.dropna(subset=["codmun7"]).copy()
