# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.

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

from config import CORES, CORES_CANAIS, CORES_CENARIOS, FUNCIONALIDADES_IMOBILIARIAS
from modules.audience import gerar_perfil_publico
from modules.budget_engine import calcular_pressao_custos, calcular_verba, calcular_vgv
from modules.data_orchestrator import FONTES_DE_DADOS, calcular_favorabilidade_mercado, coletar_todos_dados
from modules.ibge_api import (
    buscar_municipio_por_nome,
    get_dados_ibge,
    get_municipio_by_cep,
    normalizar_para_score,
    sugerir_pontuacao_localizacao,
)
from modules.media_mix import BIBLIOTECA_CAMPANHAS, recomendar_mix
from modules.report_generator import gerar_pdf
from modules.score_engine import calcular_score
from modules.termos_de_uso import exibir_footer_termos, exibir_termos_modal, render_pagina_termos


def sanitizar_html(texto: str) -> str:
    """Escapa caracteres HTML em texto de entrada do usuario para prevenir XSS."""
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


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
  .fonte-tag {
    background:#FFF7E8; color:#1B2A4A; padding:2px 8px; border-radius:4px;
    font-size:0.72rem; border:1px solid #E8A020; display:inline-block; font-weight:700;
  }
  .bloco-form {
    background: rgba(255,255,255,0.55); border: 1px solid #E5DDD0; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 8px rgba(27,42,74,0.04); min-height: 100%;
  }
  .context-shell {
    background:#FFFFFF; border:1px solid #E5DDD0; border-radius:14px; padding:20px;
    box-shadow:0 8px 24px rgba(27,42,74,0.05); margin-bottom:18px;
  }
  .context-kicker {
    font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#E8A020; font-weight:700;
  }
  .context-title {
    font-size:1.25rem; font-weight:800; color:#1B2A4A; margin-top:6px; margin-bottom:6px;
  }
  .context-body {
    color:#6B7280; font-size:0.92rem; line-height:1.55;
  }

  /* ── Navegacao por etapas ── */
  .step-nav {
    display:flex; align-items:center; gap:0; margin:0 0 28px 0;
    background:#FFFFFF; border:1px solid #E5DDD0; border-radius:12px;
    overflow:hidden; box-shadow:0 2px 8px rgba(27,42,74,0.05);
  }
  .step-item {
    flex:1; display:flex; align-items:center; gap:10px;
    padding:14px 20px; cursor:pointer; border:none; background:transparent;
    border-right:1px solid #E5DDD0; transition:background 0.15s;
  }
  .step-item:last-child { border-right:none; }
  .step-item:hover { background:#F8F6F2; }
  .step-active { background:#1B2A4A !important; }
  .step-active .step-num { background:#E8A020; color:#1B2A4A; }
  .step-active .step-label { color:#FFFFFF; }
  .step-active .step-sub { color:#C7D2E2; }
  .step-done .step-num { background:#16A34A; color:#FFFFFF; }
  .step-num {
    width:28px; height:28px; border-radius:50%; background:#E5DDD0; color:#6B7280;
    font-size:0.78rem; font-weight:800; display:flex; align-items:center;
    justify-content:center; flex-shrink:0;
  }
  .step-label { font-size:0.9rem; font-weight:700; color:#1B2A4A; line-height:1.2; }
  .step-sub { font-size:0.75rem; color:#9CA3AF; margin-top:1px; }

  /* ── Formulario ── */
  .bloco-form {
    background:#FFFFFF; border:1px solid #E5DDD0; border-radius:14px;
    padding:24px 24px 20px 24px; box-shadow:0 2px 12px rgba(27,42,74,0.05);
    height:100%;
  }
  .form-section-title {
    font-size:0.72rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.10em; color:#E8A020; margin:20px 0 12px 0;
    padding-bottom:6px; border-bottom:1px solid #F0EDE8;
  }
  .form-section-title:first-child { margin-top:0; }
  .form-block-title {
    font-size:1.45rem; font-weight:800; color:#1B2A4A; letter-spacing:0.04em;
    text-transform:uppercase; margin:0 0 16px 0;
  }
  .input-hint {
    font-size:0.76rem; color:#9CA3AF; margin:-8px 0 12px 0;
  }

  /* ── Seletor de nivel de atributo (card + radio pills) ── */
  .attr-card {
    margin-bottom:8px;
  }
  .attr-title {
    font-size:0.88rem; font-weight:700; color:#1B2A4A; margin-bottom:3px;
  }
  .attr-desc {
    font-size:0.74rem; color:#6B7280; line-height:1.4; margin-bottom:4px;
  }
  .attr-extremos {
    display:flex; justify-content:space-between;
    font-size:0.68rem; color:#9CA3AF; margin-top:-8px; margin-bottom:22px;
  }
  .func-grid-note {
    font-size:0.76rem; color:#6B7280; line-height:1.45; margin:0 0 12px 0;
  }

  /* Pills para st.radio horizontal (atributos de nivel) */
  div[data-testid="stRadio"] div[role="radiogroup"] {
    display:flex; gap:5px; flex-wrap:nowrap;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] > label {
    flex:1; min-width:0; background:#F4F1EC; border:1.5px solid #E5DDD0;
    border-radius:8px; padding:9px 4px; text-align:center; cursor:pointer;
    margin:0; display:flex; justify-content:center; align-items:center;
    transition:background 0.12s, border-color 0.12s;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    background:#EAE5DC; border-color:#C9B99A;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background:#1B2A4A; border-color:#1B2A4A;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
    color:#E8A020;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display:none;
  }
  div[data-testid="stRadio"] div[role="radiogroup"] p {
    margin:0; font-weight:700; font-size:0.88rem; color:#4B5563;
  }

  /* ── Sugestao de localizacao ── */
  .suggestion-card {
    background:#F0F9FF; border:1px solid #BAE6FD; border-left:4px solid #0EA5E9;
    border-radius:8px; padding:10px 14px; margin:10px 0 4px 0;
    font-size:0.82rem; color:#0C4A6E; line-height:1.5;
  }
  .suggestion-card strong { color:#0369A1; }

  /* ── CTA area ── */
  .cta-area {
    background:linear-gradient(135deg,#F8F6F2,#FFFFFF);
    border:1px solid #E5DDD0; border-top:2px solid #E8A020;
    border-radius:10px; padding:16px 16px 12px 16px; margin-top:20px;
  }
  .cta-hint {
    font-size:0.75rem; color:#9CA3AF; text-align:center; margin-bottom:10px;
  }
  .cta-hint a { color:#E8A020; font-weight:700; text-decoration:none; }

  /* ── Navegacao: radio oculto; nav usa botoes reais ── */
  div[data-testid="stRadio"][data-nav-radio] { display:none !important; }
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
    if formato == "numero":
        return f"{float(valor):,.0f}".replace(",", ".")
    return f"{float(valor):.2f}".replace(".", ",")


def badge_html(texto: str, cor: str) -> str:
    return f'<span class="badge-{cor}">{texto}</span>'


_ETAPAS_NAV = [
    ("1. Dados do Empreendimento", "1", "Dados"),
    ("2. Processamento",           "2", "Processamento"),
    ("3. Dashboard de Resultados", "3", "Dashboard"),
]


def render_step_nav(etapa_ativa: str) -> None:
    """Navegacao unica entre etapas."""
    etapas_keys = [e[0] for e in _ETAPAS_NAV]
    idx_ativo = etapas_keys.index(etapa_ativa) if etapa_ativa in etapas_keys else 0
    cols = st.columns(len(_ETAPAS_NAV), gap="small")
    for idx, ((chave, num, label), col) in enumerate(zip(_ETAPAS_NAV, cols)):
        is_active = chave == etapa_ativa
        is_done = idx < idx_ativo
        prefixo = "OK " if is_done else f"{num} "
        with col:
            if st.button(
                f"{prefixo}{label}",
                key=f"step_nav_{num}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                disabled=is_active,
            ):
                st.session_state["etapa_ativa"] = chave
                st.rerun()


def tipos_campanha_por_canal(canal: str) -> list[str]:
    biblioteca = BIBLIOTECA_CAMPANHAS.get(canal, {})
    return [campanha.get("tipo", "") for campanha in biblioteca.get("campanhas", []) if campanha.get("tipo")]


def nivel_selector(
    label: str,
    descricao: str,
    extremo_esq: str,
    extremo_dir: str,
    key: str,
    default: int = 3,
) -> int:
    """Seletor de nivel 1-5 renderizado como pills (st.radio estilizado)."""
    st.markdown(
        f'<div class="attr-card">'
        f'<div class="attr-title">{label}</div>'
        f'<div class="attr-desc">{descricao}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    valor = st.radio(
        f"{label} (nivel de 1 a 5)",
        options=["1", "2", "3", "4", "5"],
        index=default - 1,
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )
    st.markdown(
        f'<div class="attr-extremos"><span>{extremo_esq}</span><span>{extremo_dir}</span></div>',
        unsafe_allow_html=True,
    )
    return int(valor)


def render_form_block_title(texto: str) -> None:
    st.markdown(f'<div class="form-block-title">{texto}</div>', unsafe_allow_html=True)


def coletar_funcionalidades_selecionadas() -> list[str]:
    st.markdown('<div class="attr-card"><div class="attr-title">Funcionalidades</div></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="func-grid-note">Marque os itens presentes no empreendimento. O score considera a cesta completa e o peso de cada amenidade.</div>',
        unsafe_allow_html=True,
    )
    selecionadas: list[str] = []
    colunas = st.columns(2, gap="large")
    for idx, item in enumerate(FUNCIONALIDADES_IMOBILIARIAS):
        with colunas[idx % 2]:
            if st.checkbox(item["label"], key=f"func_item_{item['id']}"):
                selecionadas.append(item["id"])
    return selecionadas


def slider_com_descricao(
    label: str,
    icone: str,
    descricao: str,
    extremo_esq: str,
    extremo_dir: str,
    key: str,
    default: int = 3,
) -> int:
    """Mantido para compatibilidade; delega para nivel_selector."""
    return nivel_selector(label, descricao, extremo_esq, extremo_dir, key, default)


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


def area_feedback_cta(ui=st):
    container = ui.container()
    _, col_feedback, _ = container.columns([0.04, 0.92, 0.04])
    return col_feedback


def _dados_cenarios_grafico() -> list[tuple[str, str, str]]:
    return [
        ("Conservador", "conservador", CORES_CENARIOS["conservador"]),
        ("Base", "base", CORES_CENARIOS["base"]),
        ("Agressivo", "agressivo", CORES_CENARIOS["agressivo"]),
    ]


def render_graficos_cenarios(cenarios: dict) -> None:
    st.markdown("### Comparativo Visual por Escala")
    st.caption("As metricas usam escalas separadas para manter verba, leads e vendas legiveis na mesma leitura.")
    metricas = [
        ("Verba prevista", "verba_r$", formatar_moeda),
        ("Leads estimados", "leads_estimados", lambda valor: f"{valor:.0f}"),
        ("Vendas estimadas", "vendas_estimadas", lambda valor: f"{valor:.1f}"),
    ]
    cols = st.columns(3)
    for col, (titulo, chave, formatador) in zip(cols, metricas):
        with col:
            nomes = []
            valores = []
            cores = []
            textos = []
            for nome_exibicao, chave_cenario, cor in _dados_cenarios_grafico():
                valor = cenarios[chave_cenario][chave]
                nomes.append(nome_exibicao)
                valores.append(valor)
                cores.append(cor)
                textos.append(formatador(valor))
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=nomes,
                        y=valores,
                        marker_color=cores,
                        text=textos,
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate=f"%{{x}}<br>{titulo}: %{{text}}<extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                title=titulo,
                paper_bgcolor=CORES["fundo"],
                plot_bgcolor=CORES["fundo"],
                height=320,
                margin=dict(l=10, r=10, t=48, b=10),
                showlegend=False,
                yaxis_title="",
                xaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True, key=f"grafico_cenarios_{chave.replace('$', 's')}")


def render_bloco_interesse_busca(dados_trends: dict) -> None:
    st.markdown("### Interesse de Busca")
    termos = dados_trends.get("termos", [])
    assunto = dados_trends.get("assunto", "Demanda digital imobiliaria local")
    tendencia = dados_trends.get("tendencia_recente", "indisponivel")
    badge = "badge-verde" if tendencia == "crescendo" else "badge-amarelo" if tendencia == "estavel" else "badge-vermelho"
    termos_html = "".join(
        f"<span class='fonte-tag' style='margin:0 6px 6px 0;'>{termo}</span>"
        for termo in termos
    ) or "<span class='fonte-tag'>Sem termos configurados</span>"
    col_a, col_b = st.columns([1.05, 1.95])
    with col_a:
        card(
            "Leitura considerada",
            (
                f"<p style='margin:0 0 10px 0;'><strong>Assunto:</strong> {assunto}</p>"
                f"<p style='margin:0 0 6px 0;'><strong>Termos monitorados:</strong></p>"
                f"<div style='margin-bottom:12px;'>{termos_html}</div>"
                f"<p style='margin:0 0 8px 0;'><strong>Interesse medio (12m):</strong> {dados_trends.get('score_interesse', 50)}/100</p>"
                f"<p style='margin:0;'><strong>Fonte:</strong> {dados_trends.get('fonte', 'Google Trends')}</p>"
            ),
            cor_borda="#D6C5A0",
            icone="🔎",
        )
        st.markdown(f"<span class='{badge}'>Tendencia: {tendencia.title()}</span>", unsafe_allow_html=True)
    with col_b:
        serie = dados_trends.get("serie_interesse", [])
        if serie:
            df_trends = pd.DataFrame(serie)
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=df_trends["data"],
                        y=df_trends["interesse"],
                        mode="lines+markers",
                        line=dict(color=CORES["azul_escuro"], width=3),
                        marker=dict(color=CORES["dourado"], size=7),
                        fill="tozeroy",
                        fillcolor="rgba(232,160,32,0.12)",
                        hovertemplate="%{x}<br>Interesse: %{y:.0f}/100<extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                title="Interesse de busca nos ultimos 12 meses",
                paper_bgcolor=CORES["fundo"],
                plot_bgcolor=CORES["fundo"],
                height=320,
                margin=dict(l=10, r=10, t=48, b=10),
                xaxis_title="",
                yaxis_title="?ndice",
            )
            st.plotly_chart(fig, use_container_width=True, key="trends_mix")
        else:
            detalhe_erro = dados_trends.get("erro")
            texto = "Google Trends indisponivel no momento. O score usa fallback neutro quando a integracao nao responde."
            if detalhe_erro:
                texto = f"{texto} Detalhe tecnico: {detalhe_erro}"
            st.info(texto)


def render_tipos_campanha_sugeridos(canais: dict) -> None:
    canais_suportados = [canal for canal in BIBLIOTECA_CAMPANHAS if canal in canais]
    if not canais_suportados:
        return

    st.markdown("### Tipos de Campanha Sugeridos")
    st.caption("Leitura resumida dos formatos mais aderentes para os canais do cenário base.")
    cols = st.columns(len(canais_suportados))
    for col, canal in zip(cols, canais_suportados):
        biblioteca = BIBLIOTECA_CAMPANHAS[canal]
        with col:
            campanhas_html = "".join(
                f"<p style='margin:0 0 10px 0;'><strong>{campanha['tipo']}</strong>: {campanha['quando_usar']}</p>"
                for campanha in biblioteca["campanhas"]
            )
            observacao = biblioteca.get("observacao")
            if observacao:
                campanhas_html += f"<p style='margin:10px 0 0 0; color:#6B7280;'><strong>Nota:</strong> {observacao}</p>"
            card(
                canal,
                campanhas_html,
                cor_borda=CORES_CANAIS.get(canal, CORES["borda"]),
                icone="📚",
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
                "Interpretacao": dados.get("detalhe_exibicao") or interpretar_variavel(variavel, dados["valor_norm"]),
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


@st.cache_data(show_spinner=False)
def obter_pdf_bytes(resultados: dict) -> bytes:
    """Gera o PDF sob cache para evitar custo repetido a cada rerender."""
    return gerar_pdf(resultados)


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
            "Score": "?ndice de dificuldade estimada de venda (0 = facil, 100 = critico)",
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
    cidade_consulta = (cidade_manual or "").strip()
    if len(cidade_consulta) >= 6:
        try:
            localizacao = buscar_municipio_por_nome(cidade_consulta)
            dados_ibge = get_dados_ibge(localizacao["codigo_ibge"])
            return sugerir_pontuacao_localizacao(localizacao, dados_ibge)
        except Exception:
            return None
    return None


def processar_dados(form_data: dict, ui=st) -> dict:
    feedback_ui = area_feedback_cta(ui)
    status_container = feedback_ui.container()
    with status_container:
        status_box = st.empty()
        progresso = st.progress(0, text="Iniciando processamento...")
    mensagens = [
        "Consulta inicial do municipio",
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
            feedback_ui.warning("Nao foi possivel localizar o CEP automaticamente. Usando busca manual por cidade.")

    if localizacao is None:
        atualizar_progresso(20, "Buscando cidade informada", "Usando a cidade digitada como fallback para encontrar o codigo IBGE correto.")
        localizacao = buscar_municipio_por_nome(form_data["cidade_manual"])

    atualizar_progresso(35, mensagens[0], f"Consolidando os indicadores para {localizacao['municipio']}.")
    dados_publicos = coletar_todos_dados(
        localizacao["codigo_ibge"],
        localizacao["municipio"],
        localizacao["uf"],
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
        dados_fipezap=dados_publicos["fipezap"],
        dados_rib=dados_publicos["rib"],
        valor_unidade=form_data["valor_unidade"],
        tipologia=form_data["tipologia"],
    )

    vgv = calcular_vgv(form_data["valor_unidade"], form_data["volume_unidades"])
    atualizar_progresso(68, mensagens[2], "Estimando VGV, intensidade de investimento e retorno esperado por cenario.")
    resultado_verba = calcular_verba(
        vgv=vgv,
        score=resultado_score["score_final"],
        tipologia=form_data["tipologia"].lower(),
        volume_unidades=form_data["volume_unidades"],
        valor_unidade=form_data["valor_unidade"],
        municipio=localizacao.get("municipio", ""),
        uf=localizacao.get("uf", ""),
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
    progresso.empty()
    status_box.empty()
    qualidade_texto, qualidade_cor = calcular_qualidade_dados(dados_ibge)
    contexto = resultado_score.get("justificativas_contextuais", [])
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
        "atributos": atributos,
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
    if score.get("ajuste_total"):
        st.caption(
            f"Score base: {score.get('score_base', score['score_final'])}/100 | "
            f"Ajuste macro: {score.get('ajuste_macro', 0):+.1f} | "
            f"Mercado local: {score.get('ajuste_mercado_local', 0):+.1f} | "
            f"FipeZap: {score.get('ajuste_fipezap', 0):+.1f} | "
            f"RIB: {score.get('ajuste_rib', 0):+.1f} | "
            f"Macro expandido: {score.get('ajuste_macro_expandido', 0):+.1f}"
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


def _metadata_tags_html(*valores: str) -> str:
    tags = [valor for valor in valores if valor]
    return " ".join(f"<span class='fonte-tag'>{item}</span>" for item in tags)


def _bloco_contexto(titulo: str, takeaway: str, descricao: str = "", tags: str = "") -> None:
    st.markdown(
        f"""
        <div class="context-shell">
          <div class="context-kicker">{titulo}</div>
          <div class="context-title">{takeaway}</div>
          <div class="context-body">{descricao}</div>
          <div style="margin-top:10px;">{tags}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card_insight(titulo: str, valor: str, detalhe: str, destaque: str = "#E8A020") -> None:
    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid #E5DDD0;border-top:3px solid {destaque};
                    border-radius:12px;padding:18px;min-height:148px;box-shadow:0 4px 14px rgba(27,42,74,0.05);">
          <div style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;color:#6B7280;font-weight:700;">{titulo}</div>
          <div style="font-size:1.6rem;color:#1B2A4A;font-weight:800;margin:10px 0 8px 0;">{valor}</div>
          <div style="font-size:0.9rem;color:#6B7280;line-height:1.55;">{detalhe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _texto_fipezap(dados_fipezap: dict) -> str:
    if not dados_fipezap.get("disponivel"):
        return dados_fipezap.get("motivo", "FipeZap indisponivel.")
    variacao = dados_fipezap.get("variacao_12m", 0)
    if variacao > 8:
        return f"Preco medio em alta de {variacao:.1f}% em 12 meses, sinal de mercado mais aquecido."
    if variacao < 0:
        return f"Preco medio em queda de {abs(variacao):.1f}% em 12 meses, o que pode alongar a decisao de compra."
    return f"Preco medio com variacao moderada de {variacao:.1f}% em 12 meses."


def _texto_rib(dados_rib: dict) -> str:
    if not dados_rib.get("disponivel"):
        return dados_rib.get("motivo", "RIB indisponivel.")
    variacao = dados_rib.get("variacao_anual_pct", 0)
    if variacao > 10:
        return f"Registros de compra e venda crescem {variacao:.1f}% a/a, sugerindo mercado mais liquido."
    if variacao < -5:
        return f"Registros caem {abs(variacao):.1f}% a/a, indicando absorcao mais lenta."
    return f"Registros seguem estaveis em torno da media recente de {dados_rib.get('media_mensal_12m', 0):,.0f}/mes."


def _texto_pressao_custos(pressao: dict) -> str:
    if pressao.get("interpretacao"):
        return " ".join(pressao["interpretacao"])
    return "INCC, IPCA e IGP-M estao em faixa sem pressao extrema na leitura atual."


def render_contexto_macro_kpis(resultados: dict) -> None:
    dados_bcb = resultados["dados_publicos"]["bcb"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selic", formatar_valor_contexto(dados_bcb.get("selic", {}).get("valor"), "pct"))
    col2.metric(
        "Juros Imobiliario",
        formatar_valor_contexto(dados_bcb.get("juros_imobiliario", {}).get("valor"), "pct"),
    )
    col3.metric(
        "Inadimplencia",
        formatar_valor_contexto(dados_bcb.get("inadimplencia_imobiliaria", {}).get("valor"), "pct"),
    )
    col4.metric("Unidades Financiadas", formatar_valor_contexto(dados_bcb.get("unidades_financiadas", {}).get("valor"), "numero"))


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


def _render_cobertura_ajustes(ajustes: dict) -> None:
    """Mostra quais ajustes contextuais foram aplicados vs. zerados por falta de dados."""

    GRUPOS = {
        "macro": "Macro BCB (Selic, juros)",
        "mercado_local": "Mercado Local (IPEA / Trends)",
        "fipezap": "FipeZap (precos locais)",
        "rib": "RIB (registros imoveis)",
        "macro_expandido": "Macro Expandido (IPCA, inadimplencia)",
    }
    if not ajustes:
        return

    st.markdown("### Cobertura dos ajustes contextuais")
    colunas = st.columns(len(GRUPOS))
    for col, (chave, rotulo) in zip(colunas, GRUPOS.items()):
        grupo = ajustes.get(chave, {})
        valor = grupo.get("ajuste", 0.0)
        tem_justificativa = bool(grupo.get("justificativa"))
        indisponivel = tem_justificativa and any(
            "nao disponivel" in j.lower() or "nao disponiveis" in j.lower()
            for j in (grupo.get("justificativa") or [])
        )
        if indisponivel or not tem_justificativa:
            cor_borda = "#E5DDD0"
            icone = "—"
            cor_valor = "#9CA3AF"
            texto_status = "Sem dados / N/A"
        elif valor == 0.0:
            cor_borda = "#D1FAE5"
            icone = "✓"
            cor_valor = "#16A34A"
            texto_status = "Neutro (0 pts)"
        elif valor > 0:
            cor_borda = "#FEE2E2"
            icone = "▲"
            cor_valor = "#DC2626"
            texto_status = f"+{valor:.1f} pts"
        else:
            cor_borda = "#DCFCE7"
            icone = "▼"
            cor_valor = "#16A34A"
            texto_status = f"{valor:.1f} pts"

        with col:
            st.markdown(
                f"""
                <div style="border:1px solid {cor_borda};border-radius:8px;padding:10px 12px;text-align:center;">
                  <div style="font-size:1.2rem;">{icone}</div>
                  <div style="font-size:0.72rem;font-weight:700;color:#1B2A4A;margin:4px 0 2px 0;">{rotulo}</div>
                  <div style="font-size:0.85rem;font-weight:800;color:{cor_valor};">{texto_status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


_LABELS_ATRIBUTOS = {
    "concorrencia": "Concorrencia",
    "localizacao": "Localizacao",
    "inovacao": "Inovacao do produto",
    "tracao": "Tracao de demanda",
    "conexao_luxo": "Conexao com luxo",
}

def render_simulador(resultados: dict) -> None:
    """Recalcula o score em tempo real ao mover os sliders de atributos.

    Usa os dados de mercado ja coletados (sem novas chamadas de API).
    """
    with st.expander("Simulador — ajuste os atributos e veja o impacto no score", expanded=False):
        st.caption(
            "Mova os sliders abaixo para simular cenarios alternativos. "
            "O score e recalculado instantaneamente usando os mesmos dados de mercado coletados."
        )
        atributos_orig = resultados.get("atributos", {})
        dados_normalizados = resultados["dados_normalizados"]
        dados_publicos = resultados["dados_publicos"]
        tipologia = resultados["empreendimento"]["tipologia"]
        valor_unidade = resultados["empreendimento"]["valor_unidade"]
        score_original = resultados["resultado_score"]["score_final"]

        cols = st.columns(3)
        sim_atributos = {}
        for idx, (chave, rotulo) in enumerate(_LABELS_ATRIBUTOS.items()):
            with cols[idx % 3]:
                valor_orig = atributos_orig.get(chave, 3)
                sim_atributos[chave] = st.slider(
                    rotulo,
                    min_value=1,
                    max_value=5,
                    value=valor_orig,
                    key=f"sim_{chave}",
                )

        score_sim = calcular_score(
            dados_normalizados,
            {**sim_atributos, "funcionalidades": atributos_orig.get("funcionalidades", [])},
            dados_bcb=dados_publicos.get("bcb"),
            dados_ipea=dados_publicos.get("ipea"),
            dados_trends=dados_publicos.get("trends"),
            dados_fipezap=dados_publicos.get("fipezap"),
            dados_rib=dados_publicos.get("rib"),
            valor_unidade=valor_unidade,
            tipologia=tipologia,
        )

        score_novo = score_sim["score_final"]
        delta = round(score_novo - score_original, 1)
        classificacao_nova, cor_nova = score_sim["classificacao"], score_sim["cor"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Score original", score_original)
        c2.metric("Score simulado", score_novo, delta=f"{delta:+.1f} pts", delta_color="inverse")
        c3.metric("Classificacao simulada", classificacao_nova)

        if delta != 0:
            top3_sim = sorted(
                score_sim["breakdown"].items(),
                key=lambda x: x[1]["contribuicao"],
                reverse=True,
            )[:3]
            nomes = [n.replace("_", " ").title() for n, _ in top3_sim]
            st.caption(f"Fatores que mais contribuem neste cenario: {', '.join(nomes)}.")


def render_tab_score(resultados: dict) -> None:
    df_breakdown = montar_breakdown_df(resultados["resultado_score"])

    # --- Painel: Score Objetivo vs Subjetivo ---
    pesos_ibge = 0.45   # soma dos pesos IBGE em PESOS_SCORE
    pesos_produto = 0.55  # soma dos pesos de atributos do usuario
    contrib_ibge = df_breakdown[df_breakdown["Categoria"] == "Dados IBGE"]["Contribuicao"].sum()
    contrib_prod = df_breakdown[df_breakdown["Categoria"] == "Atributos do empreendimento"]["Contribuicao"].sum()
    # Normaliza cada componente para 0-100 dentro do seu proprio teto
    score_obj_pct = round((contrib_ibge / pesos_ibge) * 10, 1) if pesos_ibge else 0
    score_sub_pct = round((contrib_prod / pesos_produto) * 10, 1) if pesos_produto else 0
    contrib_ibge_pts = round(contrib_ibge * 10, 1)
    contrib_prod_pts = round(contrib_prod * 10, 1)

    st.markdown("### Decomposicao do score")
    c_obj, c_sep, c_sub = st.columns([5, 1, 5])
    with c_obj:
        st.markdown(
            f"""
            <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:14px 16px;">
              <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#1D4ED8;margin-bottom:6px;">
                Contexto de Mercado
              </div>
              <div style="font-size:0.8rem;color:#6B7280;margin-bottom:4px;">Dados IBGE + macro (peso 45%)</div>
              <div style="font-size:1.7rem;font-weight:800;color:#1B2A4A;">{score_obj_pct}/100</div>
              <div style="font-size:0.82rem;color:#6B7280;margin-top:4px;">
                Contribuicao ao score final: <strong>{contrib_ibge_pts} pts</strong>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_sep:
        st.markdown(
            "<div style='text-align:center;padding-top:28px;font-size:1.4rem;color:#6B7280;'>+</div>",
            unsafe_allow_html=True,
        )
    with c_sub:
        st.markdown(
            f"""
            <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:14px 16px;">
              <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#B45309;margin-bottom:6px;">
                Atributos do Produto
              </div>
              <div style="font-size:0.8rem;color:#6B7280;margin-bottom:4px;">Inputs do formulario (peso 55%)</div>
              <div style="font-size:1.7rem;font-weight:800;color:#1B2A4A;">{score_sub_pct}/100</div>
              <div style="font-size:0.82rem;color:#6B7280;margin-top:4px;">
                Contribuicao ao score final: <strong>{contrib_prod_pts} pts</strong>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption(
        "Contexto de mercado reflete dados demograficos e macroeconomicos objetivos. "
        "Atributos do produto refletem a avaliacao do empreendimento feita no formulario."
    )
    st.markdown("")

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

    justificativas = resultados["resultado_score"].get("justificativas_contextuais", [])
    if justificativas:
        st.markdown("### Ajustes Contextuais")
        for texto in justificativas:
            st.markdown(f"- {texto}")

    # --- Cobertura dos ajustes contextuais ---
    ajustes = resultados["resultado_score"].get("ajustes_contextuais", {})
    _render_cobertura_ajustes(ajustes)

    st.markdown("")
    render_simulador(resultados)


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

    multiplicador = resultados["resultado_verba"].get("multiplicador_praca", 1.0)
    municipio = resultados["localizacao"].get("municipio", "")
    if multiplicador > 1.0:
        st.caption(
            f"CPL ajustado por porte de praca: {municipio} aplica multiplicador "
            f"{multiplicador:.1f}x sobre o benchmark nacional "
            f"({'capital SP/RJ' if multiplicador == 1.5 else 'capital estadual'})."
        )
    render_graficos_cenarios(cenarios)


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
            }
            for canal, dados in canais.items()
        ]
    )
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

    st.markdown("### Canais Prioritarios")
    cards = st.columns(2)
    for idx, (canal, dados) in enumerate(sorted(canais.items(), key=lambda item: item[1]["budget_r$"], reverse=True)):
        with cards[idx % 2]:
            tipos = tipos_campanha_por_canal(canal)
            tipos_html = ""
            if tipos:
                tipos_html = f"<p style='margin:0 0 8px 0;'><strong>Tipos de campanha:</strong> {', '.join(tipos)}</p>"
            conteudo = (
                f"<p style='margin:0 0 8px 0;'><strong>Budget:</strong> {formatar_moeda(dados['budget_r$'])} "
                f"({dados['percentual']:.1f}%)</p>"
                f"<p style='margin:0 0 8px 0;'><strong>CPL:</strong> {formatar_moeda(dados['cpl_estimado'])} | "
                f"<strong>Leads:</strong> {dados['leads_estimados']:.0f}</p>"
                + tipos_html
                + "".join(f"<p style='margin:0 0 6px 0;'>- {tatica}</p>" for tatica in dados["taticas"])
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
    dados_fipezap = dados_publicos["fipezap"]
    dados_rib = dados_publicos["rib"]
    favorabilidade = calcular_favorabilidade_mercado(dados_bcb, dados_ipea, dados_trends, dados_fipezap, dados_rib)
    pressao = calcular_pressao_custos(dados_bcb)
    benchmark_uf = dados_bcb.get("mercado_imobiliario_uf", {})

    _bloco_contexto(
        "Leitura Executiva",
        "Pre?o, liquidez, cr?dito e demanda foram organizados para responder se o mercado ajuda a absorcao agora.",
        (
            "Os blocos abaixo seguem uma ordem de leitura mais ?til: primeiro os sinais locais de pre?o e transa??o, "
            "depois o pano de fundo de credito e custos, e por fim a demanda digital que pode acelerar ou frear a abertura."
        ),
        _metadata_tags_html(
            f"Fontes ativas: {dados_publicos.get('fontes_ativas', 0)}/7",
            f"Qualidade geral: {dados_publicos.get('qualidade_geral', 0):.0%}",
        ),
    )

    st.markdown("### PREÇOS E MERCADO LOCAL")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if dados_fipezap.get("disponivel"):
            _card_insight("FipeZap", f"R$ {dados_fipezap['preco_medio_m2']:,.0f}/m²", _texto_fipezap(dados_fipezap))
            fx1, fx2 = st.columns(2)
            fx1.metric("Variação mensal", f"{dados_fipezap['variacao_mensal']:+.2f}%")
            fx2.metric("Variação 12m", f"{dados_fipezap['variacao_12m']:+.1f}%")
            st.markdown(
                _metadata_tags_html(
                    dados_fipezap.get("fonte"),
                    f"Referencia: {dados_fipezap.get('data_referencia', 'N/D')}",
                ),
                unsafe_allow_html=True,
            )
        else:
            _card_insight("FipeZap", "Não disponível", "Não disponível na sua área ou não foi possível carregar.", destaque="#D6C5A0")
    with col_a2:
        if dados_rib.get("disponivel"):
            _card_insight("RIB / Registros", f"{dados_rib['compra_venda_mensal']:,.0f}/mes", _texto_rib(dados_rib), destaque="#1B2A4A")
            rb1, rb2 = st.columns(2)
            rb1.metric("Variacao a/a", f"{dados_rib['variacao_anual_pct']:+.1f}%")
            rb2.metric("Média 12m", f"{dados_rib['media_mensal_12m']:,.0f}")
            st.markdown(
                _metadata_tags_html(
                    dados_rib.get("fonte"),
                    f"Referencia: {dados_rib.get('data_referencia', 'N/D')}",
                ),
                unsafe_allow_html=True,
            )
        else:
            _card_insight("RIB / Registros", "Não disponível", "Não disponível na sua área ou não foi possível carregar.", destaque="#D6C5A0")

    st.markdown("### CRÉDITO E MACRO")
    render_contexto_macro_kpis(resultados)
    cols_macro = st.columns(4)
    cards_macro = [
        ("Ticket médio financiado", formatar_valor_contexto(dados_bcb.get("ticket_medio_financiado", {}).get("valor"), "moeda"), "Benchmark nacional de financiamento por unidade.", "#E8A020"),
        ("IPCA 12m", formatar_valor_contexto(dados_bcb.get("ipca_12m", {}).get("valor"), "pct"), "Inflação alta corrige renda mais devagar que o custo de vida.", "#1B2A4A"),
        ("INCC-DI", formatar_valor_contexto(dados_bcb.get("incc", {}).get("valor"), "pct"), _texto_impacto_bcb("incc", dados_bcb.get("incc", {}).get("valor")), "#C46A3A"),
        ("IGP-M 12m", formatar_valor_contexto(dados_bcb.get("igpm_12m", {}).get("valor"), "pct"), "Ajuda a ler pressão sobre aluguel e contratos imobiliários.", "#D6C5A0"),
    ]
    for coluna, (titulo, valor, detalhe, cor) in zip(cols_macro, cards_macro):
        with coluna:
            _card_insight(titulo, valor, detalhe, destaque=cor)

    col_b1, col_b2 = st.columns([1.2, 1.05])
    with col_b1:
        _card_insight("Pressão de custos", f"{pressao['pressao_incorporador']:+.1f} pts", _texto_pressao_custos(pressao), destaque="#C46A3A")
        st.markdown(
            _metadata_tags_html("BCB/SGS", f"INCC {pressao['incc']:.1f}%", f"IPCA {pressao['ipca']:.1f}%", f"IGP-M {pressao['igpm']:.1f}%"),
            unsafe_allow_html=True,
        )
    with col_b2:
        if benchmark_uf.get("disponivel"):
            _card_insight(
                f"Benchmark estadual {benchmark_uf.get('uf', '')}",
                formatar_valor_contexto(benchmark_uf.get("valor_financiado"), "moeda"),
                "Referência estadual de crédito usada como pano de fundo do mercado regional.",
                destaque="#1B2A4A",
            )
            uf1, uf2 = st.columns(2)
            uf1.metric("Unidades", formatar_valor_contexto(benchmark_uf.get("unidades_financiadas"), "numero"))
            uf2.metric("LTV médio", formatar_valor_contexto(benchmark_uf.get("ltv_medio"), "pct"))
            st.markdown(
                _metadata_tags_html(
                    benchmark_uf.get("fonte"),
                    f"Referencia: {benchmark_uf.get('data_referencia', 'N/D')}",
                ),
                unsafe_allow_html=True,
            )
        else:
            _card_insight("Benchmark estadual", "Não disponível", "Não disponível na sua área ou não foi possível carregar.", destaque="#D6C5A0")

    st.markdown("### DEMANDA DIGITAL")
    col_c1, col_c2 = st.columns([1.35, 1.0])
    with col_c1:
        serie = dados_trends.get("serie_interesse", [])
        if serie:
            df_trends = pd.DataFrame(serie)
            ultimo = df_trends.iloc[-1]
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_trends["data"],
                    y=df_trends["interesse"],
                    mode="lines",
                    line=dict(color=CORES["azul_escuro"], width=3),
                    fill="tozeroy",
                    fillcolor="rgba(232,160,32,0.10)",
                    hovertemplate="%{x}<br>Interesse: %{y:.0f}/100<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[ultimo["data"]],
                    y=[ultimo["interesse"]],
                    mode="markers+text",
                    marker=dict(size=10, color=CORES["dourado"]),
                    text=[f"{ultimo['interesse']:.0f}"],
                    textposition="top center",
                    hoverinfo="skip",
                )
            )
            fig.update_layout(
                title="Interesse de busca em 12 meses",
                paper_bgcolor=CORES["fundo"],
                plot_bgcolor=CORES["fundo"],
                height=320,
                margin=dict(l=10, r=10, t=48, b=10),
                xaxis_title="",
                yaxis_title="Índice",
            )
            st.plotly_chart(fig, use_container_width=True, key="contexto_trends")
        else:
            st.info("Não disponível na sua área ou não foi possível carregar.")
    with col_c2:
        _card_insight(
            "Google Trends",
            f"{dados_trends.get('score_interesse', 50)}/100",
            f"Tendência recente: {dados_trends.get('tendencia_recente', 'indisponivel')}. Use esta leitura para dosar urgência criativa e pressão comercial.",
            destaque="#1B2A4A",
        )
        st.markdown(
            _metadata_tags_html(
                dados_trends.get("fonte", "Google Trends"),
                f"Termos: {', '.join(dados_trends.get('termos', [])[:3]) or 'N/D'}",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("### ÍNDICE DE FAVORABILIDADE DO MERCADO")
    col_f1, col_f2 = st.columns([0.9, 2.1])
    col_f1.metric("Favorabilidade", f"{favorabilidade['score']}/10")
    col_f2.markdown(
        f"""
        <div class="context-shell" style="padding:18px;">
          <div class="context-title" style="margin-top:0;">{favorabilidade['classificacao']}</div>
          <div class="context-body">
            Esta leitura combina juros, emprego, demanda digital, valorizacao de preco e liquidez registral
            para responder se o momento ajuda ou dificulta a absorcao.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab_ibge(resultados: dict) -> None:
    st.markdown("### Fontes de Dados Utilizadas")
    df_fontes = pd.DataFrame(FONTES_DE_DADOS)
    df_fontes = df_fontes[["fonte", "uso_no_relatorio", "status_integracao"]].copy()
    col_f1, col_f2 = st.columns(2)
    col_f1.metric("Fontes mapeadas", f"{len(df_fontes)}")
    col_f2.metric("Ativas agora", f"{(pd.DataFrame(FONTES_DE_DADOS)['status_integracao'].str.contains('Ativa')).sum()}")
    st.dataframe(df_fontes, use_container_width=True, hide_index=True)


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
    pdf_bytes = obter_pdf_bytes(resultados)
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
    render_kpis(resultados)
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E5DDD0; border-radius:12px; padding:18px 20px; box-shadow:0 2px 8px rgba(27,42,74,0.05);">
          <div style="font-size:1rem; font-weight:700; color:#1B2A4A; margin-bottom:8px;">Sintese executiva</div>
          <div style="font-size:0.95rem; color:#4B5563; line-height:1.65;">
            O empreendimento <strong>{sanitizar_html(resultados['empreendimento']['nome'])}</strong>, em
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
    pdf_bytes = obter_pdf_bytes(resultados)
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

    etapa_ativa = st.session_state["etapa_ativa"]
    render_step_nav(etapa_ativa)

    if etapa_ativa == "1. Dados do Empreendimento":
        st.markdown(
            """
            <div style="background:linear-gradient(90deg,#F0EDE8,#FAF8F5);border:1px solid #E5DDD0;
                        border-left:4px solid #E8A020;border-radius:10px;padding:12px 18px;
                        margin-bottom:20px;display:flex;align-items:center;gap:12px;">
              <div style="font-size:1.3rem;">📋</div>
              <div>
                <div style="font-size:0.9rem;font-weight:700;color:#1B2A4A;">
                  Preencha os dados do lancamento para gerar o relatorio completo
                </div>
                <div style="font-size:0.78rem;color:#6B7280;margin-top:2px;">
                  Score 0-100 | Verba recomendada | Mix de mídia | Dashboard executivo
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_left, col_right = st.columns([1, 1], gap="medium")

        with col_left:
            with st.container(border=True):
                render_form_block_title("IDENTIFICAÇÃO")
                nome_empreendimento = st.text_input(
                    "Nome do empreendimento",
                    placeholder="Ex: Vista Mar Residence",
                )
                tipologia = st.selectbox("Tipologia do produto", ["Lotes", "Apartamentos"])
                valor_unidade = st.number_input(
                    "Valor por unidade (R$)",
                    min_value=50_000,
                    step=10_000,
                    value=650_000,
                    help="Valor médio de venda de cada unidade.",
                )
                volume_unidades = st.number_input(
                    "Número de unidades",
                    min_value=1,
                    max_value=5_000,
                    step=1,
                    value=120,
                    help="Quantidade total de unidades a comercializar.",
                )

                render_form_block_title("LOCALIZAÇÃO")
                cep = st.text_input(
                    "CEP",
                    placeholder="00000-000",
                    max_chars=9,
                    help="Informe o CEP do terreno para localizar o município e, quando houver confiança, rua e bairro.",
                )
                cidade_manual = st.text_input(
                    "Ou informe a cidade",
                    placeholder="Ex: Fortaleza - CE",
                    help="Usado como alternativa se o CEP não for reconhecido.",
                )

                sugestao = obter_sugestao_localizacao(cep, cidade_manual)
                if sugestao:
                    detalhes = []
                    if sugestao.get("bairro"):
                        detalhes.append(f"Bairro: <strong>{sugestao['bairro']}</strong>.")
                    if sugestao.get("rua"):
                        detalhes.append(f"Ref: {sugestao['rua']}.")
                    detalhe_str = " ".join(detalhes)
                    st.markdown(
                        f"""<div class="suggestion-card">
                          <strong>Sugest?o de localiza??o:</strong> {sugestao['score_sugerido']}/5 - {sugestao['resumo']}
                          {(' ' + detalhe_str) if detalhe_str else ''}
                        </div>""",
                        unsafe_allow_html=True,
                    )

        with col_right:
            with st.container(border=True):
                render_form_block_title("ATRIBUTOS")
                st.caption("Avalie os atributos principais em escala de 1 a 5. Em funcionalidades, marque o pacote real do empreendimento para o score ficar mais aderente ao produto.")

                r1_col1, r1_col2 = st.columns(2, gap="large")
                with r1_col1:
                    concorrencia = nivel_selector(
                        "Concorrência",
                        "Empreendimentos similares em comercialização no mesmo raio",
                        "Saturado",
                        "Livre",
                        "concorrencia",
                    )
                with r1_col2:
                    localizacao_default = sugestao["score_sugerido"] if sugestao else 3
                    localizacao = nivel_selector(
                        "Localização",
                        "Acessibilidade, infraestrutura e percepção de valor do terreno",
                        "Fraca",
                        "Premium",
                        "localizacao",
                        default=localizacao_default,
                    )

                r2_col1, r2_col2 = st.columns(2, gap="large")
                with r2_col1:
                    inovacao = nivel_selector(
                        "Inovação",
                        "Diferenciação em conceito, arquitetura ou proposta de valor",
                        "Padrão",
                        "Inovador",
                        "inovacao",
                    )
                with r2_col2:
                    tracao = nivel_selector(
                        "Tração",
                        "Vendas, fila de espera ou interesse comprovado antes do lançamento",
                        "Nenhuma",
                        "Forte",
                        "tracao",
                    )


                funcionalidades = coletar_funcionalidades_selecionadas()

                r3_col1, r3_col2 = st.columns(2, gap="large")
                with r3_col1:
                    conexao_luxo = nivel_selector(
                        "Posicionamento",
                        "Alinhamento com segmento premium ou aspiracional",
                        "Popular",
                        "Premium",
                        "conexao_luxo",
                    )
                with r3_col2:
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

                st.caption("Ao calcular, você concorda com os Termos de Uso.")
                calcular = st.button("Calcular Score e Gerar Relatório", type="primary", use_container_width=True)

        feedback_slot = col_right.empty()

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
            if erros:
                with area_feedback_cta(feedback_slot):
                    for aviso in avisos:
                        st.warning(aviso)
                    for erro in erros:
                        st.error(erro)
            else:
                try:
                    st.session_state["resultados"] = processar_dados(form_data, ui=feedback_slot)
                    preparar_historico(st.session_state["resultados"])
                    st.session_state["etapa_ativa"] = "3. Dashboard de Resultados"
                    with area_feedback_cta(feedback_slot):
                        for aviso in avisos:
                            st.warning(aviso)
                        st.success("Analise concluida com sucesso. O dashboard ja esta pronto para abertura.")
                        if st.button("Abrir dashboard completo", use_container_width=True):
                            st.rerun()
                except Exception as exc:
                    with area_feedback_cta(feedback_slot):
                        for aviso in avisos:
                            st.warning(aviso)
                        st.error(f"Nao foi possivel concluir a analise: {exc}")

    if etapa_ativa == "2. Processamento":
        if "resultados" in st.session_state:
            resultados = st.session_state["resultados"]
            st.markdown("## Processamento")
            st.caption("Resumo do que foi carregado para montar o dashboard.")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Município", resultados["localizacao"]["municipio"])
            col2.metric("Código IBGE", resultados["localizacao"]["codigo_ibge"])
            col3.metric("Score", f"{resultados['resultado_score']['score_final']}/100")
            col4.metric("Verba base", formatar_moeda(resultados["resultado_verba"]["cenarios"]["base"]["verba_r$"]))

            st.markdown("### Dados carregados")
            dados_publicos = resultados["dados_publicos"]
            blocos = [
                ("IBGE", "Indicadores municipais e normalização", True),
                ("BCB", "Crédito, inflação e contexto macro", bool(dados_publicos.get("bcb"))),
                ("Ipea", "Indicadores econômicos complementares", bool(dados_publicos.get("ipea"))),
                ("Google Trends", "Demanda digital e interesse de busca", bool(dados_publicos.get("trends"))),
                ("FipeZap", "Preço e variação local de mercado", bool(dados_publicos.get("fipezap"))),
                ("RIB", "Liquidez e registros imobiliários", bool(dados_publicos.get("rib"))),
                ("Público-alvo", "Perfil, objeções e mensagem-chave", bool(resultados.get("perfil_publico"))),
                ("Mix de mídia", "Distribuição de verba por canal", bool(resultados.get("mix_midias"))),
            ]
            for titulo, descricao, disponivel in blocos:
                status = "Carregado" if disponivel else "Não disponível"
                st.markdown(f"- **{titulo}**: {status} — {descricao}")

            funcionalidades_resumo = resultados["resultado_score"]["breakdown"].get("funcionalidades", {})
            itens_funcionalidades = funcionalidades_resumo.get("itens", [])
            st.markdown("### Pacote do produto")
            if itens_funcionalidades:
                st.markdown(f"- Funcionalidades marcadas: **{', ' .join(itens_funcionalidades)}**")
                st.markdown(f"- Cobertura ponderada: **{funcionalidades_resumo.get('cobertura', 0):.0%}**")
            else:
                st.markdown("- Funcionalidades marcadas: **Nenhuma informada**")

            st.markdown("### Localização identificada")
            st.markdown(
                f"- Município: **{resultados['localizacao']['municipio']} - {resultados['localizacao']['uf']}**\n"
                f"- Bairro: **{resultados['localizacao'].get('bairro') or 'Não identificado'}**\n"
                f"- Referência: **{resultados['localizacao'].get('rua') or 'Não identificada'}**"
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
