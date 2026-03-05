SPORT_ICONS = {
    "Trail": "🏔️",
    "Running": "🏃‍♂️",
    "Cycling": "🚴‍♂️",
    "Triathlon": "🏊‍♂️🚴‍♂️🏃‍♂️"
}

def sport_icon(sport):
    """Retourne l'icône correspondant au sport ou un drapeau par défaut."""
    return SPORT_ICONS.get(sport, "🏁")

import streamlit as st #pour codespace
from supabase import create_client #pour codespace

def get_supabase():#pour codespace
    url = st.secrets["SUPABASE_URL"]#pour codespace
    key = st.secrets["SUPABASE_KEY"]#pour codespace
    return create_client(url, key) #pour codespace


ATHLETES = [
    "BERGER Tristan",
    "BOMPAS Théo",
    "BOMPAS Romain",
    "DELCAMP Brieuc",
    "CHAPUIS Thomas", 
    "CHAPUIS Maxime", 
    "CHAPUIS Laurent",
    "CHAPUIS Romane",
    "FRANCOIS Louis",
    "FEIDT Lucie",
    "GODILLON Matthieu",
    "TRIGO Severino",
    "Tessier Myriam"
    ]


FAMILLE = [
    "CHAPUIS Thomas", 
    "CHAPUIS Maxime", 
    "CHAPUIS Laurent",
    "CHAPUIS Romane",
    "TRIGO Severino",
    "Tessier Myriam"
    ]

FAMILLE_CHAPUIS = [
    "CHAPUIS Thomas", 
    "CHAPUIS Maxime", 
    "CHAPUIS Laurent",
    "CHAPUIS Romane"
    ]

COPAINS = [
    "BERGER Tristan",
    "DELCAMP Brieuc",
    "CHAPUIS Thomas", 
    "FRANCOIS Louis",
    "FEIDT Lucie",
    "GODILLON Matthieu"
    ]
COPAINS2 = [
    "BERGER Tristan",
    "BOMPAS Théo",
    "BOMPAS Romain",
    "DELCAMP Brieuc",
    "CHAPUIS Thomas", 
    "FRANCOIS Louis",
    "FEIDT Lucie",
    "GODILLON Matthieu",
    "TEIL Thomas"
    ]

COPAINS3 = [
    "BOMPAS Théo",
    "BOMPAS Romain",
    "CHAPUIS Thomas"
    ]

options_map = {
    "FAMILLE_CHAPUIS": FAMILLE_CHAPUIS,
    "FAMILLE": FAMILLE,
    "COPAINS": COPAINS,
    "COPAINS2": COPAINS2,
    "COPAINS3": COPAINS3,
    "ATHLETES": ATHLETES
}