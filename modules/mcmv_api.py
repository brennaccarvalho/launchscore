# Copyright (c) 2026 Brenna Carvalho.
# All rights reserved.
# This software is proprietary and part of a SaaS platform.
# Unauthorized use, reproduction, or reverse engineering is prohibited.
# Use of this service is subject to proprietary restrictions. Reverse engineering, scraping, or competitive usage is strictly prohibited.

"""Integracao opcional com o Portal da Transparencia."""

from __future__ import annotations

import os

import requests

MCMV_BASE = "https://api.portaldatransparencia.gov.br/api-de-dados/minha-casa-minha-vida"
MCMV_API_KEY = os.getenv("PORTAL_TRANSPARENCIA_KEY", "")


def get_dados_mcmv(municipio: str, uf: str) -> dict:
    """Busca contratos do MCMV quando a chave estiver configurada."""

    if not MCMV_API_KEY:
        return {"disponivel": False, "motivo": "API key nao configurada"}

    headers = {"chave-api-dados": MCMV_API_KEY}
    params = {"municipio": municipio, "uf": uf, "pagina": 1}
    try:
        resp = requests.get(MCMV_BASE, headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        dados = resp.json()
        return {
            "disponivel": True,
            "quantidade_registros": len(dados) if isinstance(dados, list) else 0,
            "dados": dados,
            "fonte": "Portal Transparencia (MCMV)",
        }
    except Exception as exc:
        return {"disponivel": False, "motivo": str(exc), "fonte": "Portal Transparencia (MCMV)"}
