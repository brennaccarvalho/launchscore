"""Testes basicos para os motores de score e verba."""

from modules.budget_engine import calcular_verba, calcular_vgv, faixa_score
from modules.score_engine import calcular_score, classificar_score


def test_classificar_score_faixas():
    assert classificar_score(25)[0] == "Baixa Dificuldade"
    assert classificar_score(45)[0] == "Dificuldade Moderada"
    assert classificar_score(65)[0] == "Alta Dificuldade"
    assert classificar_score(85)[0] == "Dificuldade Critica"


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
    resultado = calcular_verba(vgv, 48, "apartamentos", 120, 650000)
    assert vgv == 78000000
    assert faixa_score(48) == "score_31_50"
    assert round(resultado["percentual_verba"], 3) == 0.035
    assert round(resultado["cenarios"]["base"]["verba_r$"], 2) == 2730000.00
    assert round(resultado["cenarios"]["base"]["roas"], 2) > 0
