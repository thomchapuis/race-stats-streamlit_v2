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

# ------------------------------------------------------------------------------------------------------------------

if 'df_complet' in st.session_state:
    df_all_parquet = st.session_state['df_complet']
    #st.write(f"Données prêtes : {len(df_all_parquet)} lignes chargées.")
else:
    st.warning("Veuillez repasser par la page d'accueil pour charger les données.")

if 'df_synthese' in st.session_state:
    df_all_parquet = st.session_state['df_synthese']
    #st.write(f"Données prêtes : {len(df_all_parquet)} lignes chargées.")
else:
    st.warning("Veuillez repasser par la page d'accueil pour charger les données.")



# ------------------------------------------------------------------------------------------------------------------


all_athletes_raw = df_all_parquet["name_key"].unique()
all_athletes = [name for name in all_athletes_raw if isinstance(name, str)]
all_athletes = sorted(all_athletes)

#nom_recherche = st.selectbox(label="Recherche athlète",options=all_athletes, index=None, placeholder="Tapez le nom d'un athlète...",key="selectbox_tab3_name")
nom_recherche = st.selectbox(
    label="Recherche athlète",
    options=all_athletes, 
    index=None, 
    placeholder="Tapez le nom d'un athlète...",
    key="selectbox_tab3_name",
    label_visibility="collapsed" # Supprime l'espace et le texte au-dessus
)
if nom_recherche:
    df_coureur = f.Filter_By_Athlete(df_all_parquet, [nom_recherche])
    nom_fiche = f" : {df_coureur.loc[df_coureur['name_key'] == nom_recherche, 'name'].iloc[0]}"
    st.header(f"👤 Fiche Coureur {nom_fiche}")
    nb_courses_coureur = df_coureur["race_id"].nunique()
    courses_par_sport = (
        df_all_parquet
        .groupby("sport")["race_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    # Affichage de la "Fiche"
    with st.container(border=True):
        # On crée deux colonnes principales : une pour l'icône, une pour tout le texte/stats
        # Le nom de l'athlète en haut
        #st.title(df_coureur.loc[df_coureur['name_key'] == nom_recherche, 'name'].iloc[0])
        #st.title(nom_recherche)
        
        # Calcul des stats par sport pour CET athlète uniquement
        courses_par_sport = (
            df_coureur.groupby("sport")["race_id"]
            .nunique()
            .sort_values(ascending=False)
        )

        # Calcul de la distance totale par sport
        dist_par_sport = (
            df_coureur.drop_duplicates(subset=['race_name'])
            .groupby('sport')['Distance']
            .sum()
        )
        
        # Sous-conteneur pour les métriques alignées horizontalement
        # On crée (Nombre de sports + 1 pour le total) colonnes
        stats_cols = st.columns(len(courses_par_sport))
        
        # 1. La métrique TOTAL dans la première sous-colonne
        #with stats_cols[0]:
            #st.metric(label="🏁 Total", value=f"{nb_courses_coureur:,}".replace(",", " "))                      
            #courses_unique = df_coureur["race_key"].unique()
            #courses_md = "\n".join([f"- {c}" for c in courses_unique])
            #st.markdown(courses_md)


        # 2. Les métriques par SPORT dans les colonnes suivantes
        for i, (sport, nb) in enumerate(courses_par_sport.items()):
            with stats_cols[i]:
        
                # Sous-DF pour le sport courant
                df_sport = (
                    df_coureur[df_coureur["sport"] == sport]
                    .drop_duplicates(subset=["race_name"])
                )
        
                distance = df_sport["Distance"].sum()
        
                label_with_icon = f"{sport_icon(sport)} {sport}"
                st.metric(
                    label=label_with_icon,
                    value=f"#{nb} | {int(distance)} km"
                )
        
                # Pie chart : distances par course
                fig = px.pie(
                    df_sport,
                    names="race_name",
                    values="Distance",
                    hole=0.4)
                fig.update_traces(
                    textinfo="none",
                    #texttemplate="%{value} km",
                    hovertemplate="<b>%{label}</b><br>%{value} km<extra></extra>")
                fig.update_layout(
                    showlegend=False,
                    width=200,   # largeur en pixels
                    height=130,   # hauteur en pixels,
                    margin=dict(l=0, r=0, t=0, b=0)  # réduire les marges pour mieux centrer
                )
                st.plotly_chart(fig)



        # --- NOUVELLE SECTION : RECORDS ---
        st.subheader("💪🏼 Meilleures Performances")
        df_coureur['Pourcentage'] = df_coureur.groupby('race_id')['rank'].transform(lambda x: (x / x.max()) * 100)
        df_solo = df_coureur[(df_coureur["name_key"] == nom_recherche) & (df_coureur["rank"] > 0)]
        
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
                st.caption(f"**Sport :** {sport_icon(longest_race_row['sport'])} {longest_race_row['sport']}")
        with col_Dist:
            with st.container(border=True):
                df_noTri = f.Filter_By_Sport(df_coureur, ['Trail','Cycling','Running'])
                df_solo_noTri = df_noTri[(df_noTri["name_key"] == nom_recherche) & (df_noTri["rank"] > 0)]
                longest_distance_row = df_solo_noTri.loc[df_solo_noTri['Distance'].idxmax()]
                st.metric(label="Plus longue distance", value=f"{longest_distance_row['Distance']}km")
                st.caption(f"**Sport :** {sport_icon(longest_distance_row['sport'])} {longest_distance_row['sport']}")
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
        participants_worst = df_coureur[df_coureur["race_id"] == row_worst["race_id"]]["rank"].max()

        best_rank_pourcentage= df_solo.loc[df_solo['Pourcentage'].idxmin()]
        worst_rank_pourcentage= df_solo.loc[df_solo['Pourcentage'].idxmax()]
        participants_best_relatif = df_coureur[df_coureur["race_id"] == best_rank_pourcentage["race_id"]]["rank"].max()
        participants_worst_relatif = df_coureur[df_coureur["race_id"] == worst_rank_pourcentage["race_id"]]["rank"].max()
    
        col_best, col_worst = st.columns(2)
        
        with col_best:
            col_best_abs, col_best_relatif = st.columns(2)
            with col_best_abs:   
                with st.container(border=True):
                    st.metric(
                        label="🥇 Meilleur Classement absolu", 
                        value=f"{int(row_best['rank'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_best['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_best)}")
                    st.caption(f"**Sport :** {sport_icon(row_best['sport'])} {row_best['sport']}")

            with col_best_relatif:   
                with st.container(border=True):
                    st.metric(
                        label="🥇 Meilleur Classement relatif", 
                        value=f"Top {best_rank_pourcentage['Pourcentage']:.2f}%"
                    )
                                            
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {best_rank_pourcentage['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_best_relatif)}")
                    st.caption(f"**Sport :** {sport_icon(best_rank_pourcentage['sport'])} {best_rank_pourcentage['sport']}")
            
            with st.container(border=True):
                df_race_best = f.Filter_By_Race(df_coureur,row_best['race_name'])
                fig_histo_coureur_best = v.Viz_Histogramme_Temps_Names(df_race_best,'time',nom_recherche)
                st.plotly_chart(fig_histo_coureur_best, width='stretch')

            
        with col_worst:
            col_worst_abs, col_worst_relatif = st.columns(2)
            with col_worst_abs:  
                with st.container(border=True):
                    st.metric(
                        label="🐢 Pire Classement absolu", 
                        value=f"{int(row_worst['rank'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_worst['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_worst)}")
                    st.caption(f"**Sport :** {sport_icon(row_worst['sport'])} {row_worst['sport']}")
            
            with col_worst_relatif:   
                with st.container(border=True):
                    st.metric(
                        label="🐢 Pire Classement relatif", 
                        value=f"Top {worst_rank_pourcentage['Pourcentage']:.2f}%"
                    )
                                            
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {worst_rank_pourcentage['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_worst_relatif)}")
                    st.caption(f"**Sport :** {sport_icon(worst_rank_pourcentage['sport'])} {worst_rank_pourcentage['sport']}")
            
            with st.container(border=True):
                df_race_worst = f.Filter_By_Race(df_coureur,row_worst['race_name'])
                fig_histo_coureur_worst = v.Viz_Histogramme_Temps_Names(df_race_worst,'time',nom_recherche)
                st.plotly_chart(fig_histo_coureur_worst, width='stretch')

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
                st.plotly_chart(fig_histo_coureur, width='stretch')    

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
    st.info("Veuillez sélectionner ou taper un nom pour afficher les statistiques.")
    nom_fiche = ""
    st.header(f"👤 Fiche Coureur {nom_fiche}")

    
