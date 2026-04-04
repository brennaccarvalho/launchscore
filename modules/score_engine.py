"""Motor de calculo do score de dificuldade de venda."""

from __future__ import annotations

from config import PESOS_SCORE


def _escala_usuario(valor: int, invertido: bool = False) -> float:
    base = ((valor - 1) / 4) * 10
    return round(10 - base, 2) if invertido else round(base, 2)


def classificar_score(score: float) -> tuple[str, str]:
    if score <= 30:
        return "Baixa Dificuldade", "verde"
    if score <= 50:
        return "Dificuldade Moderada", "amarelo"
    if score <= 70:
        return "Alta Dificuldade", "laranja"
    return "Dificuldade Critica", "vermelho"


def calcular_score(dados_normalizados: dict, atributos_usuario: dict) -> dict:
    """Combina dados externos e atributos do produto em score final."""

    valores = {
        "idh": dados_normalizados["idh"],
        "renda_media": dados_normalizados["renda_media"],
        "faixa_etaria": dados_normalizados["faixa_etaria"],
        "escolaridade": dados_normalizados["escolaridade"],
        "densidade": dados_normalizados["densidade"],
        "proporcao_alugados": dados_normalizados["proporcao_alugados"],
        "crescimento_pop": dados_normalizados["crescimento_pop"],
        "concorrencia": _escala_usuario(atributos_usuario["concorrencia"]),
        "localizacao": _escala_usuario(atributos_usuario["localizacao"]),
        "inovacao": _escala_usuario(atributos_usuario["inovacao"], invertido=True),
        "tracao": _escala_usuario(atributos_usuario["tracao"], invertido=True),
        "funcionalidades": _escala_usuario(atributos_usuario["funcionalidades"], invertido=True),
        "conexao_luxo": _escala_usuario(atributos_usuario["conexao_luxo"], invertido=True),
    }

    breakdown = {}
    score_bruto = 0.0
    for chave, peso in PESOS_SCORE.items():
        contribuicao = valores[chave] * peso
        score_bruto += contribuicao
        breakdown[chave] = {
            "peso": peso,
            "valor_norm": round(valores[chave], 2),
            "contribuicao": round(contribuicao, 4),
        }

    score_final = round(score_bruto * 10, 1)
    classificacao, cor = classificar_score(score_final)
    top3 = sorted(breakdown.items(), key=lambda item: item[1]["contribuicao"], reverse=True)[:3]
    top3_fatores_criticos = [nome for nome, _ in top3]
    justificativa = (
        "Os principais fatores de pressao sobre a venda sao "
        + ", ".join(top3_fatores_criticos[:-1])
        + (" e " if len(top3_fatores_criticos) > 1 else "")
        + top3_fatores_criticos[-1]
        + ", pois concentram a maior contribuicao ponderada no score final."
    )

    return {
        "score_final": score_final,
        "classificacao": classificacao,
        "cor": cor,
        "breakdown": breakdown,
        "top3_fatores_criticos": top3_fatores_criticos,
        "justificativa_texto": justificativa,
    }
