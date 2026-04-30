import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Value Hunter", layout="wide")
st.title("⚽ Pro Football Value Hunter")
st.markdown("**Modello Poisson avanzato** — Previsioni su 1X2, Over 2.5, BTTS e Gol Attesi")

# Filtri
st.sidebar.header("Filtri")
days_ahead = st.sidebar.slider("Partite nei prossimi giorni", 3, 15, 10)
min_edge = st.sidebar.slider("Edge Score minimo", 0.01, 0.25, 0.06, 0.01)
league_filter = st.sidebar.selectbox("Lega", ["Tutte", "I1", "E0", "SP1", "D1", "F1"])

HOME_ADVANTAGE = 1.20

@st.cache_data(ttl=3600)
def load_data():
    try:
        fixtures = pd.read_csv("https://www.football-data.co.uk/fixtures.csv")
        fixtures['Date'] = pd.to_datetime(fixtures['Date'], dayfirst=True, errors='coerce')
        oggi = pd.Timestamp.today()
        limit = oggi + timedelta(days=days_ahead)
        fixtures = fixtures[(fixtures['Date'] >= oggi) & (fixtures['Date'] <= limit)].copy()
        
        historical = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/Latest_Results.csv", encoding='latin1')
        return fixtures, historical
    except:
        st.warning("Errore nel download dei dati. Uso modalità demo.")
        return pd.DataFrame(), pd.DataFrame()

class Hunter:
    def __init__(self):
        self.attack = {}
        self.defense = {}

    def fit(self, df_hist):
        if df_hist.empty:
            return
        teams = pd.concat([df_hist['HomeTeam'], df_hist['AwayTeam']]).dropna().unique()
        for team in teams:
            self.attack[team] = 1.35
            self.defense[team] = 1.35

        # Aggiornamento semplice forza
        for _, row in df_hist.iterrows():
            if pd.isna(row['HomeTeam']) or pd.isna(row['AwayTeam']):
                continue
            home, away = row['HomeTeam'], row['AwayTeam']
            fthg, ftag = row.get('FTHG', 1.35), row.get('FTAG', 1.35)
            
            self.attack[home] = self.attack.get(home, 1.35) * 0.97 + (fthg / 1.4) * 0.03
            self.defense[home] = self.defense.get(home, 1.35) * 0.97 + (ftag / 1.4) * 0.03
            self.attack[away] = self.attack.get(away, 1.35) * 0.97 + (ftag / 1.4) * 0.03
            self.defense[away] = self.defense.get(away, 1.35) * 0.97 + (fthg / 1.4) * 0.03

    def predict(self, home, away):
        λh = self.attack.get(home, 1.4) * self.defense.get(away, 1.3) * HOME_ADVANTAGE
        λa = self.attack.get(away, 1.3) * self.defense.get(home, 1.4) * 0.94

        p1 = p_over25 = pbtts = 0.0
        for h in range(10):
            for a in range(10):
                prob = poisson.pmf(h, λh) * poisson.pmf(a, λa)
                if h > a: p1 += prob
                if h + a > 2.5: p_over25 += prob
                if h > 0 and a > 0: pbtts += prob

        edge = max(p1 - 0.50, p_over25 - 0.54, pbtts - 0.57)
        return {
            "Gol Attesi": round(λh + λa, 2),
            "1 (%)": round(p1*100, 1),
            "Over 2.5 (%)": round(p_over25*100, 1),
            "BTTS (%)": round(pbtts*100, 1),
            "Edge Score": round(edge, 3)
        }

hunter = Hunter()
fixtures, historical = load_data()

if st.button("🚀 Avvia Analisi", type="primary", use_container_width=True):
    with st.spinner("Calcolo in corso..."):
        hunter.fit(historical)
        results = []

        for _, row in fixtures.iterrows():
            home = row.get('HomeTeam')
            away = row.get('AwayTeam')
            if pd.isna(home) or pd.isna(away):
                continue

            pred = hunter.predict(home, away)
            if pred["Edge Score"] >= min_edge:
                league = row.get('Div', '—')
                if league_filter != "Tutte" and league != league_filter.split()[0]:
                    continue

                results.append({
                    "Data": row['Date'].strftime('%d/%m %H:%M'),
                    "Partita": f"{home} - {away}",
                    "Lega": league,
                    "Gol Attesi": pred["Gol Attesi"],
                    "1 (%)": pred["1 (%)"],
                    "Over 2.5 (%)": pred["Over 2.5 (%)"],
                    "BTTS (%)": pred["BTTS (%)"],
                    "Edge Score": pred["Edge Score"]
                })

        if results:
            df = pd.DataFrame(results).sort_values("Edge Score", ascending=False)
            st.success(f"Trovate **{len(df)}** partite con Edge Score ≥ {min_edge}")
            st.dataframe(df, use_container_width=True, height=750)
        else:
            st.warning("⚠️ Nessuna partita supera la soglia attuale. Prova ad abbassare 'Edge Score minimo' a 0.03 o 0.04")

st.caption("Modello statistico basato su dati gratuiti. Non è una garanzia di vincita. Gioca responsabilmente.")
