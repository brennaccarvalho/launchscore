"""Aplicativo Streamlit principal do LaunchScore."""

from __future__ import annotations

import json
import re
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from config import CORES, CORES_CANAIS, TERMOS_USO_RESUMIDOS
from modules.audience import gerar_perfil_publico
from modules.budget_engine import calcular_verba, calcular_vgv
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


def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def formatar_roas(valor: float) -> str:
    return f"{valor:.1f} : 1".replace(".", ",")


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


@st.dialog("Termos de Uso")
def mostrar_termos_dialogo() -> None:
    st.markdown("### Termos de Uso")
    st.write(TERMOS_USO_RESUMIDOS)
    st.markdown(
        """
**Clausulas de propriedade intelectual**

- A metodologia de score, os algoritmos de calculo e a interface da plataforma sao propriedade intelectual da autora.
- O uso comercial, redistribuicao ou reproducao dependem de autorizacao expressa.
- Os resultados nao substituem analise financeira, comercial ou juridica independente.
        """
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
        if st.button("📄 Ver Termos de Uso", use_container_width=True):
            mostrar_termos_dialogo()
        if "historico" in st.session_state and st.session_state["historico"]:
            st.markdown("---")
            st.markdown("### Analises recentes")
            for item in st.session_state["historico"][-3:][::-1]:
                st.markdown(
                    f"- **{item['nome']}** ({item['cidade']})  \n"
                    f"Score {item['score']}/100 | Verba base {item['verba']}"
                )
        st.markdown("---")
        st.markdown(
            """
        <div style="font-size:0.72rem; color:#9CA3AF; text-align:center; padding:8px;">
          © 2026 Brenna Carvalho<br>
          LaunchScore - Todos os direitos reservados<br>
          <a href="https://www.linkedin.com/in/brennacarvalho/" target="_blank" style="color:#E8A020;">LinkedIn</a> ·
          <span style="color:#E8A020;">Termos de Uso</span>
        </div>
            """,
            unsafe_allow_html=True,
        )


def preparar_historico(resultados: dict) -> None:
    if "historico" not in st.session_state:
        st.session_state["historico"] = []
    resumo = {
        "nome": resultados["empreendimento"]["nome"],
        "cidade": resultados["localizacao"]["municipio"],
        "score": resultados["resultado_score"]["score_final"],
        "verba": formatar_moeda(resultados["resultado_verba"]["cenarios"]["base"]["verba_r$"]),
    }
    historico = [item for item in st.session_state["historico"] if item["nome"] != resumo["nome"]]
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
    progresso = st.progress(0, text="Iniciando processamento...")
    mensagens = [
        "🔍 Consultando IBGE para dados do municipio...",
        "📊 Calculando score de dificuldade de venda...",
        "💰 Projetando verba e cenarios de investimento...",
        "📡 Montando mix de midia recomendado...",
        "👥 Definindo perfil de publico-alvo...",
        "✅ Relatorio pronto!",
    ]

    localizacao = None
    if form_data["cep"]:
        try:
            progresso.progress(10, text="Localizando municipio pelo CEP...")
            localizacao = get_municipio_by_cep(form_data["cep"])
        except Exception:
            st.warning("Nao foi possivel localizar o CEP automaticamente. Usando busca manual por cidade.")

    if localizacao is None:
        progresso.progress(20, text="Buscando municipio pela cidade informada...")
        localizacao = buscar_municipio_por_nome(form_data["cidade_manual"])

    progresso.progress(35, text=mensagens[0].replace("municipio", localizacao["municipio"]))
    dados_ibge = get_dados_ibge(localizacao["codigo_ibge"])
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
    progresso.progress(52, text=mensagens[1])
    resultado_score = calcular_score(dados_normalizados, atributos)

    vgv = calcular_vgv(form_data["valor_unidade"], form_data["volume_unidades"])
    progresso.progress(68, text=mensagens[2])
    resultado_verba = calcular_verba(
        vgv=vgv,
        score=resultado_score["score_final"],
        tipologia=form_data["tipologia"].lower(),
        volume_unidades=form_data["volume_unidades"],
        valor_unidade=form_data["valor_unidade"],
    )

    progresso.progress(82, text=mensagens[3])
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

    progresso.progress(92, text=mensagens[4])
    perfil_publico = gerar_perfil_publico(dados_ibge, form_data["tipologia"], form_data["valor_unidade"])

    progresso.progress(100, text=mensagens[5])
    qualidade_texto, qualidade_cor = calcular_qualidade_dados(dados_ibge)
    recomendacoes = (
        f"{resultado_score['justificativa_texto']} "
        f"O cenario base concentra {formatar_moeda(resultado_verba['cenarios']['base']['verba_r$'])} "
        f"em uma faixa considerada {resultado_verba['cenarios']['base']['benchmark_comparacao'].lower()} para o setor."
    )
    return {
        "empreendimento": {
            "nome": form_data.get("nome_empreendimento") or "Empreendimento analisado",
            "tipologia": form_data["tipologia"],
            "valor_unidade": form_data["valor_unidade"],
            "volume_unidades": form_data["volume_unidades"],
        },
        "localizacao": localizacao,
        "dados_ibge": dados_ibge,
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


def render_tab_cenarios(resultados: dict) -> None:
    df_tabela = montar_tabela_cenarios(resultados)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    linhas = []
    for nome, dados in resultados["resultado_verba"]["cenarios"].items():
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


def render_mix_cenario(mix: dict) -> None:
    canais = mix["canais"]
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
        fig.update_layout(paper_bgcolor=CORES["fundo"], plot_bgcolor=CORES["fundo"])
        st.plotly_chart(fig, use_container_width=True)
    with cols[1]:
        df_show = df_mix.copy()
        df_show["%"] = df_show["%"].map(lambda x: f"{x:.1f}%")
        df_show["Budget R$"] = df_show["Budget R$"].map(formatar_moeda)
        df_show["CPL Est."] = df_show["CPL Est."].map(formatar_moeda)
        df_show["Leads Est."] = df_show["Leads Est."].map(lambda x: f"{x:.0f}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    for canal, dados in canais.items():
        with st.expander(f"{dados['icone']} {canal}"):
            st.markdown(
                f"**Budget:** {formatar_moeda(dados['budget_r$'])} | "
                f"**Participacao:** {dados['percentual']:.1f}% | "
                f"**CPL:** {formatar_moeda(dados['cpl_estimado'])} | "
                f"**Leads esperados:** {dados['leads_estimados']:.0f}"
            )
            for tatica in dados["taticas"]:
                st.write(f"- {tatica}")


def render_tab_mix(resultados: dict) -> None:
    expander_flags = {"conservador": False, "base": True, "agressivo": False}
    for nome in ("conservador", "base", "agressivo"):
        with st.expander(f"Cenario {nome.capitalize()}", expanded=expander_flags[nome]):
            render_mix_cenario(resultados["mix_midias"][nome])


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


def render_tab_ibge(resultados: dict) -> None:
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
    st.dataframe(df_ibge, use_container_width=True, hide_index=True)

    df_heat = montar_breakdown_df(resultados["resultado_score"])[["Variavel", "Contribuicao"]]
    fig_heat = px.imshow(
        [df_heat["Contribuicao"].tolist()],
        x=df_heat["Variavel"].tolist(),
        y=["Peso no score"],
        color_continuous_scale=["#FAF8F5", "#E8A020", "#1B2A4A"],
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor=CORES["fundo"], plot_bgcolor=CORES["fundo"], height=260)
    st.plotly_chart(fig_heat, use_container_width=True)


def render_dashboard(resultados: dict) -> None:
    render_kpis(resultados)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Score Detalhado",
            "💰 Projecao de Cenarios",
            "📡 Mix de Midia",
            "👥 Publico-Alvo",
            "📋 Dados IBGE Utilizados",
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
        render_tab_ibge(resultados)

    st.subheader("Exportar Relatorio")
    pdf_bytes = gerar_pdf(resultados)
    cidade = resultados["localizacao"]["municipio"].replace(" ", "_").lower()
    st.download_button(
        label="📄 Baixar Relatorio Completo em PDF",
        data=pdf_bytes,
        file_name=f"launchscore_{cidade}_{date.today()}.pdf",
        mime="application/pdf",
    )
    render_copy_button(montar_resumo_compartilhamento(resultados))


def render_footer() -> None:
    st.markdown("---")
    st.markdown(
        """
<div style="background:#F0EDE8; border:1px solid #E5DDD0; border-radius:8px;
            padding:16px 24px; font-size:0.78rem; color:#6B7280; text-align:center;">
  <strong style="color:#1B2A4A;">LaunchScore</strong> e uma criacao de
  <strong style="color:#1B2A4A;">Brenna Carvalho</strong>. Todos os direitos reservados.<br>
  A metodologia de score, os algoritmos de calculo e a interface desta plataforma sao propriedade intelectual da autora.<br>
  O uso desta plataforma implica aceite dos <span style="color:#E8A020; font-weight:600;">Termos de Uso</span> ·
  <a href="https://www.linkedin.com/in/brennacarvalho/" target="_blank" style="color:#E8A020; font-weight:600;">LinkedIn</a>.
  Os resultados tem carater orientativo e nao constituem garantia de resultados financeiros.
</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    injetar_css()
    render_sidebar()
    render_header()
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    tabs = st.tabs(["1. Dados do Empreendimento", "2. Processamento", "3. Dashboard de Resultados"])

    with tabs[0]:
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
                st.info(
                    f"Sugestao automatica de localizacao a partir do CEP/cidade: "
                    f"{sugestao['score_sugerido']}/5. {sugestao['resumo']}"
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
            st.markdown("<br>", unsafe_allow_html=True)
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
                    st.success("Analise concluida com sucesso. Confira o dashboard.")
                except Exception as exc:
                    st.error(f"Nao foi possivel concluir a analise: {exc}")

    with tabs[1]:
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

    with tabs[2]:
        if "resultados" in st.session_state:
            render_dashboard(st.session_state["resultados"])
        else:
            st.info("Ainda nao ha resultados para exibir.")

    render_footer()


if __name__ == "__main__":
    main()
