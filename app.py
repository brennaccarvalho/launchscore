"""Aplicativo Streamlit principal do Score Marketing Imobiliario."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import CORES_RELATORIO
from modules.audience import gerar_perfil_publico
from modules.budget_engine import calcular_verba, calcular_vgv
from modules.ibge_api import buscar_municipio_por_nome, get_dados_ibge, get_municipio_by_cep, normalizar_para_score
from modules.media_mix import recomendar_mix
from modules.report_generator import gerar_pdf
from modules.score_engine import calcular_score


st.set_page_config(layout="wide", page_title="Score Marketing Imobiliario")


def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def obter_cor_score(cor: str) -> str:
    return CORES_RELATORIO.get(cor, CORES_RELATORIO["azul"])


def sidebar() -> None:
    st.sidebar.title("Como usar")
    st.sidebar.write("1. Informe CEP ou cidade.\n2. Preencha os atributos.\n3. Gere score, verba e mix.")
    st.sidebar.subheader("Glossario")
    st.sidebar.write("- VGV: Valor Geral de Vendas.\n- Score: dificuldade estimada.\n- Mix de midia: distribuicao da verba.")


def processar_dados(form_data: dict) -> dict:
    progresso = st.progress(0, text="Iniciando processamento...")
    localizacao = None
    if form_data["cep"]:
        try:
            progresso.progress(15, text="Localizando municipio pelo CEP...")
            localizacao = get_municipio_by_cep(form_data["cep"])
        except Exception:
            st.warning("Nao foi possivel localizar o CEP automaticamente. Usando busca manual por cidade.")

    if localizacao is None:
        if not form_data["cidade_manual"]:
            raise ValueError("Informe um CEP valido ou uma cidade manualmente.")
        progresso.progress(25, text="Buscando municipio pela cidade informada...")
        localizacao = buscar_municipio_por_nome(form_data["cidade_manual"])

    progresso.progress(40, text="Buscando dados publicos do IBGE...")
    dados_ibge = get_dados_ibge(localizacao["codigo_ibge"])
    progresso.progress(55, text="Normalizando indicadores para score...")
    dados_normalizados = normalizar_para_score(dados_ibge)

    atributos = {chave: form_data[chave] for chave in ("concorrencia", "localizacao", "inovacao", "tracao", "funcionalidades", "conexao_luxo")}
    progresso.progress(70, text="Calculando score de dificuldade...")
    resultado_score = calcular_score(dados_normalizados, atributos)

    vgv = calcular_vgv(form_data["valor_unidade"], form_data["volume_unidades"])
    progresso.progress(82, text="Projetando verba e cenarios...")
    resultado_verba = calcular_verba(vgv, resultado_score["score_final"], form_data["nivel_investimento"], form_data["tipologia"].lower(), form_data["volume_unidades"])

    progresso.progress(90, text="Gerando perfil de publico e mix de midia...")
    perfil_publico = gerar_perfil_publico(dados_ibge, form_data["tipologia"], form_data["valor_unidade"])
    mix_midias = recomendar_mix(resultado_score["score_final"], form_data["tipologia"], form_data["valor_unidade"], "base", dados_ibge, resultado_verba["cenarios"]["base"]["verba_r$"])

    progresso.progress(100, text="Analise concluida.")
    recomendacoes = (
        f"{resultado_score['justificativa_texto']} Priorize o cenario base com verba de "
        f"{formatar_moeda(resultado_verba['cenarios']['base']['verba_r$'])} e ajuste a narrativa comercial para o contexto local."
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
        "mix_midias": mix_midias,
        "recomendacoes_estrategicas": recomendacoes,
    }


def render_resultados(resultados: dict) -> None:
    score = resultados["resultado_score"]
    verba = resultados["resultado_verba"]

    st.subheader("Score e KPIs Principais")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score de Dificuldade", f"{score['score_final']}/100", score["classificacao"])
    col2.metric("VGV Total", formatar_moeda(verba["vgv"]))
    col3.metric("Verba Recomendada", formatar_moeda(verba["verba_total_r$"]))
    col4.metric("Custo por Unidade", formatar_moeda(verba["custo_por_unidade_r$"]))

    fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=score["score_final"], gauge={"axis": {"range": [0, 100]}, "bar": {"color": obter_cor_score(score["cor"])}, "steps": [{"range": [0, 30], "color": "#22c55e"}, {"range": [30, 50], "color": "#eab308"}, {"range": [50, 70], "color": "#f97316"}, {"range": [70, 100], "color": "#ef4444"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)

    with st.expander("Breakdown do Score", expanded=True):
        df_breakdown = pd.DataFrame.from_dict(score["breakdown"], orient="index").reset_index().rename(columns={"index": "variavel"})
        fig_breakdown = px.bar(df_breakdown.sort_values("contribuicao"), x="contribuicao", y="variavel", orientation="h", title="Contribuicao por variavel")
        st.plotly_chart(fig_breakdown, use_container_width=True)
        st.dataframe(df_breakdown, use_container_width=True)

    with st.expander("Cenarios de Investimento", expanded=True):
        df_cenarios = pd.DataFrame(resultados["resultado_verba"]["cenarios"]).T.reset_index().rename(columns={"index": "cenario"})
        st.dataframe(df_cenarios, use_container_width=True)
        fig_cenarios = px.bar(df_cenarios, x="cenario", y="verba_r$", color="cenario", title="Verba total por cenario")
        st.plotly_chart(fig_cenarios, use_container_width=True)

    with st.expander("Mix de Midia", expanded=True):
        cenario_selecionado = st.radio("Visualizar mix para:", ["Conservador", "Base", "Agressivo"], horizontal=True)
        verba_cenario = resultados["resultado_verba"]["cenarios"][cenario_selecionado.lower()]["verba_r$"]
        mix = recomendar_mix(score["score_final"], resultados["empreendimento"]["tipologia"], resultados["empreendimento"]["valor_unidade"], cenario_selecionado.lower(), resultados["dados_ibge"], verba_cenario)
        df_mix = pd.DataFrame([{"canal": canal, "percentual": dados["percentual"], "budget_r$": dados["budget_r$"], "taticas": " | ".join(dados["taticas"])} for canal, dados in mix["canais"].items()])
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_mix, names="canal", values="percentual", title="Distribuicao do budget"), use_container_width=True)
        with col2:
            st.dataframe(df_mix, use_container_width=True)

    with st.expander("Perfil de Publico-Alvo", expanded=True):
        perfil = resultados["perfil_publico"]
        colunas = st.columns(3)
        for idx, (chave, valor) in enumerate(perfil.items()):
            with colunas[idx % 3]:
                texto = "\n".join(f"- {item}" for item in valor) if isinstance(valor, list) else valor
                st.markdown(f"**{chave.replace('_', ' ').title()}**")
                st.write(texto)

    with st.expander("Dados IBGE Utilizados", expanded=False):
        linhas = []
        for chave, valor in resultados["dados_ibge"].items():
            if chave == "codigo_ibge":
                continue
            linhas.append({"variavel": chave, "valor": valor.get("valor"), "fonte": valor.get("fonte", "estimativa"), "estimativa": "Sim" if valor.get("fonte") == "estimativa" else "Nao"})
        st.dataframe(pd.DataFrame(linhas), use_container_width=True)

    st.subheader("Exportar Relatorio")
    pdf_bytes = gerar_pdf(resultados)
    cidade = resultados["localizacao"]["municipio"].replace(" ", "_").lower()
    st.download_button(label="📄 Baixar Relatorio Completo em PDF", data=pdf_bytes, file_name=f"score_marketing_{cidade}_{date.today()}.pdf", mime="application/pdf")


def main() -> None:
    sidebar()
    st.title("Score Marketing Imobiliario")
    st.caption("Analise automatizada de dificuldade de venda, verba e estrategia de midia.")
    tabs = st.tabs(["1. Dados do Empreendimento", "2. Processamento", "3. Dashboard de Resultados"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            nome_empreendimento = st.text_input("Nome do empreendimento", placeholder="Ex: Vista Mar Residence")
            cep = st.text_input("CEP do empreendimento", placeholder="00000-000")
            cidade_manual = st.text_input("Ou digite a cidade (fallback)", placeholder="Ex: Fortaleza - CE")
            tipologia = st.selectbox("Tipologia", ["Lotes", "Apartamentos"])
            valor_unidade = st.number_input("Valor por unidade (R$)", min_value=50000, max_value=50000000, step=10000, value=650000, help="Valor medio ou principal da unidade comercializada.")
            volume_unidades = st.number_input("Numero de unidades", min_value=1, max_value=5000, step=1, value=120, help="Quantidade total de unidades disponiveis no empreendimento.")

        with col2:
            nivel_investimento = st.slider("Nivel de investimento desejado", 1, 5, 3, help="1 = Conservador | 3 = Mercado | 5 = Agressivo")
            st.subheader("Atributos do Empreendimento")
            concorrencia = st.slider("Nivel de concorrencia na regiao", 1, 5, 3, help="1 = Sem concorrentes | 5 = Mercado saturado")
            localizacao = st.slider("Qualidade da localizacao", 1, 5, 3, help="1 = Localizacao ruim | 5 = Localizacao excelente")
            inovacao = st.slider("Inovacao do produto", 1, 5, 3, help="Quanto maior, mais diferenciada e atrativa tende a ser a proposta.")
            tracao = st.slider("Tracao comercial atual", 1, 5, 3, help="Representa vendas, leads qualificados e sinais reais de demanda.")
            funcionalidades = st.slider("Diferenciais e funcionalidades", 1, 5, 3, help="Nivel de amenidades, servicos e atributos tangiveis do produto.")
            conexao_luxo = st.slider("Conexao com segmento de luxo/aspiracional", 1, 5, 3, help="Quanto mais forte a conexao aspiracional, menor tende a ser a dificuldade.")

        if st.button("🚀 Calcular Score e Gerar Relatorio", type="primary"):
            form_data = {
                "nome_empreendimento": nome_empreendimento,
                "cep": cep,
                "cidade_manual": cidade_manual,
                "tipologia": tipologia,
                "valor_unidade": valor_unidade,
                "volume_unidades": volume_unidades,
                "nivel_investimento": nivel_investimento,
                "concorrencia": concorrencia,
                "localizacao": localizacao,
                "inovacao": inovacao,
                "tracao": tracao,
                "funcionalidades": funcionalidades,
                "conexao_luxo": conexao_luxo,
            }
            try:
                st.session_state["resultados"] = processar_dados(form_data)
                st.success("Analise concluida com sucesso. Confira as abas seguintes.")
            except Exception as exc:
                st.error(f"Nao foi possivel concluir a analise: {exc}")

    with tabs[1]:
        if "resultados" in st.session_state:
            st.write("Dados processados e prontos para visualizacao.")
            st.json({"municipio": st.session_state["resultados"]["localizacao"]["municipio"], "codigo_ibge": st.session_state["resultados"]["localizacao"]["codigo_ibge"], "score": st.session_state["resultados"]["resultado_score"]["score_final"]})
        else:
            st.info("Preencha os dados na primeira etapa para iniciar o processamento.")

    with tabs[2]:
        if "resultados" in st.session_state:
            render_resultados(st.session_state["resultados"])
        else:
            st.info("Ainda nao ha resultados para exibir.")


if __name__ == "__main__":
    main()
