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
    #df_Tri = f.Filter_By_Race(df_Tri,["BayMan","Gerarmed"])

    all_athletes_raw = df_all_parquet["name_key"].unique()
    all_athletes_filtered = [
        name for name in all_athletes_raw
        if re.match(r'^[a-zA-Z]', str(name))
    ]
    all_athletes_filtered = sorted(all_athletes_filtered)
    coureur_cherche2 = st.selectbox("Rechercher un coureur :", options=all_athletes_filtered, index=None, placeholder="Tapez le nom d'un coureur...",key="tri_tab2_v1")
    if coureur_cherche2 :
        col_tri2_1,col_tri2_2 = st.columns(2)
        fig_radar_single, df_radar_single = v.Viz_Radar_Single_Athlete(df_Tri, coureur_cherche2)
        with col_tri2_1:
            st.dataframe(df_radar_single[['race_key','rank','time','swim','t1','bike','t2','run']],hide_index=True)
            st.dataframe(df_radar_single[[
                'race_key',
                'swim_rank',
                'swim_rank_pct',
                'bike_rank',
                'bike_rank_pct',
                'run_rank',
                'run_rank_pct'
            ]].rename(columns={
                'race_key':'course',
                'swim_rank_pct': 'Swim (%)',
                'bike_rank_pct': 'Bike (%)',
                'run_rank_pct': 'Run (%)',
                'swim_rank': 'Swim',
                'bike_rank': 'Bike',
                'run_rank': 'Run'
            }),hide_index=True)
        with col_tri2_2:
            st.plotly_chart(fig_radar_single, width='stretch', key='fig3')


        tri_sports = ['swim', 't1', 'bike', 't2', 'run']
        sport_cherche2 = st.selectbox("Choisisr un sport :", options=tri_sports, index=None, placeholder="Choisir un sport",key="tri_tab2_v2")

        #df_Tri = f.Filter_By_Race(df_Tri,"Yzeron")
        #fig_histo = v.Viz_Histogramme_Temps_Names(df_Tri,'bike',coureur_cherche2)
        #st.plotly_chart(fig_histo, width='stretch', key='fig4')
        if sport_cherche2 : 
            figures_histo = v.Viz_Histogrammes_Temps_Names_Triathlon(df_Tri, sport_cherche2, coureur_cherche2)
            # Supposons que figures_histo est votre liste de figures Plotly
            for i in range(0, len(figures_histo), 3):
                # Créer 3 colonnes par ligne
                cols = st.columns(3)

                # Remplir chaque colonne avec un graphique
                for j in range(3):
                    if i + j < len(figures_histo):
                        with cols[j]:
                            st.plotly_chart(figures_histo[i + j], use_container_width=True)
        else: 
            st.empty()
    else: 
        st.empty()