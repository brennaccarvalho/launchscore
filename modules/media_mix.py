"""Recomendacao de mix de midia por perfil do empreendimento."""

from __future__ import annotations

from copy import deepcopy

from config import CORES_CANAIS, FAIXA_ECONOMICO_MAX, FAIXA_MEDIO_MAX


CPL_POR_CANAL = {
    "Meta Ads (Instagram/Facebook)": {"lotes": 120, "apartamentos": 160},
    "Google Ads (Search + Display)": {"lotes": 180, "apartamentos": 220},
    "Portais Imobiliarios (Zap/Viva/OLX)": {"lotes": 90, "apartamentos": 130},
    "WhatsApp / CRM": {"lotes": 60, "apartamentos": 80},
    "Midia OOH (outdoor/paineis)": {"lotes": 400, "apartamentos": 500},
    "Radio Local": {"lotes": 350, "apartamentos": 450},
    "Influenciadores Regionais": {"lotes": 200, "apartamentos": 280},
    "Eventos/Plantao Digital": {"lotes": 250, "apartamentos": 320},
    "LinkedIn Ads": {"lotes": 280, "apartamentos": 340},
    "CRM / E-mail Marketing": {"lotes": 70, "apartamentos": 90},
    "Influenciadores / Conteudo": {"lotes": 220, "apartamentos": 300},
}

ICONE_CANAL = {
    "Meta Ads (Instagram/Facebook)": "📱",
    "Google Ads (Search + Display)": "🔎",
    "Portais Imobiliarios (Zap/Viva/OLX)": "🏘️",
    "WhatsApp / CRM": "💬",
    "Midia OOH (outdoor/paineis)": "📍",
    "Radio Local": "📻",
    "Influenciadores Regionais": "🎥",
    "Eventos/Plantao Digital": "🎯",
    "LinkedIn Ads": "💼",
    "CRM / E-mail Marketing": "✉️",
    "Influenciadores / Conteudo": "✨",
}

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
        "Pecas com foco em patrimonio, status e localizacao premium",
    ],
    "Portais Imobiliarios (Zap/Viva/OLX)": [
        "Destaque premium dos anuncios nas primeiras posicoes",
        "Atualizacao semanal de fotos, plantas e chamadas comerciais",
        "Tratamento rapido de leads com SLA de atendimento",
    ],
    "Influenciadores / Conteudo": [
        "Parcerias com criadores alinhados ao estilo de vida aspiracional do publico",
        "Conteudo em video mostrando bairro, conveniencias e acabamento",
        "Series editoriais com prova social e bastidores do lancamento",
    ],
    "Midia OOH (outdoor/paineis)": [
        "Painel de impacto em corredores de alta circulacao",
        "Criativos com CTA simples e QR code para atendimento imediato",
        "Peças de reforco de marca em eixos premium de deslocamento",
    ],
    "CRM / E-mail Marketing": [
        "Fluxo de nutricao por etapa do funil com prova social e diferenciais",
        "Recuperacao automatizada de leads sem resposta comercial",
        "Conteudo segmentado por perfil de lead e momento de compra",
    ],
    "WhatsApp / CRM": [
        "Qualificacao rapida de leads com roteiros consultivos",
        "Listas de transmissao com ofertas e convites para visitas",
        "Follow-up humanizado com foco em agendamento",
    ],
    "Radio Local": [
        "Spots em horarios de deslocamento com reforco de localizacao",
        "Acoes de merchandising em programas de alta audiencia regional",
        "Chamadas promocionais em janelas de maior cobertura local",
    ],
    "Influenciadores Regionais": [
        "Creators locais com autoridade em bairro, urbanismo ou lifestyle",
        "Cobertura ao vivo de visitas e eventos do empreendimento",
        "Series de recomendacao com enfase em contexto local",
    ],
    "Eventos/Plantao Digital": [
        "Plantoes com corretores ao vivo e simulacao instantanea de condicoes",
        "Eventos tematicos de lancamento com captacao digital de leads",
        "Lives com tour comentado e ofertas de urgencia",
    ],
}

BIBLIOTECA_CAMPANHAS = {
    "Meta Ads (Instagram/Facebook)": {
        "fonte": "Meta for Business",
        "fonte_url": "https://www.facebook.com/business/ads/ad-objectives",
        "campanhas": [
            {
                "tipo": "Leads",
                "quando_usar": "captacao direta de cadastros com formulario instantaneo, mensagem ou ligacao.",
            },
            {
                "tipo": "Traffic",
                "quando_usar": "levar audiencia qualificada para landing page, WhatsApp ou pagina do empreendimento.",
            },
            {
                "tipo": "Awareness",
                "quando_usar": "abrir cobertura de lancamento, reforcar localizacao e ganhar lembranca de marca na regiao.",
            },
            {
                "tipo": "Sales",
                "quando_usar": "otimizar para conversoes quando pixel, CAPI e eventos qualificados ja estiverem maduros.",
            },
        ],
    },
    "Google Ads (Search + Display)": {
        "fonte": "Google Ads Help",
        "fonte_url": "https://support.google.com/google-ads/answer/2567043",
        "observacao": "O suporte do Google orienta escolher o tipo pelo objetivo da campanha e pelo inventario desejado.",
        "campanhas": [
            {
                "tipo": "Search",
                "quando_usar": "capturar demanda de alta intencao por bairro, tipologia, preco e financiamento.",
            },
            {
                "tipo": "Display",
                "quando_usar": "fazer remarketing e ampliar cobertura visual fora da busca.",
            },
            {
                "tipo": "Performance Max",
                "quando_usar": "maximizar leads com ativos multiformato e cobertura em varios canais do Google.",
            },
            {
                "tipo": "Demand Gen",
                "quando_usar": "trabalhar descoberta com video e imagem em superficies de navegacao; o Google vem migrando VAC para esse formato em abril de 2026.",
            },
        ],
    },
}


def _mix_base(tipologia: str, valor_unidade: float) -> dict[str, float]:
    tipo = tipologia.lower()
    if tipo == "apartamentos" and valor_unidade > FAIXA_MEDIO_MAX:
        return {
            "Meta Ads (Instagram/Facebook)": 28,
            "Google Ads (Search + Display)": 22,
            "LinkedIn Ads": 12,
            "Portais Imobiliarios (Zap/Viva/OLX)": 15,
            "Influenciadores / Conteudo": 10,
            "Midia OOH (outdoor/paineis)": 8,
            "CRM / E-mail Marketing": 5,
        }
    if tipo == "lotes" or valor_unidade <= FAIXA_ECONOMICO_MAX:
        return {
            "Meta Ads (Instagram/Facebook)": 35,
            "Google Ads (Search + Display)": 20,
            "Portais Imobiliarios (Zap/Viva/OLX)": 20,
            "WhatsApp / CRM": 10,
            "Midia OOH (outdoor/paineis)": 8,
            "Radio Local": 5,
            "Influenciadores Regionais": 2,
        }
    return {
        "Meta Ads (Instagram/Facebook)": 32,
        "Google Ads (Search + Display)": 23,
        "Portais Imobiliarios (Zap/Viva/OLX)": 18,
        "WhatsApp / CRM": 9,
        "Midia OOH (outdoor/paineis)": 8,
        "Influenciadores / Conteudo": 6,
        "CRM / E-mail Marketing": 4,
    }


def _redistribuir_percentuais(mix: dict[str, float]) -> dict[str, float]:
    total = sum(mix.values()) or 1
    return {
        canal: round((percentual / total) * 100, 2)
        for canal, percentual in mix.items()
        if percentual > 0
    }


def recomendar_mix(
    score: float,
    tipologia: str,
    valor_unidade: float,
    cenario: str,
    dados_ibge: dict,
    verba_total: float,
) -> dict:
    """Monta distribuicao de budget por canal, CPL, leads e taticas."""

    tipo = tipologia.lower()
    mix = deepcopy(_mix_base(tipologia, valor_unidade))

    if score > 60:
        for canal in ("Meta Ads (Instagram/Facebook)", "Google Ads (Search + Display)"):
            if canal in mix:
                mix[canal] += 2.5
        if "Midia OOH (outdoor/paineis)" in mix:
            mix["Midia OOH (outdoor/paineis)"] -= 3
        for canal in ("Influenciadores / Conteudo", "Influenciadores Regionais"):
            if canal in mix:
                mix[canal] = max(0, mix[canal] - 2)

    if score < 30:
        if "Midia OOH (outdoor/paineis)" in mix:
            mix["Midia OOH (outdoor/paineis)"] += 5
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
        mix["Eventos/Plantao Digital"] = 5

    mix = _redistribuir_percentuais(mix)
    faixa = dados_ibge.get("faixa_etaria_predominante", {}).get("valor", "")
    canais = {}
    for canal, percentual in mix.items():
        budget = verba_total * percentual / 100
        cpl = CPL_POR_CANAL.get(canal, {}).get(tipo, 180)
        leads = budget / cpl if cpl else 0.0
        canais[canal] = {
            "percentual": percentual,
            "budget_r$": budget,
            "cpl_estimado": cpl,
            "leads_estimados": leads,
            "taticas": TATICAS_CANAL.get(canal, [])[:3],
            "insight_regional": f"Ajustar criativos para a faixa etaria predominante local: {faixa}.",
            "icone": ICONE_CANAL.get(canal, "📣"),
            "cor": CORES_CANAIS.get(canal, "#1B2A4A"),
        }

    return {"cenario": cenario.capitalize(), "canais": canais}
