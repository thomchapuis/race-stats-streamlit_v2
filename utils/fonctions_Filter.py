import pandas as pd
import unicodedata
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import numpy as np
from geopy.geocoders import Nominatim


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 🔹 Fonction de Filtre
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def Filter_By_Year(df, year):
    """
    Filtre le DataFrame pour une ou plusieurs années données.
    'year' peut être un entier (2024) ou une liste [2022, 2023].
    """
    #Extraction de l'année et filtrage
    if isinstance(year, list):
        # Si on passe une liste d'années
        mask = df['race_date'].dt.year.isin(year)
    else:
        # Si on passe une seule année
        mask = df['race_date'].dt.year == year

    return df[mask].reset_index(drop=True)

def Filter_By_Sport(df, sport):
    """
    Filtre le DataFrame pour un ou plusieurs sports.
    'sport' peut être un string "Trail" ou une liste ["Trail", "Running"].
    """
    #Extraction de l'année et filtrage
    if isinstance(sport, list):
        # Si on passe une liste d'années
        mask = df['sport'].isin(sport)
    else:
        # Si on passe une seule année
        mask = df['sport'] == sport

    result = df[mask].reset_index(drop=True)

    if len(result) == 0:
        print(f"⚠️ Aucun résultat pour : {sport}. Valeurs disponibles : {df['sport'].unique()[:5]}")

    return result

def Filter_By_Race(df, race, col='race_name'):
    """
    Filtre le DataFrame pour une ou plusieurs courses.
    'race' peut être un string "EDT23" ou une liste ["EDT23", "EDT25"].
    col 'race_name' par défaut, mais possible de filter sur race_id
    """
    #Extraction de l'année et filtrage
    if isinstance(race, list):
        # Si on passe une liste d'années
        mask = df[col].isin(race)
    else:
        # Si on passe une seule année
        mask = df[col] == race

    result = df[mask].reset_index(drop=True)

    if len(result) == 0:
        print(f"⚠️ Aucun résultat pour : {race}. Valeurs disponibles : {df['race_name'].unique()[:5]}")

    return result

def Filter_By_Race_v2(df, race, year=None, distance=None):
    """
    Filtre le DataFrame par :
    - race_name (string ou liste)
    - année (optionnel, ex: 2025 → race_date commence par 2025)
    - distance (optionnel, ex: 100)
    """

    # ---- Filtre race_name ----
    if isinstance(race, list):
        mask = df["race_name"].isin(race)
    else:
        mask = df["race_name"] == race

    # ---- Filtre année ----
    if year is not None:
        mask &= df["race_date"].astype(str).str.startswith(str(year))

    # ---- Filtre distance ----
    if distance is not None:
        mask &= df["Distance"] == distance

    result = df[mask].reset_index(drop=True)

    if len(result) == 0:
        print(
            f"⚠️ Aucun résultat pour race={race}, year={year}, distance={distance}. "
            f"Valeurs dispo (race_name) : {df['race_name'].unique()[:5]}"
        )

    return result


def Filter_By_Athlete(df, name_list):
    """
    Renvoie le DataFrame complet (tous les participants) pour les courses
    où TOUS les athlètes de 'name_list' étaient présents.
    """
    if 'name_key' not in df.columns:
        df['name_key'] = df['name'].apply(get_clean_key)

    if isinstance(name_list, str):
        name_list = [name_list]

    keys_to_filter = [get_clean_key(n) for n in name_list]
    num_required = len(keys_to_filter)
    mask_athletes = df['name_key'].isin(keys_to_filter)
    race_stats = df[mask_athletes].groupby('race_id')['name_key'].nunique()
    valid_races = race_stats[race_stats == num_required].index
    result = df[df['race_id'].isin(valid_races)].reset_index(drop=True)

    return result

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 🔹 Fonction de Calcul
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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


def get_Rank_Percentage(df, col):
    """
    Calcule le centile (top %) pour chaque ligne basé sur une colonne de classement.
    Ex: Un coureur 10ème sur 100 sera dans le 'Top 10%'.
    """
    # 1. On s'assure que la colonne est numérique et sans valeurs nulles
    temp_df = df.copy()
    temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce')

    # 2. On calcule le total de participants pour cette course (basé sur les non-nuls)
    total_participants = temp_df[col].max()
    # Note : On peut aussi utiliser len(temp_df) si le classement est continu

    # 3. Calcul du pourcentage (Rang / Total) * 100
    # On arrondit à 2 décimales pour la lisibilité
    temp_df['rank_percentage'] = (temp_df[col] / total_participants) * 100

    return temp_df['rank_percentage']




def get_coords(ville):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(ville)
    
    if location:
        return location.latitude, location.longitude
    return None, None
