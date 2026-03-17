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


#st.write(df_synthese.head())
st.subheader("📊 Consulter un classement")

#all_races_v1 = sorted(df_all_parquet["race_name"].unique())
#race_recherche_v1 = st.selectbox("Rechercher une course :", options=all_races_v1, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab2_v1")

all_races_v2 = sorted(df_all_parquet["race_key"].unique())
race_recherche_v2 = st.selectbox("Rechercher une course :", options=all_races_v2, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab2_v2")



if not race_recherche_v2:
    st.warning("Veuillez sélectionner une course pour afficher le classement.")

else:
    race_recherche_v1 = df_all_parquet[df_all_parquet["race_key"]==race_recherche_v2]['race_name'].iloc[0]
    race_recherche_v1_distance = df_all_parquet[df_all_parquet["race_key"]==race_recherche_v2]['Distance'].iloc[0]
    df_Race = f.Filter_By_Race_v2(df_all_parquet, race_recherche_v1, distance=race_recherche_v1_distance)
    df_Race = df_Race.sort_values("rank")

    distance = int(df_Race['Distance'].loc[0])
    course = df_Race['race_name'].loc[0]
    d_plus = int(df_Race['D+'].loc[0]) if pd.notna(df_Race['D+'].loc[0]) else None
    race_date = df_Race['race_date'].loc[0]
    sport = df_Race['sport'].loc[0]
    participants = df_Race['name'].count()
    DNF = df_Race[df_Race['rank'] == 0].shape[0]
    formatted_date = race_date.strftime("%b. %Y")  # Ex: "Aug 2020"
    formatted_distance_dplus = f"{distance} km - {d_plus} m D+"


    # État du toggle (par défaut, le container est masqué)
    with st.container(border=True):
        show_details = st.checkbox("Afficher/Masquer les détails de la course", value=False)

    if show_details:
        
        with st.container(border=True):
            st.markdown(course)    


            with st.container(border=True):
                col1, col2, col3 = st.columns(3)

                # --- Colonne 1 : Infos sur la course ---
                with col1:

                    with st.container(border=True):
                        st.markdown(
                            """
                            <div style='display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem;'>
                                <span style='font-size: 20px;'>📅</span>
                                <div>
                                    <p style='margin: 0; color: #bdc3c7; font-size: 14px;'>Date</p>
                                    <p style='margin: 0; font-size: 18px; font-weight: bold; color: #ecf0f1;'>{}</p>
                                </div>
                            </div>
                            """.format(formatted_date),
                            unsafe_allow_html=True
                        )

                # --- Colonne 2 : Infos sur le sport et la distance ---
                with col2:
                    with st.container(border=True):
                        st.markdown(
                            """
                            <div style='display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem;'>
                                <span style='font-size: 20px;'>🚴‍♂️</span>
                                <div>
                                    <p style='margin: 0; color: #bdc3c7; font-size: 14px;'>Sport</p>
                                    <p style='margin: 0; font-size: 18px; font-weight: bold; color: #ecf0f1;'>{}</p>
                                </div>
                            </div>
                            """.format(sport),
                            unsafe_allow_html=True
                        )
                with col3:
                    with st.container(border=True):
                        st.markdown(
                            """
                            <div style='display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem;'>
                                <span style='font-size: 20px;'>📏</span>
                                <div>
                                    <p style='margin: 0; color: #bdc3c7; font-size: 14px;'>Distance/Dénivelé</p>
                                    <p style='margin: 0; font-size: 18px; font-weight: bold; color: #ecf0f1;'>{}</p>
                                </div>
                            </div>
                            """.format(formatted_distance_dplus),
                            unsafe_allow_html=True
                        )

            # --- Ligne du bas : Participants et DNF ---
            st.markdown("<hr style='border: 0; border-top: 1px solid #34495e; margin: 0.5rem 0;'>", unsafe_allow_html=True)

            col3, col4 = st.columns(2)
            with col3:
                st.markdown(
                    f"""
                    <div style='text-align: center; padding: 0.5rem;'>
                        <p style='margin: 0; color: #bdc3c7; font-size: 14px;'>Participants</p>
                        <p style='margin: 0; font-size: 24px; font-weight: bold; color: #2ecc71;'>{participants}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col4:
                st.markdown(
                    f"""
                    <div style='text-align: center; padding: 0.5rem;'>
                        <p style='margin: 0; color: #bdc3c7; font-size: 14px;'>Abandons (DNF)</p>
                        <p style='margin: 0; font-size: 24px; font-weight: bold; color: #e74c3c;'>{DNF}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )




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
    df_display = df_Race[["rank", "name", "time", "category", "sex", "rank_sex"]].copy()
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