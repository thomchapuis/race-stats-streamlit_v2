import pandas as pd
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

from utils.config import sport_icon
from utils.config import ATHLETES
#from utils.fonctions import *
from utils import fonctions_Filter as f
from utils import fonctions_Viz as v
#from utils.Upload_xlsx import *
from utils.Upload_xlsx_to_supabase import *


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------

# Vérifier si les données existent (sécurité si l'utilisateur arrive direct sur cette page)
if 'df_complet' in st.session_state:
    df_all_parquet = st.session_state['df_complet']
    df_synthese = st.session_state['df_synthese']
    
else:
    st.warning("⚠️ Veuillez passer par la page d'accueil pour initialiser les données.")
    if st.button("Aller à l'accueil"):
        st.switch_page("app.py") # Redirige l'utilisateur

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
all_athletes_raw = df_all_parquet["name_key"].unique()
all_athletes = [name for name in all_athletes_raw if isinstance(name, str)]
all_athletes = sorted(all_athletes)

#nom_recherche = st.selectbox(label="Recherche athlète",options=all_athletes, index=None, placeholder="Tapez le nom d'un athlète...",key="selectbox_tab3_name")
#nom_cherche = "chapuisthomas" 
nom_cherche = st.selectbox(
    label="Recherche athlète",
    options=all_athletes, 
    index=None, 
    placeholder="Tapez le nom d'un athlète...",
    key="selectbox_tab3_name",
    label_visibility="collapsed" # Supprime l'espace et le texte au-dessus
)

df_running = df_synthese[df_synthese['sport'].isin(['Running', 'Trail'])].copy()
df_running["Distance"] = pd.to_numeric(df_running["Distance"], errors='coerce')
df_running["D+"] = pd.to_numeric(df_running["D+"], errors='coerce').fillna(0)
df_running["Distance_Effort"] = df_running["Distance"] + (df_running["D+"] / 100)

# --- 0. Préparation (hors du if) ---
def format_allure(min_decimal):
    if pd.isna(min_decimal) or min_decimal == 0:
        return ""
    minutes = int(min_decimal)
    secondes = int((min_decimal - minutes) * 60)
    return f"{minutes}:{secondes:02d}"

cols_display = ['Année', 'Race1', 'Distance', 'D+', 'Distance_Effort', 'time', 'allure_str']

# --- 1. Initialisation des variables par défaut ---
df_plot = pd.DataFrame()
df_display = pd.DataFrame(columns=cols_display)
tick_vals, tick_text = [], []
chart_title = "Sélectionnez un athlète pour voir ses performances"

# --- 2. Logique de données ---
if nom_cherche:
    df_athlete = f.Filter_By_Athlete(df_all_parquet, [nom_cherche])
    
    if not df_athlete.empty:
        races = df_athlete['race_id'].unique()
        df_synthese_filtered = df_running[df_running['Race_id'].isin(races)].copy()
        
        # Performance spécifique
        df_perf_spec = df_athlete[df_athlete['name_key'] == nom_cherche][['race_id', 'time']]
        df_perf_spec = df_perf_spec.drop_duplicates(subset=['race_id'])
        
        df_plot = pd.merge(df_synthese_filtered, df_perf_spec, left_on='Race_id', right_on='race_id', how='left')
        
        if not df_plot.empty:
            # Calculs
            df_plot['time_min'] = pd.to_timedelta(df_plot['time']).dt.total_seconds() / 60
            df_plot['allure'] = df_plot['time_min'] / df_plot['Distance_Effort']
            df_plot['allure_str'] = df_plot['allure'].apply(format_allure)
            df_plot = df_plot.sort_values('allure')
            
            # Axes Y
            min_v, max_v = df_plot['allure'].min(), df_plot['allure'].max()
            tick_vals = np.arange(np.floor(min_v), np.ceil(max_v) + 0.5, 0.5)
            tick_text = [format_allure(v) for v in tick_vals]
            chart_title = f"Performance : {nom_cherche}"
            
            # Préparation tableau
            df_display = df_plot[cols_display].copy()
            df_display["time"] = df_display["time"].apply(
                lambda x: f"{int(x.total_seconds() // 3600):02d}:{int((x.total_seconds() % 3600) // 60):02d}:{int(x.total_seconds() % 60):02d}"
                if pd.notnull(x) else "-"
            )

# --- 3. Création du Graphique (Toujours affiché) ---
# Si df_plot est vide, Plotly affichera un graphe vide avec les axes configurés
fig = px.scatter(
    df_plot if not df_plot.empty else pd.DataFrame(columns=["Distance_Effort", "allure"]), 
    x="Distance_Effort", 
    y="allure",
    log_x=True,
    title=chart_title,
    template="plotly_dark",
    custom_data=["Race1", "allure_str"] if not df_plot.empty else None
)

fig.update_layout(
    #plot_bgcolor='black', paper_bgcolor='black', font_color='#ADFF2F',
    xaxis=dict(title="Distance-Effort (km)", gridcolor='#333333', tickvals=[5, 10, 20, 42, 80, 160]),
    yaxis=dict(
        title="Allure (min/km)", gridcolor='#333333', autorange="reversed",
        tickmode='array', tickvals=tick_vals, ticktext=tick_text
    )
)

if not df_plot.empty:
    fig.update_traces(
        marker=dict(size=14, color='#ADFF2F', line=dict(width=1, color='white')),
        hovertemplate="<b>%{customdata[0]}</b><br>Dist: %{x:.1f} km<br>Allure: %{customdata[1]}<extra></extra>"
    )

# Affichage des composants
st.plotly_chart(fig, use_container_width=True)

st.write("### Détails des courses")
st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={"allure_str": "Allure (min/km)", "Distance_Effort": "Dist. Effort"}
)


############## 2e graphe — Modèle de Riegel

############## 2e graphe — Modèle de Riegel

if not df_plot.empty:

    df_riegel = df_plot.copy()

    # Nettoyage critique
    df_riegel = df_riegel.dropna(subset=["Distance_Effort", "time_min"])
    df_riegel = df_riegel[df_riegel["Distance_Effort"] > 0]
    df_riegel = df_riegel[df_riegel["time_min"] > 0]

    if df_riegel.empty:
        st.warning("Pas assez de données valides pour le modèle Riegel.")
    else:

        distances_reelles = df_riegel["Distance_Effort"].astype(float)
        temps_reels_min = df_riegel["time_min"].astype(float)

if not df_plot.empty:

    # 1. Données propres (on repart de df_plot, plus sûr)
    distances_reelles = df_plot["Distance_Effort"].astype(float)
    temps_reels_min = df_plot["time_min"].astype(float)

    # --- Fonctions format ---
    def format_time(min_val):
        if pd.isna(min_val):
            return ""
        total_seconds = int(min_val * 60)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def format_pace(pace_min):
        if pd.isna(pace_min):
            return ""
        m = int(pace_min)
        s = int(round((pace_min - m) * 60))
        if s == 60:
            m += 1
            s = 0
        return f"{m}:{s:02d}"

    # 2. Figure
    fig2 = go.Figure()
    colors = px.colors.qualitative.Plotly
    dist_range = np.linspace(2, 50, 200)

    # 3. Courbes Riegel
    for i, (dist_ref, t_ref_min) in enumerate(zip(distances_reelles, temps_reels_min)):

        temps_estimes_min = t_ref_min * ((dist_range / dist_ref) ** 1.06)
        allure_estimee = temps_estimes_min / dist_range

        hover_text = [
            f"Temps: {format_time(t)}<br>Allure: {format_pace(p)} min/km"
            for t, p in zip(temps_estimes_min, allure_estimee)
        ]

        fig2.add_trace(go.Scatter(
            x=dist_range,
            y=allure_estimee,
            mode='lines',
            name=f"Réf {dist_ref:.1f} km",
            line=dict(dash='dash', width=1.5, color=colors[i % len(colors)]),
            opacity=0.5,
            text=hover_text,
            hovertemplate='<b>Projection</b><br>Dist: %{x:.1f} km<br>%{text}<extra></extra>'
        ))

    # 4. Points réels
    allures_reelles = temps_reels_min / distances_reelles

    hover_reels = [
        f"Temps: {format_time(t)}<br>Allure: {format_pace(p)} min/km"
        for t, p in zip(temps_reels_min, allures_reelles)
    ]

    fig2.add_trace(go.Scatter(
        x=distances_reelles,
        y=allures_reelles,
        mode='markers+text',
        name='Réel',
        text=[format_pace(p) for p in allures_reelles],
        textposition="top center",
        marker=dict(size=12, line=dict(width=2, color='white')),
        customdata=hover_reels,
        hovertemplate='<b>Réel</b><br>Dist: %{x:.1f} km<br>%{customdata}<extra></extra>'
    ))

    # 5. Axes
    min_pace = allures_reelles.min()
    max_pace = allures_reelles.max()

    pace_ticks = np.arange(np.floor(min_pace), np.ceil(max_pace) + 0.5, 0.5)
    pace_labels = [format_pace(p) for p in pace_ticks]

    fig2.update_layout(
        title="Évolution de l'Allure (min/km) — Modèle de Riegel",
        template="plotly_dark",
        # xaxis pour limite ler graphe à 40km.
        xaxis=dict(title="Distance (km)", showgrid=False,range=[0, 40]),
        yaxis=dict(
            title="Allure (min/km)",
            tickvals=pace_ticks,
            ticktext=pace_labels,
            autorange="reversed",
            gridcolor="rgba(255,255,255,0.1)"
        ),
        hovermode="closest"
    )

    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("💡 Sélectionnez un athlète pour afficher les projections Riegel.")


if not nom_cherche:
    st.info("💡 Utilisez la barre de recherche pour peupler le graphique et le tableau.")
