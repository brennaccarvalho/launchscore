"""Testes basicos para os motores de score e verba."""

from modules.budget_engine import calcular_verba, calcular_vgv
from modules.score_engine import calcular_score, classificar_score


def test_classificar_score_faixas():
    assert classificar_score(25)[0] == "🟢 Baixa Dificuldade"
    assert classificar_score(45)[0] == "🟡 Dificuldade Moderada"
    assert classificar_score(65)[0] == "🟠 Alta Dificuldade"
    assert classificar_score(85)[0] == "🔴 Dificuldade Crítica"


def test_calcular_score_retorna_breakdown_completo():
    dados_normalizados = {
        "idh": 4,
        "renda_media": 5,
        "faixa_etaria": 3,
        "escolaridade": 4,
        "densidade": 2,
        "proporcao_alugados": 4,
        "crescimento_pop": 3,
    }
    atributos = {
        "concorrencia": 3,
        "localizacao": 3,
        "inovacao": 3,
        "tracao": 3,
        "funcionalidades": 3,
        "conexao_luxo": 3,
    }
    resultado = calcular_score(dados_normalizados, atributos)
    assert "score_final" in resultado
    assert len(resultado["breakdown"]) == 13
    assert len(resultado["top3_fatores_criticos"]) == 3


def test_calcular_verba_apartamentos_score_moderado():
    vgv = calcular_vgv(650000, 120)
    resultado = calcular_verba(vgv, 48, 3, "apartamentos", 120)
    assert vgv == 78000000
    assert round(resultado["percentual_verba"], 4) == 0.0365
    assert round(resultado["verba_total_r$"], 2) == 2847000.00
    assert round(resultado["cenarios"]["conservador"]["percentual"], 3) == 0.028
