"""Configuracoes globais do Score Marketing Imobiliario."""

from __future__ import annotations

MEDIANAS_NACIONAIS = {
    "idh": 0.699,
    "renda_media_domiciliar": 2850.0,
    "densidade_populacional": 22.4,
    "proporcao_alugados": 0.18,
    "crescimento_populacional": 0.0064,
    "escolaridade_superior": 0.18,
    "faixa_etaria_centralidade": 0.55,
}

FAIXA_ECONOMICO_MAX = 500_000
FAIXA_MEDIO_MAX = 800_000

BRASILAPI_CEP = "https://brasilapi.com.br/api/cep/v2/{cep}"
IBGE_SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
IBGE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

REQUEST_TIMEOUT = 8

PESOS_SCORE = {
    "idh": 0.10,
    "renda_media": 0.12,
    "faixa_etaria": 0.06,
    "escolaridade": 0.05,
    "densidade": 0.06,
    "proporcao_alugados": 0.04,
    "crescimento_pop": 0.02,
    "concorrencia": 0.15,
    "localizacao": 0.12,
    "inovacao": 0.08,
    "tracao": 0.10,
    "funcionalidades": 0.05,
    "conexao_luxo": 0.05,
}

TABELA_VERBA = {
    "lotes": {
        "score_0_30": {"min": 0.018, "base": 0.022, "max": 0.028},
        "score_31_50": {"min": 0.025, "base": 0.030, "max": 0.038},
        "score_51_70": {"min": 0.032, "base": 0.040, "max": 0.050},
        "score_71_100": {"min": 0.045, "base": 0.058, "max": 0.075},
    },
    "apartamentos": {
        "score_0_30": {"min": 0.020, "base": 0.025, "max": 0.032},
        "score_31_50": {"min": 0.028, "base": 0.035, "max": 0.045},
        "score_51_70": {"min": 0.038, "base": 0.048, "max": 0.060},
        "score_71_100": {"min": 0.050, "base": 0.065, "max": 0.085},
    },
}

CORES_RELATORIO = {
    "azul": "#1B2A4A",
    "dourado": "#E8A020",
    "branco": "#FFFFFF",
    "cinza": "#F3F4F6",
    "verde": "#22C55E",
    "amarelo": "#EAB308",
    "laranja": "#F97316",
    "vermelho": "#EF4444",
}
