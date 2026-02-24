import pandas as pd
import streamlit as st
import plotly.express as px
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

parquet_file7 = "data/races7.parquet"
parquet_file8 = "data/races8.parquet"

df_parquet7 = load_data(parquet_file7)
df_parquet8 = load_data(parquet_file8)


#synthese_file = "data/Synthese.xlsx"
#synthese_file = "data/Synthese2.xlsx"
#synthese_file = "data/Synthese_map.xlsx"
synthese_file = "data/Synthese3.xlsx"
df_synthese = load_synthese_data(synthese_file)

df_all = pd.concat([df_parquet7, df_parquet8], ignore_index=True, sort=False)

cols_to_add = ['Race_id','Race1', 'Distance', 'D+']

# 2. On fusionne (merge) sur les noms de courses
df_all_parquet = pd.merge(
    df_all,
    df_synthese[cols_to_add],
    left_on='race_id',
    right_on='Race_id',
    how='left'
)



#df_all_parquet["race_key"] = (df_all_parquet["race_name"].astype(str)+ " - " + df_all_parquet["race_date"].astype(str).str[:4]+ " - "+ df_all_parquet["Distance"].round().astype("Int64").astype(str)+ "km")
df_all_parquet["race_key"] = (df_all_parquet["race_name"].astype(str)+ " - " + df_all_parquet["race_date"].astype(str).str[:4]+ " - "+ df_all_parquet["Distance"].round().astype("Int64").astype(str)+ "km")
#df_all_parquet["race_key"] = (df_all_parquet["race_name"].astype(str)+ " - " + df_all_parquet["race_date"].astype(str).str[:4]+ " - "+ df_all_parquet["Distance"].astype(str)+ "km")

# ---------------------------------------------------------------------------------



tab1,tab2, tab3, tab4, tab5, tab6, tab7, tabGroup = st.tabs(["Intro","📊 Classement", "👤 Coureur","🚲Triathlon", "⚙️ Settings","Test", "⚔️ Battle", "Groupe"])
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
                fig_cat = f.Viz_Barre_Categorie(df_Race)
                st.plotly_chart(fig_cat, use_container_width=True)
        with col_Sex:
            col_Sex_Histo, col_Sex_PieChart = st.columns(2)   
            with col_Sex_Histo:
                    with st.container(border=True):
                        # 1) Affichage de l'histogramme
                        #fig_histo = f.Viz_Histogramme_Temps(df_Race, 'time')
                        fig_histo = f.Viz_Histogramme_Temps_Sex(df_Race, 'time', True)
                        st.plotly_chart(fig_histo, use_container_width=True)
            with col_Sex_PieChart:
                    with st.container(border=True):
                        #2) Affichage
                        fig_Sex = f.Viz_Sexes_PieChart(df_Race)
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
                st.title(df_coureur.loc[df_coureur['name_key'] == nom_recherche, 'name'].iloc[0])
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
                            textinfo="label",
                            #texttemplate="%{value} km",
                            hovertemplate="%{value} km")
                        fig.update_layout(
                            showlegend=False,
                            width=300,   # largeur en pixels
                            height=200   # hauteur en pixels,
                            margin=dict(l=0, r=0, t=0, b=0)  # réduire les marges pour mieux centrer
                        )
                        st.markdown(
                            f"<div style='display: flex; justify-content: center;'>{st.plotly_chart(fig, use_container_width=False)._repr_html_()}</div>",
                            unsafe_allow_html=True
                        )

            
            st.divider()
            st.markdown(df_coureur["race_id"].unique())
            st.divider()

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
                    fig_histo_coureur_best = f.Viz_Histogramme_Temps_Names(df_race_best,'time',nom_recherche)
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
                    fig_histo_coureur_worst = f.Viz_Histogramme_Temps_Names(df_race_worst,'time',nom_recherche)
                    st.plotly_chart(fig_histo_coureur_worst, width='stretch')

            with st.container(border=True):
                fig_Barre_RankPct = f.Viz_Barre_RankPct(df_coureur, nom_recherche)
                st.plotly_chart(fig_Barre_RankPct, width='stretch') 
            
            with st.container(border=True):
                all_races = sorted(df_coureur["race_name"].unique())
                race_recherche2 = st.selectbox("Rechercher une course :", options=all_races, index=None, placeholder="Tapez le nom d'une course...",key="selectbox_tab3_race")
            
                if not race_recherche2:
                    st.warning("Veuillez sélectionner une course pour afficher le classement.")
                else:
                    df_Race = f.Filter_By_Race(df_all_parquet, race_recherche2)
                    fig_histo_coureur = f.Viz_Histogramme_Temps_Names(df_Race,'time',nom_recherche)
                    st.plotly_chart(fig_histo_coureur, width='stretch')                    

            with st.container(border=True):
                nom_recherche_races = f.Filter_By_Athlete(df_all_parquet,nom_recherche)['race_id'].unique()
                mask = df_synthese['Race_id'].isin(nom_recherche_races)
                result = df_synthese.loc[mask].reset_index(drop=True)
                map_nom_recherche = f.Viz_Map(result)
                st.plotly_chart(map_nom_recherche, width='stretch')   


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
            fig_sex = f.Viz_Sexes(df_all_parquet)
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
    
    fig_Battle = f.Viz_Battle_percentage(df_Battle, targets)
    st.plotly_chart(fig_Battle, use_container_width=True)

########################## ########################## ########################## ########################## ########################## 

with tabGroup:
    st.title("⚔️ Vision de groupe")
    race_selected = "NuitBlanchePilat"
    df_race = f.Filter_By_Race(df_all_parquet, race_selected)
    st.markdown(ATHLETES)
    for name in ATHLETES:
        clean_name = f.get_clean_key(name)
        row = df_race.loc[df_race['name_key'] == clean_name]
        if not row.empty:
            st.markdown(
                f"""
                **{name}**
                - ⏱ Temps : `{row.iloc[0]['time']}`
                - 🏁 Classement : **{int(row.iloc[0]['rank'])}**
                """
            )
    
    fig_Group = f.Viz_Histogramme_Temps_Names_Horizontal(df_race, 'time', ATHLETES)
    st.plotly_chart(fig_Group,use_container_width=True)
