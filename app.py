import pandas as pd
import streamlit as st
from utils import sport_icon

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
    st.write(df_all_parquet.head())
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
    st.subheader("Indicateurs clés")
    
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
