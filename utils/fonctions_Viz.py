import pandas as pd
import unicodedata
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import numpy as np
from geopy.geocoders import Nominatim
import streamlit as st

from utils import fonctions_Filter as f

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 🔹 Fonction de Viz
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def Viz_Sexes(df_all_parquet):
    df = df_all_parquet.copy()
    df['race_display'] = (
        df['race_name'] + " (" + df['race_date'].dt.year.astype(str) + ")"
    )
    # Agrégation : on garde 'race_date' pour pouvoir trier après le groupby
    summary = df.groupby(['race_date', 'race_display']).agg({
        'sex': [
            ('nb F', lambda x: (x == 'F').sum()),
            ('nb H', lambda x: (x == 'H').sum())
        ]
    }).reset_index()

    # Nettoyage des noms de colonnes suite à l'agrégation nommée
    summary.columns = ['race_date', 'race_display', 'nb F', 'nb H']

    # 3. Tri par date (ordre croissant)
    summary = summary.sort_values('race_date')

    # 4. Création du graphique
    fig = px.bar(summary,
                x='race_display',
                y=['nb F', 'nb H'],
                title='Répartition Relative Hommes/Femmes par Course',
                labels={'value': 'Nombre', 'variable': 'Genre', 'race_display': 'Course'},
                template='plotly_dark',
                text_auto='d', # Affiche les entiers
                color_discrete_map={'nb F': '#e84393', 'nb H': '#3498db'})
    
    
    # 5. Application de la normalisation à 100%
    fig.update_traces(
        marker_line_width=0,    # Supprime l'épaisseur du trait de contour
        textposition='inside', 
        textfont_color="white"
    )
    
    fig.update_layout(
        barmode='stack',
        barnorm='percent',
        hovermode="x unified",
        xaxis_title=""
    )

    # Ajustements des axes
    fig.update_yaxes(title="Pourcentage (%)", range=[0, 100])
    fig.update_xaxes(tickangle=-45)

    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit

def Viz_Sexes_PieChart(df_single_race):
    #if len(df_single_race['race_name'].unique()) > 1:
    #   raise ValueError("Le DataFrame doit contenir les données d'une seule course.")

    # Calcul du nombre de femmes et d'hommes
    nb_F = (df_single_race['sex'] == 'F').sum()
    nb_H = (df_single_race['sex'] == 'H').sum()

    # Création des données pour le camembert
    data = {
        'Genre': ['Femmes', 'Hommes'],
        'Nombre': [nb_F, nb_H]
    }

    # Création du camembert
    fig = px.pie(
        names=['Femmes', 'Hommes'],
        values=[nb_F, nb_H],
        #title=f"Répartition Hommes/Femmes - {df_single_race['race_name'].iloc[0]} ({df_single_race['race_date'].dt.year.iloc[0]})",
        title=None,
        color=['Femmes', 'Hommes'],
        color_discrete_map={'Femmes': '#e84393', 'Hommes': '#3498db'},
        hole=0.6
    )

    # Personnalisation de la mise en page
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        showlegend=False,
        marker=dict(line=dict(color='#000000', width=1))
    )

    fig.update_layout(
        title=None,
        template='plotly_dark'
    )

    return fig


def Viz_Barre_Categorie(df_race):
    """
    Diagramme en barres du nombre de coureurs par catégorie,
    avec les barres découpées par sexe (H/F).
    
    df_race : DataFrame de la course
    """
    df = df_race.copy()

    # Vérifie qu'on a bien les colonnes nécessaires
    if not {'category', 'sex'}.issubset(df.columns):
        raise ValueError("Le DataFrame doit contenir les colonnes 'category' et 'sex'")

    # 1. Compter le nombre de coureurs par catégorie et sexe
    df_count = df.groupby(['category', 'sex']).size().reset_index(name='count')

    # 2. Titre dynamique
    #race_key = df['race_key'].iloc[0] if 'race_key' in df.columns else "la course"

    # 3. Diagramme en barres empilées
    fig = px.bar(
        df_count,
        x='category',
        y='count',
        color='sex',
        text='count',  # Affiche le nombre sur chaque barre
        barmode='stack',
        labels={'category':'Catégorie', 'count':'Nombre de coureurs', 'sex':'Sexe'},
        #title=f"Répartition des coureurs par catégorie et sexe : {race_key}",
        title="Répartition des coureurs par catégorie et sexe",
        color_discrete_map={'H':'#3498db','F':'#e84393'},  # Bleu homme, rouge femme
        #color_discrete_map={'Femmes': '#e84393', 'Hommes': '#3498db'},
        template='plotly_dark'
    )

    fig.update_traces(textposition='inside',showlegend=False,)
    fig.update_layout(xaxis_title="Catégorie", yaxis_title="Nombre de coureurs")

    return fig


def Viz_Barre_RankPct(df, name_key):
    """
    Affiche un diagramme en barres pour chaque course d'un athlète,
    avec la hauteur = 100 - pourcentage du classement
    (meilleur = barre plus haute)
    
    df : DataFrame contenant tous les coureurs avec colonnes ['race_key', 'name_key', 'rank']
    name_key : identifiant de l'athlète à filtrer
    """
    # 1. Filtrer l'athlète
    df_athlete = df[df['name_key'] == name_key].copy()
    
    if df_athlete.empty:
        raise ValueError(f"Aucun résultat trouvé pour l'athlète '{name_key}'")
    
    # 2. Nombre total de participants par course (max rank)
    total_participants = df.groupby('race_key')['rank'].max().reset_index()
    total_participants.rename(columns={'rank':'total'}, inplace=True)
    
    # Merge pour ajouter total participants dans df_athlete
    df_athlete = df_athlete.merge(total_participants, on='race_key', how='left')
    
    # 3. Calcul du pourcentage de classement et score
    df_athlete['rank_pct'] = df_athlete['rank'] / df_athlete['total'] * 100
    df_athlete['score'] = 100 - df_athlete['rank_pct']
    #df_athlete['rank_display'] = df_athlete['rank'].apply(lambda x: f"{int(x)}er" if x == 1 else f"{int(x)}e")
    df_athlete['rank_pct_display'] = df_athlete['rank_pct'].apply(lambda x: f"Top {x:.1f}%")
    df_athlete["time_display"] = df_athlete["time"].apply(
        lambda x: f"{int(x.total_seconds() // 3600):02d}:{int((x.total_seconds() % 3600) // 60):02d}:{int(x.total_seconds() % 60):02d}")
    
    # 1. On transforme les colonnes en texte (en gérant le cas "1er")
    df_athlete['rank_display'] = df_athlete['rank'].astype(int).astype(str) + "e"
    df_athlete['rank_display'] = df_athlete['rank_display'] + "/" + df_athlete['total'].astype(int).astype(str)

    st.write(df_athlete.head())

    # 4. Diagramme en barres simple
    fig = px.bar(
        df_athlete.sort_values('score', ascending=False),
        x='race_key',
        y='score',
        text='rank_pct_display',  # affiche le rang exact
        hover_data={
            'race_key': True,      # Affiche la clé de la course
            'time_display':True,
            'rank_pct_display':False,
            'rank_display': True,  # Affiche le rang formaté (ex: 66e)
            'score': False,         # On cache le score s'il n'est pas souhaité au survol
            'total':False
        },
        title=f"Les Performances de {name_key}",
        template='plotly_dark',
        color_discrete_sequence=['#2ecc71']
    )
    
    fig.update_traces(textposition='outside')

    # --- Suppression de l'unité et des chiffres sur l'axe Y ---
    fig.update_yaxes(
        showticklabels=False, # Cache les chiffres (0, 20, 40...)
        title_text="",        # Supprime le titre "score"
        showgrid=False        # Optionnel : supprime les lignes de grille pour un look plus clean
    )

    fig.update_layout(
        #yaxis=dict(range=[0,110], title="Performance (%)"),
        yaxis=dict(range=[0,110], title=None),
        xaxis_title=None,
        showlegend=False
    )

    # On définit le template personnalisé pour afficher uniquement les valeurs brutes
    fig.update_traces(
        hovertemplate=(
            "%{customdata[1]}<br>" +     
            "%{customdata[2]}<br>" +    
            "%{customdata[0]}<br>" +
            #"<b>%{customdata[3]}</b>" +          # rank_pct_display (ex: 4,2%) seul
            "<extra></extra>"                    # Cache la boîte secondaire (le nom de la trace)
        )
    )
    
    return fig


def Viz_Histogramme_Temps(df_race, col):
    """
    Trace l'histogramme des temps pour une course donnée.
    la colonne s'appelle choisie est col: par example 'time' ou "t1"
    """
    df = df_race.copy()

    # 1. Conversion des temps en format timedelta puis en minutes
    # On gère le cas où le temps est déjà numérique ou au format string HH:MM:SS
    if df[col].dtype == 'object'or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        # Si c'est déjà des secondes/minutes
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Création du titre dynamique
    race_name = df['race_name'].iloc[0] if 'race_name' in df.columns else "la course"

    # 3. Tracé de l'histogramme
    fig = px.histogram(df,
                       x="col_min",
                       title=f"Distribution des temps : {race_name}| {col}",
                       labels={'col_min': 'Temps (minutes)', 'count': 'Nombre de coureurs'},
                       nbins=30,             # Ajuste la précision des barres
                       template='plotly_dark',
                       color_discrete_sequence=['#2ecc71'], # Un vert sportif
                       marginal="rug")      # Ajoute des petits traits en bas pour voir chaque coureur

    # 4. Améliorations visuelles
    fig.update_layout(
        bargap=0.1,
        xaxis_title="Temps (minutes)",
        yaxis_title="Nombre de coureurs",
        showlegend=False,
        template='plotly_dark'
    )
    
    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit


def Viz_Histogramme_Temps_Sex(df_race, col, Sex=False):
    """
    Trace l'histogramme des temps pour une course donnée.
    Si Sex=True, superpose les histogrammes des hommes et des femmes.
    """
    df = df_race.copy()

    # 1. Conversion des temps en minutes
    if df[col].dtype == 'object' or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Tracé de l'histogramme
    if Sex and 'sex' in df.columns:
        fig = px.histogram(df,
                           x="col_min",
                           color='sex',
                           barmode='overlay',
                           title=f"Distribution des temps : {df['race_name'].iloc[0] if 'race_name' in df.columns else 'la course'} | {col}",
                           labels={'col_min': 'Temps (minutes)', 'count': 'Nombre de coureurs'},
                           nbins=30,
                           template='plotly_dark',
                           color_discrete_map={'H': '#3498db', 'F': '#e84393'},
                           #marginal="rug",
                           opacity=0.75)
    else:
        fig = px.histogram(df,
                           x="col_min",
                           title=f"Distribution des temps : {df['race_name'].iloc[0] if 'race_name' in df.columns else 'la course'} | {col}",
                           labels={'col_min': 'Temps (minutes)', 'count': 'Nombre de coureurs'},
                           nbins=30,
                           template='plotly_dark',
                           color_discrete_sequence=['#2ecc71'],
                           marginal="rug")

    # 3. Améliorations visuelles
    fig.update_layout(
        bargap=0.1,
        xaxis_title="Temps (minutes)",
        yaxis_title="Nombre de coureurs",
        showlegend=False
        #showlegend=Sex  # Affiche la légende uniquement si Sex=True
    )

    return fig


def Viz_Histogramme_Temps_Names(df_race, col, names):
    """
    Trace l'histogramme des temps pour une course donnée avec des traits verticaux pour les temps de plusieurs personnes.

    Parameters:
    - df_race: DataFrame contenant les données de la course.
    - col: Nom de la colonne contenant les temps (ex: 'time' ou 't1').
    - names: Liste des noms des personnes (ou un seul nom) dont les temps seront mis en évidence.
    """
    df = df_race.copy()

    # Convertir names en liste si ce n'est pas déjà le cas
    if isinstance(names, str):
        names = [names]

    # 1. Conversion des temps en format timedelta puis en minutes
    if df[col].dtype == 'object' or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Récupération des temps des personnes cherchées
    temps_dict = {}
    for name in names:
        clean_name = get_clean_key(name)
        temps = df.loc[df['name_key'] == clean_name, 'col_min'].values
        if len(temps) > 0:
            full_name = df.loc[df['name_key'] == clean_name, 'name'].values[0]
            temps_dict[full_name] = temps[0]

    # 3. Création du titre dynamique
    race_name = df['race_name'].iloc[0] if 'race_name' in df.columns else "la course"
    df['col_min_display'] = df['col_min'].apply(lambda m: f"{int(m // 60):02d}h{int((m % 60) // 60):02d}")
    
    # 4. Tracé de l'histogramme
    fig = px.histogram(
        df,
        x="col_min",
        #title=f"Distribution des temps : {race_name} | {col}",
        title=f"{race_name} - Distribution des temps",
        labels={'count': 'Nombre de coureurs'},
        hover_data={
            'col_min_display': True
        },
        nbins=30,
        template='plotly_dark',
        color_discrete_sequence=['#2ecc71']
    )

    # 5. Ajout des traits verticaux pour chaque personne
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan']  # Liste de couleurs pour les traits
    for i, (name, temps) in enumerate(temps_dict.items()):
        fig.add_vline(
            x=temps,
            line_dash="dash",
            line_color=colors[i % len(colors)],
            annotation_text=f"{name}",
            annotation_position="top left",
            annotation_textangle=-90
        )

    # 6. Calcul des bornes inférieures des barres pour les ticks
    bin_edges = np.histogram_bin_edges(df['col_min'], bins=30)
    tickvals = bin_edges[:-1]  # On prend la borne inférieure de chaque barre
    #ticktext = [str(pd.Timedelta(minutes=m).round('1s')).split()[2] for m in tickvals]
    #ticktext = [str(pd.Timedelta(seconds=m)).split()[2][:-3] for m in tickvals] #FAUX
    #ticktext = [str(pd.Timedelta(minutes=m)).split()[2][:-3] for m in tickvals]
    ticktext = [
        f"{int(m // 60):02d}h{int(m % 60):02d}"
        for m in tickvals
    ]

    # 7. Mise à jour de l'axe des abscisses
    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=45
    )

    # 8. Améliorations visuelles
    fig.update_layout(
        bargap=0.1,
        xaxis_title=None,
        yaxis_title="Nombre de coureurs",
        showlegend=False,
        template='plotly_dark'
    )

     # 9. Ajout d'un "sous-titre"
    if len(names)==1:
        texte_annotation = "\n".join([
            f"{k} : {int(v // 3600):02d}:{int((v % 3600) // 60):02d}:{int(v % 60):02d}" 
            for k, v in temps_dict.items()
        ])
        fig.add_annotation(
            text=texte_annotation,   # texte à afficher
            xref="paper", yref="paper",     # coordonnées relatives à la figure (0-1)
            x=1, y=1.2,                       # position (1,1) = coin supérieur droit
            xanchor='right', yanchor='top', # ancrage du texte
            showarrow=False,
            #font=dict(size=14, color="black")
        )
    
    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit

def Viz_Histogramme_Temps_Names_Horizontal(df_race, col, names):
    """
    Trace l'histogramme des temps pour une course donnée avec des traits verticaux pour les temps de plusieurs personnes.

    Parameters:
    - df_race: DataFrame contenant les données de la course.
    - col: Nom de la colonne contenant les temps (ex: 'time' ou 't1').
    - names: Liste des noms des personnes (ou un seul nom) dont les temps seront mis en évidence.
    """
    df = df_race.copy()

    # Convertir names en liste si ce n'est pas déjà le cas
    if isinstance(names, str):
        names = [names]

    # 1. Conversion des temps en format timedelta puis en minutes
    if df[col].dtype == 'object' or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Récupération des temps des personnes cherchées
    temps_dict = {}
    for name in names:
        clean_name = get_clean_key(name)

        row = df.loc[df['name_key'] == clean_name, ['name', 'col_min', 'rank']]

        if not row.empty:
            full_name = row.iloc[0]['name']
            temps = row.iloc[0]['col_min']
            rank = row.iloc[0]['rank']

            temps_dict[full_name] = {
                "temps": temps,
                "rank": rank
            }

    # 3. Création du titre dynamique
    race_name = df['race_name'].iloc[0] if 'race_name' in df.columns else "la course"


    # 4. Tracé de l'histogramme
    fig = px.violin(
        df,
        y="col_min",
        #box=True,          # ajoute la boxplot au centre
        points=False,      # True si tu veux afficher les points individuels
        #title=f"Distribution des temps : {race_name} | {col}",
        labels={'col_min': 'Temps'},
        template='plotly_dark',
        color_discrete_sequence=['#2ecc71']
    )

    fig.update_traces(
        meanline_visible=True  # affiche la moyenne
    )
    
    # 🔽 Tri par temps
    temps_dict_sorted = dict(
        sorted(
            temps_dict.items(),
            key=lambda item: item[1]["temps"]
        )
    )
    for i, (name, data) in enumerate(temps_dict_sorted.items()):
        temps = data["temps"]
        rank = data["rank"]
    
        if i % 2 == 0:
            # 👉 À DROITE
            x0, x1 = 0.5, 0.8
            x_text = 0.8
            xanchor = "left"
        else:
            # 👈 À GAUCHE
            x0, x1 = 0.5, 0.2
            x_text = 0.2
            xanchor = "right"
    
        # Ligne horizontale
        fig.add_shape(
            type="line",
            xref="paper",
            yref="y",
            x0=x0,
            x1=x1,
            y0=temps,
            y1=temps,
            line=dict(
                color="gray",
                width=1
            )
        )
    
        # Annotation
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=x_text,
            y=temps,
            #text=f"#{rank} – {name}",
            text=f"{name} - {rank}e ",
            showarrow=False,
            xanchor=xanchor,
            align="left",
            font=dict(size=8)
        )

    # 6. Calcul des bornes inférieures des barres pour les ticks
    bin_edges = np.histogram_bin_edges(df['col_min'], bins=10)
    tickvals = bin_edges[:-1]  # On prend la borne inférieure de chaque barre
    ticktext = [
        f"{int(m // 60):02d}h{int(m % 60):02d}"
        for m in tickvals
    ]

    # 7. Mise à jour de l'axe des abscisses
    fig.update_yaxes(
        tickvals=tickvals,
        ticktext=ticktext
        #tickangle=45
    )

    # 8. Améliorations visuelles
    fig.update_layout(
        bargap=0.1,
        #title = None,
        #xaxis_title="Nombre de coureurs",
        xaxis_title=None,
        yaxis_title="Temps",
        height=600,
        margin=dict(l=40, r=40, t=10, b=10),
        showlegend=False,
        template='plotly_dark'
    )

    fig.update_traces(
        hoveron="points"
    )
    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit

def Viz_Violin_Group(df_race, col, names):
    """
    Trace un violin plot horizontal des temps pour chaque 'race_id' présent dans df_race,
    avec des lignes et annotations pour des athlètes spécifiques.

    Parameters:
    - df_race: DataFrame contenant les données de la course.
    - col: Nom de la colonne contenant les temps (ex: 'time').
    - names: Liste des noms des personnes (ou un seul nom) dont les temps seront mis en évidence.
    """

    df = df_race.copy()

    # Convertir names en liste si ce n'est pas déjà le cas
    if isinstance(names, str):
        names = [names]

    # 1. Conversion des temps en minutes
    if df[col].dtype == 'object' or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Préparer le dictionnaire des athlètes
    temps_dict = {}
    for name in names:
        clean_name = get_clean_key(name)
        row = df.loc[df['name_key'] == clean_name, ['name', 'col_min', 'rank', 'race_id']]

        if not row.empty:
            for _, r in row.iterrows():
                full_name = r['name']
                race_id = r['race_id']
                temps = r['col_min']
                rank = r['rank']

                if race_id not in temps_dict:
                    temps_dict[race_id] = {}
                temps_dict[race_id][full_name] = {
                    "temps": temps,
                    "rank": rank
                }

    # 3. Créer le violin plot pour chaque race_id
    fig = px.violin(
        df,
        x='race_id',
        y='col_min',
        points=False,
        labels={'col_min': 'Temps', 'race_id': 'Course'},
        template='plotly_dark',
        color_discrete_sequence=['#2ecc71']
    )
    #fig.update_traces(meanline_visible=True,hovertemplate="%{y:.2f} min<extra></extra>")
    # ⚡ Hover minimal pour toutes les traces
    #for trace in fig.data:
        #trace.hovertemplate = "%{y:.2f} min<extra></extra>"

    # 4. Ajouter les lignes et annotations pour chaque race_id
    for race_id, athletes in temps_dict.items():
        athletes_sorted = dict(sorted(athletes.items(), key=lambda item: item[1]['temps']))

        for i, (name, data) in enumerate(athletes_sorted.items()):
            temps = data["temps"]
            rank = data["rank"]

            # Position horizontale du trait et du texte
            if i % 2 == 0:
                x0, x1 = 0.5, 0.8
                x_text = 0.8
                xanchor = "left"
            else:
                x0, x1 = 0.5, 0.2
                x_text = 0.2
                xanchor = "right"

            # Ligne horizontale
            fig.add_shape(
                type="line",
                xref="x",
                yref="y",
                x0=race_id,  # position sur la course
                x1=race_id,
                y0=temps,
                y1=temps,
                line=dict(color="gray", width=1)
            )

            # Annotation
            fig.add_annotation(
                x=race_id,
                y=temps,
                text=f"{name} - {rank}e",
                showarrow=False,
                xanchor=xanchor,
                align="left",
                font=dict(size=8)
            )

    # 5. Mise à jour des axes
    bin_edges = np.histogram_bin_edges(df['col_min'], bins=10)
    tickvals = bin_edges[:-1]
    ticktext = [f"{int(m // 60):02d}h{int(m % 60):02d}" for m in tickvals]

    fig.update_yaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        title="Temps"
    )

    fig.update_layout(
        xaxis_title="Course (race_id)",
        height=600,
        margin=dict(l=40, r=40, t=10, b=40),
        showlegend=False,
        template='plotly_dark'
    )

    return fig

def Viz_Violin_Group2(df_race, col, names):
    """
    Trace un violin plot horizontal des temps pour chaque 'race_id' présent dans df_race,
    avec des lignes et annotations pour des athlètes spécifiques.
    
    Parameters:
    - df_race: DataFrame contenant les données de la course.
    - col: Nom de la colonne contenant les temps (ex: 'time').
    - names: Liste des noms des personnes (ou un seul nom) dont les temps seront mis en évidence.
    """

    df = df_race.copy()

    # Convertir names en liste si ce n'est pas déjà le cas
    if isinstance(names, str):
        names = [names]

    # 1. Conversion des temps en minutes
    if df[col].dtype == 'object' or pd.api.types.is_timedelta64_dtype(df[col]):
        df['col_td'] = pd.to_timedelta(df[col])
        df['col_min'] = df['col_td'].dt.total_seconds() / 60
    else:
        df['col_min'] = df[col]

    df = df[df['col_min'] > 0]

    # 2. Préparer le dictionnaire des athlètes par race_id
    temps_dict = {}
    for name in names:
        clean_name = get_clean_key(name)
        row = df.loc[df['name_key'] == clean_name, ['name', 'col_min', 'rank', 'race_id']]

        if not row.empty:
            for _, r in row.iterrows():
                full_name = r['name']
                race_id = r['race_id']
                temps = r['col_min']
                rank = r['rank']

                if race_id not in temps_dict:
                    temps_dict[race_id] = {}
                temps_dict[race_id][full_name] = {
                    "temps": temps,
                    "rank": rank
                }

    # 3. Créer le figure go.Figure
    fig = go.Figure()

    # Ajouter un violin pour chaque race_id
    for race_id, df_r in df.groupby('race_id'):
        fig.add_trace(go.Violin(
            y=df_r['col_min'],
            name=str(race_id),
            points=False,         # pas de points individuels
            box_visible=True,     # boxplot au centre
            line_color='#2ecc71',
            meanline_visible=True,
            hoverinfo='y',        # n’affiche que la valeur y
            showlegend=False
        ))

    # 4. Ajouter lignes et annotations pour les athlètes
    for race_id, athletes in temps_dict.items():
        athletes_sorted = dict(sorted(athletes.items(), key=lambda item: item[1]['temps']))

        for i, (name, data) in enumerate(athletes_sorted.items()):
            temps = data["temps"]
            rank = data["rank"]

            # Ligne horizontale
            fig.add_shape(
                type="line",
                x0=-0.5,               # x coord pour traverser le violin
                x1=0.5,                # x coord pour traverser le violin
                xref=f"x",             # violin position relative automatique
                y0=temps,
                y1=temps,
                line=dict(color="gray", width=1)
            )

            # Annotation
            if i % 2 == 0:
                x_text = 0.5
                xanchor = "left"
            else:
                x_text = -0.5
                xanchor = "right"

            fig.add_annotation(
                x=x_text,
                y=temps,
                xref='x',
                yref='y',
                text=f"{name} - {rank}e",
                showarrow=False,
                xanchor=xanchor,
                font=dict(size=8)
            )

    # 5. Axe y en HH:MM pour lisibilité
    bin_edges = np.histogram_bin_edges(df['col_min'], bins=10)
    tickvals = bin_edges[:-1]
    ticktext = [f"{int(m // 60):02d}h{int(m % 60):02d}" for m in tickvals]

    fig.update_yaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        title="Temps"
    )

    fig.update_layout(
        xaxis_title="Course (race_id)",
        height=600,
        margin=dict(l=40, r=40, t=10, b=40),
        template='plotly_dark'
    )

    return fig

def Viz_Radar_Triathlon(df, names_list):
    """
    Trace un Radar par course, pour chaque course de df dans laquelle au moins 1 athlète de names_list à participer.
    Affiche le 'rank' pour swim, bike, run, T1,T2.
    
    Parameters:
    - df : df_Tri = f.Filter_By_Sport(df_all_parquet, "Triathlon") -> un df filtré uniquement sur le Triathlon.
    - names_lits: la liste des athlètes qu'on veut comparer.
    """

    required_cols = ['swim', 'bike', 'run'] # On ne garde que les courses qui ont au moins une valeur non nulle dans ces colonnes
    valid_races = []
    for race in df['race_name'].unique():
        df_check = df[df['race_name'] == race]
        if not df_check[required_cols].dropna(how='all').empty:
            valid_races.append(race)

    if not valid_races:
        print("Aucune course avec des splits (Swim/Bike/Run) n'a été trouvée.")
        return

    n_races = len(valid_races)
    cols = min(3, n_races)
    rows = math.ceil(n_races / cols)

    specs = [[{'type': 'polar'} for _ in range(cols)] for _ in range(rows)]
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=valid_races,
        specs=specs,
        horizontal_spacing=0.1,
        vertical_spacing=0.1
    )

    categories = ['Total', 'Swim', 'T1', 'Bike', 'T2', 'Run']
    cols_metrics = ['rank', 'swim', 't1', 'bike', 't2', 'run']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']

    # 2. Boucle sur les courses valides
    for idx, race in enumerate(valid_races):
        row = (idx // cols) + 1
        col = (idx % cols) + 1
        df_race = df[df['race_name'] == race].copy()

        for i, name in enumerate(names_list):
            search_key = get_clean_key(name)
            indices = df_race[df_race['name_key'].str.contains(search_key, case=False, na=False)].index
            if indices.empty:
                continue

            # 3. Extraction et vérification des NaNs pour cet athlète
            scores = []
            has_nan = False
            for m in cols_metrics:
                series_rank = df_race[m].rank(method='min', ascending=True)
                val = series_rank.loc[indices[0]]
                #print(m)
                #print(val)

                if pd.isna(val):
                    has_nan = True
                    break
                scores.append(int(val))

            # Si l'athlète a des NaNs dans ses splits pour CETTE course, on ne le trace pas
            if has_nan:
                continue

            fig.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=f"{name}",
                line_color=colors[i % len(colors)],
                showlegend=(idx == 0)
            ), row=row, col=col)


        polar_name = 'polar' if idx == 0 else f'polar{idx + 1}'
        limit = int(df_race['rank'].max())
        fig.update_layout({
            polar_name: dict(
                radialaxis=dict(
                    range=[1, limit],
                    visible=True,
                    tickfont_size=6,
                    # On force Plotly à ne pas arrondir à 100
                    autorange=False
                )
            )
        })

    fig.update_layout(
        height=500 * rows,
        title_text="Analyse Multi-Courses - Classement par sports",
        template='plotly_dark'
    )
    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit




def Viz_Radar_Triathlon2(df, names_list, mode='rank'):
    """
    Trace un Radar par course, pour chaque course de df dans laquelle au moins 1 athlète de names_list a participé.
    Affiche soit le 'rank' (classement absolu) soit le 'rank_pct' (classement en pourcentage).
    -> la même chose que Viz_Radar_Triathlon, simplement ajouté la sélection du mode 'rank' ou 'rank_pct'.

    Parameters:
    - df: DataFrame filtré sur le Triathlon.
    - names_list: Liste des athlètes à comparer.
    - mode: 'rank' (par défaut) ou 'rank_pct' pour choisir le type de classement à afficher.
    """

    required_cols = ['swim', 'bike', 'run']
    valid_races = []
    for race in df['race_name'].unique():
        df_check = df[df['race_name'] == race]
        if not df_check[required_cols].dropna(how='all').empty:
            valid_races.append(race)

    if not valid_races:
        print("Aucune course avec des splits (Swim/Bike/Run) n'a été trouvée.")
        return

    n_races = len(valid_races)
    cols = min(3, n_races)
    rows = math.ceil(n_races / cols)

    specs = [[{'type': 'polar'} for _ in range(cols)] for _ in range(rows)]
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=valid_races,
        specs=specs,
        horizontal_spacing=0.1,
        vertical_spacing=0.1
    )

    categories = ['Total', 'Swim', 'T1', 'Bike', 'T2', 'Run']
    cols_metrics = ['rank', 'swim', 't1', 'bike', 't2', 'run']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']

    for idx, race in enumerate(valid_races):
        row = (idx // cols) + 1
        col = (idx % cols) + 1
        df_race = df[df['race_name'] == race].copy()

        for i, name in enumerate(names_list):
            search_key = get_clean_key(name)
            indices = df_race[df_race['name_key'].str.contains(search_key, case=False, na=False)].index
            if indices.empty:
                continue

            scores = []
            has_nan = False
            for m in cols_metrics:
                if mode == 'rank':
                    series_rank = df_race[m].rank(method='min', ascending=True)
                    val = series_rank.loc[indices[0]]
                elif mode == 'rank_pct':
                    series_rank = df_race[m].rank(method='min', ascending=True, pct=True)
                    val = series_rank.loc[indices[0]] * 100  # Convertir en pourcentage

                if pd.isna(val):
                    has_nan = True
                    break
                scores.append(float(val))

            if has_nan:
                continue

            fig.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=f"{name}",
                line_color=colors[i % len(colors)],
                showlegend=(idx == 0)
            ), row=row, col=col)

        polar_name = 'polar' if idx == 0 else f'polar{idx + 1}'
        if mode == 'rank':
            limit = int(df_race['rank'].max())
        elif mode == 'rank_pct':
            limit = 100  # Pourcentage max

        fig.update_layout({
            polar_name: dict(
                radialaxis=dict(
                    range=[1, limit],
                    visible=True,
                    tickfont_size=6,
                    autorange=False
                )
            )
        })

    fig.update_layout(
        height=500 * rows,
        title_text=f"Analyse Multi-Courses - Classement {'absolu' if mode == 'rank' else 'en pourcentage'} par sports",
        template='plotly_dark'
    )
    return fig


def Viz_Radar_Single_Athlete(df, athlete_name):
    """
    Trace un radar superposé pour un seul coureur, sur toutes les courses auxquelles il a participé.
    Affiche un DataFrame détaillé pour déboguer les calculs de pourcentage.
    """
    search_key = get_clean_key(athlete_name)
    df_athlete = f.Filter_By_Athlete(df, search_key)

    if df_athlete.empty:
        st.warning(f"Aucune donnée trouvée pour le coureur : {athlete_name}")
        return

    # Affichage du DataFrame détaillé pour le débogage
    races = df_athlete['race_name'].unique()
    debug_data = []

    for race in races:
        df_race = df_athlete[df_athlete['race_name'] == race]
        row = {
            'race_key': df_race['race_key'].iloc[0],
            'name': df_race['name'].iloc[0],
            'time': df_race['time'].iloc[0],
            'rank': df_race['rank'].iloc[0]
        }

        for m in ['swim', 'bike', 'run', 't1', 't2']:
            row[f"{m}"] = df_race[m].iloc[0]
            row[f"{m}_rank"] = df_race[m].rank(method='min', ascending=True).iloc[0]
            row[f"{m}_rank_pct"] = df_race[m].rank(method='min', ascending=True, pct=True).iloc[0] * 100

        debug_data.append(row)

    df_debug = pd.DataFrame(debug_data)
    st.dataframe(df_debug)

    # Initialisation de la figure
    fig = go.Figure()

    categories = ['Total', 'Swim', 'T1', 'Bike', 'T2', 'Run']
    cols_metrics = ['rank', 'swim', 't1', 'bike', 't2', 'run']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#1abc9c', '#d35400']

    # Boucle sur les courses
    for i, race in enumerate(races):
        df_race = df_athlete[df_athlete['race_name'] == race]
        scores = []
        has_nan = False

        # Calcul des scores en rank_pct
        for m in cols_metrics:
            series_rank = df_race[m].rank(method='min', ascending=True, pct=True)
            val = series_rank.iloc[0] * 100  # Convertir en pourcentage
            if pd.isna(val):
                has_nan = True
                break
            scores.append(100 - float(val))

        if has_nan:
            continue

        # Ajout de la trace pour cette course
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=f"{race}",
            line_color=colors[i % len(colors)],
            opacity=0.7
        ))

    # Mise en forme du radar
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 100],  # Échelle en pourcentage
                visible=True,
                tickfont_size=10,
                tickvals=[0, 20, 40, 60, 80, 100],  # Valeurs affichées
                ticktext=['100%', '80%', '60%', '40%', '20%', '0%']  # Légendes inversées
            )
        ),
        title=f"Comparaison des performances de {athlete_name} (en %) sur toutes ses courses",
        template='plotly_dark',
        height=600
    )

    return fig



def Viz_Battle_percentage(df_Battle, targets):
    """
    Affiche un diagramme course par course des pourcentages de classement
    Parameters:
    - df_race: DataFrame contenant les données de la course.
    - targets = ["chapuisthomas", "bompastheo"]
    """
    date_col = 'race_date' 
    df_Battle[date_col] = pd.to_datetime(df_Battle[date_col])
    df_Battle = df_Battle.sort_values(date_col, ascending=True)

    df_plot = df_Battle.copy()
    df_plot['Pourcentage'] = df_plot.groupby('race_name')['rank'].transform(lambda x: (x / x.max()) * 100)


    df_plot = df_plot[df_plot['name_key'].isin(targets)]
    df_plot['text_label'] = df_plot['Pourcentage'].round(1).astype(str) + "%"
    df_plot = df_plot[['race_name', 'name_key', 'Pourcentage', 'text_label']].rename(
        columns={'race_name': 'Course', 'name_key': 'Coureur'}
    )

    #df_plot['Performance_Inv'] = 100 - df_plot['Pourcentage']
    df_plot['Performance_Inv'] = 90 - df_plot['Pourcentage']

    df_plot['Val_Graph'] = df_plot.apply(
        lambda x: -x['Performance_Inv'] if x['Coureur'] == targets[0] else x['Performance_Inv'], 
        axis=1
    )
    fig = px.bar(
        df_plot,
        y="Course",
        x="Val_Graph",
        color="Coureur",
        orientation='h',
        text="text_label",
        template="plotly_dark",
        category_orders={"Course": df_plot['Course'].unique().tolist()},
        color_discrete_map={targets[0]: "#EF553B", targets[1]: "#636EFA"}
    )


    fig.update_layout(
        xaxis=dict(title='',showticklabels=False, showgrid=False, zeroline=True, zerolinecolor='gray', range=[-90, 90]),
        yaxis=dict(title='',showticklabels=False, showgrid=False),
        bargap=0.4,
        showlegend=False
    )

    fig.update_traces(textposition='outside', cliponaxis=False)

    for i, row in df_plot.drop_duplicates('Course').iterrows():
        fig.add_annotation(
            x=0, y=row['Course'],
            text=f"<b>{row['Course']}</b>",
            showarrow=False,
            font=dict(size=11, color="white"),
            bgcolor="rgba(0,0,0,0)"
        )

    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit

def Viz_Battle_Time_by_Races(df_TT, athletes):
    """
    Affiche un diagramme course par course avec le temps des 2 athletes côte à côtes sur chaque course.
    Parameters:
    - df_TT: DataFrame contenant les données filtrées par Filter_By_Athlete2(col='race_id', tol=False) -> on ne veut que les courses contenant les 2 athlètes.
    - athletes = ["CHAPUIS Thomas", "BOMPAS Theo"] : les 2 athlètes qu'on veut comparer
    """
    # 1. Créer un dictionnaire {nom_course: date} pour éviter les .iloc[0] répétitifs
    race_date_map = df_TT.groupby('race_name')['race_date'].first().to_dict()
    
    races = df_TT['race_name'].unique()
    rows = []

    for r in races:
        df_race = df_TT[df_TT['race_name'] == r]
        current_race_date = race_date_map.get(r) # Récupération directe

        for name in athletes:
            clean_name = get_clean_key(name)
            t = df_race.loc[df_race['name_key'] == clean_name, 'time']
            name_display = df_race.loc[df_race['name_key'] == clean_name, 'name']

            if not t.empty:
                val_t = t.iloc[0]
                rows.append({
                    "athlete": name,
                    "athlete_display": name_display.iloc[0],
                    "race": r,
                    "race_date": current_race_date,
                    "time_sec": val_t.total_seconds()
                })
    
    df_cumul = pd.DataFrame(rows)
    #st.write(df_cumul.columns)
    #st.write(df_cumul['athlete_display'])

    df_cumul["race_date"] = pd.to_datetime(df_cumul["race_date"])
    df_cumul = df_cumul.sort_values("race_date")

    noms_uniques = df_cumul['athlete_display'].unique()
    titre_dynamique = f"{noms_uniques[0]} vs {noms_uniques[1]}"

    # Formatage HH:MM:SS (vectorisé)
    df_cumul["time_display"] = (
        (df_cumul["time_sec"] // 3600).astype(int).astype(str).str.zfill(2) + ":" +
        ((df_cumul["time_sec"] % 3600) // 60).astype(int).astype(str).str.zfill(2) + ":" +
        (df_cumul["time_sec"] % 60).astype(int).astype(str).str.zfill(2)
    )

    fig1 = px.bar(
        df_cumul,
        x="race",
        y="time_sec",           
        color="athlete",
        barmode="group",
        title=titre_dynamique,
        text="time_display",    
        custom_data=["time_display", 'athlete_display'] 
    )

    fig1.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Course : %{x}<br>Temps : %{customdata[0]}<extra></extra>",        
        textposition='outside'
    )
    
    fig1.update_layout(
        showlegend=False,  # <--- Supprime totalement la légende
        xaxis_title=None,
        yaxis_title=None)
    
    fig1.update_yaxes(showticklabels=False, title=None)
    # On force l'axe X à suivre l'ordre du DataFrame trié
    fig1.update_xaxes(type='category', categoryorder='array', categoryarray=df_cumul['race'].unique())
    fig1.update_layout(xaxis_title=None, legend_title=None)
    
    return fig1

def Viz_Map(df_Synthese):
    fig = px.scatter_geo(
        df_Synthese,
        lat="lat",
        lon="lon",
        hover_name="Race1",
    )

    # ── Style géographique ───────────────────────────
    fig.update_geos(
        scope="europe",
        projection_type="mercator",

        # Fond
        bgcolor="black",
        showland=False,
        showocean=False,
        showlakes=False,

        # Frontières
        showcountries=True,
        countrycolor="white",
        countrywidth=1,

        # Cadre / côtes
        showcoastlines=False,
        showframe=False,

        # Zoom France
        lataxis_range=[41, 51],
        lonaxis_range=[-6, 10],
    )

    # ── Points (courses) ─────────────────────────────
    fig.update_traces(
        marker=dict(
            size=7,
            color="#2ecc71",
            opacity=0.85,
            line=dict(width=0)
        )
    )

    # ── Layout général ───────────────────────────────
    fig.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        margin=dict(l=0, r=0, t=50, b=0),
        font=dict(color="white"),
    )

    return fig

def get_coords(ville):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(ville)
    
    if location:
        return location.latitude, location.longitude
    return None, None

def Viz_Map_Ville(nom_ville):
    latitude, longitude = get_coords(nom_ville)
      
    # 1. Utiliser scatter_geo au lieu de scatter_mapbox
    fig = px.scatter_geo(
        {"lat": [latitude], "lon": [longitude], "ville": [nom_ville]},
        lat="lat",
        lon="lon",
        hover_name="ville",    # Titre en gras dans le hover
        hover_data={           # On définit ce qu'on affiche ou cache
            "lat": False,      # Cache la latitude
            "lon": False,      # Cache la longitude
            "ville": False     # Cache la répétition de la ville sous le titre
        }
    )

    # 2. Configuration géographique (Fonctionne avec scatter_geo)
    fig.update_geos(
        scope="europe",
        projection_type="mercator",
        resolution=50,

        # Fond de carte
        showland=True,
        landcolor="black",      # Terre en noir
        showocean=True,
        oceancolor="black",     # Mer en noir
        showlakes=False,

        # Frontières
        showcountries=True,
        countrycolor="white",   # Frontières en blanc
        countrywidth=1,

        # Zoom sur la France
        lataxis_range=[41, 51],
        lonaxis_range=[-6, 10],
        
        showframe=False,
    )

    # 3. Style visuel du point et du layout
    fig.update_traces(marker=dict(size=15, color="#2ecc71")) # Pour bien voir le point

    fig.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )

    return fig

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
