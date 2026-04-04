"""Termos de uso completos e componentes de exibicao."""

from __future__ import annotations

import streamlit as st

VERSAO = "1.0"
DATA = "Abril de 2026"
AUTORA = "Brenna Carvalho"
LINKEDIN = "https://www.linkedin.com/in/brennacarvalho/"
APP_URL = "https://launchscorebrenna.streamlit.app"

TERMOS_COMPLETOS = """
LAUNCHSCORE — SCORE MARKETING IMOBILIÁRIO
TERMOS DE USO — Versão 1.0 — Abril de 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. APRESENTAÇÃO E ACEITE

Bem-vindo ao LaunchScore, plataforma de inteligência para estratégia de marketing
imobiliário desenvolvida e operada por Brenna Carvalho ("Empresa", "nós", "nosso").

Ao acessar ou utilizar o LaunchScore, você ("Usuário") declara ter lido, compreendido
e aceito integralmente estes Termos de Uso e nossa Política de Privacidade. Se você
não concorda com qualquer disposição aqui contida, não utilize a plataforma.

O uso continuado da plataforma após qualquer alteração nos Termos constituirá
aceitação tácita das modificações.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. DESCRIÇÃO DO SERVIÇO

O LaunchScore é uma aplicação web que oferece:

• Cálculo automatizado de score de dificuldade de venda de empreendimentos imobiliários
• Cruzamento de dados públicos via APIs do IBGE (SIDRA), BrasilAPI, Banco Central do
  Brasil (BCB/SGS), Ipeadata e outras fontes públicas
• Projeção de verba de marketing sobre o VGV do empreendimento
• Geração de cenários de investimento (conservador, base e agressivo)
• Recomendações de mix de mídia online e offline
• Perfil de público-alvo baseado em dados demográficos públicos
• Relatório exportável em formato PDF

Os resultados gerados pela plataforma têm caráter orientativo e não constituem
garantia de resultados comerciais ou financeiros.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. PROPRIEDADE INTELECTUAL

Todo o conteúdo da plataforma — incluindo, mas não se limitando a: código-fonte,
algoritmos, metodologia de score, pesos e parâmetros do modelo, interface visual,
logotipo, textos, gráficos e relatórios gerados — é de propriedade exclusiva de
Brenna Carvalho e protegido pelas leis brasileiras de propriedade intelectual
(Lei nº 9.610/1998 e Lei nº 9.609/1998).

É expressamente proibido ao Usuário:

• Copiar, reproduzir ou distribuir a metodologia de score sem autorização escrita
• Realizar engenharia reversa do algoritmo de cálculo
• Utilizar os relatórios gerados para fins de concorrência direta com a autora
• Sublicenciar, vender ou transferir o acesso à plataforma a terceiros

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. DADOS E PRIVACIDADE

O LaunchScore coleta e processa as seguintes informações:

• Dados inseridos pelo usuário: CEP, tipologia, valor de unidade, volume e atributos
  do empreendimento
• Dados públicos: informações obtidas via APIs do IBGE, BrasilAPI, BCB e Ipeadata
  (de domínio público)
• Dados de uso: logs de acesso, tempo de sessão e funcionalidades utilizadas

Os dados inseridos pelo usuário não são compartilhados com terceiros e são utilizados
exclusivamente para geração dos resultados na plataforma. Os dados de empreendimentos
podem ser anonimizados e utilizados para melhoria do modelo de score, sem identificação
do usuário ou do empreendimento específico.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. LIMITAÇÃO DE RESPONSABILIDADE

O LaunchScore é fornecido "como está" (as is), sem garantias expressas ou implícitas
de qualquer natureza.

A autora não se responsabiliza por:

• Decisões de investimento tomadas com base nos relatórios gerados pela plataforma
• Imprecisões nos dados públicos fornecidos pelo IBGE, BrasilAPI, BCB ou Ipeadata
• Indisponibilidade temporária de APIs externas que comprometam a completude dos dados
• Diferenças entre o desempenho projetado e o resultado real de campanhas de marketing
• Perdas financeiras diretas ou indiretas decorrentes do uso da plataforma

O uso da plataforma é de inteira responsabilidade do usuário. Recomendamos que as
projeções geradas sejam validadas por profissionais especializados antes de qualquer
tomada de decisão.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. USO PERMITIDO E PROIBIDO

USO PERMITIDO:
• Análise de empreendimentos imobiliários próprios ou de clientes diretos
• Planejamento estratégico de campanhas de marketing imobiliário
• Elaboração de apresentações internas ou para clientes
• Benchmarking de investimento em marketing no setor imobiliário

USO PROIBIDO:
• Utilização da plataforma para criar produto ou serviço concorrente
• Extração automatizada de dados (scraping) da plataforma
• Tentativa de acesso não autorizado a dados de outros usuários
• Inserção de dados falsos com o intuito de manipular o modelo
• Uso da plataforma para fins ilegais ou que violem direitos de terceiros

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. DISPONIBILIDADE DO SERVIÇO

A autora empenha-se em manter a plataforma disponível de forma contínua, porém não
garante disponibilidade ininterrupta. Manutenções programadas serão comunicadas com
antecedência mínima de 24 horas. Interrupções causadas por falhas em serviços de
terceiros (IBGE, BrasilAPI, BCB, infraestrutura de nuvem) estão fora do controle
da autora.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. ALTERAÇÕES NOS TERMOS

A autora reserva-se o direito de modificar estes Termos a qualquer momento.
Alterações relevantes serão comunicadas ao usuário por notificação na plataforma.
A versão vigente estará sempre disponível na plataforma com a data de última
atualização.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. VIGÊNCIA E RESCISÃO

Estes Termos entram em vigor no momento do primeiro acesso à plataforma e
permanecem válidos enquanto o usuário utilizar o serviço. A autora reserva-se
o direito de suspender ou encerrar o acesso de usuários que violem estes Termos,
sem aviso prévio e sem necessidade de justificativa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. LEI APLICÁVEL E FORO

Estes Termos são regidos pelas leis da República Federativa do Brasil. Eventuais
disputas serão submetidas ao foro da Comarca de Fortaleza, Estado do Ceará, com
exclusão de qualquer outro, por mais privilegiado que seja.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. CONTATO

Para dúvidas, solicitações ou comunicações relacionadas a estes Termos:
LinkedIn: https://www.linkedin.com/in/brennacarvalho/
Plataforma: https://launchscorebrenna.streamlit.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© 2026 Brenna Carvalho — LaunchScore. Todos os direitos reservados.
Metodologia proprietária protegida pela Lei nº 9.609/1998.
"""


def exibir_termos_modal() -> None:
    """Exibe os termos completos em um expander estilizado."""

    with st.expander("📄 Termos de Uso Completos — LaunchScore", expanded=False):
        st.markdown(
            f"""
        <div style="background:#FAF8F5; border:1px solid #E5DDD0; border-radius:8px;
                    padding:24px; font-family:'Courier New', monospace; font-size:0.82rem;
                    color:#1B2A4A; line-height:1.7; max-height:500px; overflow-y:auto;">
            <pre style="white-space:pre-wrap; font-family:inherit;">{TERMOS_COMPLETOS}</pre>
        </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇️ Baixar Termos de Uso (.txt)",
            data=TERMOS_COMPLETOS.encode("utf-8"),
            file_name="termos_de_uso_launchscore.txt",
            mime="text/plain",
        )


def exibir_footer_termos() -> None:
    """Footer compacto com link para os termos."""

    st.markdown(
        """
    <div style="background:#F0EDE8; border:1px solid #E5DDD0; border-top:3px solid #E8A020;
                border-radius:8px; padding:14px 24px; font-size:0.78rem; color:#6B7280;
                text-align:center; margin-top:32px;">
      <strong style="color:#1B2A4A;">LaunchScore</strong> é uma criação de
      <a href="https://www.linkedin.com/in/brennacarvalho/" target="_blank"
         style="color:#E8A020; font-weight:700; text-decoration:none;">Brenna Carvalho</a>.
      Todos os direitos reservados. A metodologia de score, os algoritmos de cálculo e a
      interface desta plataforma são propriedade intelectual da autora, protegida pela
      Lei nº 9.609/1998.<br>
      O uso desta plataforma implica aceite integral dos Termos de Uso acima.
      Os resultados têm caráter orientativo e não constituem garantia de resultados financeiros.
    </div>
        """,
        unsafe_allow_html=True,
    )
