"""Configuracoes globais do LaunchScore."""

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

CORES = {
    "fundo": "#FAF8F5",
    "fundo_card": "#FFFFFF",
    "fundo_sidebar": "#F0EDE8",
    "azul_escuro": "#1B2A4A",
    "dourado": "#E8A020",
    "dourado_claro": "#F5C84A",
    "texto_primario": "#1B2A4A",
    "texto_secundario": "#6B7280",
    "verde": "#16A34A",
    "amarelo": "#CA8A04",
    "laranja": "#EA580C",
    "vermelho": "#DC2626",
    "borda": "#E5DDD0",
}

FAIXA_ECONOMICO_MAX = 500_000
FAIXA_MEDIO_MAX = 800_000

BRASILAPI_CEP = "https://brasilapi.com.br/api/cep/v2/{cep}"
VIACEP_CEP = "https://viacep.com.br/ws/{cep}/json/"
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

BENCHMARK_CPL = {
    "lotes": {"conservador": 180, "base": 140, "agressivo": 110},
    "apartamentos": {"conservador": 220, "base": 170, "agressivo": 130},
}

TAXA_CONVERSAO = {
    "score_0_30": 0.025,
    "score_31_50": 0.018,
    "score_51_70": 0.013,
    "score_71_100": 0.009,
}

BENCHMARKS_SETOR = {
    "lotes": {"media_pct_vgv": 0.032, "range": "2,5% - 4,5%"},
    "apartamentos": {"media_pct_vgv": 0.038, "range": "3,0% - 5,5%"},
}

CORES_CANAIS = {
    "Meta Ads (Instagram/Facebook)": "#1B2A4A",
    "Google Ads (Search + Display)": "#3B82F6",
    "Portais Imobiliarios (Zap/Viva/OLX)": "#E8A020",
    "WhatsApp / CRM": "#16A34A",
    "Midia OOH (outdoor/paineis)": "#EA580C",
    "Radio Local": "#9333EA",
    "Influenciadores Regionais": "#EC4899",
    "Eventos/Plantao Digital": "#F5C84A",
    "LinkedIn Ads": "#0077B5",
    "CRM / E-mail Marketing": "#6B7280",
    "Influenciadores / Conteudo": "#EC4899",
}

CORES_RELATORIO = {
    "azul": CORES["azul_escuro"],
    "dourado": CORES["dourado"],
    "branco": CORES["fundo_card"],
    "cinza": CORES["texto_secundario"],
    "verde": CORES["verde"],
    "amarelo": CORES["amarelo"],
    "laranja": CORES["laranja"],
    "vermelho": CORES["vermelho"],
}

PDF_RODAPE = (
    "Criado por Brenna Carvalho | LaunchScore | "
    "launchscorebrenna.streamlit.app | linkedin.com/in/brennacarvalho"
)

TERMOS_USO_RESUMIDOS = """
1. O LaunchScore e sua metodologia sao propriedade intelectual de Brenna Carvalho.
2. O relatorio possui carater orientativo e nao constitui garantia de resultado financeiro.
3. O uso comercial, copia integral ou redistribuicao da metodologia depende de autorizacao da autora.
4. As recomendacoes dependem da qualidade dos dados publicos disponiveis e dos dados inseridos pelo usuario.
5. Ao utilizar a plataforma, o usuario declara ciencia dessas limitacoes e dos Termos de Uso.
""".strip()
