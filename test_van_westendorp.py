# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

"""Testes para o simulador de preco ideal."""

import pandas as pd
import pytest

from modules.van_westendorp import calcular_van_westendorp, normalizar_dataframe_pesquisa


def _amostra_base() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"too_cheap": 10, "cheap": 20, "expensive": 30, "too_expensive": 40, "pi_cheap": 1, "pi_expensive": 2, "include": 1},
            {"too_cheap": 15, "cheap": 25, "expensive": 40, "too_expensive": 55, "pi_cheap": 1, "pi_expensive": 3, "include": 1},
            {"too_cheap": 25, "cheap": 30, "expensive": 35, "too_expensive": 40, "pi_cheap": 3, "pi_expensive": 3, "include": 1},
            {"too_cheap": 5, "cheap": 15, "expensive": 25, "too_expensive": 35, "pi_cheap": 2, "pi_expensive": 4, "include": 1},
        ]
    )


def test_normalizar_dataframe_rejeita_ordem_invalida():
    dados = _amostra_base()
    dados.loc[0, "cheap"] = 9

    with pytest.raises(ValueError, match="ordem"):
        normalizar_dataframe_pesquisa(dados)


def test_calcular_van_westendorp_retorna_resumo_e_curvas():
    resultado = calcular_van_westendorp(_amostra_base(), price_step=5)

    assert resultado["resumo"]["n_respostas"] == 4
    assert {"price", "too_cheap", "cheap", "expensive", "too_expensive", "purchase_intent", "reach", "revenue_index"} <= set(
        resultado["curvas"].columns
    )
    assert resultado["resumo"]["preco_otimo_receita"] >= 0
    assert resultado["resumo"]["preco_otimo_classico"] is not None
    assert resultado["resumo"]["faixa_aceitavel_min"] is not None


def test_curvas_classicas_respeitam_monotonicidade():
    curvas = calcular_van_westendorp(_amostra_base(), price_step=5)["curvas"]

    assert curvas["too_cheap"].is_monotonic_decreasing
    assert curvas["cheap"].is_monotonic_decreasing
    assert curvas["expensive"].is_monotonic_increasing
    assert curvas["too_expensive"].is_monotonic_increasing
