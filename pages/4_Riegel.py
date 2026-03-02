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

# Vérifier si les données existent (sécurité si l'utilisateur arrive direct sur cette page)
if 'df_complet' in st.session_state:
    df_all_parquet = st.session_state['df_complet']
    df_synthese = st.session_state['df_synthese']
    
else:
    st.warning("⚠️ Veuillez passer par la page d'accueil pour initialiser les données.")
    if st.button("Aller à l'accueil"):
        st.switch_page("app.py") # Redirige l'utilisateur

# ------------------------------------------------------------------------------------------------------------------

df_running = df_synthese[df_synthese['sport'].isin(['Running', 'Trail'])].copy()

df_running["Distance"] = pd.to_numeric(df_running["Distance"], errors='coerce')
df_running["D+"] = pd.to_numeric(df_running["D+"], errors='coerce').fillna(0)

df_running["Distance_Effort"] = df_running["Distance"] + (df_running["D+"] / 100)


nom_cherche = "chapuisthomas" 
df_athlete = f.Filter_By_Athlete(df_all_parquet,'Thomas CHAPUIS')

races = df_athlete['race_id'].unique()
df_synthese_filtered = df_running[df_running['Race_id'].isin(races)].copy()
df_perf_thomas = df_athlete[df_athlete['name_key'] == nom_cherche][['race_id', 'time']]
df_perf_thomas = df_perf_thomas.drop_duplicates(subset=['race_id'])

df_synthese_filtered = pd.merge(
    df_synthese_filtered,
    df_perf_thomas,
    left_on='Race_id', 
    right_on='race_id',
    how='left'
)

if 'race_id' in df_synthese_filtered.columns:
    df_synthese_filtered = df_synthese_filtered.drop(columns=['race_id'])



# 1. Conversion du temps en minutes (ou heures) pour l'axe Y
# On suppose que 'time' est au format HH:MM:SS
df_synthese_filtered['time_min'] = pd.to_timedelta(df_synthese_filtered['time']).dt.total_seconds() / 60
df_synthese_filtered['allure'] = df_synthese_filtered['time_min'] / df_synthese_filtered['Distance_Effort']

def format_allure(min_decimal):
    if pd.isna(min_decimal):
        return ""
    minutes = int(min_decimal)
    secondes = int((min_decimal - minutes) * 60)
    return f"{minutes}:{secondes:02d}"

df_synthese_filtered['allure_str'] = df_synthese_filtered['allure'].apply(format_allure)
df_synthese_filtered = df_synthese_filtered.sort_values('allure')

# --- 2. Configuration des paliers de l'axe Y (toutes les 30s ou 1min) ---
# On crée des graduations mathématiques pour l'axe Y
min_val = df_synthese_filtered['allure'].min()
max_val = df_synthese_filtered['allure'].max()
# On crée des paliers de 0.5 (30 secondes) pour l'échelle
tick_vals = np.arange(np.floor(min_allure), np.ceil(max_allure) + 0.5, 0.5)
tick_text = [format_allure(v) for v in tick_vals]

# --- 3. Création du graphique ---
fig = px.scatter(
    df_synthese_filtered,
    x="Distance_Effort",
    y="allure", # On utilise la valeur numérique pour le placement
    log_x=True, # Recommandé pour la cohérence des distances trail/ultra
    title="Performance : Allure Effort vs Distance Effort",
    # On ajoute Race1 et allure_str dans les données personnalisées pour le hover
    custom_data=["Race1", "allure_str"], 
    template="plotly_dark"
)

# --- 4. Personnalisation du Hover et des Points ---
fig.update_traces(
    marker=dict(
        size=14, 
        color='#ADFF2F', # Vert Sportif
        line=dict(width=1, color='white'),
        opacity=0.8
    ),
    # Configuration du Hover : on affiche Race1 et l'allure formatée
    hovertemplate="<b>%{customdata[0]}</b><br>" +
                  "Distance Effort: %{x:.1f} km<br>" +
                  "Allure Effort: %{customdata[1]} min/km<extra></extra>"
)

# --- 5. Ajustement des axes et du design ---
fig.update_layout(
    plot_bgcolor='black',
    paper_bgcolor='black',
    font_color='#ADFF2F',
    xaxis=dict(
        title="Distance-Effort (km) - Échelle Log",
        showgrid=True, 
        gridcolor='#333333',
        tickvals=[5, 10, 20, 42, 80, 160] # Repères familiers
    ),
    yaxis=dict(
        title="Allure (min/km)",
        showgrid=True, 
        gridcolor='#333333',
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        autorange="reversed" # Plus rapide (ex: 4:00) en haut
    )
)

st.plotly_chart(fig, use_container_width=True)
