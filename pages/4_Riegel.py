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


st.write("tab import de course via fichier")
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

# 2. Création du graphique
fig = px.scatter(
    df_synthese_filtered,
    x="Distance_Effort",
    y="allure_str",
    #log_x=True,  # Activation de l'échelle logarithmique sur l'axe X
    #text="Race1", # Affiche le nom de la course au survol
    title="Performance : Temps vs Distance",
    labels={"allure_str": "Allure (min/km)", "Distance_Effort": "Distance-Effort (km)"},
    template="plotly_dark" # Fond noir natif
)

# 3. Personnalisation des couleurs et du style
fig.update_traces(
    marker=dict(
        size=12, 
        color='#ADFF2F', # Le "Vert Sportif" (GreenYellow)
        line=dict(width=2, color='white')
    ),
    textposition='top center'
)

# Ajustement du fond et de la grille
fig.update_layout(
    plot_bgcolor='black',
    paper_bgcolor='black',
    font_color='#ADFF2F',
    xaxis=dict(showgrid=True, gridcolor='#333333'),
    yaxis=dict(showgrid=True, gridcolor='#333333')
)

# 4. Affichage dans Streamlit
st.plotly_chart(fig, use_container_width=True)
