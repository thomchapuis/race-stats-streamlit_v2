import pandas as pd
import streamlit as st

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
    st.metric(
        label="Source des données",
        value=data_file
    )  
    
    nb_courses = df_all_parquet["race_id"].nunique() 
    st.subheader("Indicateurs clés")
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        st.metric(
            label="Source des données",
            value=data_file
        )     
    with col2:
        st.metric(
            label="🏁 Nombre de courses",
            value=f"{nb_courses:,}".replace(",", " ")
        )
    
    st.subheader("Sports représentés")
    courses_par_sport = (
        df_all_parquet
        .groupby("sport")["race_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    
    # Affichage en cartes (colonnes dynamiques)
    with st.container(border=True):
        cols = st.columns(len(courses_par_sport))
    
        for col, (sport, nb) in zip(cols, courses_par_sport.items()):
            with col:
                st.metric(
                    label=sport,
                    value=f"{nb:,}".replace(",", " "),
                )

########################## ########################## ########################## ########################## ########################## 
