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

st.dataframe(
    df_running[["Année", "Race1", "Distance", "D+", "Distance_Effort"]],
    column_config={
        "Distance": st.column_config.NumberColumn("Dist. (km)", format="%.1f"),
        "D+": st.column_config.NumberColumn("D+ (m)", format="%d"),
        "Distance_Effort": st.column_config.NumberColumn("Km-Effort", format="%.2f")
    },
    hide_index=True
)


df_athlete = f.Filter_By_Athlete(df_all_parquet,'Thomas CHAPUIS')
st.dataframe(df_athlete['race_name'].unique())
