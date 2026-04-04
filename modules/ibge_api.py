"""Integracoes com BrasilAPI e IBGE para enriquecimento dos dados."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
import streamlit as st

from config import (
    BRASILAPI_CEP,
    IBGE_MUNICIPIOS,
    IBGE_SIDRA_BASE,
    MEDIANAS_NACIONAIS,
    REQUEST_TIMEOUT,
)


def _limpar_cep(cep: str) -> str:
    return "".join(char for char in (cep or "") if char.isdigit())


def _request_json(url: str) -> Any:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _embalar_variavel(
    valor: Any,
    *,
    fonte_tipo: str,
    fonte_nome: str,
    fonte_detalhe: str,
    mediana_nacional: Any = None,
    extra: dict | None = None,
) -> dict:
    payload = {
        "valor": valor,
        "fonte": fonte_tipo,
        "fonte_nome": fonte_nome,
        "fonte_detalhe": fonte_detalhe,
        "mediana_nacional": mediana_nacional,
    }
    if extra:
        payload.update(extra)
    return payload


@st.cache_data(ttl=3600)
def get_municipio_by_cep(cep: str) -> dict:
    """Busca municipio pela BrasilAPI a partir do CEP."""

    cep_limpo = _limpar_cep(cep)
    if len(cep_limpo) != 8:
        raise ValueError("CEP invalido. Informe 8 digitos.")

    try:
        data = _request_json(BRASILAPI_CEP.format(cep=cep_limpo))
        return {
            "municipio": data.get("city", ""),
            "uf": data.get("state", ""),
            "codigo_ibge": str(data.get("ibge", "")),
            "cep": cep_limpo,
            "bairro": data.get("neighborhood", ""),
            "rua": data.get("street", ""),
            "fonte": "BrasilAPI",
        }
    except Exception as exc:
        raise RuntimeError("Nao foi possivel localizar o CEP automaticamente.") from exc


@st.cache_data(ttl=3600)
def buscar_municipio_por_nome(cidade_uf: str) -> dict:
    """Busca codigo IBGE a partir do nome da cidade informado manualmente."""

    termo = (cidade_uf or "").strip()
    if not termo:
        raise ValueError("Informe uma cidade para busca manual.")

    consulta = termo.replace(" - ", "/").replace("-", "/")
    url = f"{IBGE_MUNICIPIOS}/{consulta}"
    data = _request_json(url)
    if isinstance(data, list):
        data = data[0] if data else {}
    regiao = data.get("microrregiao", {}).get("mesorregiao", {}).get("UF", {})
    return {
        "municipio": data.get("nome", termo),
        "uf": regiao.get("sigla", ""),
        "codigo_ibge": str(data.get("id", "")),
        "cep": "",
        "bairro": "",
        "rua": "",
        "fonte": "IBGE Municipios",
    }


def _sidra_url(tabela: str, variavel: str, codigo_ibge: str, periodo: str = "2022") -> str:
    return (
        f"{IBGE_SIDRA_BASE}/{tabela}/periodos/{periodo}/variaveis/{variavel}"
        f"?localidades=N6[{codigo_ibge}]"
    )


def _parse_sidra_valor(payload: Any) -> float | None:
    if not isinstance(payload, list) or len(payload) < 2:
        return None

    valores = []
    for row in payload[1:]:
        valor = row.get("V")
        if valor in (None, "...", "-", ""):
            continue
        try:
            valores.append(float(str(valor).replace(",", ".")))
        except ValueError:
            continue

    return valores[0] if valores else None


def _buscar_renda_media(codigo_ibge: str) -> dict:
    valor = _parse_sidra_valor(_request_json(_sidra_url("3170", "5930", codigo_ibge)))
    if valor is None:
        raise ValueError("SIDRA sem valor de renda.")
    return _embalar_variavel(
        valor,
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 3170, Variavel 5930, periodo 2022",
        mediana_nacional=MEDIANAS_NACIONAIS["renda_media_domiciliar"],
    )


def _calcular_centralidade_etaria(grupo: str) -> float:
    texto = (grupo or "").lower()
    if any(faixa in texto for faixa in ["30", "35", "40", "45", "50"]):
        return 0.15
    if any(faixa in texto for faixa in ["25", "55", "60"]):
        return 0.45
    return 0.8


def _buscar_faixa_etaria(codigo_ibge: str) -> dict:
    payload = _request_json(_sidra_url("9514", "93", codigo_ibge))
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("SIDRA sem distribuicao etaria.")

    grupos = []
    for row in payload[1:]:
        grupo = row.get("D3N") or row.get("D4N") or row.get("D5N") or "Nao informado"
        valor = row.get("V")
        try:
            percentual = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            continue
        grupos.append({"grupo": grupo, "valor": percentual})

    if not grupos:
        raise ValueError("Sem grupos etarios validos.")

    predominante = max(grupos, key=lambda item: item["valor"])
    return _embalar_variavel(
        predominante["grupo"],
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 9514, Variavel 93, periodo 2022",
        mediana_nacional="35 a 49 anos",
        extra={
            "centralidade": _calcular_centralidade_etaria(predominante["grupo"]),
            "distribuicao": grupos,
        },
    )


def _buscar_escolaridade(codigo_ibge: str) -> dict:
    valor = _parse_sidra_valor(_request_json(_sidra_url("3175", "5935", codigo_ibge)))
    if valor is None:
        raise ValueError("SIDRA sem escolaridade.")
    return _embalar_variavel(
        max(0.0, min(1.0, valor / 100 if valor > 1 else valor)),
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 3175, Variavel 5935, periodo 2022",
        mediana_nacional=MEDIANAS_NACIONAIS["escolaridade_superior"],
    )


def _buscar_densidade(codigo_ibge: str) -> dict:
    valor = _parse_sidra_valor(_request_json(_sidra_url("202", "605", codigo_ibge)))
    if valor is None:
        raise ValueError("SIDRA sem densidade.")
    return _embalar_variavel(
        valor,
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 202, Variavel 605, periodo 2022",
        mediana_nacional=MEDIANAS_NACIONAIS["densidade_populacional"],
    )


def _buscar_proporcao_alugados(codigo_ibge: str) -> dict:
    valor = _parse_sidra_valor(_request_json(_sidra_url("3163", "1000096", codigo_ibge)))
    if valor is None:
        raise ValueError("SIDRA sem proporcao de alugados.")
    return _embalar_variavel(
        max(0.0, min(1.0, valor / 100 if valor > 1 else valor)),
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 3163, Variavel 1000096, periodo 2022",
        mediana_nacional=MEDIANAS_NACIONAIS["proporcao_alugados"],
    )


def _buscar_populacao(codigo_ibge: str, ano: str) -> float:
    valor = _parse_sidra_valor(_request_json(_sidra_url("4709", "93", codigo_ibge, periodo=ano)))
    if valor is None:
        raise ValueError("SIDRA sem populacao.")
    return valor


def _buscar_crescimento_populacional(codigo_ibge: str) -> dict:
    pop_2022 = _buscar_populacao(codigo_ibge, "2022")
    pop_2010 = _buscar_populacao(codigo_ibge, "2010")
    if pop_2010 <= 0:
        raise ValueError("Populacao de 2010 invalida.")
    return _embalar_variavel(
        (pop_2022 - pop_2010) / pop_2010,
        fonte_tipo="api",
        fonte_nome="IBGE SIDRA",
        fonte_detalhe="Tabela 4709, Variavel 93, periodos 2010 e 2022",
        mediana_nacional=MEDIANAS_NACIONAIS["crescimento_populacional"],
        extra={"pop_2010": pop_2010, "pop_2022": pop_2022},
    )


def _buscar_idh(codigo_ibge: str) -> dict:
    return _embalar_variavel(
        MEDIANAS_NACIONAIS["idh"],
        fonte_tipo="estimativa",
        fonte_nome="Atlas Brasil (fallback estatistico)",
        fonte_detalhe="Sem API publica confiavel no fluxo automatico atual",
        mediana_nacional=MEDIANAS_NACIONAIS["idh"],
    )


def _fallback_por_variavel(nome: str) -> dict:
    mapa = {
        "renda_media_domiciliar": _embalar_variavel(
            MEDIANAS_NACIONAIS["renda_media_domiciliar"],
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Mediana nacional usada por indisponibilidade da API",
            mediana_nacional=MEDIANAS_NACIONAIS["renda_media_domiciliar"],
        ),
        "idh": _buscar_idh(""),
        "faixa_etaria_predominante": _embalar_variavel(
            "35 a 49 anos",
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Faixa etaria central media nacional",
            mediana_nacional="35 a 49 anos",
            extra={
                "centralidade": MEDIANAS_NACIONAIS["faixa_etaria_centralidade"],
                "distribuicao": [],
            },
        ),
        "escolaridade": _embalar_variavel(
            MEDIANAS_NACIONAIS["escolaridade_superior"],
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Percentual medio nacional estimado",
            mediana_nacional=MEDIANAS_NACIONAIS["escolaridade_superior"],
        ),
        "densidade_populacional": _embalar_variavel(
            MEDIANAS_NACIONAIS["densidade_populacional"],
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Mediana nacional usada por indisponibilidade da API",
            mediana_nacional=MEDIANAS_NACIONAIS["densidade_populacional"],
        ),
        "proporcao_alugados": _embalar_variavel(
            MEDIANAS_NACIONAIS["proporcao_alugados"],
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Mediana nacional usada por indisponibilidade da API",
            mediana_nacional=MEDIANAS_NACIONAIS["proporcao_alugados"],
        ),
        "crescimento_populacional": _embalar_variavel(
            MEDIANAS_NACIONAIS["crescimento_populacional"],
            fonte_tipo="estimativa",
            fonte_nome="Fallback nacional",
            fonte_detalhe="Mediana nacional usada por indisponibilidade da API",
            mediana_nacional=MEDIANAS_NACIONAIS["crescimento_populacional"],
            extra={"pop_2010": None, "pop_2022": None},
        ),
    }
    return mapa[nome]


@st.cache_data(ttl=3600)
def get_dados_ibge(codigo_ibge: str) -> dict:
    """Coleta dados publicos e aplica fallbacks quando necessario."""

    tarefas = {
        "renda_media_domiciliar": _buscar_renda_media,
        "idh": _buscar_idh,
        "faixa_etaria_predominante": _buscar_faixa_etaria,
        "escolaridade": _buscar_escolaridade,
        "densidade_populacional": _buscar_densidade,
        "proporcao_alugados": _buscar_proporcao_alugados,
        "crescimento_populacional": _buscar_crescimento_populacional,
    }
    resultados: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=len(tarefas)) as executor:
        future_map = {executor.submit(func, codigo_ibge): nome for nome, func in tarefas.items()}
        for future in as_completed(future_map):
            nome = future_map[future]
            try:
                resultados[nome] = future.result()
            except Exception:
                resultados[nome] = _fallback_por_variavel(nome)

    return {"codigo_ibge": codigo_ibge, **resultados}


def _clamp(valor: float, minimo: float = 0.0, maximo: float = 10.0) -> float:
    return max(minimo, min(maximo, valor))


def normalizar_para_score(dados_ibge: dict) -> dict:
    """Normaliza dados para escala 0 a 10 onde 10 e maior dificuldade."""

    renda = dados_ibge["renda_media_domiciliar"]["valor"]
    idh = dados_ibge["idh"]["valor"]
    centralidade_etaria = dados_ibge["faixa_etaria_predominante"].get(
        "centralidade", MEDIANAS_NACIONAIS["faixa_etaria_centralidade"]
    )
    escolaridade = dados_ibge["escolaridade"]["valor"]
    densidade = dados_ibge["densidade_populacional"]["valor"]
    alugados = dados_ibge["proporcao_alugados"]["valor"]
    crescimento = dados_ibge["crescimento_populacional"]["valor"]

    return {
        "renda_media": _clamp(10 - ((renda - 1500) / 5500) * 10),
        "idh": _clamp(10 - ((idh - 0.55) / 0.30) * 10),
        "faixa_etaria": _clamp(centralidade_etaria * 10),
        "escolaridade": _clamp(10 - (escolaridade * 10)),
        "densidade": _clamp(10 - ((densidade - 10) / 290) * 10),
        "proporcao_alugados": _clamp(10 - ((alugados - 0.05) / 0.35) * 10),
        "crescimento_pop": _clamp(10 - ((crescimento + 0.05) / 0.25) * 10),
    }


def sugerir_pontuacao_localizacao(localizacao: dict, dados_ibge: dict | None = None) -> dict:
    """Sugere nota de localizacao a partir do CEP e contexto municipal."""

    score = 3.0
    motivos = []
    bairro = (localizacao.get("bairro") or "").strip()
    rua = (localizacao.get("rua") or "").strip()
    if bairro:
        score += 0.5
        motivos.append(f"CEP identificado no bairro {bairro}.")
    else:
        motivos.append("CEP sem bairro detalhado; sugestao baseada no municipio.")
    if rua:
        score += 0.2

    if dados_ibge:
        renda = dados_ibge["renda_media_domiciliar"]["valor"]
        densidade = dados_ibge["densidade_populacional"]["valor"]
        idh = dados_ibge["idh"]["valor"]
        if renda >= MEDIANAS_NACIONAIS["renda_media_domiciliar"] * 1.2:
            score += 0.6
            motivos.append("Renda media local acima da mediana nacional.")
        elif renda < MEDIANAS_NACIONAIS["renda_media_domiciliar"] * 0.9:
            score -= 0.4
            motivos.append("Renda media local abaixo da mediana nacional.")

        if densidade >= MEDIANAS_NACIONAIS["densidade_populacional"] * 2:
            score += 0.4
            motivos.append("Boa densidade urbana e potencial de demanda.")
        elif densidade < MEDIANAS_NACIONAIS["densidade_populacional"]:
            score -= 0.2
            motivos.append("Densidade menor, o que pode reduzir fluxo espontaneo.")

        if idh >= 0.72:
            score += 0.3
            motivos.append("Ambiente socioeconomico favorece percepcao de valor.")

    score = int(round(max(1, min(5, score))))
    return {
        "score_sugerido": score,
        "motivos": motivos[:3],
        "resumo": " ".join(motivos[:3]),
    }
