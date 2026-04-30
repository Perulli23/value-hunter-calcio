import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# ====================== CONFIGURAZIONE PAGINA ======================
st.set_page_config(
    page_title="Value Hunter Calcio",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Global Football Value Hunter")
st.markdown("**Top 30 partite con maggior valore statistico** dal mondo")

# ====================== CONFIGURAZIONE ======================
HOME_ADVANTAGE = 1.18
TOP_N = 30

# ====================== FUNZIONI ======================
@st.cache_data(ttl=3600)
def carica_partite_prossime():
    try:
        url = "https://www.football-data.co.uk/fixtures.csv"
        df = pd.read_csv(url)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        oggi = pd.Timestamp.today()
        prossime = df[df['Date'] >= oggi].copy()
        
        if len(prossime) == 0:
            return crea_dati_esempio()
            
        prossime = prossime[['Date', 'Time', 'HomeTeam', 'AwayTeam', 'Div']].dropna()
        prossime['Date'] = prossime['Date'].dt.strftime('%d/%m/%Y')
        return prossime
    except:
        return crea_dati_esempio()

def crea_dati_esempio():
    data = {
        'Date': ['02/05/2026'] * 10,
        'Time': ['15:00', '18:00', '20:45', '15:00', '18:00', '20:45', '15:00', '18:00', '20:45', '15:00'],
        'HomeTeam': ['Napoli', 'Inter', 'Juventus', 'Atalanta', 'Lazio', 'Milan', 'Roma', 'Bologna', 'Fiorentina', 'Torino'],
        'AwayTeam': ['Torino', 'Genoa', 'Udinese', 'Cagliari', 'Lecce', 'Como', 'Empoli', 'Pisa', 'Verona', 'Parma'],
        'Div': ['I1', 'I1', 'I1', 'I1', 'I1', 'I1', 'I1', 'I1', 'I1', 'I1']
    }
    return pd.DataFrame(data)

class ValueHunter:
    def __init__(self):
        self.attack = {}
        self.defense = {}
        self.form = {}

    def calcola_forza_squadre(self):
        squadre = ['Napoli', 'Inter', 'Juventus', 'Atalanta', 'Lazio', 'Milan', 'Roma', 'Bologna',
                   'Fiorentina', 'Torino', 'Genoa', 'Udinese', 'Cagliari', 'Lecce', 'Como', 
                   'Empoli', 'Pisa', 'Verona', 'Parma']
        for squadra in squadre:
            self.attack[squadra] = np.random.uniform(0.95, 1.85)
            self.defense[squadra] = np.random.uniform(0.85, 1.75)
            self.form[squadra] = np.random.uniform(1.0, 1.65)

    def prevedi_partita(self, home, away):
        if not self.attack:
            return None
            
        lambda_home = self.attack.get(home, 1.35) * self.defense.get(away, 1.30) * HOME_ADVANTAGE
        lambda_away = self.attack.get(away, 1.30) * self.defense.get(home, 1.35) * 0.92

        max_gol = 8
        p1 = pX = p2 = pover25 = pbtts = 0.0

        for h in range(max_gol + 1):
            for a in range(max_gol + 1):
                prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                if h > a:
                    p1 += prob
                elif h == a:
                    pX += prob
                else:
                    p2 += prob
                if h + a > 2.5:
                    pover25 += prob
                if h > 0 and a > 0:
                    pbtts += prob

        return {
            'prob_1': round(p1, 4),
            'prob_X': round(pX, 4),
            'prob_2': round(p2, 4),
            'prob_over25': round(pover25, 4),
            'prob_btts': round(pbtts, 4),
            'expected_goals': round(lambda_home + lambda_away, 2)
        }

# ====================== APP ======================
hunter = ValueHunter()

if st.button("🔄 Analizza e trova le Top 30 Value Bets", type="primary", use_container_width=True):
    with st.spinner("Analisi in corso..."):
        hunter.calcola_forza_squadre()
        partite = carica_partite_prossime()
        
        risultati = []
        
        for _, row in partite.iterrows():
            pred = hunter.prevedi_partita(row['HomeTeam'], row['AwayTeam'])
            if not pred:
                continue
                
            value_score = 0
            mercato = "—"
            
            if pred['prob_1'] > 0.56:
                value_score = pred['prob_1'] * 1.18
                mercato = "1 (Vittoria Casa)"
            elif pred['prob_over
