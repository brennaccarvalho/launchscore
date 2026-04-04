"""Calculos de VGV, verba recomendada, cenarios e benchmarks."""

from __future__ import annotations

from config import BENCHMARKS_SETOR, BENCHMARK_CPL, TABELA_VERBA, TAXA_CONVERSAO


def calcular_vgv(valor_unidade: float, volume_unidades: int) -> float:
    return valor_unidade * volume_unidades


def faixa_score(score: float) -> str:
    if score <= 30:
        return "score_0_30"
    if score <= 50:
        return "score_31_50"
    if score <= 70:
        return "score_51_70"
    return "score_71_100"


def classificar_percentual_vs_benchmark(percentual: float, tipologia: str) -> str:
    media = BENCHMARKS_SETOR[tipologia]["media_pct_vgv"]
    if percentual < media * 0.9:
        return "Abaixo do benchmark"
    if percentual > media * 1.1:
        return "Acima do benchmark"
    return "Dentro do benchmark"


def _texto_resultado(cenario: str) -> str:
    if cenario == "conservador":
        return "Ritmo de vendas mais lento. Indicado para fases iniciais ou periodos de menor demanda."
    if cenario == "agressivo":
        return "Maxima velocidade de vendas. Indicado para lancamentos em mercados competitivos ou com prazo de entrega curto."
    return "Equilibrio entre investimento e resultado. Recomendado para a maioria dos lancamentos."


def calcular_verba(
    vgv: float,
    score: float,
    tipologia: str,
    volume_unidades: int,
    valor_unidade: float,
) -> dict:
    """Calcula cenarios financeiros completos a partir do score."""

    chave_tipologia = tipologia.strip().lower()
    faixa = faixa_score(score)
    referencia = TABELA_VERBA[chave_tipologia][faixa]
    benchmark_setor = BENCHMARKS_SETOR[chave_tipologia]
    taxa_conversao = TAXA_CONVERSAO[faixa]

    cenarios = {}
    for nome, campo in (("conservador", "min"), ("base", "base"), ("agressivo", "max")):
        percentual = referencia[campo]
        verba = vgv * percentual
        custo_unidade = verba / volume_unidades
        cpl = BENCHMARK_CPL[chave_tipologia][nome]
        leads = verba / cpl if cpl else 0.0
        vendas = leads * taxa_conversao
        receita = vendas * valor_unidade
        roas = receita / verba if verba else 0.0
        cenarios[nome] = {
            "percentual": percentual,
            "verba_r$": verba,
            "custo_unidade": custo_unidade,
            "leads_estimados": leads,
            "cpl_estimado": cpl,
            "vendas_estimadas": vendas,
            "receita_estimada": receita,
            "roas": roas,
            "resultado_esperado": _texto_resultado(nome),
            "benchmark_comparacao": classificar_percentual_vs_benchmark(percentual, chave_tipologia),
        }

    base = cenarios["base"]
    return {
        "vgv": vgv,
        "percentual_verba": base["percentual"],
        "verba_total_r$": base["verba_r$"],
        "custo_por_unidade_r$": base["custo_unidade"],
        "faixa_score": faixa,
        "taxa_conversao": taxa_conversao,
        "benchmark_setor": benchmark_setor,
        "cenarios": cenarios,
    }
