import pandas as pd
import streamlit as st
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
        #name_list = [name for sublist in name_list for name in sublist]


    keys_to_filter = [get_clean_key(n) for n in name_list]
    num_required = len(keys_to_filter)
    mask_athletes = df['name_key'].isin(keys_to_filter)
    race_stats = df[mask_athletes].groupby('race_name')['name_key'].nunique()
    valid_races = race_stats[race_stats == num_required].index
    result = df[df['race_name'].isin(valid_races)].reset_index(drop=True)

    return result

def Filter_By_Athlete2(df, name_list, tolerance=True):
    """
    Filtre les courses selon la présence des athlètes de name_list.
    
    Args:
        df (DataFrame): Les données de courses.
        name_list (list|str): Liste des athlètes cibles.
        tolerance (bool): Si True, autorise 1 absent (si <4 noms) ou 2 absents (si >=4).
                         Si False, exige 100% de présence.
    """
    if 'name_key' not in df.columns:
        df['name_key'] = df['name'].apply(get_clean_key)

    if isinstance(name_list, str):
        name_list = [name_list]

    keys_to_filter = [get_clean_key(n) for n in name_list]
    num_total = len(keys_to_filter)
    
    # --- Calcul du seuil de présence ---
    if not tolerance:
        # Mode strict : tout le monde doit être là
        min_required = num_total
    else:
        # Mode flexible : calcul selon la taille du groupe
        if num_total < 5:
            #min_required = max(1, num_total - 1)
            min_required = num_total - 1
        else:
            min_required = num_total - 2

    # Filtrage des lignes correspondant aux athlètes cibles
    mask_athletes = df['name_key'].isin(keys_to_filter)
    
    # Comptage par course
    race_counts = df[mask_athletes].groupby('race_name')['name_key'].nunique()
    
    # Identification des courses valides selon le seuil
    valid_races = race_counts[race_counts >= min_required].index
    
    # Retourne le DF complet pour ces courses
    result = df[df['race_name'].isin(valid_races)].reset_index(drop=True)

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

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def get_coords(ville):
    geolocator = Nominatim(
        user_agent="my_app_thomas",  # important: user_agent explicite
        timeout=10                   # augmente le timeout
    )
    
    try:
        location = geolocator.geocode(ville)
        if location:
            return location.latitude, location.longitude
        return None, None
    
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None, None


def get_coords(ville):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(ville)
    
    if location:
        return location.latitude, location.longitude
    return None, None


import colorsys

def generate_gradient(start_hex, end_hex, n):
    """Génère une palette de couleurs entre start_hex et end_hex."""
    start_rgb = tuple(int(start_hex[i:i+2], 16) for i in (1, 3, 5))
    end_rgb = tuple(int(end_hex[i:i+2], 16) for i in (1, 3, 5))
    colors = []
    for i in range(n):
        ratio = i / (n - 1)
        r = int(start_rgb[0] * (1 - ratio) + end_rgb[0] * ratio)
        g = int(start_rgb[1] * (1 - ratio) + end_rgb[1] * ratio)
        b = int(start_rgb[2] * (1 - ratio) + end_rgb[2] * ratio)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors
