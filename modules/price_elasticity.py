"""Simulador simples de elasticidade de preco para o LaunchScore."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calcular_curva_elasticidade(
    *,
    preco_base: float,
    vendas_base: float,
    estoque_total: int,
    elasticidade: float,
    desconto_max_pct: float,
    acrescimo_max_pct: float,
    custo_incentivo_pct: float = 0.0,
    eficiencia_incentivo: float = 1.0,
    passo_pct: float = 0.01,
) -> dict:
    """Calcula curva de demanda, receita e velocidade por nivel de preco."""
    if preco_base <= 0:
        raise ValueError("O preco base deve ser maior que zero.")
    if vendas_base <= 0:
        raise ValueError("As vendas base devem ser maiores que zero.")
    if estoque_total <= 0:
        raise ValueError("O estoque total deve ser maior que zero.")
    if passo_pct <= 0:
        raise ValueError("O passo percentual deve ser maior que zero.")

    variacao = np.arange(-desconto_max_pct, acrescimo_max_pct + passo_pct, passo_pct, dtype=float)
    preco_tabela = preco_base * (1 + variacao)

    incentivo_pct = np.where(variacao < 0, custo_incentivo_pct, 0.0)
    desconto_pct = np.where(variacao < 0, -variacao, 0.0)
    estimulo_percebido = desconto_pct + incentivo_pct * eficiencia_incentivo
    preco_percebido = preco_base * (1 - estimulo_percebido)
    preco_percebido = np.maximum(preco_percebido, preco_base * 0.05)

    fator_demanda = (preco_base / preco_percebido) ** elasticidade
    vendas_estimadas = np.minimum(vendas_base * fator_demanda, estoque_total)
    receita_bruta = preco_tabela * vendas_estimadas
    custo_incentivo = preco_base * incentivo_pct * vendas_estimadas
    receita_liquida = receita_bruta - custo_incentivo

    curva = pd.DataFrame(
        {
            "variacao_pct": variacao,
            "desconto_pct": desconto_pct,
            "acrescimo_pct": np.where(variacao > 0, variacao, 0.0),
            "incentivo_pct": incentivo_pct,
            "preco_tabela": preco_tabela,
            "preco_percebido": preco_percebido,
            "fator_demanda": fator_demanda,
            "vendas_estimadas": vendas_estimadas,
            "receita_bruta": receita_bruta,
            "custo_incentivo": custo_incentivo,
            "receita_liquida": receita_liquida,
            "sellout_pct": vendas_estimadas / estoque_total,
        }
    )

    idx_base = int(np.argmin(np.abs(curva["variacao_pct"].to_numpy())))
    idx_receita = int(curva["receita_liquida"].idxmax())
    idx_volume = int(curva["vendas_estimadas"].idxmax())

    resumo = {
        "preco_base": float(curva.loc[idx_base, "preco_tabela"]),
        "vendas_base": float(curva.loc[idx_base, "vendas_estimadas"]),
        "receita_base": float(curva.loc[idx_base, "receita_liquida"]),
        "melhor_preco_receita": float(curva.loc[idx_receita, "preco_tabela"]),
        "melhor_variacao_receita": float(curva.loc[idx_receita, "variacao_pct"]),
        "melhor_receita": float(curva.loc[idx_receita, "receita_liquida"]),
        "melhor_preco_volume": float(curva.loc[idx_volume, "preco_tabela"]),
        "melhor_variacao_volume": float(curva.loc[idx_volume, "variacao_pct"]),
        "melhor_volume": float(curva.loc[idx_volume, "vendas_estimadas"]),
    }

    return {"curva": curva, "resumo": resumo}
