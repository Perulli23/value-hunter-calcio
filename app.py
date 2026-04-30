import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

st.set_page_config(page_title="Value Hunter", page_icon="⚽", layout="wide")

st.title("⚽ Global Football Value Hunter")
st.markdown("**Top 30 Value Bets** - Analisi statistica sul calcio")

HOME_ADVANTAGE = 1.18
TOP_N = 30

@st.cache_data
def crea_dati_esempio():
    data = {
        'Date': ['02/05/2026'] * 12,
        'Time': ['15:00','18:00','20:45'] * 4,
        'HomeTeam': ['Napoli','Inter','Juventus','Atalanta','Lazio','Milan','Roma','Bologna','Fiorentina','Torino','Como','Empoli'],
        'AwayTeam': ['Torino','Genoa','Udinese','Cagliari','Lecce','Verona','Parma','Pisa','Sassuolo','Cremonese','Modena','Bari'],
        'Div': ['I1'] * 12
    }
    return pd.DataFrame(data)

class ValueHunter:
    def __init__(self):
        self.attack = {}
        self.defense = {}

    def calcola_forza(self):
        squadre = ['Napoli','Inter','Juventus','Atalanta','Lazio','Milan','Roma','Bologna',
                   'Fiorentina','Torino','Como','Empoli','Genoa','Udinese','Cagliari']
        for s in squadre:
            self.attack[s] = np.random.uniform(0.9, 1.9)
            self.defense[s] = np.random.uniform(0.8, 1.8)

    def prevedi(self, home, away):
        lambda_home = self.attack.get(home, 1.4) * self.defense.get(away, 1.3) * HOME_ADVANTAGE
        lambda_away = self.attack.get(away, 1.3) * self.defense.get(home, 1.4) * 0.9

        p1 = p_over = pbtts = 0.0
        for h in range(9):
            for a in range(9):
                prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                if h > a:
                    p1 += prob
                if h + a > 2.5:
                    p_over += prob
                if h > 0 and a > 0:
                    pbtts += prob

        return {
            'prob_1': round(p1, 4),
            'prob_over25': round(p_over, 4),
            'prob_btts': round(pbtts, 4),
            'expected_goals': round(lambda_home + lambda_away, 2)
        }

# ====================== APP ======================
hunter = ValueHunter()

if st.button("🔄 Analizza le Prossime Partite", type="primary", use_container_width=True):
    with st.spinner("Calcolo in corso..."):
        hunter.calcola_forza()
        df = crea_dati_esempio()
        
        risultati = []
        
        for _, row in df.iterrows():
            pred = hunter.prevedi(row['HomeTeam'], row['AwayTeam'])
            if not pred:
                continue
                
            value_score = 0
            mercato = "—"
            
            if pred['prob_1'] > 0.56:
                value_score = pred['prob_1'] * 1.18
                mercato = "1 (Vittoria Casa)"
            elif pred['prob_over25'] > 0.57:
                value_score = pred['prob_over25'] * 1.15
                mercato = "Over 2.5"
            elif pred['prob_btts'] > 0.60:
                value_score = pred['prob_btts'] * 1.10
                mercato = "BTTS"
            
            if value_score > 0.55:
                risultati.append({
                    "Partita": f"{row['HomeTeam']} - {row['AwayTeam']}",
                    "Data": f"{row['Date']} ore {row['Time']}",
                    "Gol Attesi": pred['expected_goals'],
                    "Mercato": mercato,
                    "Probabilità (%)": round(max(pred['prob_1'], pred['prob_over25'], pred['prob_btts']) * 100, 1),
                    "Value Score": round(value_score, 3)
                })
        
        if risultati:
            df_top = pd.DataFrame(risultati).sort_values("Value Score", ascending=False).head(TOP_N)
            st.success(f"✅ Trovate {len(df_top)} opportunità")
            st.dataframe(df_top, use_container_width=True, height=700)
        else:
            st.warning("Nessuna value bet trovata.")

st.caption("⚠️ Strumento per studio e analisi. Gioca responsabilmente solo su operatori ADM.")
