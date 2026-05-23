# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Radar Institucional Unificado",
    layout="wide"
)

st.title("📊 Radar Institucional Unificado")

st.write(
    "Fluxo + Armadilhas + Continuidade + Fibonacci Institucional"
)

# =========================================================
# UNIVERSO
# =========================================================

UNIVERSO = [

    "PETR4.SA","VALE3.SA","BBAS3.SA","ITUB4.SA","BBDC4.SA",
    "WEGE3.SA","PRIO3.SA","RENT3.SA","ELET3.SA","ELET6.SA",
    "CPLE6.SA","CMIG4.SA","TAEE11.SA","EGIE3.SA","VIVT3.SA",
    "TIMS3.SA","ABEV3.SA","RADL3.SA","SUZB3.SA","GGBR4.SA",
    "GOAU4.SA","USIM5.SA","CSNA3.SA","RAIL3.SA","SBSP3.SA",
    "EQTL3.SA","HYPE3.SA","MULT3.SA","LREN3.SA","ARZZ3.SA",
    "TOTS3.SA","EMBR3.SA","JBSS3.SA","BEEF3.SA","MRFG3.SA",
    "BRFS3.SA","SLCE3.SA","SMTO3.SA","B3SA3.SA","BBSE3.SA",
    "BPAC11.SA","SANB11.SA","ITSA4.SA","BRSR6.SA","CXSE3.SA",
    "POMO4.SA","STBP3.SA","TUPY3.SA","DIRR3.SA","CYRE3.SA",
    "EZTC3.SA","JHSF3.SA","KEPL3.SA","POSI3.SA","MOVI3.SA",
    "PETZ3.SA","COGN3.SA","YDUQ3.SA","MGLU3.SA","NTCO3.SA",
    "AZUL4.SA","GOLL4.SA","CVCB3.SA","RRRP3.SA","RECV3.SA",
    "ENAT3.SA","ORVR3.SA","AURE3.SA","ENEV3.SA","UGPA3.SA",

    "BOVA11.SA","IVVB11.SA","SMAL11.SA","GOLD11.SA",
    "DIVO11.SA","NDIV11.SA",

    "HGLG11.SA","XPLG11.SA","VISC11.SA","MXRF11.SA",
    "KNRI11.SA","KNCR11.SA","KNIP11.SA","CPTS11.SA",
    "IRDM11.SA","TRXF11.SA","TGAR11.SA","HGRU11.SA",
    "ALZR11.SA","AUVP11.SA","IEEX11.SA","UTLL11.SA",

    "AAPL34.SA","AMZO34.SA","GOGL34.SA","MSFT34.SA",
    "TSLA34.SA","META34.SA","NFLX34.SA","NVDC34.SA",
    "MELI34.SA","BABA34.SA","DISB34.SA","PYPL34.SA",
    "JNJB34.SA","VISA34.SA","WMTB34.SA","NIKE34.SA",
    "ADBE34.SA","CSCO34.SA","INTC34.SA","JPMC34.SA",
    "ORCL34.SA","QCOM34.SA","SBUX34.SA","TXN34.SA",
    "ABTT34.SA","AMGN34.SA","AXPB34.SA","BERK34.SA"

]

# =========================================================
# EMA
# =========================================================

def ema(series, period=69):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()

# =========================================================
# SCORE ARMADILHA
# =========================================================

def score_armadilha(df):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)

    df["Vol_MA20"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )

    ultimo = df.iloc[-1]

    anterior = df.iloc[-2]

    bull = 0
    bear = 0

    rng = (
        ultimo["High"]
        - ultimo["Low"]
    )

    if rng == 0:
        return 0

    # Bull Trap
    if (
        ultimo["High"] > anterior["High"]
        and ultimo["Close"] < anterior["High"]
    ):
        bull += 40

    if (
        ultimo["Volume"]
        > ultimo["Vol_MA20"] * 1.3
        and ultimo["Close"] < ultimo["Open"]
    ):
        bull += 25

    if ultimo["Close"] < ultimo["EMA69"]:
        bull += 15

    # Bear Trap
    if (
        ultimo["Low"] < anterior["Low"]
        and ultimo["Close"] > anterior["Low"]
    ):
        bear += 40

    if (
        ultimo["Volume"]
        > ultimo["Vol_MA20"] * 1.3
        and ultimo["Close"] > ultimo["Open"]
    ):
        bear += 25

    if ultimo["Close"] > ultimo["EMA69"]:
        bear += 15

    return min(max(bull, bear), 100)

# =========================================================
# SCORE FLUXO
# =========================================================

def score_fluxo(df):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)

    df["Ret"] = (
        df["Close"]
        .pct_change()
    )

    df["Vol_MA20"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )

    ultimo = df.iloc[-1]

    score = 0

    # Tendência
    if ultimo["Close"] > ultimo["EMA69"]:
        score += 30

    # Volume
    if (
        ultimo["Volume"]
        > ultimo["Vol_MA20"] * 1.5
    ):
        score += 30

    elif (
        ultimo["Volume"]
        > ultimo["Vol_MA20"]
    ):
        score += 15

    # Retorno positivo
    if ultimo["Ret"] > 0:
        score += 20

    # Fechamento forte
    rng = (
        ultimo["High"]
        - ultimo["Low"]
    )

    if rng > 0:

        pos = (
            (
                ultimo["Close"]
                - ultimo["Low"]
            )
            / rng
        )

        if pos > 0.7:
            score += 20

    return min(score, 100)

# =========================================================
# SCORE CONTINUIDADE
# =========================================================

def score_continuidade(df, fluxo_score):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)

    df["Ret"] = (
        df["Close"]
        .pct_change()
    )

    vol = (
        df["Ret"]
        .rolling(20)
        .std()
        .iloc[-1]
    )

    ultimo = df.iloc[-1]

    prob = 50

    prob += (
        (fluxo_score - 50)
        * 0.6
    )

    prob += (
        (
            ultimo["Close"]
            / ultimo["EMA69"]
        ) - 1
    ) * 200

    prob -= vol * 400

    return max(5, min(95, prob))

# =========================================================
# SCORE FIBONACCI
# =========================================================

def score_fibonacci(df):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)

    df["Vol_MA20"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )

    periodo = df.tail(60)

    topo = periodo["High"].max()

    fundo = periodo["Low"].min()

    amplitude = topo - fundo

    if amplitude <= 0:
        return 0

    fib_382 = topo - (amplitude * 0.382)

    fib_50 = topo - (amplitude * 0.50)

    fib_618 = topo - (amplitude * 0.618)

    ultimo = df.iloc[-1]

    close = ultimo["Close"]

    score = 0

    dist_382 = abs(close - fib_382) / close
    dist_50 = abs(close - fib_50) / close
    dist_618 = abs(close - fib_618) / close

    if dist_382 < 0.03:
        score += 20

    if dist_50 < 0.03:
        score += 30

    if dist_618 < 0.03:
        score += 40

    if close > ultimo["Open"]:
        score += 10

    if (
        ultimo["Volume"]
        > ultimo["Vol_MA20"]
    ):
        score += 10

    if close > ultimo["EMA69"]:
        score += 10

    return min(score, 100)

# =========================================================
# FUNÇÃO DE ANÁLISE
# =========================================================

def analisar_ativo(ticker):

    try:

        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        # Corrige MultiIndex
        if isinstance(
            df.columns,
            pd.MultiIndex
        ):
            df.columns = (
                df.columns
                .get_level_values(0)
            )

        if df.empty:
            return None

        if len(df) < 80:
            return None

        arm = score_armadilha(df)

        arm_ajustada = 100 - arm

        flux = score_fluxo(df)

        cont = score_continuidade(
            df,
            flux
        )

        fib = score_fibonacci(df)

        final_score = (
            (0.25 * arm_ajustada)
            + (0.30 * flux)
            + (0.30 * cont)
            + (0.15 * fib)
        )

        return {
            "Ticker": ticker.replace(".SA", ""),
            "Armadilha": round(arm, 1),
            "Fluxo": round(flux, 1),
            "Continuidade": round(cont, 1),
            "Fibonacci": round(fib, 1),
            "Score Final": round(final_score, 1)
        }

    except Exception as e:

        st.warning(
            f"Erro em {ticker}: {e}"
        )

        return None

# =========================================================
# SCANNER INDIVIDUAL
# =========================================================

st.subheader("🔎 Scanner Individual")

ativo_escolhido = st.selectbox(
    "Escolha um ativo:",
    UNIVERSO
)

if st.button("📌 Escanear Ativo"):

    resultado_individual = analisar_ativo(
        ativo_escolhido
    )

    if resultado_individual:

        st.dataframe(
            pd.DataFrame([resultado_individual]),
            use_container_width=True
        )

    else:

        st.error(
            "Não foi possível analisar este ativo."
        )

# =========================================================
# RADAR COMPLETO
# =========================================================

st.subheader("📡 Radar Completo")

if st.button("🚀 Rodar Radar Geral"):

    resultados = []

    progresso = st.progress(0)

    for i, ticker in enumerate(UNIVERSO):

        resultado = analisar_ativo(ticker)

        if resultado:
            resultados.append(resultado)

        progresso.progress(
            (i + 1)
            / len(UNIVERSO)
        )

    # =====================================================
    # RESULTADOS
    # =====================================================

    if resultados:

        df_final = pd.DataFrame(
            resultados
        )

        df_final = (
            df_final
            .sort_values(
                "Score Final",
                ascending=False
            )
        )

        st.subheader(
            "🏆 Ranking Institucional"
        )

        st.dataframe(
            df_final,
            use_container_width=True
        )

        st.subheader(
            "🔥 Top 10"
        )

        st.dataframe(
            df_final.head(10),
            use_container_width=True
        )

    else:

        st.error(
            "Nenhum ativo retornou dados válidos."
        )

    else:

        st.error(
            "Nenhum ativo retornou dados válidos."
        )
