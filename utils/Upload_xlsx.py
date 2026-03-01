import pandas as pd
import os

def parse_race_key(race_key: str):
    date_str, sport, *name_parts, race_distance = race_key.split("_")
    race_date = pd.to_datetime(date_str, format="%Y%m%d")
    race_name = " ".join(name_parts)
    return race_key, race_name, sport, race_date, race_distance

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


def load_all_races(file):
    dfs = []
    df = load_race(file)
    filename_base = os.path.splitext(file.name)[0]
    
    race_id, race_name, sport, race_date, race_distance = parse_race_key(filename_base)

    df["race_id"] = race_id
    df["race_name"] = race_name
    df["sport"] = sport
    df["race_date"] = race_date
    df["race_distance"] = race_date
    
    #dfs.append(df)
    #dfs = pd.concat(dfs, ignore_index=True)
    
    save_path = os.path.join('data', f"{filename_base}.parquet")
    # Conversion et sauvegarde
    df.to_parquet(save_path, index=False)
    
    return save_path, df


def get_clean_key(text):
    if not isinstance(text, str): return ""
    # 1. Suppression des accents
    text = "".join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    # 2. Minuscules et suppression de la ponctuation de base (tirets, virgules)
    text = text.lower().replace('-', ' ').replace(',', ' ')
    # 3. Tri des mots (pour l'ordre Nom Prénom)
    parts = text.split()
    parts.sort()
    return "".join(parts) # On colle tout pour une comparaison stricte
