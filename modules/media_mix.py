"""Recomendacao de mix de midia por perfil do empreendimento."""

from __future__ import annotations

from copy import deepcopy

from config import FAIXA_ECONOMICO_MAX, FAIXA_MEDIO_MAX


TATICAS_CANAL = {
    "Meta Ads (Instagram/Facebook)": [
        "Campanhas de conversao com segmentacao geolocalizada por raio do empreendimento",
        "Stories e Reels com tours, maquete e diferenciais do produto",
        "Retargeting para visitantes da landing page com condicoes comerciais",
    ],
    "Google Ads (Search + Display)": [
        "Palavras-chave de alta intencao com foco em bairro, tipologia e faixa de valor",
        "Remarketing em display para usuarios que pesquisaram financiamento ou imoveis similares",
        "Campanhas locais com extensoes de chamada e rota para o stand",
    ],
    "LinkedIn Ads": [
        "Segmentacao por cargos de renda alta e decisores familiares",
        "Conteudo institucional sobre valorizacao e seguranca patrimonial",
    ],
    "Portais Imobiliarios (Zap/Viva/OLX)": [
        "Destaque premium dos anuncios nas primeiras posicoes",
        "Atualizacao semanal de fotos, plantas e chamadas comerciais",
        "Tratamento rapido de leads com SLA de atendimento",
    ],
    "Influenciadores / Conteudo": [
        "Parcerias com criadores alinhados ao estilo de vida aspiracional do publico",
        "Conteudo em video mostrando bairro, conveniencias e acabamento",
    ],
    "Mídia OOH (outdoor/painéis)": [
        "Painel de impacto em corredores de alta circulacao",
        "Criativos com CTA simples e QR code para atendimento imediato",
    ],
    "CRM / E-mail Marketing": [
        "Fluxo de nutricao por etapa do funil com prova social e diferenciais",
        "Recuperacao automatizada de leads sem resposta comercial",
    ],
    "WhatsApp / CRM": [
        "Qualificacao rapida de leads com roteiros consultivos",
        "Listas de transmissao com ofertas e convites para visitas",
    ],
    "Rádio Local": [
        "Spots em horarios de deslocamento com reforco de localizacao",
        "Acoes de merchandising em programas de alta audiencia regional",
    ],
    "Influenciadores Regionais": [
        "Creators locais com autoridade em bairro, urbanismo ou lifestyle",
        "Cobertura ao vivo de visitas e eventos do empreendimento",
    ],
    "Eventos/Plantão Digital": [
        "Plantoes com corretores ao vivo e simulacao instantanea de condicoes",
        "Eventos tematicos de lancamento com captacao digital de leads",
    ],
}


def _mix_base(tipologia: str, valor_unidade: float) -> dict[str, float]:
    tipologia = tipologia.lower()
    if tipologia == "apartamentos" and valor_unidade > FAIXA_MEDIO_MAX:
        return {
            "Meta Ads (Instagram/Facebook)": 28,
            "Google Ads (Search + Display)": 22,
            "LinkedIn Ads": 12,
            "Portais Imobiliarios (Zap/Viva/OLX)": 15,
            "Influenciadores / Conteudo": 10,
            "Mídia OOH (outdoor/painéis)": 8,
            "CRM / E-mail Marketing": 5,
        }

    if tipologia == "lotes" or valor_unidade <= FAIXA_ECONOMICO_MAX:
        return {
            "Meta Ads (Instagram/Facebook)": 35,
            "Google Ads (Search + Display)": 20,
            "Portais Imobiliarios (Zap/Viva/OLX)": 20,
            "WhatsApp / CRM": 10,
            "Mídia OOH (outdoor/painéis)": 8,
            "Rádio Local": 5,
            "Influenciadores Regionais": 2,
        }

    return {
        "Meta Ads (Instagram/Facebook)": 32,
        "Google Ads (Search + Display)": 23,
        "Portais Imobiliarios (Zap/Viva/OLX)": 18,
        "WhatsApp / CRM": 9,
        "Mídia OOH (outdoor/painéis)": 8,
        "Influenciadores / Conteudo": 6,
        "CRM / E-mail Marketing": 4,
    }


def _redistribuir_percentuais(mix: dict[str, float]) -> dict[str, float]:
    total = sum(mix.values())
    return {canal: round((percentual / total) * 100, 2) for canal, percentual in mix.items()}


def recomendar_mix(
    score: float,
    tipologia: str,
    valor_unidade: float,
    cenario: str,
    dados_ibge: dict,
    verba_total: float,
) -> dict:
    """Monta distribuicao de budget por canal e taticas associadas."""

    mix = deepcopy(_mix_base(tipologia, valor_unidade))

    if score > 60:
        for canal in ("Meta Ads (Instagram/Facebook)", "Google Ads (Search + Display)"):
            if canal in mix:
                mix[canal] += 2.5
        if "Mídia OOH (outdoor/painéis)" in mix:
            mix["Mídia OOH (outdoor/painéis)"] -= 3
        for canal in ("Influenciadores / Conteudo", "Influenciadores Regionais"):
            if canal in mix:
                mix[canal] = max(0, mix[canal] - 2)

    if score < 30:
        if "Mídia OOH (outdoor/painéis)" in mix:
            mix["Mídia OOH (outdoor/painéis)"] += 5
        for canal in ("Meta Ads (Instagram/Facebook)", "Google Ads (Search + Display)"):
            if canal in mix:
                mix[canal] -= 1.5
        for canal in ("CRM / E-mail Marketing", "WhatsApp / CRM"):
            if canal in mix:
                mix[canal] += 2

    cenario_key = cenario.strip().lower()
    if cenario_key == "conservador":
        mix = {canal: pct for canal, pct in mix.items() if pct >= 5}
    elif cenario_key == "agressivo":
        origem = "CRM / E-mail Marketing" if "CRM / E-mail Marketing" in mix else "WhatsApp / CRM"
        if origem in mix:
            mix[origem] = max(0, mix[origem] - 5)
        mix["Eventos/Plantão Digital"] = 5

    mix = _redistribuir_percentuais(mix)
    faixa = dados_ibge.get("faixa_etaria_predominante", {}).get("valor", "")
    canais = {}
    for canal, percentual in mix.items():
        canais[canal] = {
            "percentual": percentual,
            "budget_r$": verba_total * percentual / 100,
            "taticas": TATICAS_CANAL.get(canal, [])[:3],
            "insight_regional": f"Ajustar criativos para a faixa etaria predominante local: {faixa}.",
        }

    return {"cenario": cenario.capitalize(), "canais": canais}
