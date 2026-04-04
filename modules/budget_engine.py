"""Calculos de VGV, verba recomendada e cenarios de investimento."""

from __future__ import annotations

from config import TABELA_VERBA


def calcular_vgv(valor_unidade: float, volume_unidades: int) -> float:
    return valor_unidade * volume_unidades


def _faixa_score(score: float) -> str:
    if score <= 30:
        return "score_0_30"
    if score <= 50:
        return "score_31_50"
    if score <= 70:
        return "score_51_70"
    return "score_71_100"


def calcular_verba(
    vgv: float,
    score: float,
    nivel_investimento: int,
    tipologia: str,
    volume_unidades: int,
) -> dict:
    """Calcula percentual, verba total e cenarios a partir do score."""

    chave_tipologia = tipologia.strip().lower()
    faixa = _faixa_score(score)
    referencia = TABELA_VERBA[chave_tipologia][faixa]
    percentual = referencia["min"] + (
        (referencia["max"] - referencia["min"]) * (nivel_investimento - 1) / 4
    )
    verba_total = vgv * percentual
    custo_unidade = verba_total / volume_unidades

    cenarios = {}
    for nome, campo in (("conservador", "min"), ("base", "base"), ("agressivo", "max")):
        percentual_cenario = referencia[campo]
        verba_cenario = vgv * percentual_cenario
        cenarios[nome] = {
            "percentual": percentual_cenario,
            "verba_r$": verba_cenario,
            "custo_unidade": verba_cenario / volume_unidades,
        }

    return {
        "vgv": vgv,
        "percentual_verba": percentual,
        "verba_total_r$": verba_total,
        "custo_por_unidade_r$": custo_unidade,
        "cenarios": cenarios,
    }
