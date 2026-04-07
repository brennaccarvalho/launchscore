# Copyright (c) 2026 Brenna Carvalho. All rights reserved.
"""
Script de uso unico para popular data/idhm_municipios.csv com dados do IDHM
de todos os 5.570 municipios brasileiros.

Fonte: Ipeadata (IDHM — Atlas Brasil / PNUD/IPEA/FJP, Censo 2010)
       IBGE (lista de municipios com codigos e UF)

Como usar:
    cd launchscore
    python scripts/populate_idhm.py

O arquivo data/idhm_municipios.csv sera gerado/sobrescrito.
Tempo estimado: 30-60 segundos (duas requisicoes HTTP grandes).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

OUTPUT = Path("data/idhm_municipios.csv")
TIMEOUT = 30

# ---------------------------------------------------------------------------
# 1. Buscar lista de municipios do IBGE (codigo 7 digitos + nome + UF)
# ---------------------------------------------------------------------------

def _buscar_municipios_ibge() -> pd.DataFrame:
    print("Buscando lista de municipios no IBGE...")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    dados = resp.json()

    rows = []
    for m in dados:
        cod6 = str(m["id"])           # 6 digitos (sem digito verificador)
        cod7 = cod6 + "0"             # convenção Ipeadata usa codigo 7 digitos (cod6 + "0")
        nome = m["nome"]
        uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
        rows.append({"codmun7": int(cod7), "municipio": nome, "uf": uf})

    df = pd.DataFrame(rows)
    print(f"  {len(df)} municipios carregados.")
    return df


# ---------------------------------------------------------------------------
# 2. Buscar IDHM do Ipeadata (serie IDHM — codigo: ADH_IDHM)
# ---------------------------------------------------------------------------

def _buscar_idhm_ipeadata() -> pd.DataFrame:
    print("Buscando IDHM de todos os municipios no Ipeadata...")
    # Ipeadata OData — serie ADH_IDHM contem IDHM municipal (Censo 2010)
    url = (
        "http://www.ipeadata.gov.br/api/odata4/ValoresSerie"
        "?$filter=SERCODIGO eq 'ADH_IDHM'"
        "&$select=TERCODIGO,VALVALOR"
    )
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    valores = resp.json().get("value", [])

    rows = []
    for v in valores:
        cod = str(v.get("TERCODIGO", "")).strip()
        val = v.get("VALVALOR")
        if cod and val is not None:
            try:
                rows.append({"codmun7": int(cod), "IDHM": float(val)})
            except (ValueError, TypeError):
                pass

    df = pd.DataFrame(rows).drop_duplicates("codmun7")
    print(f"  {len(df)} registros de IDHM carregados.")
    return df


def _buscar_subindice_ipeadata(serie: str, coluna: str) -> pd.DataFrame:
    """Busca um subindice do IDHM (renda, longevidade, educacao)."""
    url = (
        f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie"
        f"?$filter=SERCODIGO eq '{serie}'"
        f"&$select=TERCODIGO,VALVALOR"
    )
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    valores = resp.json().get("value", [])
    rows = []
    for v in valores:
        cod = str(v.get("TERCODIGO", "")).strip()
        val = v.get("VALVALOR")
        if cod and val is not None:
            try:
                rows.append({"codmun7": int(cod), coluna: float(val)})
            except (ValueError, TypeError):
                pass
    return pd.DataFrame(rows).drop_duplicates("codmun7")


# ---------------------------------------------------------------------------
# 3. Montar e salvar CSV
# ---------------------------------------------------------------------------

def main() -> None:
    df_mun = _buscar_municipios_ibge()
    df_idhm = _buscar_idhm_ipeadata()

    print("Buscando subindices IDHM_Renda, IDHM_Long, IDHM_E...")
    try:
        df_renda = _buscar_subindice_ipeadata("ADH_IDHM_R", "IDHM_Renda")
        df_long  = _buscar_subindice_ipeadata("ADH_IDHM_L", "IDHM_Long")
        df_educ  = _buscar_subindice_ipeadata("ADH_IDHM_E", "IDHM_E")
    except Exception as e:
        print(f"  Aviso: nao foi possivel carregar subindices ({e}). Continuando sem eles.")
        df_renda = df_long = df_educ = pd.DataFrame(columns=["codmun7"])

    df = (
        df_mun
        .merge(df_idhm, on="codmun7", how="left")
        .merge(df_renda, on="codmun7", how="left")
        .merge(df_long,  on="codmun7", how="left")
        .merge(df_educ,  on="codmun7", how="left")
    )

    # Ranking por IDHM decrescente (1 = maior IDHM)
    df = df.sort_values("IDHM", ascending=False).reset_index(drop=True)
    df["ranking"] = df["IDHM"].rank(ascending=False, method="min").astype("Int64")

    # Reordenar colunas na ordem esperada por atlas_brasil.py
    cols = ["codmun7", "municipio", "uf", "IDHM", "IDHM_Renda", "IDHM_Long", "IDHM_E", "ranking"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8")

    total = len(df)
    com_idhm = df["IDHM"].notna().sum()
    print(f"\nConcluido! {OUTPUT} gerado.")
    print(f"  Total de municipios : {total}")
    print(f"  Com IDHM preenchido : {com_idhm} ({com_idhm/total*100:.1f}%)")
    sem = total - com_idhm
    if sem:
        print(f"  Sem IDHM (fallback) : {sem} — atlas_brasil.py usara mediana nacional para esses")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"\nErro de rede: {e}")
        print("Verifique sua conexao e tente novamente.")
        sys.exit(1)
