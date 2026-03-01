import pandas as pd
import os
import unicodedata
import streamlit as st
from st_supabase_connection import SupabaseConnection

# --- TES FONCTIONS DE PARSING (Inchangées ou presque) ---

def parse_race_key(race_key: str):
    # Gestion d'erreur si le format du nom de fichier est mauvais
    parts = race_key.split("_")
    if len(parts) < 4:
        st.error(f"Le nom du fichier '{race_key}' doit suivre le format : AAAAMMJJ_SPORT_NOM_DISTANCE")
        return None
    
    date_str, sport, *name_parts, race_distance = parts
    race_date = pd.to_datetime(date_str, format="%Y%m%d").date() # .date() pour SQL
    race_name = " ".join(name_parts)
    return race_key, race_name, sport, race_date, race_distance

def get_clean_key(text):
    if not isinstance(text, str) or text == "": return ""
    text = "".join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    text = text.lower().replace('-', ' ').replace(',', ' ')
    parts = text.split()
    parts.sort()
    return "".join(parts)

# --- FONCTION DE CHARGEMENT ET ENVOI ---

def save_to_database(file):
    """
    Lit le fichier, le nettoie et l'envoie vers Supabase
    """
    # 1. Connexion à Supabase
    conn = st.connection("supabase", type=SupabaseConnection)
    
    # 2. Chargement initial via ta fonction load_race
    df = load_race(file)
    
    # 3. Récupération des infos du fichier
    filename_base = os.path.splitext(file.name)[0]
    race_info = parse_race_key(filename_base)
    
    if race_info is None:
        return None, None
        
    race_id, race_name, sport, race_date, race_distance = race_info

    # 4. Ajout des métadonnées de course au DataFrame
    df["race_id"] = race_id
    df["race_name"] = race_name
    df["sport"] = sport
    df["race_date"] = str(race_date) # Conversion en string pour JSON
    df["race_distance"] = race_distance
    
    # 5. Création de la name_key pour chaque athlète
    if "name" in df.columns:
        df["name_key"] = df["name"].apply(get_clean_key)

    # 6. Préparation pour SQL (Conversion des Timedelta en String HH:MM:SS)
    # Supabase/Postgres accepte le format string pour les colonnes 'interval'
    time_cols = ["time", "swim", "bike", "t1", "t2", "run"]
    for col in time_cols:
        if col in df.columns:
            # On convertit les Timedelta en chaînes de caractères lisibles par SQL
            df[col] = df[col].apply(lambda x: str(x).split()[-1] if pd.notnull(x) else None)

    # 7. Envoi vers Supabase
    try:
        # On convertit le DF en liste de dictionnaires
        records = df.to_dict(orient="records")
        
        # Insertion par lots (bulk insert)
        conn.table("resultats_courses").insert(records).execute()
        
        st.success(f"✅ {len(df)} lignes insérées dans la base de données !")
        return True, df
    
    except Exception as e:
        st.error(f"Erreur Supabase : {e}")
        return False, None

# --- DANS TON APP STREAMLIT ---
uploaded_file = st.file_uploader("Fichier classement", type=["xlsx"])
if uploaded_file:
    if st.button("🚀 Importer dans la base permanente"):
        success, data = save_to_database(uploaded_file)
