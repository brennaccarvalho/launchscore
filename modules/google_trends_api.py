"""Integracao opcional com Google Trends via pytrends."""

from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from pytrends.request import TrendReq
except Exception:  # pragma: no cover - depende de biblioteca opcional
    TrendReq = None


@st.cache_data(ttl=7200)
def get_tendencia_busca(cidade: str, tipologia: str) -> dict:
    """Busca tendencia de interesse por imoveis na cidade nos ultimos 12 meses."""

    if TrendReq is None:
        return {
            "tendencia": "indisponivel",
            "score_interesse": 50,
            "serie_interesse": [],
            "fonte": "Google Trends indisponivel (pytrends nao instalado)",
        }

    try:
        pytrends = TrendReq(hl="pt-BR", tz=-180, timeout=(8, 25))
        termos = {
            "Lotes": [f"lotes {cidade}", f"terrenos {cidade}", "comprar lote"],
            "Apartamentos": [f"apartamentos {cidade}", f"imoveis {cidade}", "comprar apartamento"],
        }
        kw_list = termos.get(tipologia, [f"imoveis {cidade}"])[:3]
        pytrends.build_payload(kw_list, timeframe="today 12-m", geo="BR")
        df = pytrends.interest_over_time()
        if df.empty:
            return {
                "tendencia": "indisponivel",
                "score_interesse": 50,
                "serie_interesse": [],
                "fonte": "Google Trends (pytrends)",
            }

        serie = df[kw_list[0]].astype(float)
        tendencia = serie.iloc[-4:].mean() - serie.iloc[:4].mean()
        serie_saida = [{"data": idx.strftime("%Y-%m-%d"), "interesse": float(valor)} for idx, valor in serie.items()]
        return {
            "media_interesse_12m": int(serie.mean()),
            "tendencia_recente": "crescendo" if tendencia > 5 else "estavel" if tendencia > -5 else "caindo",
            "score_interesse": int(serie.mean()),
            "serie_interesse": serie_saida,
            "termos": kw_list,
            "fonte": "Google Trends (pytrends)",
        }
    except Exception as exc:  # pragma: no cover - depende de servico externo
        return {
            "tendencia": "indisponivel",
            "score_interesse": 50,
            "serie_interesse": [],
            "erro": str(exc),
            "fonte": "Google Trends (pytrends)",
        }
