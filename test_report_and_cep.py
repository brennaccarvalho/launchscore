"""Testes para combinacao de CEP e geracao do PDF executivo."""

from modules.ibge_api import _combinar_payload_cep
from modules.report_generator import gerar_pdf


def _mock_resultados() -> dict:
    breakdown = {
        "concorrencia": {"contribuicao": 1.8},
        "localizacao": {"contribuicao": 1.4},
        "renda_media": {"contribuicao": 1.2},
        "tracao": {"contribuicao": 1.1},
        "idh": {"contribuicao": 0.9},
        "inovacao": {"contribuicao": 0.8},
        "funcionalidades": {"contribuicao": 0.7},
        "conexao_luxo": {"contribuicao": 0.6},
        "densidade": {"contribuicao": 0.5},
        "escolaridade": {"contribuicao": 0.4},
        "faixa_etaria": {"contribuicao": 0.3},
        "proporcao_alugados": {"contribuicao": 0.2},
        "crescimento_pop": {"contribuicao": 0.1},
    }
    cenarios = {
        "conservador": {
            "percentual": 0.028,
            "verba_r$": 2184000,
            "custo_unidade": 18200,
            "leads_estimados": 980,
            "cpl_estimado": 220,
            "roas": 3.2,
            "vendas_estimadas": 18,
            "benchmark_comparacao": "Levemente abaixo do benchmark",
        },
        "base": {
            "percentual": 0.035,
            "verba_r$": 2730000,
            "custo_unidade": 22750,
            "leads_estimados": 1400,
            "cpl_estimado": 170,
            "roas": 4.1,
            "vendas_estimadas": 24,
            "benchmark_comparacao": "Em linha com o benchmark",
        },
        "agressivo": {
            "percentual": 0.045,
            "verba_r$": 3510000,
            "custo_unidade": 29250,
            "leads_estimados": 1800,
            "cpl_estimado": 140,
            "roas": 4.7,
            "vendas_estimadas": 29,
            "benchmark_comparacao": "Acima do benchmark",
        },
    }
    return {
        "empreendimento": {
            "nome": "Vista Mar Residence",
            "tipologia": "Apartamentos",
        },
        "localizacao": {
            "municipio": "Fortaleza",
            "uf": "CE",
            "bairro": "Meireles",
        },
        "resultado_score": {
            "score_final": 48.0,
            "classificacao": "Dificuldade Moderada",
            "cor": "amarelo",
            "breakdown": breakdown,
        },
        "resultado_verba": {
            "vgv": 78000000,
            "cenarios": cenarios,
        },
        "mix_midias": {
            "base": {
                "canais": {
                    "Meta Ads (Instagram/Facebook)": {
                        "percentual": 0.35,
                        "budget_r$": 955500,
                        "leads_estimados": 540,
                        "cor": "#1B2A4A",
                        "taticas": ["Capte demanda com foco em geolocalizacao premium", "Teste criativos com prova de valor e lifestyle"],
                    },
                    "Google Ads (Search + Display)": {
                        "percentual": 0.30,
                        "budget_r$": 819000,
                        "leads_estimados": 420,
                        "cor": "#3B82F6",
                        "taticas": ["Capture demanda de alta intencao por tipologia", "Proteja buscas de marca e concorrencia"],
                    },
                    "Portais Imobiliarios (Zap/Viva/OLX)": {
                        "percentual": 0.20,
                        "budget_r$": 546000,
                        "leads_estimados": 280,
                        "cor": "#E8A020",
                        "taticas": ["Manter inventario com destaque premium", "Atualizar prova comercial e fotos com frequencia"],
                    },
                    "WhatsApp / CRM": {
                        "percentual": 0.15,
                        "budget_r$": 409500,
                        "leads_estimados": 160,
                        "cor": "#16A34A",
                        "taticas": ["Responder em ate 5 minutos", "Automatizar follow-up com prova e disponibilidade"],
                    },
                }
            }
        },
        "perfil_publico": {
            "faixa_etaria_primaria": "35-44 anos",
            "faixa_etaria_secundaria": "45-54 anos",
            "renda_familiar_estimada": "R$ 18 mil a R$ 25 mil",
            "escolaridade": "Superior completo",
            "motivacoes_compra": ["seguranca patrimonial", "endereco valorizado", "qualidade de vida"],
            "objecoes_tipicas": ["receio com taxa de juros", "comparacao com usados prontos", "tempo de obra"],
            "mensagem_chave": "Apresente o empreendimento como uma decisao de patrimonio com localizacao forte e liquidez sustentada.",
        },
        "dados_publicos": {
            "bcb": {
                "selic": {"valor": 10.5},
                "juros_imobiliario": {"valor": 9.8},
                "incc": {"valor": 6.2},
            },
            "ipea": {
                "pib_percapita": {"valor": 42500},
                "desemprego": {"valor": 8.4},
                "gini": {"valor": 0.52},
            },
            "trends": {
                "score_interesse": 58,
                "tendencia_recente": "crescendo",
                "termos": ["apartamentos Fortaleza", "imoveis Fortaleza"],
            },
        },
        "recomendacoes_estrategicas": "A pressao comercial esta concentrada em concorrencia e localizacao percebida, pedindo narrativa forte, prova de valor e verba consistente desde a abertura.",
    }


def test_combinar_payload_cep_prioriza_bairro_do_viacep():
    resultado = _combinar_payload_cep(
        "60165120",
        {
            "city": "Fortaleza",
            "state": "CE",
            "ibge": "2304400",
            "neighborhood": "Centro",
            "street": "Rua A",
        },
        {
            "localidade": "Fortaleza",
            "uf": "CE",
            "ibge": "2304400",
            "bairro": "Meireles",
            "logradouro": "Rua B",
        },
    )

    assert resultado["bairro"] == "Meireles"
    assert resultado["rua"] == "Rua B"
    assert resultado["fonte"] == "ViaCEP + BrasilAPI"


def test_gerar_pdf_retorna_bytes_com_assinatura_pdf():
    pdf = gerar_pdf(_mock_resultados())

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000
