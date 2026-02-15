import pandas as pd
import streamlit as st
from utils.config import sport_icon
#from utils.fonctions import *
from utils import fonctions as f


data_file = "data/races5.parquet"

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    return pd.read_parquet(data_file)

df_all_parquet = load_data()

tab1,tab2, tab3 = st.tabs(["Tab1", "Tab2", "Settings ⚙️"])
########################## ########################## ########################## ########################## ########################## 
with tab1:
    st.write(df_all_parquet.head())
########################## ########################## ########################## ########################## ########################## 
with tab2:
    st.subheader("Analyse comparative : Triathlon")

    liste_athletes = ["CHAPUIS Thomas", "BOMPAS Théo"]
    df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon")
    with st.container(border=True):
        st.write("📊 **Comparaison des performances (Radar)**")
        
        # Appel de ta fonction de visualisation
        # Assure-toi que Viz_Radar_Triathlon utilise st.plotly_chart ou st.pyplot en interne
        Viz_Radar_Triathlon(df_TT, liste_athletes)

########################## ########################## ########################## ########################## ########################## 
with tab3:
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
