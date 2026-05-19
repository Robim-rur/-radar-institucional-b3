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
st.write("Fluxo + Armadilhas + Continuidade Probabilística")

# =========================================================
# UNIVERSO
# =========================================================

UNIVERSO = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "BBAS3.SA",
    "WEGE3.SA",
    "RENT3.SA",
    "ABEV3.SA",
    "MGLU3.SA",
    "LREN3.SA",
    "BPAC11.SA",
    "SUZB3.SA",
    "EGIE3.SA",
    "ELET3.SA",
    "ELET6.SA",
    "PRIO3.SA"
]

# =========================================================
# EMA
# =========================================================

def ema(series, period=69):
    return series.ewm(span=period, adjust=False).mean()

# =========================================================
# SCORE ARMADILHA
# =========================================================

def score_armadilha(df):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)
    df["Vol_MA20"] = df["Volume"].rolling(20).mean()

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2]

    bull = 0
    bear = 0

    rng = ultimo["High"] - ultimo["Low"]

    if rng == 0:
        return 0

    # Bull Trap
    if (
        ultimo["High"] > anterior["High"]
        and ultimo["Close"] < anterior["High"]
    ):
        bull += 40

    if (
        ultimo["Volume"] > ultimo["Vol_MA20"] * 1.3
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
        ultimo["Volume"] > ultimo["Vol_MA20"] * 1.3
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

    df["Ret"] = df["Close"].pct_change()

    df["Vol_MA20"] = df["Volume"].rolling(20).mean()

    ultimo = df.iloc[-1]

    score = 0

    # Tendência
    if ultimo["Close"] > ultimo["EMA69"]:
        score += 30

    # Volume
    if ultimo["Volume"] > ultimo["Vol_MA20"] * 1.5:
        score += 30

    elif ultimo["Volume"] > ultimo["Vol_MA20"]:
        score += 15

    # Retorno positivo
    if ultimo["Ret"] > 0:
        score += 20

    # Fechamento forte
    rng = ultimo["High"] - ultimo["Low"]

    if rng > 0:

        pos = (
            (ultimo["Close"] - ultimo["Low"])
            / rng
        )

        if pos > 0.8:
            score += 20

    return min(score, 100)

# =========================================================
# SCORE CONTINUIDADE
# =========================================================

def score_continuidade(df, fluxo_score):

    df = df.copy()

    df["EMA69"] = ema(df["Close"], 69)

    df["Ret"] = df["Close"].pct_change()

    vol = df["Ret"].rolling(20).std().iloc[-1]

    ultimo = df.iloc[-1]

    prob = 50

    prob += (fluxo_score - 50) * 0.5

    prob += (
        (
            ultimo["Close"]
            / ultimo["EMA69"]
        ) - 1
    ) * 150

    prob -= vol * 800

    return max(5, min(95, prob))

# =========================================================
# EXECUÇÃO
# =========================================================

if st.button("📡 Rodar Radar"):

    resultados = []

    progresso = st.progress(0)

    for i, ticker in enumerate(UNIVERSO):

        try:

            # =================================================
            # DOWNLOAD
            # =================================================

            df = yf.download(
                ticker,
                period="6mo",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            # Corrige MultiIndex do yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # =================================================
            # VALIDAÇÃO
            # =================================================

            if df.empty:
                continue

            if len(df) < 80:
                continue

            # =================================================
            # SCORES
            # =================================================

            arm = score_armadilha(df)

            flux = score_fluxo(df)

            cont = score_continuidade(df, flux)

            # =================================================
            # SCORE FINAL
            # =================================================

            final_score = (
                (0.30 * arm)
                + (0.35 * flux)
                + (0.35 * cont)
            )

            resultados.append({
                "Ticker": ticker.replace(".SA", ""),
                "Armadilha": round(arm, 1),
                "Fluxo": round(flux, 1),
                "Continuidade": round(cont, 1),
                "Score Final": round(final_score, 1)
            })

        except Exception as e:

            st.warning(f"Erro em {ticker}: {e}")

            continue

        progresso.progress(
            (i + 1) / len(UNIVERSO)
        )

    # =========================================================
    # RESULTADOS
    # =========================================================

    if resultados:

        df_final = pd.DataFrame(resultados)

        df_final = df_final.sort_values(
            "Score Final",
            ascending=False
        )

        st.subheader("🏆 Ranking Institucional")

        st.dataframe(
            df_final,
            use_container_width=True
        )

        st.subheader("🔥 Top 5")

        st.dataframe(
            df_final.head(5),
            use_container_width=True
        )

    else:

        st.error(
            "Nenhum ativo retornou dados válidos."
        )
