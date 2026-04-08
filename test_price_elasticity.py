# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

"""Testes para o simulador de elasticidade de preco."""

from modules.price_elasticity import calcular_curva_elasticidade


def test_curva_elasticidade_retorna_colunas_essenciais():
    resultado = calcular_curva_elasticidade(
        preco_base=500000,
        vendas_base=20,
        estoque_total=120,
        elasticidade=1.4,
        desconto_max_pct=0.15,
        acrescimo_max_pct=0.1,
        custo_incentivo_pct=0.02,
        eficiencia_incentivo=0.5,
    )

    curva = resultado["curva"]
    assert {"preco_tabela", "vendas_estimadas", "receita_liquida", "sellout_pct"} <= set(curva.columns)
    assert resultado["resumo"]["melhor_receita"] > 0


def test_desconto_eleva_demanda_quando_elasticidade_positiva():
    resultado = calcular_curva_elasticidade(
        preco_base=500000,
        vendas_base=20,
        estoque_total=120,
        elasticidade=1.5,
        desconto_max_pct=0.1,
        acrescimo_max_pct=0.0,
        custo_incentivo_pct=0.0,
        eficiencia_incentivo=1.0,
    )
    curva = resultado["curva"]
    base = curva.iloc[(curva["variacao_pct"] - 0).abs().argsort()[:1]].iloc[0]
    desconto = curva.iloc[0]

    assert desconto["vendas_estimadas"] > base["vendas_estimadas"]
