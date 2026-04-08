"""Ferramentas para simulacao de preco ideal via Van Westendorp."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

COLUNAS_BASE = [
    "too_cheap",
    "cheap",
    "expensive",
    "too_expensive",
    "pi_cheap",
    "pi_expensive",
    "include",
]

CALIBRACAO_PADRAO = {
    1: 0.7,
    2: 0.5,
    3: 0.3,
    4: 0.1,
    5: 0.0,
}

TEMPLATE_EXEMPLO = pd.DataFrame(
    [
        {"too_cheap": 250000, "cheap": 320000, "expensive": 390000, "too_expensive": 470000, "pi_cheap": 1, "pi_expensive": 2, "include": 1},
        {"too_cheap": 280000, "cheap": 340000, "expensive": 410000, "too_expensive": 500000, "pi_cheap": 2, "pi_expensive": 3, "include": 1},
        {"too_cheap": 300000, "cheap": 360000, "expensive": 430000, "too_expensive": 520000, "pi_cheap": 2, "pi_expensive": 3, "include": 1},
        {"too_cheap": 260000, "cheap": 330000, "expensive": 400000, "too_expensive": 480000, "pi_cheap": 1, "pi_expensive": 2, "include": 1},
    ]
)


@dataclass(frozen=True)
class Intersecao:
    nome: str
    preco: float | None


def template_csv_bytes() -> bytes:
    return TEMPLATE_EXEMPLO.to_csv(index=False).encode("utf-8")


def carregar_pesquisa_preco(uploaded_file) -> pd.DataFrame:
    nome = uploaded_file.name.lower()
    if nome.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if nome.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Formato nao suportado. Use CSV ou XLSX.")


def normalizar_dataframe_pesquisa(df: pd.DataFrame) -> pd.DataFrame:
    renomeadas = {col: str(col).strip().lower().replace(" ", "_") for col in df.columns}
    dados = df.rename(columns=renomeadas).copy()

    ausentes = [col for col in COLUNAS_BASE if col not in dados.columns]
    if ausentes:
        faltantes = ", ".join(ausentes)
        raise ValueError(f"Colunas obrigatorias ausentes: {faltantes}.")

    dados = dados[COLUNAS_BASE].copy()
    for coluna in ["too_cheap", "cheap", "expensive", "too_expensive", "pi_cheap", "pi_expensive", "include"]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    dados = dados.dropna(subset=["too_cheap", "cheap", "expensive", "too_expensive", "pi_cheap", "pi_expensive"])
    dados["include"] = dados["include"].fillna(1)
    dados = dados[dados["include"] != 0].copy()
    if dados.empty:
        raise ValueError("Nenhuma resposta valida encontrada apos aplicar o filtro de inclusao.")

    ordem_valida = (
        (dados["too_cheap"] <= dados["cheap"])
        & (dados["cheap"] <= dados["expensive"])
        & (dados["expensive"] <= dados["too_expensive"])
    )
    if not ordem_valida.all():
        indices_invalidos = dados.index[~ordem_valida].tolist()
        primeiros = ", ".join(str(int(idx) + 2) for idx in indices_invalidos[:5])
        raise ValueError(
            "Algumas respostas nao respeitam a ordem too_cheap <= cheap <= expensive <= too_expensive. "
            f"Confira as linhas: {primeiros}."
        )

    for coluna in ["pi_cheap", "pi_expensive"]:
        valores_invalidos = ~dados[coluna].astype(int).isin(CALIBRACAO_PADRAO)
        if valores_invalidos.any():
            raise ValueError(f"A coluna {coluna} deve usar apenas notas de 1 a 5.")
        dados[coluna] = dados[coluna].astype(int)

    return dados.reset_index(drop=True)


def _curva_maior_igual(series: pd.Series, precos: np.ndarray) -> np.ndarray:
    valores = series.to_numpy(dtype=float)
    return np.array([(valores >= preco).mean() for preco in precos], dtype=float)


def _curva_menor_igual(series: pd.Series, precos: np.ndarray) -> np.ndarray:
    valores = series.to_numpy(dtype=float)
    return np.array([(valores <= preco).mean() for preco in precos], dtype=float)


def _interpolar_intersecao(
    precos: np.ndarray,
    serie_a: np.ndarray,
    serie_b: np.ndarray,
) -> float | None:
    diferenca = serie_a - serie_b
    zeros = np.where(np.isclose(diferenca, 0.0, atol=1e-9))[0]
    if len(zeros):
        return float(precos[zeros[0]])

    sinais = np.sign(diferenca)
    cruzamentos = np.where(sinais[:-1] * sinais[1:] < 0)[0]
    if not len(cruzamentos):
        return None

    idx = int(cruzamentos[0])
    x1, x2 = float(precos[idx]), float(precos[idx + 1])
    y1, y2 = float(diferenca[idx]), float(diferenca[idx + 1])
    if np.isclose(y1, y2):
        return x1
    return x1 - y1 * (x2 - x1) / (y2 - y1)


def _aplicar_ajuste_empates(df: pd.DataFrame) -> pd.DataFrame:
    dados = df.copy()
    dados["tc_adj"] = dados["too_cheap"]
    dados["c_adj"] = np.where(dados["cheap"] == dados["too_cheap"], dados["cheap"] + 0.00001, dados["cheap"])
    dados["e_adj"] = np.where(dados["expensive"] == dados["cheap"], dados["expensive"] + 0.00002, dados["expensive"])
    dados["te_adj"] = np.where(dados["too_expensive"] == dados["expensive"], dados["too_expensive"] + 0.00003, dados["too_expensive"])
    return dados


def _simular_probabilidade_individual(
    linha: pd.Series,
    precos: np.ndarray,
    calibracao: dict[int, float],
    fator_too_expensive: float,
    fator_too_cheap: float,
) -> tuple[np.ndarray, np.ndarray]:
    p1 = float(linha["tc_adj"])
    p2 = float(linha["c_adj"])
    p3 = float(linha["e_adj"])
    p4 = float(linha["te_adj"])

    q2 = float(calibracao[int(linha["pi_cheap"])])
    q3 = float(calibracao[int(linha["pi_expensive"])])
    q4 = fator_too_expensive * q3
    q1 = fator_too_cheap * q2

    probs = np.zeros_like(precos, dtype=float)

    abaixo = precos < p1
    probs[abaixo] = q1

    faixa_1 = (precos >= p1) & (precos <= p2)
    if faixa_1.any():
        proporcao = (precos[faixa_1] - p1) / (p2 - p1)
        probs[faixa_1] = q1 * (1 - proporcao) + q2 * proporcao

    faixa_2 = (precos > p2) & (precos <= p3)
    if faixa_2.any():
        proporcao = (precos[faixa_2] - p2) / (p3 - p2)
        probs[faixa_2] = q2 * (1 - proporcao) + q3 * proporcao

    faixa_3 = (precos > p3) & (precos <= p4)
    if faixa_3.any():
        proporcao = (precos[faixa_3] - p3) / (p4 - p3)
        probs[faixa_3] = q3 * (1 - proporcao) + q4 * proporcao

    aceitavel = ((precos >= p2) & (precos <= p3)).astype(float)
    return probs, aceitavel


def calcular_van_westendorp(
    df: pd.DataFrame,
    *,
    price_step: float | None = None,
    calibration: dict[int, float] | None = None,
    factor_too_expensive: float = 0.0,
    factor_too_cheap: float = 1.0,
) -> dict:
    dados = normalizar_dataframe_pesquisa(df)
    dados = _aplicar_ajuste_empates(dados)
    calibration = calibration or CALIBRACAO_PADRAO

    minimo = float(dados["too_cheap"].min())
    maximo = float(dados["too_expensive"].max())
    amplitude = maximo - minimo
    if price_step is None:
        step_bruto = amplitude / 40 if amplitude > 0 else max(minimo * 0.05, 1)
        price_step = max(round(step_bruto / 1000) * 1000, 1000)
    price_step = float(price_step)

    preco_inicio = max(0.0, np.floor(minimo / price_step) * price_step)
    preco_fim = np.ceil(maximo / price_step) * price_step
    precos = np.arange(preco_inicio, preco_fim + price_step, price_step, dtype=float)

    curva_too_cheap = _curva_maior_igual(dados["tc_adj"], precos)
    curva_cheap = _curva_maior_igual(dados["c_adj"], precos)
    curva_expensive = _curva_menor_igual(dados["e_adj"], precos)
    curva_too_expensive = _curva_menor_igual(dados["te_adj"], precos)

    matriz_probs = []
    matriz_aceitavel = []
    for _, linha in dados.iterrows():
        probs, aceitavel = _simular_probabilidade_individual(
            linha,
            precos,
            calibration,
            factor_too_expensive,
            factor_too_cheap,
        )
        matriz_probs.append(probs)
        matriz_aceitavel.append(aceitavel)

    probs_medias = np.vstack(matriz_probs).mean(axis=0)
    alcance_medio = np.vstack(matriz_aceitavel).mean(axis=0)
    receita_indice = precos * probs_medias

    curvas = pd.DataFrame(
        {
            "price": precos,
            "too_cheap": curva_too_cheap,
            "cheap": curva_cheap,
            "expensive": curva_expensive,
            "too_expensive": curva_too_expensive,
            "purchase_intent": probs_medias,
            "reach": alcance_medio,
            "revenue_index": receita_indice,
        }
    )

    intersecoes = {
        "pmc": _interpolar_intersecao(precos, curva_too_cheap, curva_expensive),
        "opp": _interpolar_intersecao(precos, curva_cheap, curva_expensive),
        "idp": _interpolar_intersecao(precos, curva_too_cheap, curva_too_expensive),
        "pme": _interpolar_intersecao(precos, curva_cheap, curva_too_expensive),
    }

    idx_receita = int(curvas["revenue_index"].idxmax())
    idx_alcance = int(curvas["purchase_intent"].idxmax())

    resumo = {
        "n_respostas": int(len(dados)),
        "preco_otimo_receita": float(curvas.loc[idx_receita, "price"]),
        "receita_indice_max": float(curvas.loc[idx_receita, "revenue_index"]),
        "preco_maior_intencao": float(curvas.loc[idx_alcance, "price"]),
        "intencao_max": float(curvas.loc[idx_alcance, "purchase_intent"]),
        "faixa_aceitavel_min": intersecoes["pmc"],
        "faixa_aceitavel_max": intersecoes["pme"],
        "preco_indiferenca": intersecoes["idp"],
        "preco_otimo_classico": intersecoes["opp"],
    }

    return {
        "input": dados,
        "curvas": curvas,
        "resumo": resumo,
        "intersecoes": intersecoes,
        "price_step": price_step,
    }
