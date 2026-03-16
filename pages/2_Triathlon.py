import pandas as pd
import numpy as np
import os
import re
import streamlit as st
import plotly.express as px
from datetime import datetime

from utils.config import sport_icon
from utils.config import ATHLETES
#from utils.fonctions import *
from utils import fonctions_Filter as f
from utils import fonctions_Viz as v
#from utils.Upload_xlsx import *
from utils.Upload_xlsx_to_supabase import *

# ------------------------------------------------------------------------------------------------------------------

# Vérifier si les données existent (sécurité si l'utilisateur arrive direct sur cette page)
if 'df_complet' in st.session_state:
    df_all_parquet = st.session_state['df_complet']
    df_synthese = st.session_state['df_synthese']
    
    #st.success("Données chargées depuis la session !")
    # Ton code Riegel ici...
    
else:
    st.warning("⚠️ Veuillez passer par la page d'accueil pour initialiser les données.")
    if st.button("Aller à l'accueil"):
        st.switch_page("app.py") # Redirige l'utilisateur

# ------------------------------------------------------------------------------------------------------------------

tab1,tab2 = st.tabs(["Triathlon1","Triathlon 2"])
df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon")

with tab1:
    st.subheader("Analyse comparative : Triathlon")

    liste_athletes = ["chapuisthomas", "bompastheo", "bompasromain"]
    all_athletes_raw = df_all_parquet["name_key"].unique()
    all_athletes_filtered = [
        name for name in all_athletes_raw
        if re.match(r'^[a-zA-Z]', str(name))
    ]
    all_athletes_filtered = sorted(all_athletes_filtered)
    
    nouveaux_coureurs = st.multiselect(
        "Sélectionnez les coureurs à ajouter :",
        options=all_athletes_filtered,
        default=liste_athletes  # Optionnel : pré-sélectionner les coureurs déjà dans la liste
    )

    # Bouton pour valider l'ajout
    if st.button("Ajouter les coureurs sélectionnés"):
        liste_athletes = list(set(liste_athletes + nouveaux_coureurs))  # Évite les doublons
        #st.success(f"Nouvelle liste : {liste_athletes}")
        # Ici, tu peux aussi sauvegarder la liste mise à jour si nécessaire

    
    with st.container(border=True):
        #st.write("📊 **Comparaison des performances (Radar)**")
        
        fig_radar = v.Viz_Radar_Triathlon(df_Tri, liste_athletes)          
        st.plotly_chart(fig_radar, width='stretch', key='fig1')

    with st.container(border=True):
        #st.write("📊 **Comparaison des performances (Radar)**")
        fig_radar2 = v.Viz_Radar_Triathlon2(df_Tri, liste_athletes, mode='rank_pct')          
        st.plotly_chart(fig_radar2, width='stretch', key='fig2')


with tab2:
    df_Tri = f.Filter_By_Race(df_Tri,["Gerarmed"])
    fig_radar_single = v.Viz_Radar_Single_Athlete(df_Tri, "chapuisthomas")
    st.plotly_chart(fig_radar_single, width='stretch', key='fig3')