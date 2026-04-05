"""Aplicativo Streamlit principal do LaunchScore."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from config import CORES, CORES_CANAIS
from modules.audience import gerar_perfil_publico
from modules.budget_engine import calcular_verba, calcular_vgv
from modules.data_orchestrator import FONTES_DE_DADOS, calcular_favorabilidade_mercado, coletar_todos_dados
from modules.ibge_api import (
    buscar_municipio_por_nome,
    get_dados_ibge,
    get_municipio_by_cep,
    normalizar_para_score,
    sugerir_pontuacao_localizacao,
)
from modules.media_mix import recomendar_mix
from modules.report_generator import gerar_pdf
from modules.score_engine import calcular_score
from modules.termos_de_uso import exibir_footer_termos, exibir_termos_modal, render_pagina_termos


st.set_page_config(layout="wide", page_title="LaunchScore")


def injetar_css() -> None:
    st.markdown(
        """
<style>
  .stApp { background-color: #FAF8F5; }
  [data-testid="stSidebar"] { background-color: #F0EDE8; border-right: 2px solid #E8A020; }
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; color: #1B2A4A; }
  h1 { font-size: 2rem; font-weight: 800; color: #1B2A4A; }
  h2 { font-size: 1.3rem; font-weight: 700; color: #1B2A4A; border-left: 4px solid #E8A020; padding-left: 10px; }
  h3 { font-size: 1.05rem; font-weight: 600; color: #1B2A4A; }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1B2A4A, #2D4270);
    color: #FFFFFF; border: none; border-radius: 8px; font-weight: 700;
    font-size: 1rem; padding: 0.75rem 2rem; transition: all 0.2s;
  }
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #E8A020, #F5C84A);
    color: #1B2A4A; transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(232,160,32,0.4);
  }
  .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
    background-color: #FFFFFF; border: 1.5px solid #E5DDD0; border-radius: 6px; color: #1B2A4A;
  }
  .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
    border-color: #E8A020; box-shadow: 0 0 0 2px rgba(232,160,32,0.2);
  }
  .stSlider > div > div > div > div { background: #E8A020 !important; }
  .stSlider > div > div > div { background: #E5DDD0 !important; }
  .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #E5DDD0; gap: 8px; }
  .stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 6px 6px 0 0; color: #6B7280;
    font-weight: 600; padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background: #1B2A4A !important; color: #FFFFFF !important; border-bottom: 3px solid #E8A020;
  }
  [data-testid="metric-container"] {
    background: #FFFFFF; border: 1px solid #E5DDD0; border-top: 3px solid #E8A020;
    border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(27,42,74,0.06);
  }
  [data-testid="metric-container"] label {
    color: #6B7280; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
  }
  [data-testid="metric-container"] [data-testid="metric-value"] { color: #1B2A4A; font-weight: 800; font-size: 1.6rem; }
  .streamlit-expanderHeader { background: #F0EDE8; border-radius: 8px; font-weight: 600; color: #1B2A4A; }
  .stDataFrame { border: 1px solid #E5DDD0; border-radius: 8px; }
  .stDownloadButton > button {
    background: #1B2A4A; color: #FFFFFF; border: 2px solid #E8A020; border-radius: 8px; font-weight: 700;
  }
  .stDownloadButton > button:hover { background: #E8A020; color: #1B2A4A; }
  .stProgress > div > div { background: linear-gradient(90deg, #1B2A4A, #E8A020); }
  .badge-verde { background:#DCFCE7; color:#15803D; padding:4px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; display:inline-block; }
  .badge-amarelo { background:#FEF9C3; color:#854D0E; padding:4px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; display:inline-block; }
  .badge-laranja { background:#FFEDD5; color:#9A3412; padding:4px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; display:inline-block; }
  .badge-vermelho { background:#FEE2E2; color:#991B1B; padding:4px 12px; border-radius:20px; font-weight:700; font-size:0.85rem; display:inline-block; }
  .fonte-tag { background:#F0EDE8; color:#6B7280; padding:2px 8px; border-radius:4px; font-size:0.72rem; border:1px solid #E5DDD0; display:inline-block; }
  .bloco-form {
    background: rgba(255,255,255,0.55); border: 1px solid #E5DDD0; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 8px rgba(27,42,74,0.04); min-height: 100%;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
<div style="background:linear-gradient(135deg,#1B2A4A,#2D4270); padding:28px 32px; border-radius:12px; margin-bottom:24px; border-bottom:4px solid #E8A020;">
  <div style="display:flex; align-items:center; gap:16px;">
    <div style="background:#E8A020; width:48px; height:48px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.5rem;">🏢</div>
    <div>
      <h1 style="color:#FFFFFF; margin:0; font-size:1.8rem; font-weight:800;">LaunchScore</h1>
      <p style="color:#E8A020; margin:0; font-size:0.9rem; font-weight:500;">Score Marketing Imobiliario - por Brenna Carvalho</p>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_header_executive() -> None:
    st.markdown(
        """
<div style="background:linear-gradient(135deg,#16233D,#24365F); padding:28px 32px; border-radius:14px; margin-bottom:24px; border:1px solid rgba(232,160,32,0.25); box-shadow:0 10px 30px rgba(27,42,74,0.10);">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:24px;">
    <div>
      <div style="display:inline-block; font-size:0.76rem; font-weight:700; letter-spacing:0.12em; color:#E8A020; text-transform:uppercase; margin-bottom:10px;">
        Inteligencia de lancamento imobiliario
      </div>
      <h1 style="color:#FFFFFF; margin:0; font-size:2rem; font-weight:800; line-height:1.08;">LaunchScore</h1>
      <p style="color:#D8DEE9; margin:8px 0 0 0; font-size:0.96rem; max-width:720px;">
        Score comercial, verba recomendada, projecao de cenarios e mix de midia em leitura executiva.
      </p>
    </div>
    <div style="min-width:220px; text-align:right;">
      <div style="font-size:0.78rem; color:#E8A020; font-weight:700; text-transform:uppercase; letter-spacing:0.08em;">Autoria</div>
      <div style="font-size:1rem; color:#FFFFFF; font-weight:700; margin-top:4px;">Brenna Carvalho</div>
      <div style="font-size:0.84rem; color:#C7D2E2; margin-top:4px;">Metodologia proprietaria LaunchScore</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def formatar_roas(valor: float) -> str:
    return f"{valor:.1f} : 1".replace(".", ",")


def formatar_valor_contexto(valor: float | int | None, formato: str = "numero") -> str:
    if valor is None:
        return "Indisponivel"
    if formato == "pct":
        return f"{float(valor):.1f}%".replace(".", ",")
    if formato == "bilhoes":
        return f"R$ {float(valor):.1f} bi".replace(".", ",")
    if formato == "indice":
        return f"{float(valor):.2f}".replace(".", ",")
    if formato == "moeda":
        return formatar_moeda(float(valor))
    return f"{float(valor):.2f}".replace(".", ",")


def badge_html(texto: str, cor: str) -> str:
    return f'<span class="badge-{cor}">{texto}</span>'


def slider_com_descricao(
    label: str,
    icone: str,
    descricao: str,
    extremo_esq: str,
    extremo_dir: str,
    key: str,
    default: int = 3,
) -> int:
    st.markdown(
        f"""
    <div style="margin-bottom:4px;">
      <span style="font-weight:700; color:#1B2A4A; font-size:0.95rem;">{icone} {label}</span><br>
      <span style="color:#6B7280; font-size:0.8rem;">{descricao}</span>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#9CA3AF; margin-bottom:-12px;">
      <span>{extremo_esq}</span><span>{extremo_dir}</span>
    </div>
        """,
        unsafe_allow_html=True,
    )
    return st.slider("", 1, 5, default, key=key, label_visibility="collapsed")


def card(titulo: str, conteudo_html: str, cor_borda: str = "#E5DDD0", icone: str = "") -> None:
    st.markdown(
        f"""
    <div style="background:#FFFFFF; border:1px solid {cor_borda}; border-top:3px solid {cor_borda};
                border-radius:10px; padding:20px; margin-bottom:16px;
                box-shadow:0 2px 8px rgba(27,42,74,0.06);">
      <h3 style="margin-top:0; color:#1B2A4A;">{icone} {titulo}</h3>
      {conteudo_html}
    </div>
        """,
        unsafe_allow_html=True,
    )


def calcular_qualidade_dados(dados_ibge: dict) -> tuple[str, str]:
    variaveis = [v for k, v in dados_ibge.items() if k != "codigo_ibge"]
    total = len(variaveis) or 1
    reais = sum(1 for v in variaveis if v.get("fonte") == "api")
    pct = reais / total * 100
    if pct >= 80:
        return "Alta confiabilidade", "verde"
    if pct >= 50:
        return "Confiabilidade media", "amarelo"
    return "Dados estimados - use com cautela", "vermelho"


def validar_inputs(form_data: dict) -> list[tuple[str, str]]:
    mensagens = []
    cep = form_data["cep"].strip()
    if cep and not re.fullmatch(r"\d{5}-?\d{3}", cep):
        mensagens.append(("erro", "CEP invalido. Use o formato 00000-000."))
    if form_data["tipologia"] == "Lotes" and form_data["valor_unidade"] > 2_000_000:
        mensagens.append(("aviso", "Valor por lote acima de R$ 2.000.000. Confira se o ticket esta correto."))
    if form_data["tipologia"] == "Lotes" and form_data["volume_unidades"] > 2000:
        mensagens.append(("aviso", "Volume acima de 2.000 lotes. Valide se o numero de unidades esta correto."))
    if form_data["tipologia"] == "Apartamentos" and form_data["volume_unidades"] > 1000:
        mensagens.append(("aviso", "Volume acima de 1.000 apartamentos. Valide se o numero de unidades esta correto."))
    if not cep and not form_data["cidade_manual"].strip():
        mensagens.append(("erro", "Informe um CEP valido ou uma cidade de fallback."))
    return mensagens


def interpretar_variavel(variavel: str, valor: float) -> str:
    if variavel == "concorrencia":
        return "⚠️ Mercado saturado - aumenta a dificuldade de venda" if valor >= 7.5 else "✅ Pressao competitiva controlada"
    if variavel == "localizacao":
        return "⚠️ Localizacao fragil para o ticket" if valor >= 6 else "✅ Boa localizacao - reduz a dificuldade"
    if variavel == "renda_media":
        return "📊 Renda media local abaixo da faixa ideal para esse ticket" if valor >= 6 else "📊 Renda local favorece absorcao"
    if variavel == "idh":
        return "📉 Ambiente socioeconomico eleva a complexidade comercial" if valor >= 6 else "📈 Ambiente socioeconomico favoravel"
    if variavel in {"inovacao", "tracao", "funcionalidades", "conexao_luxo"}:
        return "⚠️ Produto precisa de reforco de proposta de valor" if valor >= 6 else "✅ Produto ajuda a reduzir friccao"
    return "⚠️ Pressiona o score" if valor >= 6 else "✅ Contribuicao sob controle"


def categoria_variavel(variavel: str) -> str:
    return "Dados IBGE" if variavel in {
        "idh",
        "renda_media",
        "faixa_etaria",
        "escolaridade",
        "densidade",
        "proporcao_alugados",
        "crescimento_pop",
    } else "Atributos do empreendimento"


def montar_breakdown_df(resultado_score: dict) -> pd.DataFrame:
    linhas = []
    for variavel, dados in resultado_score["breakdown"].items():
        categoria = categoria_variavel(variavel)
        linhas.append(
            {
                "Variavel": variavel,
                "Categoria": categoria,
                "Peso": dados["peso"],
                "Valor Normalizado": dados["valor_norm"],
                "Contribuicao": dados["contribuicao"],
                "Interpretacao": interpretar_variavel(variavel, dados["valor_norm"]),
            }
        )
    return pd.DataFrame(linhas)


def montar_tabela_cenarios(resultados: dict) -> pd.DataFrame:
    verba = resultados["resultado_verba"]
    benchmark = verba["benchmark_setor"]
    cenarios = verba["cenarios"]
    return pd.DataFrame(
        {
            "Indicador": [
                "% do VGV",
                "Verba Total",
                "Custo por Unidade",
                "Leads Estimados*",
                "Custo por Lead (CPL)*",
                "ROAS Estimado*",
                "Benchmark do setor",
                "Resultado Esperado",
            ],
            "🔵 Conservador": [
                formatar_percentual(cenarios["conservador"]["percentual"]),
                formatar_moeda(cenarios["conservador"]["verba_r$"]),
                formatar_moeda(cenarios["conservador"]["custo_unidade"]),
                f"{cenarios['conservador']['leads_estimados']:.0f}",
                formatar_moeda(cenarios["conservador"]["cpl_estimado"]),
                formatar_roas(cenarios["conservador"]["roas"]),
                f"{benchmark['range']} | {cenarios['conservador']['benchmark_comparacao']}",
                cenarios["conservador"]["resultado_esperado"],
            ],
            "⚡ Base (Recomendado)": [
                formatar_percentual(cenarios["base"]["percentual"]),
                formatar_moeda(cenarios["base"]["verba_r$"]),
                formatar_moeda(cenarios["base"]["custo_unidade"]),
                f"{cenarios['base']['leads_estimados']:.0f}",
                formatar_moeda(cenarios["base"]["cpl_estimado"]),
                formatar_roas(cenarios["base"]["roas"]),
                f"{benchmark['range']} | {cenarios['base']['benchmark_comparacao']}",
                cenarios["base"]["resultado_esperado"],
            ],
            "🔴 Agressivo": [
                formatar_percentual(cenarios["agressivo"]["percentual"]),
                formatar_moeda(cenarios["agressivo"]["verba_r$"]),
                formatar_moeda(cenarios["agressivo"]["custo_unidade"]),
                f"{cenarios['agressivo']['leads_estimados']:.0f}",
                formatar_moeda(cenarios["agressivo"]["cpl_estimado"]),
                formatar_roas(cenarios["agressivo"]["roas"]),
                f"{benchmark['range']} | {cenarios['agressivo']['benchmark_comparacao']}",
                cenarios["agressivo"]["resultado_esperado"],
            ],
        }
    )


def montar_resumo_compartilhamento(resultados: dict) -> str:
    base = resultados["resultado_verba"]["cenarios"]["base"]
    score = resultados["resultado_score"]
    return (
        f"LaunchScore | {resultados['empreendimento']['nome']} | "
        f"{resultados['localizacao']['municipio']}\n"
        f"Score: {score['score_final']}/100 - {score['classificacao']}\n"
        f"VGV: {formatar_moeda(resultados['resultado_verba']['vgv'])} | "
        f"Verba recomendada: {formatar_moeda(base['verba_r$'])} ({formatar_percentual(base['percentual'])} do VGV)\n"
        f"ROAS estimado cenario base: {formatar_roas(base['roas'])}\n"
        "Gerado por LaunchScore - por Brenna Carvalho"
    )


def render_copy_button(texto: str) -> None:
    payload = json.dumps(texto)
    components.html(
        f"""
        <button
            onclick='navigator.clipboard.writeText({payload}).then(() => {{
                const el = document.getElementById("copy-status");
                if (el) el.innerText = "Resumo copiado para a area de transferencia.";
            }})'
            style="width:100%; background:#1B2A4A; color:#FFFFFF; border:2px solid #E8A020;
                   border-radius:8px; font-weight:700; padding:12px; cursor:pointer;">
            📋 Copiar resumo para compartilhamento
        </button>
        <div id="copy-status" style="font-size:12px; color:#6B7280; margin-top:8px;"></div>
        """,
        height=70,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
        <div style="text-align:center; padding:16px 0 24px 0;">
          <div style="background:#1B2A4A; color:#E8A020; font-size:1.5rem; font-weight:800;
                      padding:12px; border-radius:10px; margin-bottom:8px;">LS</div>
          <div style="font-size:0.75rem; color:#6B7280;">por Brenna Carvalho</div>
        </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Como usar")
        st.markdown(
            """
1. Informe o CEP ou cidade
2. Preencha os dados do empreendimento
3. Configure os atributos com atencao as descricoes
4. Clique em **Calcular** para gerar o relatorio completo
            """
        )
        st.markdown("---")
        st.markdown("### Glossario")
        glossario = {
            "VGV": "Valor Geral de Vendas - total de receita potencial do empreendimento",
            "Score": "Indice de dificuldade estimada de venda (0 = facil, 100 = critico)",
            "CPL": "Custo por Lead - quanto custa gerar um contato qualificado",
            "ROAS": "Retorno sobre o investimento em midia",
            "Mix de Midia": "Distribuicao estrategica do budget entre canais de comunicacao",
            "Tracao": "Evidencia de demanda ja demonstrada antes do lancamento formal",
        }
        for termo, definicao in glossario.items():
            with st.expander(f"**{termo}**"):
                st.write(definicao)
        st.markdown("---")
        exibir_termos_modal()
        if "historico" in st.session_state and st.session_state["historico"]:
            st.markdown("---")
            st.markdown("### Analises recentes")
            for indice, item in enumerate(st.session_state["historico"][-3:][::-1]):
                rotulo = f"{item['nome']} · {item['cidade']}"
                detalhes = f"Score {item['score']}/100 | Verba base {item['verba']}"
                if item.get("bairro"):
                    detalhes += f" | Bairro {item['bairro']}"
                if item.get("resultados"):
                    if st.button(rotulo, key=f"historico_{item.get('id', indice)}", use_container_width=True):
                        abrir_analise_recente(item)
                else:
                    st.markdown(f"**{rotulo}**")
                st.caption(detalhes)


def abrir_analise_recente(item: dict) -> None:
    if not item.get("resultados"):
        return
    st.session_state["resultados"] = deepcopy(item["resultados"])
    st.session_state["etapa_ativa"] = "3. Dashboard de Resultados"
    st.rerun()


def preparar_historico(resultados: dict) -> None:
    if "historico" not in st.session_state:
        st.session_state["historico"] = []
    identificador = "|".join(
        [
            resultados["empreendimento"]["nome"].strip().lower(),
            resultados["localizacao"]["municipio"].strip().lower(),
            resultados["empreendimento"]["tipologia"].strip().lower(),
        ]
    )
    resumo = {
        "id": identificador,
        "nome": resultados["empreendimento"]["nome"],
        "cidade": resultados["localizacao"]["municipio"],
        "bairro": resultados["localizacao"].get("bairro", ""),
        "score": resultados["resultado_score"]["score_final"],
        "verba": formatar_moeda(resultados["resultado_verba"]["cenarios"]["base"]["verba_r$"]),
        "resultados": deepcopy(resultados),
    }
    historico = [item for item in st.session_state["historico"] if item.get("id") != resumo["id"]]
    historico.append(resumo)
    st.session_state["historico"] = historico[-3:]


def obter_sugestao_localizacao(cep: str, cidade_manual: str) -> dict | None:
    cep_limpo = re.sub(r"\D", "", cep or "")
    if len(cep_limpo) == 8:
        try:
            localizacao = get_municipio_by_cep(cep_limpo)
            dados_ibge = get_dados_ibge(localizacao["codigo_ibge"])
            return sugerir_pontuacao_localizacao(localizacao, dados_ibge)
        except Exception:
            return None
    if cidade_manual:
        try:
            localizacao = buscar_municipio_por_nome(cidade_manual)
            dados_ibge = get_dados_ibge(localizacao["codigo_ibge"])
            return sugerir_pontuacao_localizacao(localizacao, dados_ibge)
        except Exception:
            return None
    return None


def processar_dados(form_data: dict) -> dict:
    status_box = st.empty()
    progresso = st.progress(0, text="Iniciando processamento...")
    mensagens = [
        "Consulta de dados publicos do municipio",
        "Calculo do score de dificuldade de venda",
        "Projecao de verba e cenarios de investimento",
        "Montagem do mix de midia recomendado",
        "Definicao do perfil de publico-alvo",
        "Relatorio pronto",
    ]

    def atualizar_progresso(percentual: int, titulo: str, detalhe: str) -> None:
        progresso.progress(percentual, text=f"{percentual}% concluido")
        status_box.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E5DDD0; border-radius:12px; padding:14px 16px; margin:10px 0 14px 0;">
              <div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; color:#E8A020; font-weight:700;">
                Gerando analise
              </div>
              <div style="font-size:1.02rem; color:#1B2A4A; font-weight:800; margin-top:4px;">{titulo}</div>
              <div style="font-size:0.88rem; color:#6B7280; margin-top:6px;">{detalhe}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    localizacao = None
    if form_data["cep"]:
        try:
            atualizar_progresso(10, "Localizando municipio", "Validando o CEP e identificando automaticamente a cidade do empreendimento.")
            localizacao = get_municipio_by_cep(form_data["cep"])
        except Exception:
            st.warning("Nao foi possivel localizar o CEP automaticamente. Usando busca manual por cidade.")

    if localizacao is None:
        atualizar_progresso(20, "Buscando cidade informada", "Usando a cidade digitada como fallback para encontrar o codigo IBGE correto.")
        localizacao = buscar_municipio_por_nome(form_data["cidade_manual"])

    atualizar_progresso(35, mensagens[0], f"Coletando dados de mercado para {localizacao['municipio']} e consolidando as fontes disponiveis.")
    dados_publicos = coletar_todos_dados(
        localizacao["codigo_ibge"],
        localizacao["municipio"],
        form_data["tipologia"],
    )
    dados_ibge = dados_publicos["ibge"]
    dados_normalizados = normalizar_para_score(dados_ibge)
    sugestao_localizacao = sugerir_pontuacao_localizacao(localizacao, dados_ibge)

    atributos = {
        chave: form_data[chave]
        for chave in (
            "concorrencia",
            "localizacao",
            "inovacao",
            "tracao",
            "funcionalidades",
            "conexao_luxo",
        )
    }
    atualizar_progresso(52, mensagens[1], "Combinando contexto local, atributos do produto e ajustes macroeconomicos.")
    resultado_score = calcular_score(
        dados_normalizados,
        atributos,
        dados_bcb=dados_publicos["bcb"],
        dados_ipea=dados_publicos["ipea"],
        dados_trends=dados_publicos["trends"],
    )

    vgv = calcular_vgv(form_data["valor_unidade"], form_data["volume_unidades"])
    atualizar_progresso(68, mensagens[2], "Estimando VGV, intensidade de investimento e retorno esperado por cenario.")
    resultado_verba = calcular_verba(
        vgv=vgv,
        score=resultado_score["score_final"],
        tipologia=form_data["tipologia"].lower(),
        volume_unidades=form_data["volume_unidades"],
        valor_unidade=form_data["valor_unidade"],
    )

    atualizar_progresso(82, mensagens[3], "Distribuindo a verba entre canais para os cenarios conservador, base e agressivo.")
    mixes = {}
    for cenario in ("conservador", "base", "agressivo"):
        mixes[cenario] = recomendar_mix(
            resultado_score["score_final"],
            form_data["tipologia"],
            form_data["valor_unidade"],
            cenario,
            dados_ibge,
            resultado_verba["cenarios"][cenario]["verba_r$"],
        )

    atualizar_progresso(92, mensagens[4], "Traduzindo os dados em perfil de publico, objecoes e mensagem-chave.")
    perfil_publico = gerar_perfil_publico(dados_ibge, form_data["tipologia"], form_data["valor_unidade"])

    atualizar_progresso(100, mensagens[5], "O dashboard esta pronto para leitura executiva.")
    qualidade_texto, qualidade_cor = calcular_qualidade_dados(dados_ibge)
    contexto = resultado_score.get("justificativa_macro", []) + resultado_score.get("justificativa_mercado_local", [])
    recomendacoes = (
        f"{resultado_score['justificativa_texto']} "
        f"O cenario base concentra {formatar_moeda(resultado_verba['cenarios']['base']['verba_r$'])} "
        f"em uma faixa considerada {resultado_verba['cenarios']['base']['benchmark_comparacao'].lower()} para o setor."
    )
    if contexto:
        recomendacoes += " Contexto de mercado: " + " | ".join(contexto) + "."
    return {
        "empreendimento": {
            "nome": form_data.get("nome_empreendimento") or "Empreendimento analisado",
            "tipologia": form_data["tipologia"],
            "valor_unidade": form_data["valor_unidade"],
            "volume_unidades": form_data["volume_unidades"],
        },
        "localizacao": localizacao,
        "dados_ibge": dados_ibge,
        "dados_publicos": dados_publicos,
        "dados_normalizados": dados_normalizados,
        "resultado_score": resultado_score,
        "resultado_verba": resultado_verba,
        "perfil_publico": perfil_publico,
        "mix_midias": mixes,
        "recomendacoes_estrategicas": recomendacoes,
        "sugestao_localizacao": sugestao_localizacao,
        "qualidade_dados": {"texto": qualidade_texto, "cor": qualidade_cor},
    }


def render_kpis(resultados: dict) -> None:
    score = resultados["resultado_score"]
    base = resultados["resultado_verba"]["cenarios"]["base"]
    qualidade = resultados["qualidade_dados"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score / 100", f"{score['score_final']}")
    col2.metric("VGV Total", formatar_moeda(resultados["resultado_verba"]["vgv"]))
    col3.metric("Verba Base", formatar_moeda(base["verba_r$"]))
    col4.metric("Custo/Unidade Base", formatar_moeda(base["custo_unidade"]))
    st.markdown(
        badge_html(qualidade["texto"], qualidade["cor"]) + " " +
        badge_html(score["classificacao"], score["cor"]),
        unsafe_allow_html=True,
    )
    if score.get("ajuste_macro") or score.get("ajuste_mercado_local"):
        st.caption(
            f"Score base: {score.get('score_base', score['score_final'])}/100 | "
            f"Ajuste macro: {score.get('ajuste_macro', 0):+.1f} | "
            f"Ajuste mercado local: {score.get('ajuste_mercado_local', 0):+.1f}"
        )

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score["score_final"],
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": CORES[score["cor"]]},
                "bgcolor": CORES["fundo"],
                "steps": [
                    {"range": [0, 30], "color": "#DCFCE7"},
                    {"range": [30, 50], "color": "#FEF3C7"},
                    {"range": [50, 70], "color": "#FFEDD5"},
                    {"range": [70, 100], "color": "#FEE2E2"},
                ],
            },
        )
    )
    fig_gauge.update_layout(
        paper_bgcolor=CORES["fundo"],
        plot_bgcolor=CORES["fundo"],
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)


def render_contexto_macro_kpis(resultados: dict) -> None:
    dados_bcb = resultados["dados_publicos"]["bcb"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selic", formatar_valor_contexto(dados_bcb.get("selic", {}).get("valor"), "pct"))
    col2.metric(
        "Juros Imobiliario",
        formatar_valor_contexto(dados_bcb.get("juros_imobiliario", {}).get("valor"), "pct"),
    )
    col3.metric(
        "Credito Imobiliario",
        formatar_valor_contexto(dados_bcb.get("concessoes_credito", {}).get("valor"), "bilhoes"),
    )
    col4.metric("INCC-DI", formatar_valor_contexto(dados_bcb.get("incc", {}).get("valor"), "pct"))


def _texto_impacto_bcb(chave: str, valor: float | None) -> str:
    if valor is None:
        return "Sem leitura recente disponivel para interpretacao automatica."
    if chave == "selic":
        return "Juros mais baixos tendem a facilitar a decisao do comprador." if valor < 10 else "Juros altos tornam o credito mais seletivo e podem alongar a venda."
    if chave == "juros_imobiliario":
        return "Financiamento mais acessivel ajuda a converter ticket medio." if valor < 9 else "Custo do financiamento ainda pressiona a conversao do comprador."
    if chave == "ivg_r":
        return "Preco de imoveis em alta reforca percepcao de valorizacao." if valor > 0 else "Mercado sem sinal forte de valorizacao recente."
    if chave == "incc":
        return "Custo de obra moderado ajuda o empreendedor a preservar margem." if valor < 8 else "Custo de construcao em alta pressiona margem e precificacao."
    return "Indicador usado como contexto macro do mercado imobiliario."


def render_tab_score(resultados: dict) -> None:
    df_breakdown = montar_breakdown_df(resultados["resultado_score"])
    fig = px.bar(
        df_breakdown.sort_values("Contribuicao"),
        x="Contribuicao",
        y="Variavel",
        orientation="h",
        color="Categoria",
        color_discrete_map={
            "Dados IBGE": CORES["azul_escuro"],
            "Atributos do empreendimento": CORES["dourado"],
        },
    )
    fig.update_layout(paper_bgcolor=CORES["fundo"], plot_bgcolor=CORES["fundo"], height=440)
    st.plotly_chart(fig, use_container_width=True)

    tabela = df_breakdown.copy()
    tabela["Peso"] = tabela["Peso"].apply(lambda x: f"{x:.0%}")
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.markdown("### Top 3 fatores criticos")
    cols = st.columns(3)
    top3 = df_breakdown.sort_values("Contribuicao", ascending=False).head(3).to_dict("records")
    for col, item in zip(cols, top3):
        with col:
            card(
                item["Variavel"].replace("_", " ").title(),
                (
                    f"<p style='margin:0 0 8px 0;color:#6B7280;'>{item['Interpretacao']}</p>"
                    f"<p style='margin:0;font-weight:700;color:#DC2626;'>Contribuicao: {item['Contribuicao']:.2f}</p>"
                ),
                cor_borda="#FCA5A5",
                icone="⚠️",
            )


    justificativas = resultados["resultado_score"].get("justificativa_macro", []) + resultados["resultado_score"].get("justificativa_mercado_local", [])
    if justificativas:
        st.markdown("### Ajustes Contextuais")
        for texto in justificativas:
            st.markdown(f"- {texto}")


def render_tab_cenarios(resultados: dict) -> None:
    cenarios = resultados["resultado_verba"]["cenarios"]
    cols = st.columns(3)
    meta = {
        "conservador": ("🔵 Conservador", "#DBEAFE"),
        "base": ("⚡ Base", "#FEF3C7"),
        "agressivo": ("🔴 Agressivo", "#FEE2E2"),
    }
    for idx, nome in enumerate(("conservador", "base", "agressivo")):
        dados = cenarios[nome]
        titulo, fundo = meta[nome]
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background:{fundo}; border:1px solid #E5DDD0; border-radius:12px; padding:16px; min-height:220px;">
                  <div style="font-weight:800; color:#1B2A4A; margin-bottom:8px;">{titulo}</div>
                  <div style="font-size:1.4rem; font-weight:800; color:#1B2A4A;">{formatar_moeda(dados['verba_r$'])}</div>
                  <div style="color:#6B7280; font-size:0.85rem; margin-bottom:10px;">{formatar_percentual(dados['percentual'])} do VGV</div>
                  <div style="font-size:0.92rem; color:#1B2A4A;"><strong>Leads:</strong> {dados['leads_estimados']:.0f}</div>
                  <div style="font-size:0.92rem; color:#1B2A4A;"><strong>Vendas estimadas:</strong> {dados['vendas_estimadas']:.1f}</div>
                  <div style="font-size:0.92rem; color:#1B2A4A;"><strong>ROAS:</strong> {formatar_roas(dados['roas'])}</div>
                  <div style="margin-top:10px; color:#6B7280; font-size:0.82rem;">{dados['resultado_esperado']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    df_tabela = montar_tabela_cenarios(resultados)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    linhas = []
    for nome, dados in cenarios.items():
        linhas.extend(
            [
                {"Cenario": nome.capitalize(), "Indicador": "Verba", "Valor": dados["verba_r$"]},
                {"Cenario": nome.capitalize(), "Indicador": "Leads", "Valor": dados["leads_estimados"]},
                {"Cenario": nome.capitalize(), "Indicador": "Vendas", "Valor": dados["vendas_estimadas"]},
            ]
        )
    fig = px.bar(pd.DataFrame(linhas), x="Cenario", y="Valor", color="Indicador", barmode="group")
    fig.update_layout(paper_bgcolor=CORES["fundo"], plot_bgcolor=CORES["fundo"], height=420)
    st.plotly_chart(fig, use_container_width=True)


def render_mix_cenario(nome_cenario: str, mix: dict) -> None:
    canais = mix["canais"]
    total_budget = sum(dados["budget_r$"] for dados in canais.values())
    total_leads = sum(dados["leads_estimados"] for dados in canais.values())
    canal_lider = max(canais.items(), key=lambda item: item[1]["budget_r$"])[0]
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Budget do cenario", formatar_moeda(total_budget))
    col_b.metric("Leads estimados", f"{total_leads:.0f}")
    col_c.metric("Canal lider", canal_lider)

    df_mix = pd.DataFrame(
        [
            {
                "Canal": canal,
                "%": dados["percentual"],
                "Budget R$": dados["budget_r$"],
                "CPL Est.": dados["cpl_estimado"],
                "Leads Est.": dados["leads_estimados"],
                "Taticas Principais": " | ".join(dados["taticas"]),
            }
            for canal, dados in canais.items()
        ]
    )
    cols = st.columns([1, 1])
    with cols[0]:
        fig = px.pie(
            df_mix,
            names="Canal",
            values="%",
            color="Canal",
            color_discrete_map=CORES_CANAIS,
        )
        fig.update_layout(
            paper_bgcolor=CORES["fundo"],
            plot_bgcolor=CORES["fundo"],
            legend_title_text="Canais",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"mix_pizza_{nome_cenario}")
    with cols[1]:
        df_show = df_mix.copy()
        df_show["%"] = df_show["%"].map(lambda x: f"{x:.1f}%")
        df_show["Budget R$"] = df_show["Budget R$"].map(formatar_moeda)
        df_show["CPL Est."] = df_show["CPL Est."].map(formatar_moeda)
        df_show["Leads Est."] = df_show["Leads Est."].map(lambda x: f"{x:.0f}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    st.markdown("### Canais Prioritarios")
    cards = st.columns(2)
    for idx, (canal, dados) in enumerate(sorted(canais.items(), key=lambda item: item[1]["budget_r$"], reverse=True)):
        with cards[idx % 2]:
            conteudo = (
                f"<p style='margin:0 0 8px 0;'><strong>Budget:</strong> {formatar_moeda(dados['budget_r$'])} "
                f"({dados['percentual']:.1f}%)</p>"
                f"<p style='margin:0 0 8px 0;'><strong>CPL:</strong> {formatar_moeda(dados['cpl_estimado'])} | "
                f"<strong>Leads:</strong> {dados['leads_estimados']:.0f}</p>"
                + "".join(f"<p style='margin:0 0 6px 0;'>• {tatica}</p>" for tatica in dados["taticas"])
            )
            card(canal, conteudo, cor_borda=dados["cor"], icone=dados["icone"])


def render_tab_mix(resultados: dict) -> None:
    st.markdown(
        "<p style='color:#6B7280;'>Cada aba mostra a distribuicao recomendada de budget, os canais lideres e o potencial de geracao de leads por cenario.</p>",
        unsafe_allow_html=True,
    )
    tab_cons, tab_base, tab_agr = st.tabs(["🔵 Conservador", "⚡ Base (Recomendado)", "🔴 Agressivo"])
    with tab_cons:
        render_mix_cenario("conservador", resultados["mix_midias"]["conservador"])
    with tab_base:
        render_mix_cenario("base", resultados["mix_midias"]["base"])
    with tab_agr:
        render_mix_cenario("agressivo", resultados["mix_midias"]["agressivo"])


def render_tab_publico(resultados: dict) -> None:
    perfil = resultados["perfil_publico"]
    c1, c2 = st.columns(2)
    with c1:
        card(
            "Perfil Demografico",
            (
                f"<p><strong>Faixa primaria:</strong> {perfil['faixa_etaria_primaria']}</p>"
                f"<p><strong>Faixa secundaria:</strong> {perfil['faixa_etaria_secundaria']}</p>"
                f"<p><strong>Renda familiar:</strong> {perfil['renda_familiar_estimada']}</p>"
                f"<p><strong>Escolaridade:</strong> {perfil['escolaridade']}</p>"
            ),
            icone="👤",
        )
        card(
            "Motivacoes de Compra",
            "".join(f"<p>✅ {item}</p>" for item in perfil["motivacoes_compra"]),
            cor_borda="#F5C84A",
            icone="🎯",
        )
        card(
            "Onde Encontrar esse Publico",
            "".join(
                f"<p><strong>{item['canal']}:</strong> {item['descricao']}</p>"
                for item in perfil["canais_preferidos"]
            ),
            icone="📡",
        )
    with c2:
        card(
            "Comportamento",
            "".join(f"<p>🔹 {item}</p>" for item in perfil["perfil_comportamental"]),
            icone="🧠",
        )
        card(
            "Objecoes Tipicas",
            "".join(
                f"<p>⚠️ {obj}<br><span style='color:#6B7280;'>Resposta sugerida: {perfil['respostas_objecoes'][obj]}</span></p>"
                for obj in perfil["objecoes_tipicas"]
            ),
            cor_borda="#FDBA74",
            icone="🛡️",
        )
        card(
            "Mensagem-Chave Recomendada",
            f"<p style='font-size:1.05rem; font-weight:700; color:#1B2A4A;'>{perfil['mensagem_chave']}</p>",
            cor_borda="#E8A020",
            icone="✨",
        )


def render_tab_contexto_mercado(resultados: dict) -> None:
    dados_publicos = resultados["dados_publicos"]
    dados_bcb = dados_publicos["bcb"]
    dados_ipea = dados_publicos["ipea"]
    dados_trends = dados_publicos["trends"]
    favorabilidade = calcular_favorabilidade_mercado(dados_bcb, dados_ipea, dados_trends)

    st.markdown("### Cenário Macroeconômico Atual")
    render_contexto_macro_kpis(resultados)
    macro_cols = st.columns(3)
    cards_macro = [
        ("Selic", dados_bcb.get("selic", {}).get("valor"), "pct", _texto_impacto_bcb("selic", dados_bcb.get("selic", {}).get("valor"))),
        ("Juros Financiamento", dados_bcb.get("juros_imobiliario", {}).get("valor"), "pct", _texto_impacto_bcb("juros_imobiliario", dados_bcb.get("juros_imobiliario", {}).get("valor"))),
        ("IVG-R", dados_bcb.get("ivg_r", {}).get("valor"), "indice", _texto_impacto_bcb("ivg_r", dados_bcb.get("ivg_r", {}).get("valor"))),
    ]
    for idx, (titulo, valor, formato, texto) in enumerate(cards_macro):
        with macro_cols[idx]:
            card(
                titulo,
                f"<p style='font-size:1.25rem; font-weight:800; color:#1B2A4A;'>{formatar_valor_contexto(valor, formato)}</p><p style='margin:0; color:#6B7280;'>{texto}</p>",
                cor_borda="#D6C5A0",
                icone="📊",
            )

    st.markdown("### Contexto Local")
    local_cols = st.columns(4)
    local_cols[0].metric("PIB per capita", formatar_valor_contexto(dados_ipea.get("pib_percapita", {}).get("valor"), "moeda"))
    local_cols[1].metric("Gini", formatar_valor_contexto(dados_ipea.get("gini", {}).get("valor"), "indice"))
    local_cols[2].metric("Desemprego", formatar_valor_contexto(dados_ipea.get("desemprego", {}).get("valor"), "pct"))
    local_cols[3].metric("IDHM", formatar_valor_contexto(dados_publicos["idhm"].get("idhm"), "indice"))

    st.markdown("### Demanda Digital")
    tendencia = dados_trends.get("tendencia_recente", "indisponivel")
    badge = "badge-verde" if tendencia == "crescendo" else "badge-amarelo" if tendencia == "estavel" else "badge-vermelho"
    st.markdown(f"<span class='{badge}'>Tendência: {tendencia.title()}</span>", unsafe_allow_html=True)
    serie = dados_trends.get("serie_interesse", [])
    if serie:
        df_trends = pd.DataFrame(serie)
        fig = px.line(df_trends, x="data", y="interesse", markers=True, title="Interesse de busca nos últimos 12 meses")
        fig.update_layout(paper_bgcolor=CORES["fundo"], plot_bgcolor=CORES["fundo"], height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Google Trends indisponível no momento. O score usa fallback neutro quando essa fonte nao responde.")

    st.markdown("### Índice de Favorabilidade do Mercado")
    col_a, col_b = st.columns([1, 2])
    col_a.metric("Favorabilidade", f"{favorabilidade['score']}/10")
    col_b.markdown(
        f"<div style='padding-top:8px; font-size:1rem; font-weight:700; color:#1B2A4A;'>{favorabilidade['classificacao']}</div>"
        f"<div style='color:#6B7280; margin-top:6px;'>Leitura combinada de juros, emprego e demanda digital para avaliar o timing do lançamento.</div>",
        unsafe_allow_html=True,
    )


def render_tab_ibge(resultados: dict) -> None:
    st.markdown("### Fontes de Dados Utilizadas")
    df_fontes = pd.DataFrame(FONTES_DE_DADOS)
    df_fontes["gratuita"] = df_fontes["gratuita"].map(lambda x: "Sim" if x else "Nao")
    df_fontes["requer_key"] = df_fontes["requer_key"].map(lambda x: "Sim" if x else "Nao")
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("Fontes mapeadas", f"{len(df_fontes)}")
    col_f2.metric("Ativas agora", f"{(pd.DataFrame(FONTES_DE_DADOS)['status_integracao'].str.contains('Ativa')).sum()}")
    col_f3.metric("Dependem de chave/conta", f"{(pd.DataFrame(FONTES_DE_DADOS)['requer_key']).sum()}")
    st.dataframe(df_fontes, use_container_width=True, hide_index=True)

    st.markdown("### Dados Municipais e Normalizacao")
    linhas = []
    for chave, dados in resultados["dados_ibge"].items():
        if chave == "codigo_ibge":
            continue
        mediana = dados.get("mediana_nacional")
        valor = dados.get("valor")
        comparacao = "-"
        if isinstance(valor, (int, float)) and isinstance(mediana, (int, float)):
            comparacao = "▲ acima da media" if valor >= mediana else "▼ abaixo da media"
        chave_norm = {
            "renda_media_domiciliar": "renda_media",
            "faixa_etaria_predominante": "faixa_etaria",
            "densidade_populacional": "densidade",
            "proporcao_alugados": "proporcao_alugados",
            "crescimento_populacional": "crescimento_pop",
            "escolaridade": "escolaridade",
            "idh": "idh",
        }.get(chave, chave)
        linhas.append(
            {
                "Variavel": chave,
                "Valor para o Municipio": valor,
                "Mediana Nacional": mediana,
                "Comparacao": comparacao,
                "Valor Normalizado (0-10)": resultados["dados_normalizados"].get(chave_norm),
                "Fonte": dados.get("fonte_detalhe"),
                "Confiabilidade": "REAL" if dados.get("fonte") == "api" else "ESTIMATIVA",
            }
        )
    df_ibge = pd.DataFrame(linhas)
    reais = (df_ibge["Confiabilidade"] == "REAL").sum()
    estimativas = (df_ibge["Confiabilidade"] == "ESTIMATIVA").sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Indicadores utilizados", f"{len(df_ibge)}")
    col2.metric("Dados reais", f"{reais}")
    col3.metric("Estimativas", f"{estimativas}")
    st.dataframe(df_ibge, use_container_width=True, hide_index=True)

    st.markdown("### Novas Fontes Complementares")
    complementares = [
        {
            "Fonte": "BCB/SGS",
            "Resumo": formatar_valor_contexto(resultados["dados_publicos"]["bcb"].get("selic", {}).get("valor"), "pct"),
            "Status": resultados["dados_publicos"]["bcb"].get("selic", {}).get("fonte"),
        },
        {
            "Fonte": "Ipeadata",
            "Resumo": formatar_valor_contexto(resultados["dados_publicos"]["ipea"].get("pib_percapita", {}).get("valor"), "moeda"),
            "Status": resultados["dados_publicos"]["ipea"].get("pib_percapita", {}).get("fonte"),
        },
        {
            "Fonte": "Atlas Brasil",
            "Resumo": formatar_valor_contexto(resultados["dados_publicos"]["idhm"].get("idhm"), "indice"),
            "Status": resultados["dados_publicos"]["idhm"].get("fonte"),
        },
        {
            "Fonte": "Google Trends",
            "Resumo": str(resultados["dados_publicos"]["trends"].get("score_interesse", 50)),
            "Status": resultados["dados_publicos"]["trends"].get("fonte"),
        },
    ]
    st.dataframe(pd.DataFrame(complementares), use_container_width=True, hide_index=True)

    df_heat = montar_breakdown_df(resultados["resultado_score"])[["Variavel", "Contribuicao"]]
    fig_heat = px.bar(
        df_heat.sort_values("Contribuicao", ascending=False),
        x="Contribuicao",
        y="Variavel",
        orientation="h",
        color="Contribuicao",
        color_continuous_scale=["#FAF8F5", "#E8A020", "#1B2A4A"],
        title="Variaveis com maior peso no score",
    )
    fig_heat.update_layout(
        paper_bgcolor=CORES["fundo"],
        plot_bgcolor=CORES["fundo"],
        height=320,
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_heat, use_container_width=True, key="ibge_peso_score")


def render_dashboard(resultados: dict) -> None:
    render_kpis(resultados)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📊 Score Detalhado",
            "💰 Projecao de Cenarios",
            "📡 Mix de Midia",
            "👥 Publico-Alvo",
            "📈 Contexto de Mercado",
            "📋 Dados Utilizados",
        ]
    )
    with tab1:
        render_tab_score(resultados)
    with tab2:
        render_tab_cenarios(resultados)
    with tab3:
        render_tab_mix(resultados)
    with tab4:
        render_tab_publico(resultados)
    with tab5:
        render_tab_contexto_mercado(resultados)
    with tab6:
        render_tab_ibge(resultados)

    st.subheader("Exportar Apresentacao")
    pdf_bytes = gerar_pdf(resultados)
    cidade = resultados["localizacao"]["municipio"].replace(" ", "_").lower()
    st.download_button(
        label="📄 Baixar apresentacao executiva em PDF",
        data=pdf_bytes,
        file_name=f"launchscore_{cidade}_{date.today()}.pdf",
        mime="application/pdf",
    )
    render_copy_button(montar_resumo_compartilhamento(resultados))


def secao_resultado(titulo: str, subtitulo: str | None = None) -> None:
    st.markdown(
        f"""
        <div style="margin:28px 0 14px 0;">
          <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.10em; text-transform:uppercase; color:#E8A020; margin-bottom:6px;">
            Leitura executiva
          </div>
          <div style="font-size:1.45rem; font-weight:800; color:#1B2A4A;">{titulo}</div>
          {f'<div style="font-size:0.95rem; color:#6B7280; margin-top:6px; max-width:920px;">{subtitulo}</div>' if subtitulo else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_story(resultados: dict) -> None:
    score = resultados["resultado_score"]
    base = resultados["resultado_verba"]["cenarios"]["base"]

    secao_resultado(
        "1. Resumo do caso",
        "Comece aqui: este bloco resume a situacao comercial do empreendimento e qual intensidade de investimento faz mais sentido como ponto de partida.",
    )
    st.markdown("### Cenário Macroeconômico Atual")
    render_contexto_macro_kpis(resultados)
    render_kpis(resultados)
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E5DDD0; border-radius:12px; padding:18px 20px; box-shadow:0 2px 8px rgba(27,42,74,0.05);">
          <div style="font-size:1rem; font-weight:700; color:#1B2A4A; margin-bottom:8px;">Sintese executiva</div>
          <div style="font-size:0.95rem; color:#4B5563; line-height:1.65;">
            O empreendimento <strong>{resultados['empreendimento']['nome']}</strong>, em
            <strong>{resultados['localizacao']['municipio']} - {resultados['localizacao']['uf']}</strong>,
            apresenta score de <strong>{score['score_final']}/100</strong>, classificado como
            <strong>{score['classificacao']}</strong>. O ponto de partida recomendado e o
            <strong>cenario base</strong>, com investimento de <strong>{formatar_moeda(base['verba_r$'])}</strong>,
            equivalente a <strong>{formatar_percentual(base['percentual'])}</strong> do VGV.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    secao_resultado(
        "2. O que explica o score",
        "Esta etapa mostra os fatores que mais pesam na dificuldade de venda e onde a estrategia precisa agir primeiro.",
    )
    render_tab_score(resultados)

    secao_resultado(
        "3. Quanto investir",
        "Agora a leitura financeira fica clara: compare conservador, base e agressivo como alternativas de intensidade comercial.",
    )
    render_tab_cenarios(resultados)

    secao_resultado(
        "4. Onde alocar a verba",
        "Depois da decisao de investimento, a distribuicao entre canais mostra quais frentes lideram a estrategia em cada cenario.",
    )
    render_tab_mix(resultados)

    secao_resultado(
        "5. Para quem comunicar",
        "Com a verba e os canais definidos, o proximo passo e alinhar mensagem, objecoes e tom comercial ao publico mais aderente ao ticket e ao contexto local.",
    )
    render_tab_publico(resultados)

    secao_resultado(
        "6. Contexto de mercado",
        "Antes da decisao final, vale ler o pano de fundo macro, local e de demanda digital que pode acelerar ou frear o lancamento.",
    )
    render_tab_contexto_mercado(resultados)

    secao_resultado(
        "7. Evidencias que sustentam a analise",
        "Aqui ficam os indicadores publicos utilizados, a comparacao com referencias nacionais e a confiabilidade dos dados.",
    )
    render_tab_ibge(resultados)

    st.subheader("Exportar Apresentacao")
    pdf_bytes = gerar_pdf(resultados)
    cidade = resultados["localizacao"]["municipio"].replace(" ", "_").lower()
    st.download_button(
        label="Baixar apresentacao executiva em PDF",
        data=pdf_bytes,
        file_name=f"launchscore_{cidade}_{date.today()}.pdf",
        mime="application/pdf",
    )
    render_copy_button(montar_resumo_compartilhamento(resultados))


def render_footer() -> None:
    st.markdown("---")
    exibir_footer_termos()


def main() -> None:
    injetar_css()
    view = st.query_params.get("view", "")
    if isinstance(view, list):
        view = view[0] if view else ""
    if view == "termos":
        render_pagina_termos()
        return
    render_sidebar()
    render_header_executive()
    if "historico" not in st.session_state:
        st.session_state["historico"] = []
    if "etapa_ativa" not in st.session_state:
        st.session_state["etapa_ativa"] = "1. Dados do Empreendimento"

    etapa_ativa = st.radio(
        "Navegacao",
        ["1. Dados do Empreendimento", "2. Processamento", "3. Dashboard de Resultados"],
        index=["1. Dados do Empreendimento", "2. Processamento", "3. Dashboard de Resultados"].index(st.session_state["etapa_ativa"]),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["etapa_ativa"] = etapa_ativa

    if etapa_ativa == "1. Dados do Empreendimento":
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown('<div class="bloco-form">', unsafe_allow_html=True)
            st.markdown("## Dados do Empreendimento")
            nome_empreendimento = st.text_input("Nome do empreendimento", placeholder="Ex: Vista Mar Residence")
            cep = st.text_input("CEP do empreendimento", placeholder="00000-000", max_chars=9)
            cidade_manual = st.text_input("Cidade (fallback)", placeholder="Ex: Fortaleza - CE")
            tipologia = st.selectbox("Tipologia", ["Lotes", "Apartamentos"])
            valor_unidade = st.number_input("Valor por unidade (R$)", min_value=50000, step=10000, value=650000)
            volume_unidades = st.number_input("Numero de unidades", min_value=1, max_value=5000, step=1, value=120)
            sugestao = obter_sugestao_localizacao(cep, cidade_manual)
            if sugestao:
                detalhes_localizacao = []
                if sugestao.get("bairro"):
                    detalhes_localizacao.append(f"Bairro identificado: {sugestao['bairro']}.")
                if sugestao.get("rua"):
                    detalhes_localizacao.append(f"Endereco de referencia: {sugestao['rua']}.")
                st.info(
                    f"Sugestao automatica de localizacao a partir do CEP/cidade: "
                    f"{sugestao['score_sugerido']}/5. {sugestao['resumo']} "
                    f"{' '.join(detalhes_localizacao)}"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="bloco-form">', unsafe_allow_html=True)
            st.markdown("## Atributos do Empreendimento")
            concorrencia = slider_com_descricao(
                "Concorrencia",
                "🏁",
                "Quantos empreendimentos similares estao sendo comercializados no mesmo raio de influencia",
                "Mercado saturado",
                "Sem concorrentes",
                "concorrencia",
            )
            localizacao_default = sugestao["score_sugerido"] if sugestao else 3
            localizacao = slider_com_descricao(
                "Localizacao",
                "📍",
                "Qualidade da localizacao considerando acessibilidade, infraestrutura e percepcao de valor",
                "Localizacao fraca",
                "Localizacao premium",
                "localizacao",
                default=localizacao_default,
            )
            inovacao = slider_com_descricao(
                "Inovacao",
                "💡",
                "O quanto o produto se diferencia do padrao de mercado em conceito, arquitetura ou proposta",
                "Produto padrao",
                "Altamente inovador",
                "inovacao",
            )
            tracao = slider_com_descricao(
                "Tracao",
                "📈",
                "Vendas ja realizadas, fila de espera, interesse comprovado ou historico de lancamentos anteriores",
                "Sem tracao",
                "Forte tracao",
                "tracao",
            )
            funcionalidades = slider_com_descricao(
                "Funcionalidades",
                "⚙️",
                "Quantidade e qualidade de diferenciais (lazer, tecnologia, sustentabilidade, acabamento)",
                "Funcionalidades basicas",
                "Produto completo",
                "funcionalidades",
            )
            conexao_luxo = slider_com_descricao(
                "Conexao com luxo",
                "💎",
                "Alinhamento do produto com o posicionamento premium ou aspiracional de mercado",
                "Produto popular",
                "Altamente aspiracional",
                "conexao_luxo",
            )
            st.markdown(
                """
<p style="font-size:0.75rem; color:#9CA3AF; text-align:center; margin-top:8px;">
  Ao calcular, voce concorda com os
  <a href="?view=termos" target="_blank" style="color:#E8A020; font-weight:700; text-decoration:none;">Termos de Uso</a> da plataforma.
</p>
<br>
                """,
                unsafe_allow_html=True,
            )
            calcular = st.button("🚀 Calcular Score e Gerar Relatorio", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        form_data = {
            "nome_empreendimento": nome_empreendimento,
            "cep": cep,
            "cidade_manual": cidade_manual,
            "tipologia": tipologia,
            "valor_unidade": valor_unidade,
            "volume_unidades": volume_unidades,
            "concorrencia": concorrencia,
            "localizacao": localizacao,
            "inovacao": inovacao,
            "tracao": tracao,
            "funcionalidades": funcionalidades,
            "conexao_luxo": conexao_luxo,
        }

        if calcular:
            mensagens = validar_inputs(form_data)
            erros = [texto for tipo, texto in mensagens if tipo == "erro"]
            avisos = [texto for tipo, texto in mensagens if tipo == "aviso"]
            for aviso in avisos:
                st.warning(aviso)
            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                try:
                    st.session_state["resultados"] = processar_dados(form_data)
                    preparar_historico(st.session_state["resultados"])
                    st.session_state["etapa_ativa"] = "3. Dashboard de Resultados"
                    st.success("Analise concluida com sucesso. O dashboard ja esta pronto para abertura.")
                    if st.button("Abrir dashboard completo", use_container_width=True):
                        st.rerun()
                except Exception as exc:
                    st.error(f"Nao foi possivel concluir a analise: {exc}")

    if etapa_ativa == "2. Processamento":
        if "resultados" in st.session_state:
            st.markdown("## Processamento")
            st.json(
                {
                    "municipio": st.session_state["resultados"]["localizacao"]["municipio"],
                    "codigo_ibge": st.session_state["resultados"]["localizacao"]["codigo_ibge"],
                    "score": st.session_state["resultados"]["resultado_score"]["score_final"],
                    "confiabilidade": st.session_state["resultados"]["qualidade_dados"]["texto"],
                }
            )
        else:
            st.info("Preencha os dados na primeira etapa para iniciar o processamento.")

    if etapa_ativa == "3. Dashboard de Resultados":
        if "resultados" in st.session_state:
            render_dashboard_story(st.session_state["resultados"])
        else:
            st.info("Ainda nao ha resultados para exibir.")

    render_footer()


if __name__ == "__main__":
    main()
