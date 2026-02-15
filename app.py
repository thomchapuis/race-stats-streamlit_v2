import pandas as pd
import streamlit as st
from utils.config import sport_icon
from utils.config import ATHLETES
#from utils.fonctions import *
from utils import fonctions as f


st.set_page_config(layout="wide")

@st.cache_data
def load_data(file_path):
    return pd.read_parquet(file_path)

@st.cache_data
def load_synthese_data(file_path):
    df = pd.read_excel(file_path)
    return df

parquet_file = "data/races5.parquet"
synthese_file = "data/Synthese.xlsx"

df_all = load_data(parquet_file)
df_synthese = load_synthese_data(synthese_file)

df_all_parquet = pd.merge(
    df_all, 
    df_synthese[['Race', 'Distance']], 
    left_on='race_name', 
    right_on='Race', 
    how='left'
)

# ---------------------------------------------------------------------------------



tab1,tab2, tab3, tab4, tab5 = st.tabs(["Intro","Classement", "👤 Coureur","🚲Triathlon", "⚙️ Settings"])
########################## ########################## ########################## ########################## ########################## 
with tab1:
    st.write(df_synthese.head())
    #st.write(df_all_parquet.head())

    dist_par_sport = (
        df_all_parquet.drop_duplicates(subset=['race_name']) # On garde 1 ligne par course
        .groupby('sport')['Distance']                 # On groupe par sport
        .sum()                                        # On additionne
    )

    st.write(dist_par_sport)
    
########################## ########################## ########################## ########################## ########################## 
with tab2:
    #st.write(df_synthese.head())
    st.subheader("📊 Consulter un classement")

    all_races = sorted(df_all_parquet["race_name"].unique())
    race_recherche1 = st.selectbox("Rechercher une course :", options=all_races, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab2")

    if not race_recherche1:
        st.warning("Veuillez sélectionner une course pour afficher le classement.")
    else:
        df_Race = f.Filter_By_Race(df_all_parquet, race_recherche1)
        df_Race = df_Race.sort_values("rank")
    
        # 1) Affichage de l'histogramme
        fig_histo = f.Viz_Histogramme_Temps(df_Race, 'time')
        st.plotly_chart(fig_histo, use_container_width=True)
    
        # 2) Affichage du classement
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
with tab3:
    st.header("👤 Fiche Coureur")
    all_athletes = sorted(df_all_parquet["name_key"].unique())
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
            col_icon, col_content = st.columns([1, 5])
            
            with col_icon:
                # On peut agrandir l'icône avec du HTML si besoin, ou simplement :
                st.write("# 🏃‍♂️") 
            
            with col_content:
                # Le nom de l'athlète en haut
                st.title(nom_recherche)
                
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
                stats_cols = st.columns(len(courses_par_sport) + 1)
                
                # 1. La métrique TOTAL dans la première sous-colonne
                with stats_cols[0]:
                    st.metric(
                        label="🏁 Total", 
                        value=f"{nb_courses_coureur:,}".replace(",", " ")
                    )

                # 2. Les métriques par SPORT dans les colonnes suivantes
                for i, (sport, nb) in enumerate(courses_par_sport.items()):
                    with stats_cols[i + 1]:
                        distance = dist_par_sport.get(sport, 0)
                        label_with_icon = f"{sport_icon(sport)} {sport}"
                
                        if sport == "Triathlon":
                            st.metric(
                                label=label_with_icon,
                                value=f"#{nb}"
                            )
                        else:
                            st.metric(
                                label=label_with_icon,
                                value=f"#{nb} | {int(distance)}km"
                            )
            st.divider()

            # --- NOUVELLE SECTION : RECORDS ---
            st.subheader("💪🏼 Meilleures Performances")
            df_solo = df_coureur[(df_coureur["name_key"] == nom_recherche) & (df_coureur["rank"] > 0)]
            st.metric(df_solo.iloc[0, 18])
            longest_race = df_solo.loc[df_solo['Distance_x'].max()]
            st.metric(
                label="Plus longue course", 
                value=f"{int(longest_race['Distance_x'])}"
            )
            # Affichage du nom de la course et du sport
            st.caption(f"**Course :** {row_best['race_name']}")
            
            # --- NOUVELLE SECTION : RECORDS ---
            st.subheader("🏆 Records de classement")
            df_solo = df_coureur[(df_coureur["name_key"] == nom_recherche) & (df_coureur["rank"] > 0)]
            row_best = df_solo.loc[df_solo["rank"].idxmin()]
            row_worst = df_solo.loc[df_solo["rank"].idxmax()]
            participants_best = df_coureur[df_coureur["race_id"] == row_best["race_id"]]["rank"].max()
            participants_worst = df_coureur[df_coureur["race_id"] == row_worst["race_id"]]["rank"].max()
        
            col_best, col_worst = st.columns(2)
            
            with col_best:
                with st.container(border=True):
                    st.metric(
                        label="🥇 Meilleur Classement", 
                        value=f"{int(row_best['rank'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_best['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_best)}")
                    st.caption(f"**Sport :** {sport_icon(row_best['sport'])} {row_best['sport']}")
                
                with st.container(border=True):
                    df_race_best = f.Filter_By_Race(df_coureur,row_best['race_name'])
                    fig_histo_coureur_best = f.Viz_Histogramme_Temps_Names(df_race_best,'time',nom_recherche)
                    st.plotly_chart(fig_histo_coureur_best, width='stretch')

                
            with col_worst:
                with st.container(border=True):
                    st.metric(
                        label="🐢 Pire Classement", 
                        value=f"{int(row_worst['rank'])}e"
                    )
                    # Affichage du nom de la course et du sport
                    st.caption(f"**Course :** {row_worst['race_name']}")
                    st.caption(f"**Finishers :** {int(participants_worst)}")
                    st.caption(f"**Sport :** {sport_icon(row_worst['sport'])} {row_worst['sport']}")
                
                with st.container(border=True):
                    df_race_worst = f.Filter_By_Race(df_coureur,row_worst['race_name'])
                    fig_histo_coureur_worst = f.Viz_Histogramme_Temps_Names(df_race_worst,'time',nom_recherche)
                    st.plotly_chart(fig_histo_coureur_worst, width='stretch')
            
            with st.container(border=True):
                all_races = sorted(df_coureur["race_name"].unique())
                race_recherche2 = st.selectbox("Rechercher une course :", options=all_races, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab3_race")
            
                if not race_recherche2:
                    st.warning("Veuillez sélectionner une course pour afficher le classement.")
                else:
                    df_Race = f.Filter_By_Race(df_all_parquet, race_recherche2)
                    fig_histo_coureur = f.Viz_Histogramme_Temps_Names(df_Race,'time',nom_recherche)
                    st.plotly_chart(fig_histo_coureur, width='stretch')                    

    

    else:
        st.info("Veuillez sélectionner ou taper un nom pour afficher les statistiques.")
        
########################## ########################## ########################## ########################## ########################## 
with tab4:
    st.subheader("Analyse comparative : Triathlon")

    liste_athletes = ["CHAPUIS Thomas", "BOMPAS Théo"]
    df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon")
    with st.container(border=True):
        st.write("📊 **Comparaison des performances (Radar)**")
        
        fig_radar = f.Viz_Radar_Triathlon(df_Tri, liste_athletes)          
        st.plotly_chart(fig_radar, width='stretch')

########################## ########################## ########################## ########################## ########################## 
with tab5:
    # 1) Affichage de la source de données tout en haut
    st.metric(label="Source des données", value=parquet_file)
    
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
