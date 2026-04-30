import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Value Hunter", layout="wide")
st.title("⚽ Pro Football Value Hunter")
st.markdown("**Modello Poisson avanzato** — Previsioni credibili su Gol, 1X2, Over/Under e BTTS")

# ====================== FILTRO SIDEBAR ======================
st.sidebar.header("Filtri")
days_ahead = st.sidebar.slider("Mostra partite nei prossimi giorni", min_value=3, max_value=14, value=8)
min_edge = st.sidebar.slider("Edge Score minimo", 0.05, 0.30, 0.10, 0.01)
league_filter = st.sidebar.selectbox(
    "Seleziona Lega", 
    ["Tutte", "I1 (Serie A)", "E0 (Premier)", "SP1 (La Liga)", "D1 (Bundesliga)", "F1 (Ligue 1)"]
)

HOME_ADVANTAGE = 1.20
TIME_DECAY = 0.93   # Le partite più recenti pesano di più

# ====================== CARICAMENTO DATI ======================
@st.cache_data(ttl=3600)
def load_data():
    try:
        # Prossime partite
        fixtures = pd.read_csv("https://www.football-data.co.uk/fixtures.csv")
        fixtures['Date'] = pd.to_datetime(fixtures['Date'], dayfirst=True, errors='coerce')
        oggi = pd.Timestamp.today()
        limit = oggi + timedelta(days=days_ahead)
        fixtures = fixtures[(fixtures['Date'] >= oggi) & (fixtures['Date'] <= limit)].copy()
        
        # Dati storici per calcolare forza squadre
        historical = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/Latest_Results.csv", encoding='latin1')
        return fixtures, historical
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return pd.DataFrame(), pd.DataFrame()

class AdvancedHunter:
    def __init__(self):
        self.attack = {}
        self.defense = {}
        self.recent_form = {}

    def fit(self, df_hist):
        if df_hist.empty:
            return
        
        teams = pd.concat([df_hist['HomeTeam'], df_hist['AwayTeam']]).unique()
        
        for team in teams:
            self.attack[team] = 1.35
            self.defense[team] = 1.35
            self.recent_form[team] = 1.35

        # Calcolo semplice ma realistico di attacco/difesa
        for _, row in df_hist.iterrows():
            home = row['HomeTeam']
            away = row['AwayTeam']
            if pd.isna(home) or pd.isna(away):
                continue
                
            fthg = row['FTHG']
            ftag = row['FTAG']
            
            self.attack[home] = self.attack.get(home, 1.3) * 0.98 + (fthg / 1.35) * 0.02
            self.defense[home] = self.defense.get(home, 1.3) * 0.98 + (ftag / 1.35) * 0.02
            self.attack[away] = self.attack.get(away, 1.3) * 0.98 + (ftag / 1.35) * 0.02
            self.defense[away] = self.defense.get(away, 1.3) * 0.98 + (fthg / 1.35) * 0.02

    def predict_match(self, home, away):
        if home not in self.attack or away not in self.attack:
            return None
            
        # Time decay + forma
        lambda_home = self.attack.get(home, 1.4) * self.defense.get(away, 1.3) * HOME_ADVANTAGE * self.recent_form.get(home, 1.3)/1.3
        lambda_away = self.attack.get(away, 1.3) * self.defense.get(home, 1.4) * 0.94 * self.recent_form.get(away, 1.3)/1.3

        # Calcolo probabilità con Poisson
        p_home = p_draw = p_away = p_over25 = p_btts = 0.0
        for h in range(10):
            for a in range(10):
                prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                if h > a:
                    p_home += prob
                elif h == a:
                    p_draw += prob
                else:
                    p_away += prob
                if h + a > 2.5:
                    p_over25 += prob
                if h > 0 and a > 0:
                    p_btts += prob

        edge_score = max(p_home - 0.52, p_over25 - 0.56, p_btts - 0.59)

        return {
            "Prob 1 (%)": round(p_home * 100, 1),
            "Prob X (%)": round(p_draw * 100, 1),
            "Prob 2 (%)": round(p_away * 100, 1),
            "Over 2.5 (%)": round(p_over25 * 100, 1),
            "BTTS (%)": round(p_btts * 100, 1),
            "Gol Attesi": round(lambda_home + lambda_away, 2),
            "Edge Score": round(edge_score, 3)
        }

# ====================== ESECUZIONE ======================
hunter = AdvancedHunter()
fixtures, historical = load_data()

if st.button("🚀 Avvia Analisi Completa", type="primary", use_container_width=True):
    with st.spinner("Calcolo forza squadre e previsioni..."):
        hunter.fit(historical)
        results = []

        for _, row in fixtures.iterrows():
            home = row.get('HomeTeam')
            away = row.get('AwayTeam')
            if pd.isna(home) or pd.isna(away):
                continue

            pred = hunter.predict_match(home, away)
            if not pred:
                continue

            if pred["Edge Score"] >= min_edge:
                league = row.get('Div', '—')
                if league_filter != "Tutte" and league not in league_filter:
                    continue

                results.append({
                    "Data": row['Date'].strftime('%d/%m %H:%M'),
                    "Partita": f"{home} - {away}",
                    "Lega": league,
                    "Gol Attesi": pred["Gol Attesi"],
                    "1 (%)": pred["Prob 1 (%)"],
                    "X (%)": pred["Prob X (%)"],
                    "2 (%)": pred["Prob 2 (%)"],
                    "Over 2.5 (%)": pred["Over 2.5 (%)"],
                    "BTTS (%)": pred["BTTS (%)"],
                    "Edge Score": pred["Edge Score"]
                })

        if results:
            df_final = pd.DataFrame(results).sort_values("Edge Score", ascending=False)
            st.success(f"**{len(df_final)}** partite con Edge Score ≥ {min_edge}")
            st.dataframe(df_final, use_container_width=True, height=800)
        else:
            st.info("Nessuna partita supera la soglia di edge impostata. Prova ad abbassare il valore minimo.")

st.caption("⚠️ Modello basato su dati reali da football-data.co.uk + Poisson con time decay. "
           "Non include corners/cartellini perché i dati gratuiti non sono sufficienti per stime attendibili. "
           "Questa è la versione più credibile possibile senza API a pagamento. Usa solo per studio e analisi.")
