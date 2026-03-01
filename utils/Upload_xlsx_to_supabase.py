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


TIME_COLUMNS = [
    "chip time",
    "chip result",
    "time",
    "temps",
    "tempstotal_h",
]

COLUMN_ALIASES = {
    "chip time": "time",
    "chip result": "time",
    "temps": "time",
    "tempstotal_h": "time",
    "dossard": "bib",
    "doss.": "bib",
    "dos": "bib",
    "sexe": "sex",
    "gender": "sex",
    "classement": "rank",
    "categorie": "category",
    "catégorie": "category",
    "cat": "category",
    "cat.": "category",
}


def load_race(file):
    df = pd.read_excel(file)
    # --- normalisation des noms de colonnes ---
    df.columns = (df.columns.str.lower().str.strip())

    # --- mapping intelligent des colonnes ---
    rename_map = {}
    for col in df.columns:
        if col in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col]
        elif col in TIME_COLUMNS:
            rename_map[col] = "time"

    df = df.rename(columns=rename_map)

    # --- schéma cible ---
    expected_cols = [ "name", "bib", "sex", "time", "category", "club", "rank", "swim", "t1", "bike", "t2", "run"]

    df = df[[c for c in expected_cols if c in df.columns]].copy()

    # --- nettoyages ---
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()

    if "bib" in df.columns:
        df["bib"] = pd.to_numeric(df["bib"], errors="coerce")
        df["bib"] = df["bib"].fillna(0).astype(int)

    if "rank" in df.columns:
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
        df["rank"] = df["rank"].fillna(0).astype(int)

    if "sex" in df.columns:
      df["sex"] = df["sex"].replace(["MALE", "Homme", "M"], "H")
      df["sex"] = df["sex"].replace(["FEMALE", "Femme"], "F")

    time_columns = ["time", "swim", "bike", "T1", "T2", "run"]

    for col in time_columns:
        if col in df.columns:
            # Nettoyage et conversion en une seule étape
            df[col] = pd.to_timedelta(
                df[col].astype(str).str.strip().replace({"nan": None, "": None}),
                errors="coerce"
        )
    # --- normalisation des autres colonnes ---
    for col in ["name", "sex", "category", "club"]:
      if col in df.columns:
          df[col] = (
              df[col]
              .astype("string")
              .str.strip()
          )

    return df


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



# Remplacement de ta commande :
def load_supabase_data():
    # .select("*") récupère toutes les colonnes
    # .execute() lance la requête
    response = conn.table("resultats_courses").select("*").execute()
    
    # On transforme le résultat en DataFrame Pandas
    return pd.DataFrame(response.data)

# Utilisation :
df_sport = load_supabase_data()

