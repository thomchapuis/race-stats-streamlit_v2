import pandas as pd
import numpy as np
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


from utils.config import *
#from utils.fonctions import *
from utils import fonctions_Filter as f
from utils import fonctions_Viz as v
#from utils.Upload_xlsx import *
from utils.Upload_xlsx_to_supabase import *
# ---------------------------------------------------------------------------------
#from utils.config import get_supabase #codespace
#supabase = get_supabase() #codespace

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
    df_all['rank_sex'] = 0  # Initialize with 0
    mask = df_all['rank'] > 0
    df_all.loc[mask, 'rank_sex'] = df_all.loc[mask].groupby(['sex', 'race_id'])['rank'].rank(method='first')

        
    # Merge et Traitement
    cols_to_add = ['Race_id','Race1', 'Distance', 'D+']
    df_merged = pd.merge(
        df_all, df_syn[cols_to_add],
        left_on='race_id', right_on='Race_id', how='left'
    )
    
    # Nettoyage
    df_merged["Distance"] = pd.to_numeric(df_merged["Distance"], errors='coerce')

    #debug
    # Afficher les types de données
    print("Types de données :")
    print(df_merged[["race_name", "race_date", "Distance"]].dtypes)

    # Afficher le nombre de valeurs manquantes
    print("\nValeurs manquantes :")
    print(df_merged[["race_name", "race_date", "Distance"]].isna().sum())

    # Afficher les premières lignes pour repérer les anomalies
    print("\nAperçu des données :")
    print(df_merged[["race_name", "race_date", "Distance"]].head(10))

    df_merged["race_key"] = (df_merged["race_name"].astype(str) + " - " + 
                             df_merged["race_date"].astype(str).str[:4] + " - " + 
                             df_merged["Distance"].round().fillna(0).astype("Int64").astype(str) + "km")
    df_merged['category_unisex'] = df_merged['category'].str.replace(r'[HF]$', '', regex=True)

    

    
    # Stockage
    st.session_state['df_complet'] = df_merged
    st.session_state['df_synthese'] = df_syn

# 3. Récupération pour l'usage local dans app.py
df_all_parquet = st.session_state['df_complet']
df_synthese = st.session_state['df_synthese']

# ---------------------------------------------------------------------------------



tab1,tab2, tab5, tab7, tabGroup,tabToDo = st.tabs(["Intro","📊 Classement", "⚙️ Settings", "⚔️ Battle", "Groupe","ToDo"])
########################## ########################## ########################## ########################## ########################## 
with tab1:
    st.header("📌 Introduction")
    st.markdown("Bienvenue dans l'application de suivi des Performances !")

    st.markdown(df_all_parquet.columns)
    st.markdown(df_all_parquet['race_id'].unique())
    st.markdown("---")
    
    st.markdown("load_supabase_data")
    df_db = load_supabase_data()
    st.markdown(df_db)
    st.caption("© 2026 - Application de suivi")

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
    
    df_all_parquet['category_unisex'] = df_all_parquet['category'].str.replace(r'[HF]$', '', regex=True)
    st.write(df_all_parquet['category_unisex'].unique())
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

    
    # --- 2. SECTION STATISTIQUES (COLONNES GAUCHE / DROITE) ---
    col_stats_left, col_stats_right = st.columns(2)
    with col_stats_left:
        st.empty()
    with col_stats_right:
        st.empty()
    st.divider()

    targets =  [athlete1,athlete2]
    df_Battle = f.Filter_By_Athlete2(df_all_parquet,targets,col='race_id', tolerance=False)
    
    if targets and not df_Battle.empty:

        fig_Battle = v.Viz_Battle_percentage(df_Battle, targets)
        st.plotly_chart(fig_Battle, use_container_width=True)


        st.divider()
        st.divider()

        #athletes = ["CHAPUIS Thomas", "BOMPAS Théo"]
        #df_TT = f.Filter_By_Athlete2(df_all_parquet,targets,col='race_id', tolerance=False)
        
        fig1 = v.Viz_Battle_Time_by_Races(df_Battle,targets)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
    
    else: 
        st.warning("🤝 Aucune course commune trouvée pour ces deux athlètes.")

    st.divider()

    targets =  ["CHAPUIS Thomas", "BOMPAS Théo"]
    df_Battle = f.Filter_By_Athlete2(df_all_parquet,targets,col='race_id', tolerance=False)
    races = df_Battle['race_name'].unique()
    rows = []
    for r in races:
        df_race = f.Filter_By_Race(df_Battle, r)
        for name in targets:
            t = df_race.loc[df_race['name_key'] == get_clean_key(name),'time']
            date = df_race.loc[df_race['name_key'] == get_clean_key(name),'race_date']

            if not t.empty:
                rows.append({
                    "athlete": name,
                    "race": r,
                    'race_date': date.iloc[0],
                    "time": t.iloc[0]
                })

    df_cumul = pd.DataFrame(rows)
    df_cumul = df_cumul.sort_values("race_date")  # si dispo
    df_cumul["time_sec"] = df_cumul["time"].dt.total_seconds()

    df_cumul["cumul_sec"] = (df_cumul.groupby("athlete")["time_sec"].cumsum())
    #st.dataframe(df_cumul)
    df_wide = df_cumul.copy()
    df_wide = (
        df_cumul
        .pivot(index=["race", "race_date"], columns="athlete", values="time_sec")
        .reset_index()
    )
    #st.dataframe(df_wide)
    df_wide["thomas_sec"] = df_wide["CHAPUIS Thomas"]
    df_wide["theo_sec"] = df_wide["BOMPAS Théo"]

    df_wide["delta_theo_sec"] = (
        df_wide["BOMPAS Théo"] - df_wide["CHAPUIS Thomas"]
    )
    df_wide = df_wide.sort_values("race_date")  # si dispo
    #st.dataframe(df_wide)
    df_wide["delta_cumul_sec"] = (df_wide["delta_theo_sec"].cumsum())
    #st.dataframe(df_wide)


    # 1. Préparation des formats texte pour les temps individuels
    def format_simple(seconds):
        s = abs(int(seconds))
        m = s // 60
        h = m // 60
        sec = s % 60
        min = m % 60
        if h > 0 :
            texte = f"{h}h{min}min"
        else:
            texte = f"{min}min{sec:02d}s"
        return texte

    df_wide["thomas_txt"] = df_wide["CHAPUIS Thomas"].apply(format_simple)
    df_wide["theo_txt"] = df_wide["BOMPAS Théo"].apply(format_simple)
    df_wide["delta_theo_txt"] = df_wide["delta_theo_sec"].apply(format_simple)
    df_wide["delta_cumul_txt"] = df_wide["delta_cumul_sec"].apply(format_simple)
    
    colors_conditions = ['#2ecc71' if val < 0 else '#e74c3c' for val in df_wide["delta_theo_sec"]]
    custom_data_list = list(zip(
        df_wide["thomas_txt"], # Utilise les colonnes formatées min/sec
        df_wide["theo_txt"], 
        df_wide["delta_theo_txt"],
        df_wide["delta_cumul_txt"]
    ))
    fig3 = go.Figure()

    # 1. Barre pour le delta de la course (Simple)
    fig3.add_trace(go.Bar(
        x=df_wide["race"],
        y=df_wide["delta_theo_sec"] / 60,
        name="Écart Course (min)",
        marker_color=colors_conditions,
        #marker_color="rgb(158,202,225)",
        customdata=custom_data_list,
        opacity=0.6,
        hovertemplate=(
            "Thomas : %{customdata[0]}<br>" +
            "Théo : %{customdata[1]}<br>" +
            "Écart : %{customdata[2]}</b>" +
            "<extra></extra>"
        ),
    ))

    # 2. Ligne pour le delta cumulé
    fig3.add_trace(go.Scatter(
        x=df_wide["race"],
        y=df_wide["delta_cumul_sec"] / 60,
        name="Écart Cumulé (min)",
        mode="lines+markers",
        line=dict(color="firebrick", width=3),
        customdata=custom_data_list,
        hovertemplate="<b>Écart Cumulé total : </b><br>%{customdata[3]}<extra></extra>"
    ))

    # Mise en forme
    fig3.update_layout(
        title="Analyse des écarts : Théo vs Thomas",
        xaxis_title=None,
        yaxis_title="Minutes",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        hovermode="x unified" # Permet de voir les deux valeurs en même temps au survol
    )

    # Optionnel : Ajouter une ligne horizontale à zéro pour voir qui est devant
    fig3.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)

    st.plotly_chart(fig3, use_container_width=True)
# --------------------------------------------------------------------------------------------------------------------------------------------

    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st

    def Viz_Athlete_Comparison_Delta(df_Battle, targets):
        """
        Génère un graphique comparatif des écarts entre deux athlètes.
        targets[0] est la référence, targets[1] est l'athlète comparé.
        """
        races = df_Battle['race_name'].unique()
        rows = []
        
        # On récupère les clés propres pour le filtrage
        key0 = get_clean_key(targets[0])
        key1 = get_clean_key(targets[1])

        for r in races:
            df_race = df_Battle[df_Battle['race_name'] == r]
            for name in targets:
                mask = df_race['name_key'] == get_clean_key(name)
                t = df_race.loc[mask, 'time']
                date = df_race.loc[mask, 'race_date']

                if not t.empty:
                    rows.append({
                        "athlete": name,
                        "race": r,
                        'race_date': date.iloc[0],
                        "time": t.iloc[0]
                    })

        if not rows:
            st.warning("Pas de données communes pour ces athlètes.")
            return None

        df_cumul = pd.DataFrame(rows)
        df_cumul = df_cumul.sort_values("race_date")
        df_cumul["time_sec"] = df_cumul["time"].dt.total_seconds()

        # Pivot dynamique basé sur les noms dans targets
        df_wide = (
            df_cumul
            .pivot(index=["race", "race_date"], columns="athlete", values="time_sec")
            .reset_index()
        )
        
        # Gestion des noms de colonnes dynamiques
        name0, name1 = targets[0], targets[1]
        
        # Calcul du delta (Athlète 2 - Athlète 1)
        df_wide["delta_sec"] = df_wide[name1] - df_wide[name0]
        df_wide = df_wide.sort_values("race_date")
        df_wide["delta_cumul_sec"] = df_wide["delta_sec"].cumsum()

        # Fonctions de formatage
        def format_raw(seconds):
            s = abs(int(seconds))
            h, m, sec = s // 3600, (s % 3600) // 60, s % 60
            return f"{h}h{m}min" if h > 0 else f"{m}min{sec:02d}s"

        def format_delta(seconds):
            signe = "+" if seconds > 0 else "-"
            s = abs(int(seconds))
            h, m, sec = s // 3600, (s % 3600) // 60, s % 60
            res = f"{h}h{m}min" if h > 0 else f"{m}min{sec:02d}s"
            return f"{signe}{res}"

        df_wide["t0_txt"] = df_wide[name0].apply(format_raw)
        df_wide["t1_txt"] = df_wide[name1].apply(format_raw)
        df_wide["delta_txt"] = df_wide["delta_sec"].apply(format_delta)
        df_wide["delta_cumul_txt"] = df_wide["delta_cumul_sec"].apply(format_delta)
        
        # Couleurs : Vert si targets[1] est plus rapide (delta négatif)
        colors = ['#2ecc71' if val < 0 else '#e74c3c' for val in df_wide["delta_sec"]]
        
        custom_data_list = list(zip(
            df_wide["t0_txt"], 
            df_wide["t1_txt"], 
            df_wide["delta_txt"],
            df_wide["delta_cumul_txt"]
        ))

        fig = go.Figure()

        # Barres : Delta par course
        fig.add_trace(go.Bar(
            x=df_wide["race"],
            y=df_wide["delta_sec"] / 60,
            name=f"Écart {name1}",
            marker_color=colors,
            customdata=custom_data_list,
            opacity=0.6,
            hovertemplate=(
                f"<b>{name0}</b> : %{{customdata[0]}}<br>" +
                f"<b>{name1}</b> : %{{customdata[1]}}<br>" +
                "Écart : %{customdata[2]}<extra></extra>"
            ),
        ))

        # Ligne : Delta cumulé
        fig.add_trace(go.Scatter(
            x=df_wide["race"],
            y=df_wide["delta_cumul_sec"] / 60,
            name="Cumul",
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
            customdata=custom_data_list,
            hovertemplate="<b>Écart Cumulé total :</b> %{customdata[3]}<extra></extra>"
        ))

        fig.update_layout(
            title=f"Duel : {name0} vs {name1}",
            yaxis_title="Minutes (Ecart)",
            template="plotly_dark",
            hovermode="x unified",
            showlegend=False
        )

        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)

        return fig
    
    
    targets =  [athlete1,athlete2]
    df_Battle = f.Filter_By_Athlete2(df_all_parquet,targets,col='race_id', tolerance=False)
    if targets and not df_Battle.empty:
        fig2 = Viz_Athlete_Comparison_Delta(df_Battle, targets)
        st.plotly_chart(fig2, use_container_width=True)
    else : 
        st.empty()


########################## ########################## ########################## ########################## ########################## 

with tabGroup:
    st.title("⚔️ Vision de groupe")
    
    col_sel1, col_sel2 = st.columns(2)
    
    # 1. Sélection du Groupe
    with col_sel1:
        groupe_choice = st.selectbox(
            "Choisissez un groupe :", 
            options=list(options_map.keys()), 
            index=None, 
            placeholder="Tapez le nom d'un groupe...",
            key="selectbox_tabGroup_group"
        )

    if not groupe_choice:
        st.info("Veuillez sélectionner un groupe pour afficher les statistiques.")
        st.stop() # On arrête l'exécution ici si pas de groupe

    # --- Préparation des données du groupe ---
    groupe_selectionne = options_map[groupe_choice]
    groupe_selectionne_clean = [get_clean_key(a) for a in groupe_selectionne]
    
    with col_sel1:
        st.write(f"**Membres :** {', '.join(groupe_selectionne)}")

    # 2. Sélection de la Course
    # On filtre les courses dispo pour ce groupe spécifique
    df_filtered_athletes = f.Filter_By_Athlete2(df_all_parquet, groupe_selectionne)
    all_races_v1 = sorted(df_filtered_athletes["race_name"].unique())

    with col_sel2:
        race_selected = st.selectbox(
            "Rechercher une course :", 
            options=all_races_v1, 
            index=None, 
            placeholder="Tapez le nom d'une course...",
            key="selectbox_tabGroup_race"
        )

    if not race_selected:
        st.info("Veuillez sélectionner une course.")
        st.stop()

    # --- Logique d'affichage une fois tout sélectionné ---
    df_race = f.Filter_By_Race(df_all_parquet, race_selected)
    
    # Aperçu tableau (Optionnel : tu peux le mettre dans une st.expander)
    st.markdown("###### Aperçu des performances du groupe")
    df_display = df_race[df_race['name_key'].isin(groupe_selectionne_clean)].copy()
    
    if not df_display.empty:
        # Formatage du temps
        df_display["time"] = df_display["time"].apply(
            lambda x: f"{int(x.total_seconds() // 3600):02d}:{int((x.total_seconds() % 3600) // 60):02d}:{int(x.total_seconds() % 60):02d}"
            if pd.notnull(x) else "-"
        )
        st.dataframe(df_display[["rank", "name", "time"]], use_container_width=True, hide_index=True)

    # --- Affichage des graphiques par race_key ---
    st.divider()
    grouped = df_race.groupby('race_key')
    n_cols = len(grouped)

    if n_cols > 0:
        # On limite à 3 colonnes max pour la lisibilité, sinon on crée des lignes
        cols = st.columns(n_cols)
        for i, (race_key, df_id) in enumerate(grouped):
            with cols[i]:
                st.markdown(f"**{race_key}**")
                fig_Group = v.Viz_Histogramme_Temps_Names_Horizontal(df_id, 'time', groupe_selectionne)
                st.plotly_chart(fig_Group, use_container_width=True)
    else:
        st.warning("Aucune donnée détaillée disponible pour les segments de cette course.")

########################## ########################## ########################## ########################## ########################## 

with tabToDo: 
    with st.container(border=True):
        st.write("tab import de course via fichier")
    with st.container(border=True):
        st.write("ajouter un warning pour les homonymes")
    with st.container(border=True):
        st.write("ajouter de quoi remplir le fichier synthese")
        st.write("calcul de latitude liongitude dans le upload synthèse")
        st.write("ajout d'un champ date d'import ?")
    with st.container(border=True):
        st.write("imports : (i) Yzeron les temps sont en minutes, pas en heure. (ii) Annecy pb avec des NaN dans les catégories ? ajouter unknow en plus de M et F ")
    

        
