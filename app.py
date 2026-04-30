import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# Configurazione della pagina
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
        # Scarica le partite future
        url = "https://www.football-data.co.uk/fixtures.csv"
        df = pd.read_csv(url)
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        oggi = pd.Timestamp.today()
        prossime = df[df['Date'] >= oggi].copy()
        
        if len(prossime) == 0:
            st.warning("Non trovate partite future. Uso dati di esempio.")
            return crea_dati_esempio()
            
        prossime = prossime[['Date', 'Time', 'HomeTeam', 'AwayTeam', 'Div']].dropna()
        prossime['Date'] = prossime['Date'].dt.strftime('%d/%m/%Y')
        return prossime
    except:
        st.info("Impossibile scaricare i dati live. Uso partite di esempio.")
        return crea_dati_esempio()

def crea_dati_esempio():
    data = {
        'Date': ['02/05/2026']*10,
        'Time': ['15:00', '18:00', '20:45', '15:00', '18:00', '20:45', '15:00', '18:00', '20:45', '15:00'],
        'HomeTeam': ['Napoli', 'Inter', 'Juventus', 'Atalanta', 'Lazio', 'Milan', 'Roma', 'Bologna', 'Fiorentina', 'Torino'],
        'AwayTeam': ['Torino', 'Genoa', 'Udinese', 'Cagliari', 'Lecce', 'Como', 'Empoli', 'Pisa', 'Verona', 'Parma'],
        'Div': ['I1', 'I1', 'I
