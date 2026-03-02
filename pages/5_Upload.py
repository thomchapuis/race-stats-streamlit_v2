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



st.header("Importer une nouvelle course")
def interface_ajout_course():
    # Connexion à Supabase
    conn = st.connection("supabase", type=SupabaseConnection)

    # Création du formulaire
    with st.form("form_nouvelle_course", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            race_name = st.text_input("Nom de la course", placeholder="Ex: SaintéLyon")
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                race_date = st.date_input("Date de la course", datetime.now())
            with col1_2:
                ville = st.text_input("Ville")    
        
        with col2:   
            race_id = st.text_input("ID de la course (ex: 20240512_trail_lyon_21)", help="Identifiant unique")
            sport = st.selectbox("Sport", ["Running", "Trail", "Cycling", "Triathlon"])
            distance = 0
            format_tri = None
            
            col_Run, col_Deniv, col_Tri = st.columns(3)
            with col_Run:
                distance = st.number_input("Distance (km)", min_value=0, step=1, format=None,key="input_distance")
            with col_Deniv:
                denivele = st.number_input("Dénivelé Positif (D+ en m)", min_value=0, step=10)
            with col_Tri:
                format_tri = st.text_input("Format", placeholder="Ex: XS, S, M, L, XL",key="input_tri")

            denivele = st.number_input("Dénivelé Positif (D+ en m)", min_value=0, step=10)
        
        
        submit_button = st.form_submit_button("🚀 Enregistrer dans la base de données")

    if submit_button:
        if not race_id or not race_name:
            st.error("L'ID et le Nom de la course sont obligatoires.")
        else:
            # Préparation des données
            nouvelle_ligne = {
                "Race_id": race_id,
                "Race1": race_name,
                "date": str(race_date), # Format YYYY-MM-DD pour SQL
                "Année": race_date.year,
                "sport": sport,
                "Ville": ville,
                "Distance": str(distance),
                "Format": format_tri,
                "D+": denivele}

            try:
                # Utilisation de .upsert() pour mettre à jour si l'ID existe déjà, sinon insérer
                conn.table("synthese").upsert(nouvelle_ligne, on_conflict="Race_id").execute()
                st.success(f"✅ La course '{race_name}' a été ajoutée avec succès !")
                st.balloons()
                fig_Map_Ville = v.Viz_Map_Ville(ville)
                st.plotly_chart(fig_Map_Ville, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur lors de l'enregistrement : {e}")


    
# Appel de la fonction dans ton app
interface_ajout_course()




st.divider()
st.markdown("""
Pour ajouter un nouveau classement,  glisser un fichier **Excel (.xlsx)** ci-dessous. 
colonnes : name, bib, rank, time, category, sex.
""")

# Composant de chargement de fichier
#uploaded_file = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])
uploaded_file = st.file_uploader("Fichier classement", type=["xlsx"])


if uploaded_file:
    # Bouton pour lancer la conversion
    if st.button("Convertir et Enregistrer"):
        with st.spinner('Traitement en cours...'):
            #path, data = save_as_parquet(uploaded_file)
            #st.write(load_race(uploaded_file).head(3))
            #path, data = load_all_races(uploaded_file)
            success, data = save_to_database(uploaded_file)
            if success:
                st.success("✅ Données enregistrées avec succès dans Supabase !")
                
                # Petit aperçu des données importées
                st.write("### Aperçu des données envoyées :")
                st.dataframe(data.head())
                
                # Informations sur les colonnes et le volume
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Lignes importées", len(data))
                with col2:
                    st.metric("Colonnes traitées", len(data.columns))
                
                st.info(f"Course détectée : **{data['race_name'].iloc[0]}** ({data['race_distance'].iloc[0]})")
            else:
                st.error("L'importation a échoué. Vérifiez vos secrets Supabase ou le format du fichier.")
st.divider()

# Test de lecture brute
try:
    st.write("Vérification de la connexion subpabase (secrets) ...")
    st.write(f"URL configurée : {st.secrets['connections']['supabase']['SUPABASE_URL']}")
    # On affiche juste les 5 premiers caractères de la clé pour vérifier
    key_start = st.secrets['connections']['supabase']['SUPABASE_KEY'][:5]
    st.write(f"Début de la clé : {key_start}...")
except Exception as e:
    st.error(f"Erreur de lecture des secrets : {e}")

# Tentative de connexion
st.divider()
from st_supabase_connection import SupabaseConnection
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    st.success("✅ Connexion établie avec succès !")
except Exception as e:
    st.error(f"La connexion a échoué : {e}")
    
