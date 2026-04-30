import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

st.set_page_config(page_title="Value Hunter", page_icon="⚽", layout="centered")

st.title("⚽ Value Hunter Calcio")
st.write("Top Value Bets - Analisi semplice")

if st.button("🔄 Avvia Analisi", type="primary"):
    with st.spinner("Sto calcolando..."):
        # Dati di esempio
        partite = [
            ("Napoli", "Torino"), ("Inter", "Genoa"), ("Juventus", "Udinese"),
            ("Atalanta", "Cagliari"), ("Lazio", "Lecce"), ("Milan", "Como")
        ]
        
        risultati = []
        for home, away in partite:
            # Previsione semplice
            prob_casa = np.random.uniform(0.45, 0.68)
            prob_over = np.random.uniform(0.50, 0.65)
            
            score = 0
            mercato = ""
            if prob_casa > 0.57:
                score = prob_casa * 1.2
                mercato = "1 - Vittoria Casa"
            elif prob_over > 0.58:
                score = prob_over * 1.15
                mercato = "Over 2.5"
            
            if score > 0.6:
                risultati.append({
                    "Partita": f"{home} - {away}",
                    "Mercato": mercato,
                    "Probabilità": round(prob_casa*100 if "1" in mercato else prob_over*100, 1),
                    "Value Score": round(score, 2)
                })
        
        if risultati:
            df = pd.DataFrame(risultati).sort_values("Value Score", ascending=False)
            st.success(f"Trovate {len(df)} opportunità")
            st.dataframe(df, use_container_width=True)
        else:
            st.write("Nessuna opportunità trovata in questo momento.")

st.caption("Versione semplificata - Gioca responsabilmente")
