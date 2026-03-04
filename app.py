import pandas as pd
import os
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
# ---------------------------------------------------------------------------------


st.set_page_config(layout="wide")
parquet_file7 = "data/races7.parquet"
parquet_file8 = "data/races8.parquet"

# 1. Définition des fonctions de cache (si pas déjà dans utils)
@st.cache_data
def load_all_initial_data():
    df7 = pd.read_parquet(parquet_file7)
    df8 = pd.read_parquet(parquet_file8)
    df_db = load_supabase_data()
    df_syn = load_supabase_synthese()
    return df7, df8, df_db, df_syn

# 2. Logique de Session State
if 'df_complet' not in st.session_state:
    # Chargement
    df_p7, df_p8, df_db, df_syn = load_all_initial_data()
    
    # Concaténation
    df_all = pd.concat([df_p7, df_p8, df_db], ignore_index=True, sort=False)
    
    # Merge et Traitement
    cols_to_add = ['Race_id','Race1', 'Distance', 'D+']
    df_merged = pd.merge(
        df_all, df_syn[cols_to_add],
        left_on='race_id', right_on='Race_id', how='left'
    )
    
    # Nettoyage
    df_merged["Distance"] = pd.to_numeric(df_merged["Distance"], errors='coerce')
    df_merged["race_key"] = (df_merged["race_name"].astype(str) + " - " + 
                             df_merged["race_date"].astype(str).str[:4] + " - " + 
                             df_merged["Distance"].round().fillna(0).astype("Int64").astype(str) + "km")
    
    # Stockage
    st.session_state['df_complet'] = df_merged
    st.session_state['df_synthese'] = df_syn

# 3. Récupération pour l'usage local dans app.py
df_all_parquet = st.session_state['df_complet']
df_synthese = st.session_state['df_synthese']

# ---------------------------------------------------------------------------------



tab1,tab2, tab4, tab5, tab6, tab7, tabGroup,tabToDo = st.tabs(["Intro","📊 Classement","🚲Triathlon", "⚙️ Settings","Test", "⚔️ Battle", "Groupe","ToDo"])
########################## ########################## ########################## ########################## ########################## 
with tab1:
    st.header("📌 Introduction")
    st.markdown("Bienvenue dans l'application de suivi des Performances !")

    st.markdown(df_all_parquet.columns)
    st.markdown("---")
    st.caption("© 2026 - Application de suivi")

########################## ########################## ########################## ########################## ########################## 
with tab6:
    st.write(df_synthese)
    #st.write(df_all_parquet.head())
    st.write(
        df_all_parquet[["Race1", "race_name", "race_key", "Distance"]]
        .drop_duplicates(subset="race_key")
    )

    dist_par_sport = (
        df_all_parquet.drop_duplicates(subset=['race_name']) # On garde 1 ligne par course
        .groupby('sport')['Distance']                 # On groupe par sport
        .sum()                                        # On additionne
    )

    st.write(dist_par_sport)

    # Test
    #lat, lon = f.get_coords("Lyon, France")
    #st.write(f"Lat: {lat}, Lon: {lon}")
    
########################## ########################## ########################## ########################## ########################## 
with tab2:
    #st.write(df_synthese.head())
    st.subheader("📊 Consulter un classement")

    all_races_v1 = sorted(df_all_parquet["race_name"].unique())
    race_recherche_v1 = st.selectbox("Rechercher une course :", options=all_races_v1, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab2_v1")

    all_races_v2 = sorted(df_all_parquet["race_key"].unique())
    race_recherche_v2 = st.selectbox("Rechercher une course :", options=all_races_v2, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab2_v2")

    if not race_recherche_v2:
        st.warning("Veuillez sélectionner une course pour afficher le classement.")
    
    else: 
        st.write(int(df_all_parquet.loc[df_all_parquet["race_key"] == race_recherche_v2, "race_date"].astype(str).str[:4].iloc[0]))
        st.write(int(df_all_parquet.loc[df_all_parquet["race_key"] == race_recherche_v2, "Distance"].iloc[0]))

    
    if not race_recherche_v1:
        st.warning("Veuillez sélectionner une course pour afficher le classement.")
    else:
        df_Race = f.Filter_By_Race_v2(df_all_parquet, race_recherche_v1)
        df_Race = df_Race.sort_values("rank")

        col_Category, col_Sex = st.columns(2)
        with col_Category:
            with st.container(border=True):
                #st.write("📊 Histogramme des catégories à venir")
                fig_cat = v.Viz_Barre_Categorie(df_Race)
                st.plotly_chart(fig_cat, use_container_width=True)
        with col_Sex:
            col_Sex_Histo, col_Sex_PieChart = st.columns(2)   
            with col_Sex_Histo:
                    with st.container(border=True):
                        # 1) Affichage de l'histogramme
                        #fig_histo = v.Viz_Histogramme_Temps(df_Race, 'time')
                        fig_histo = v.Viz_Histogramme_Temps_Sex(df_Race, 'time', True)
                        st.plotly_chart(fig_histo, use_container_width=True)
            with col_Sex_PieChart:
                    with st.container(border=True):
                        #2) Affichage
                        fig_Sex = v.Viz_Sexes_PieChart(df_Race)
                        st.plotly_chart(fig_Sex, use_container_width=True)
        
        # 3) Affichage du classement
        st.write("Classement complet")
        df_display = df_Race[["rank", "name", "time", "category", "sex"]].copy()
        df_display["time"] = df_display["time"].apply(
            lambda x: f"{int(x.total_seconds() // 3600):02d}:{int((x.total_seconds() % 3600) // 60):02d}:{int(x.total_seconds() % 60):02d}"
            if pd.notnull(x) else "-"
        )
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
########################## ########################## ########################## ########################## ########################## 
########################## ########################## ########################## ########################## ########################## 
with tab4:
    st.subheader("Analyse comparative : Triathlon")

    liste_athletes = ["CHAPUIS Thomas", "BOMPAS Théo"]
    df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon")
    with st.container(border=True):
        st.write("📊 **Comparaison des performances (Radar)**")
        
        fig_radar = v.Viz_Radar_Triathlon(df_Tri, liste_athletes)          
        st.plotly_chart(fig_radar, width='stretch')

########################## ########################## ########################## ########################## ########################## 
with tab5:
    # 1) Affichage de la source de données tout en haut
    st.metric(label="Source des données 1", value=parquet_file7)
    st.metric(label="Source des données2", value=parquet_file8)

    
    # Préparation des données
    nb_courses = df_all_parquet["race_id"].nunique()
    courses_par_sport = (
        df_all_parquet
        .groupby("sport")["race_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    st.subheader("Nombre de courses enregistrées")
    
    # 2) Un seul gros container pour le total et le détail par sport
    with st.container(border=True):
        # On crée autant de colonnes que (Total + nombre de sports)
        # Le premier chiffre de la liste définit la largeur relative
        cols = st.columns(len(courses_par_sport) + 1)
        
        with cols[0]:
            st.metric(
                label="🏁 Total", 
                value=f"{nb_courses:,}".replace(",", " ")
            )

        for col, (sport, nb) in zip(cols[1:], courses_par_sport.items()):
            with col:
                label_with_icon = f"{sport_icon(sport)} {sport}"
                st.metric(
                    label=label_with_icon,
                    value=f"{nb:,}".replace(",", " ")
                )
        with st.container(border=True):
            fig_sex = v.Viz_Sexes(df_all_parquet)
            st.plotly_chart(fig_sex, use_container_width=True)
            
########################## ########################## ########################## ########################## ########################## 

with tab7:
    st.title("⚔️ Battle : Duel de Performance")
    
    # --- 1. BARRE DE SÉLECTION (SIDEBAR OU TOP) ---
    # On récupère la liste des athlètes pour les menus déroulants
    all_athletes = sorted(df_all_parquet['name_key'].unique())
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        athlete1 = st.selectbox("Sélectionner le premier coureur", all_athletes, index=None,placeholder="Tapez le nom d'un athlète...",key="selectbox_Battle_name1")
    
    with col_sel2:
        athlete2 = st.selectbox("Sélectionner le second coureur", all_athletes, index=None,placeholder="Tapez le nom d'un athlète...",key="selectbox_Battle_name2")
    
    st.divider()
    
    # --- 2. SECTION STATISTIQUES (COLONNES GAUCHE / DROITE) ---
    col_stats_left, col_stats_right = st.columns(2)

    st.divider()

    targets =  [athlete1,athlete2]
    df_Battle = f.Filter_By_Athlete(df_all_parquet,targets)
    
    fig_Battle = v.Viz_Battle_percentage(df_Battle, targets)
    st.plotly_chart(fig_Battle, use_container_width=True)

########################## ########################## ########################## ########################## ########################## 

with tabGroup:
    st.title("⚔️ Vision de groupe")
    #race_selected = "NuitBlanchePilat"
    ATHLETES_CLEAN = [get_clean_key(a) for a in ATHLETES]
    
    all_races_v1 = sorted(df_all_parquet["race_name"].unique())
    race_selected = st.selectbox("Rechercher une course :", options=all_races_v1, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tabGroup")

    if race_selected:
        df_race = f.Filter_By_Race(df_all_parquet, race_selected)
        
    
        col_Group1, col_Group2 = st.columns(2)
        with col_Group1:
            st.dataframe(df_race)
            st.dataframe(df_race[df_race['name_key'].isin(ATHLETES_CLEAN)])
            
        with col_Group2:
            fig_Group = v.Viz_Histogramme_Temps_Names_Horizontal(df_race, 'time', ATHLETES)
            st.plotly_chart(fig_Group,use_container_width=True)
    else:
        st.info("Veuillez sélectionner ou taper un nom pour afficher les statistiques.")
        nom_fiche = ""
########################## ########################## ########################## ########################## ########################## 

with tabToDo: 
    with st.container(border=True):
        st.write("tab import de course via fichier")
    with st.container(border=True):
        st.write("ajouter un warning pour les homonymes")
    with st.container(border=True):
        st.write("ajouter de quoi remplir le fichier synthese")
    

        
