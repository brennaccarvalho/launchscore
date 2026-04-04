"""Geracao do perfil de publico-alvo a partir dos dados locais."""

from __future__ import annotations

from config import FAIXA_ECONOMICO_MAX, FAIXA_MEDIO_MAX


def _faixa_renda(valor_unidade: float, renda_media: float) -> str:
    multiplicador = 3.0 if valor_unidade <= FAIXA_ECONOMICO_MAX else 5.0
    if valor_unidade > FAIXA_MEDIO_MAX:
        multiplicador = 8.0
    base = renda_media * multiplicador
    return f"R$ {base:,.0f} – R$ {base * 1.8:,.0f}/mes".replace(",", ".")


def gerar_perfil_publico(dados_ibge: dict, tipologia: str, valor_unidade: float) -> dict:
    """Constroi um perfil de audiencia em linguagem de marketing."""

    faixa_principal = dados_ibge["faixa_etaria_predominante"]["valor"]
    faixa_secundaria = "30–44 anos" if "35" in faixa_principal else "45–59 anos"
    escolaridade_pct = dados_ibge["escolaridade"]["valor"]
    escolaridade = (
        "Ensino superior completo ou pos-graduacao"
        if escolaridade_pct >= 0.25
        else "Ensino medio completo a superior incompleto"
    )
    perfil = [
        "Busca seguranca patrimonial e previsibilidade de longo prazo",
        "Valoriza conveniencia, mobilidade e qualidade de vida no entorno",
        "Pesquisa antes de falar com o corretor e compara diferenciais com rapidez",
        "Responde bem a prova social, tour visual e simulacao financeira clara",
    ]
    if tipologia.lower() == "lotes":
        perfil.append("Tem forte interesse em potencial de valorizacao da regiao")

    motivacoes = [
        "Desejo de sair do aluguel ou trocar por um imovel melhor posicionado",
        "Protecao de patrimonio em ativo real com perspectiva de valorizacao",
        "Melhor adequacao do imovel ao momento de vida da familia",
    ]
    if valor_unidade > FAIXA_MEDIO_MAX:
        motivacoes.append("Status e alinhamento com um estilo de vida aspiracional")

    return {
        "faixa_etaria_primaria": faixa_principal,
        "faixa_etaria_secundaria": faixa_secundaria,
        "renda_familiar_estimada": _faixa_renda(valor_unidade, dados_ibge["renda_media_domiciliar"]["valor"]),
        "escolaridade": escolaridade,
        "perfil_comportamental": perfil[:5],
        "motivacoes_compra": motivacoes[:4],
        "objecoes_tipicas": [
            "Receio com momento de compra e condicoes de financiamento",
            "Comparacao com opcoes concorrentes no mesmo raio geografico",
            "Duvida sobre prazo de entrega, liquidez ou valorizacao futura",
        ],
        "canais_preferidos": [
            "Instagram e Facebook com conteudo regionalizado",
            "Google Search para termos de alta intencao",
            "Portais imobiliarios e atendimento consultivo por WhatsApp",
        ]
        + (["LinkedIn e conteudo premium de lifestyle e investimento"] if valor_unidade > FAIXA_MEDIO_MAX else []),
        "mensagem_chave": "Um empreendimento pensado para unir localizacao, valorizacao e decisao de compra com mais seguranca.",
    }
