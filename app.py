import pandas as pd
import streamlit as st
from utils.config import sport_icon
from utils.config import ATHLETES
#from utils.fonctions import *
from utils import fonctions as f


data_file = "data/races5.parquet"

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    return pd.read_parquet(data_file)

df_all_parquet = load_data()

tab1,tab2, tab3, tab4 = st.tabs(["Tab1", "Tab2","Tab3", "Settings ⚙️"])
########################## ########################## ########################## ########################## ########################## 
with tab1:
    st.write(df_all_parquet.head())
    
########################## ########################## ########################## ########################## ########################## 
with tab2:
    st.header("👤 Fiche Identité Coureur")

    # 0) Barre de recherche
    # On peut proposer une liste déroulante avec recherche intégrée pour éviter les fautes de frappe
    all_athletes = sorted(df_all_parquet["name_key"].unique())
    nom_recherche = st.selectbox("Rechercher un coureur :", options=all_athletes, index=None, placeholder="Tapez le nom d'un athlète...")

    #df_filtered = f.Filter_By_Athlete(df_all_parquet,nom_recherche)
    #st.write(df_filtered['race_name'].unique())

    if nom_recherche:
        df_coureur = f.Filter_By_Athlete(df_all_parquet, [nom_recherche])
        nb_courses_coureur = df_coureur["race_id"].nunique()

        # Affichage de la "Fiche"
        with st.container(border=True):
            col_icon, col_txt = st.columns([1, 4])
            
            with col_icon:
                st.write("# 🏃‍♂️") # Icone de profil
            
            with col_txt:
                st.title(nom_recherche)
                st.metric(label="Nombre total de courses", value=nb_courses_coureur)

            st.divider()

            # Optionnel : Afficher les sports pratiqués par ce coureur
            st.write("**Sports pratiqués :**")
            sports_du_coureur = df_coureur["sport"].unique()
            
            # On utilise ta fonction sport_icon pour chaque sport trouvé
            cols_sports = st.columns(len(sports_du_coureur))
            for i, sport in enumerate(sports_du_coureur):
                with cols_sports[i]:
                    st.write(f"{sport_icon(sport)} {sport}")

            # Optionnel : Afficher la liste de ses dernières courses
            st.write("**Historique récent :**")
            st.dataframe(
                df_coureur[["date", "race_name", "sport", "rank"]].sort_values("date", ascending=False).head(5),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Veuillez sélectionner ou taper un nom pour afficher les statistiques.")
########################## ########################## ########################## ########################## ########################## 
with tab3:
    st.subheader("Analyse comparative : Triathlon")

    liste_athletes = ["CHAPUIS Thomas", "BOMPAS Théo"]
    df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon")
    with st.container(border=True):
        st.write("📊 **Comparaison des performances (Radar)**")
        
        fig_radar = f.Viz_Radar_Triathlon(df_Tri, liste_athletes)          
        st.plotly_chart(fig_radar, use_container_width=True)

########################## ########################## ########################## ########################## ########################## 
with tab4:
    # 1) Affichage de la source de données tout en haut
    st.metric(label="Source des données", value=data_file)
    
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
########################## ########################## ########################## ########################## ########################## 
