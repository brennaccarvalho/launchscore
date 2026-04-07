# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

"""Calculos de VGV, verba recomendada, cenarios e benchmarks."""

from __future__ import annotations

import unicodedata

from config import BENCHMARKS_SETOR, BENCHMARK_CPL, CAPITAIS_ESTADUAIS_NORM, TABELA_VERBA, TAXA_CONVERSAO


def _normalizar_nome(nome: str) -> str:
    """Remove acentos e converte para minusculo para comparacao de nomes."""
    return (
        unicodedata.normalize("NFKD", str(nome))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


def calcular_multiplicador_cpl(municipio: str, uf: str) -> float:
    """Retorna multiplicador de CPL com base no porte da praca.

    - SP/RJ capital: 1.5x (mercados digitais mais competitivos do pais)
    - Outras capitais estaduais: 1.3x (leilao de midia mais caro que interior)
    - Interior: 1.0x (baseline)
    """
    nome_norm = _normalizar_nome(municipio)
    uf_upper = (uf or "").strip().upper()
    if nome_norm in CAPITAIS_ESTADUAIS_NORM and uf_upper in ("SP", "RJ"):
        return 1.5
    if nome_norm in CAPITAIS_ESTADUAIS_NORM:
        return 1.3
    return 1.0


def calcular_vgv(valor_unidade: float, volume_unidades: int) -> float:
    return valor_unidade * volume_unidades


def calcular_pressao_custos(dados_bcb: dict) -> dict:
    """Calcula uma leitura simples de pressao de custos e aluguel."""

    incc = float(dados_bcb.get("incc", {}).get("valor") or 0.0)
    igpm = float(dados_bcb.get("igpm_12m", {}).get("valor") or 0.0)
    ipca = float(dados_bcb.get("ipca_12m", {}).get("valor") or 0.0)
    selic = float(dados_bcb.get("selic", {}).get("valor") or 0.0)

    pressao_incorporador = incc - ipca
    urgencia_locatario = igpm
    interpretacao: list[str] = []
    if pressao_incorporador > 3:
        interpretacao.append(
            f"INCC {incc:.1f}% vs IPCA {ipca:.1f}% indica custo de construcao acima da inflacao geral."
        )
    if urgencia_locatario > 8:
        interpretacao.append(
            f"IGP-M em {igpm:.1f}% sugere aluguel pressionado, o que pode elevar a urgencia de compra."
        )
    if selic > 12 and igpm > 8:
        interpretacao.append(
            "Juro alto com aluguel pressionado cria dilema para o comprador entre financiar caro ou seguir alugando caro."
        )
    return {
        "incc": incc,
        "igpm": igpm,
        "ipca": ipca,
        "selic": selic,
        "pressao_incorporador": round(pressao_incorporador, 1),
        "urgencia_locatario": round(urgencia_locatario, 1),
        "interpretacao": interpretacao,
    }


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
    municipio: str = "",
    uf: str = "",
) -> dict:
    """Calcula cenarios financeiros completos a partir do score.

    O CPL e ajustado pelo porte da praca: capitais pagam mais pelo leilao de midia.
    A taxa de conversao varia por tipologia (lotes vs apartamentos).
    """

    chave_tipologia = tipologia.strip().lower()
    faixa = faixa_score(score)
    referencia = TABELA_VERBA[chave_tipologia][faixa]
    benchmark_setor = BENCHMARKS_SETOR[chave_tipologia]
    taxa_conversao = TAXA_CONVERSAO[chave_tipologia][faixa]
    multiplicador_praca = calcular_multiplicador_cpl(municipio, uf)

    cenarios = {}
    for nome, campo in (("conservador", "min"), ("base", "base"), ("agressivo", "max")):
        percentual = referencia[campo]
        verba = vgv * percentual
        custo_unidade = verba / volume_unidades
        cpl_base = BENCHMARK_CPL[chave_tipologia][nome]
        cpl = round(cpl_base * multiplicador_praca)
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
        "multiplicador_praca": multiplicador_praca,
        "benchmark_setor": benchmark_setor,
        "cenarios": cenarios,
    }
