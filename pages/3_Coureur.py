import pandas as pd
import numpy as np
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
st.header(f"👤 Stats par Personne ")

# Initialiser l'état de session dès le début
if "active_athlete" not in st.session_state:
    st.session_state.active_athlete = "Athlète 1"

all_athletes_raw = df_all_parquet["name_key"].unique()
all_athletes = [name for name in all_athletes_raw if isinstance(name, str)]
all_athletes = sorted(all_athletes)

#nom_recherche = st.selectbox(label="Recherche athlète",options=all_athletes, index=None, placeholder="Tapez le nom d'un athlète...",key="selectbox_tab3_name")
col_Athlete1, col_Empty1, col_Athlete2 = st.columns([12, 1, 12])

with col_Athlete1:
    nom_recherche1 = st.selectbox(
        label="Recherche athlète",
        options=all_athletes,
        index=None,
        placeholder="Tapez le nom d'un athlète...",
        key="selectbox_tab3_name1",
        label_visibility="collapsed"
    )

with col_Athlete2:
    nom_recherche2 = st.selectbox(
        label="Recherche athlète",
        options=all_athletes,
        index=None,
        placeholder="Tapez le nom d'un athlète...",
        key="selectbox_tab3_name2",
        label_visibility="collapsed"
    )

with col_Empty1:
    # Bouton pour basculer entre les deux athlètes

    # Création de l'interrupteur
    option_A = nom_recherche1
    option_B = nom_recherche2
    switch = st.toggle(" ")
    if switch:
        selection = option_B
        #st.write(f"Sélection: {selection}")
    else:
        selection = option_A
        #st.write(f"Sélection: {selection}")
        

nom_recherche = selection
if nom_recherche:
    st.write(f"**Athlète actif :** {df_all_parquet.loc[df_all_parquet['name_key'] == nom_recherche, 'name'].iloc[0]}")
    df_coureur = f.Filter_By_Athlete2(df_all_parquet, [nom_recherche], 'race_id')
    #nom_fiche = f" : {df_coureur.loc[df_coureur['name_key'] == nom_recherche, 'name'].iloc[0]}"
    #st.header(f"👤 Fiche Coureur {nom_fiche}")
    nb_courses_coureur = df_coureur["race_id"].nunique()
    courses_par_sport = (
        df_all_parquet
        .groupby("sport")["race_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    # Affichage de la "Fiche"
    with st.container(border=True):

        SPORTS_FIXES = ["Cycling", "Trail", "Running", "Triathlon"]
        stats_cols = st.columns(len(SPORTS_FIXES))
        #def Viz_Pie_Chart_Summary_Athlete():
        for i, sport in enumerate(SPORTS_FIXES):
            with stats_cols[i]:
                # Filtrage du sport
                df_sport = df_coureur[df_coureur["sport"] == sport].drop_duplicates(subset=["race_name"])
                
                # Calcul des métriques
                nb_courses = len(df_sport)
                distance_totale = df_sport["Distance"].sum() if nb_courses > 0 else 0
                
                # Affichage de la métrique
                label_with_icon = f"{sport_icon(sport)} {sport}"
                st.metric(
                    label=label_with_icon,
                    value=f"#{nb_courses} | {int(distance_totale)} km"
                )
                fig_key = f"empty_pie_chart_{sport}"
                # Logique du graphique
                if nb_courses > 0:
                    # Graphique normal
                    custom_colors = f.generate_gradient("#2ecc71", "#ffffff", 5)
                    fig = px.pie(
                        df_sport,
                        names="race_name",
                        values="Distance",
                        hole=0.4,
                        color_discrete_sequence=custom_colors
                    )
                    fig.update_traces(
                        textinfo="none",
                        hovertemplate="<b>%{label}</b><br>%{value} km<extra></extra>"
                    )
                else:
                    # Graphique "Grisé" (Données vides)
                    fig = px.pie(
                        values=[1], 
                        names=["Aucune donnée"], 
                        hole=0.4,
                        color_discrete_sequence=["#333333"] # Gris foncé
                    )
                    fig.update_traces(
                        textinfo="none",
                        hovertemplate="Aucune activité enregistrée<extra></extra>",
                        hoverinfo="label"
                    )

                # Mise en forme commune
                fig.update_layout(
                    showlegend=False,
                    width=200,
                    height=130,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)', # Fond transparent
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=fig_key)
        #return fig   
        
    #fig = Viz_Pie_Chart_Summary_Athlete()
    


        # --- NOUVELLE SECTION : RECORDS ---
        st.subheader("💪🏼 Meilleures Performances")
        df_coureur['Pourcentage'] = df_coureur.groupby('race_id')['rank'].transform(lambda x: (x / x.max()) * 100)
        df_solo = df_coureur[(df_coureur["name_key"] == nom_recherche) & (df_coureur["rank"] > 0)]
        sexe_coureur = df_coureur.loc[
            (df_coureur["name_key"] == nom_recherche) &
            (df_coureur["rank"] > 0),
            "sex"
        ].iloc[0]
        
        
        #st.dataframe(df_coureur)

        longest_race_row = df_solo.loc[df_solo['time'].idxmax()]
        td = longest_race_row['time']            
        hours = td.components.hours
        minutes = td.components.minutes
        seconds = td.components.seconds

        col_Duration, col_Dist, col_Empty1,col_Empty2 = st.columns(4)
        with col_Duration:
            with st.container(border=True):
                #st.metric(label="Plus longue course", value=f"{longest_race_row['time']}")
                #st.metric(label="Plus longue course", value=f"{hours:02d}h{minutes:02d}min{seconds:02d}sec") # Afficher au format HH:MM:SS
                st.metric(label="Plus longue course", value=f"{hours:02d}h{minutes:02d}min") # Afficher au format HH:MM
                st.caption(f"{sport_icon(longest_race_row['sport'])} {longest_race_row['race_key']}")
        with col_Dist:
            with st.container(border=True):
                df_noTri = f.Filter_By_Sport(df_coureur, ['Trail','Cycling','Running'])
                df_solo_noTri = df_noTri[(df_noTri["name_key"] == nom_recherche) & (df_noTri["rank"] > 0)]
                longest_distance_row = df_solo_noTri.loc[df_solo_noTri['Distance'].idxmax()]
                st.metric(label="Plus longue distance", value=f"{longest_distance_row['Distance']}km")
                st.caption(f"{sport_icon(longest_distance_row['sport'])} {longest_distance_row['race_key']}")
        with col_Empty1:
            st.empty()
        with col_Empty2:
            st.empty()

        
        # --- NOUVELLE SECTION : RECORDS ---
        st.subheader("🏆 Records de classement")
        #df_solo = df_coureur[(df_coureur["name_key"] == nom_recherche) & (df_coureur["rank"] > 0)]
        row_best = df_solo.loc[df_solo["rank"].idxmin()]
        row_worst = df_solo.loc[df_solo["rank"].idxmax()]
        participants_best = df_coureur[df_coureur["race_id"] == row_best["race_id"]]["rank"].max()
        #st.write(participants_best)
        participants_worst = df_coureur[df_coureur["race_id"] == row_worst["race_id"]]["rank"].max()

        best_rank_pourcentage= df_solo.loc[df_solo['Pourcentage'].idxmin()]
        #worst_rank_pourcentage= df_solo.loc[df_solo['Pourcentage'].idxmax()]
        participants_best_relatif = df_coureur[df_coureur["race_id"] == best_rank_pourcentage["race_id"]]["rank"].max()
        #participants_worst_relatif = df_coureur[df_coureur["race_id"] == worst_rank_pourcentage["race_id"]]["rank"].max()

        row_best_sex = df_solo.loc[df_solo["rank_sex"].idxmin()]
        participants_best_sex = df_coureur[
            (df_coureur["race_id"] == row_best_sex["race_id"]) &
            (df_coureur["sex"] == sexe_coureur)
        ]["rank_sex"].max()

        best_rank_pourcentage_sex= df_solo.loc[df_solo['Pourcentage'].idxmin()]
        participants_best_relatif_sex = df_coureur[df_coureur["race_id"] == best_rank_pourcentage_sex["race_id"]]["rank_sex"].max()

        #st.dataframe(df_coureur)

        col_best, col_sex = st.columns(2)
        
        with col_best:
            col_best_abs, col_best_relatif = st.columns(2)
            with col_best_abs:   
                with st.container(border=True):
                    st.metric(
                        label="🥇 Meilleur Classement absolu", 
                        value=f"{int(row_best['rank'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_best['race_key']}")
                    st.caption(f"**Finishers :** {int(participants_best)}")
                    #st.caption(f"**Sport :** {sport_icon(row_best['sport'])} {row_best['sport']}")

            with col_best_relatif:   
                with st.container(border=True):
                    st.metric(
                        label="🥇 Meilleur Classement relatif", 
                        value=f"Top {best_rank_pourcentage['Pourcentage']:.2f}%"
                    )
                                            
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {best_rank_pourcentage['race_key']}")
                    st.caption(f"**Finishers :** {int(participants_best_relatif)}")
                    #st.caption(f"**Sport :** {sport_icon(best_rank_pourcentage['sport'])} {best_rank_pourcentage['sport']}")
            
            with st.container(border=True):
                df_race_best = f.Filter_By_Race(df_coureur,row_best['race_name'])
                fig_histo_coureur_best = v.Viz_Histogramme_Temps_Names(df_race_best,'time',nom_recherche)
                st.plotly_chart(fig_histo_coureur_best, width='stretch')

            
        with col_sex:
            col_sex_abs, col_sex_relatif = st.columns(2)
            with col_sex_abs:  
                with st.container(border=True):
                    st.metric(
                        label="Meilleur Classement absolu - par sexe", 
                        value=f"{int(row_best_sex['rank_sex'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_best_sex['race_key']}")
                    st.caption(f"**Finishers ({sexe_coureur}):** {int(participants_best_sex)}")
                    #st.caption(f"**Sport :** {sport_icon(row_worst['sport'])} {row_worst['sport']}")
            
            with col_sex_relatif:   
                with st.container(border=True):
                    st.metric(
                        label="Meilleur Classement Relatif - par sexe", 
                        value=f"Top {best_rank_pourcentage_sex['Pourcentage']:.2f}%"
                    )
                                            
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {best_rank_pourcentage_sex['race_key']}")
                    st.caption(f"**Finishers ({sexe_coureur}):** {int(participants_best_relatif_sex)}")
                    #st.caption(f"**Sport :** {sport_icon(worst_rank_pourcentage['sport'])} {worst_rank_pourcentage['sport']}")
            
            with st.container(border=True):
                df_race_sex = f.Filter_By_Race(df_coureur,row_best_sex['race_name'])
                fig_histo_coureur_sex = v.Viz_Histogramme_Temps_Names(df_race_sex,'time',nom_recherche)
                st.plotly_chart(fig_histo_coureur_sex, width='stretch',key="histo_coureur_sex")

        with st.container(border=True):
            fig_Barre_RankPct = v.Viz_Barre_RankPct(df_coureur, nom_recherche)
            st.plotly_chart(fig_Barre_RankPct, width='stretch') 
        
        with st.container(border=True):
            all_races = sorted(df_coureur["race_name"].unique())
            race_recherche2 = st.selectbox("Rechercher une course :", options=all_races, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab3_race")
        
            if not race_recherche2:
                st.warning("Veuillez sélectionner une course pour afficher le classement.")
            else:
                df_Race = f.Filter_By_Race(df_all_parquet, race_recherche2)
                fig_histo_coureur = v.Viz_Histogramme_Temps_Names(df_Race,'time',nom_recherche)
                st.plotly_chart(fig_histo_coureur, width='stretch', key="histo_coureur")    

        with st.container(border=True):                    
                df_coureur['finishers'] = df_coureur.groupby(['race_id'])['rank'].transform('max').astype(int)
                df_coureur['rank %'] = df_coureur['rank']/df_coureur['finishers']
                
                df_coureur['rank sex'] = df_coureur.groupby(['race_id', 'sex'])['rank'].rank(method='min')
                df_coureur['finishers sex'] = df_coureur.groupby(['race_id',])['rank sex'].transform('max').astype(int)
                df_coureur['rank sex %'] = df_coureur['rank sex']/df_coureur['finishers sex']
                
                df_athlete_races = df_coureur[df_coureur['name_key'] == nom_recherche].copy()
                
                df_athlete_races['time'] = df_athlete_races['time'].apply(lambda x: str(x).split()[-1].split('.')[0])
                df_athlete_races['rank %'] = df_athlete_races['rank %'].map(lambda x: f"{x:.2%}")
                df_athlete_races['rank sex %'] = df_athlete_races['rank sex %'].map(lambda x: f"{x:.2%}")
                df_athlete_races['rank sex'] = df_athlete_races['rank sex'].astype('Int64')
                col = ['name','sex','time', 'rank','finishers', 'rank %', 'rank sex','finishers sex','rank sex %','race_key']
                
                st.write(df_athlete_races[col])

        with st.container(border=True):
            nom_recherche_races = f.Filter_By_Athlete(df_all_parquet,nom_recherche)['race_id'].unique()
            mask = df_synthese['Race_id'].isin(nom_recherche_races)
            result = df_synthese.loc[mask].reset_index(drop=True)
            map_nom_recherche = v.Viz_Map(result)
            st.plotly_chart(map_nom_recherche, width='stretch')   


else:
    st.info("Aucun Athlète sélectionné")

    
