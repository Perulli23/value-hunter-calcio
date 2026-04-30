import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Value Hunter", layout="wide")
st.title("⚽ Pro Football Value Hunter")
st.markdown("**Modello Poisson migliorato** — Cerco di trovare value bets reali")

# Filtri
st.sidebar.header("Filtri")
days_ahead = st.sidebar.slider("Giorni da analizzare", 5, 20, 12)
min_edge = st.sidebar.slider("Edge Score minimo", 0.01, 0.25, 0.03, 0.01)
league_filter = st.sidebar.selectbox("Lega", ["Tutte", "I1", "E0", "SP1", "D1", "F1"])

HOME_ADVANTAGE = 1.20

@st.cache_data(ttl=1800)
def load_data(days):
    try:
        # Carica fixtures
        fixtures = pd.read_csv("https://www.football-data.co.uk/fixtures.csv", encoding='latin1')
        fixtures['Date'] = pd.to_datetime(fixtures['Date'], dayfirst=True, errors='coerce')
        
        oggi = pd.Timestamp.today().normalize()
        limit = oggi + timedelta(days=days)
        
        # Filtro partite future
        upcoming = fixtures[(fixtures['Date'] >= oggi) & (fixtures['Date'] <= limit)].copy()
        upcoming = upcoming.dropna(subset=['HomeTeam', 'AwayTeam'])
        
        # Carica risultati storici recenti
        historical = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/Latest_Results.csv", encoding='latin1')
        
        st.sidebar.success(f"Partite trovate: {len(upcoming)}")
        return upcoming, historical
    except Exception as e:
        st.error(f"Errore download: {e}")
        return pd.DataFrame(), pd.DataFrame()

class SimpleHunter:
    def __init__(self):
        self.attack = {}
        self.defense = {}

    def fit(self, hist):
        if hist.empty:
            return
        teams = pd.concat([hist['HomeTeam'], hist['AwayTeam']]).dropna().unique()
        for t in teams:
            self.attack[t] = 1.35
            self.defense[t] = 1.35

        # Aggiornamento forza
        for _, row in hist.iterrows():
            if pd.isna(row.get('HomeTeam')) or pd.isna(row.get('AwayTeam')):
                continue
            h, a = row['HomeTeam'], row['AwayTeam']
            fthg = row.get('FTHG', 1.3)
            ftag = row.get('FTAG', 1.3)
            
            self.attack[h] = self.attack.get(h, 1.35) * 0.96 + (fthg / 1.38) * 0.04
            self.defense[h] = self.defense.get(h, 1.35) * 0.96 + (ftag / 1.38) * 0.04
            self.attack[a] = self.attack.get(a, 1.35) * 0.96 + (ftag / 1.38) * 0.04
            self.defense[a] = self.defense.get(a, 1.35) * 0.96 + (fthg / 1.38) * 0.04

    def predict(self, home, away):
        λh = self.attack.get(home, 1.4) * self.defense.get(away, 1.3) * HOME_ADVANTAGE
        λa = self.attack.get(away, 1.3) * self.defense.get(home, 1.4) * 0.93

        p1 = p_over25 = pbtts = 0.0
        for h in range(10):
            for a in range(10):
                prob = poisson.pmf(h, λh) * poisson.pmf(a, λa)
                if h > a: p1 += prob
                if h + a > 2.5: p_over25 += prob
                if h > 0 and a > 0: pbtts += prob

        edge = max(p1 - 0.48, p_over25 - 0.53, pbtts - 0.56)   # soglia più permissiva
        return {
            "Gol Attesi": round(λh + λa, 2),
            "1 (%)": round(p1*100, 1),
            "Over 2.5 (%)": round(p_over25*100, 1),
            "BTTS (%)": round(pbtts*100, 1),
            "Edge Score": round(edge, 3)
        }

hunter = SimpleHunter()
fixtures, historical = load_data(days_ahead)

if st.button("🚀 Avvia Analisi", type="primary", use_container_width=True):
    with st.spinner("Analisi in corso..."):
        hunter.fit(historical)
        results = []

        for _, row in fixtures.iterrows():
            home = row.get('HomeTeam')
            away = row.get('AwayTeam')
            if not home or not away:
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
            st.success(f"✅ Trovate **{len(df)}** partite con Edge ≥ {min_edge}")
            st.dataframe(df, use_container_width=True, height=800)
        else:
            st.error("❌ Ancora nessuna partita con edge sufficiente.")
            st.info("Consigli:")
            st.info("• Abbassa ulteriormente Edge Score a **0.01** o **0.02**")
            st.info("• Aumenta i giorni a 15")
            st.info("• Prova a cambiare lega o ricarica l'app")

st.caption("Versione migliorata - Edge Score più permissivo. Se non esce nulla, il problema è la mancanza di partite imminenti nei dati gratuiti.")
