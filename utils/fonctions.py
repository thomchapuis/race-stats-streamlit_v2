import pandas as pd
import unicodedata
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import numpy as np

# ---------------------------------------------------------------------------------------
# 🔹 Fonction de Viz
# ---------------------------------------------------------------------------------------
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

    # 4. Tracé de l'histogramme
    fig = px.histogram(
        df,
        x="col_min",
        title=f"Distribution des temps : {race_name} | {col}",
        labels={'col_min': 'Temps', 'count': 'Nombre de coureurs'},
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
        xaxis_title="Temps",
        yaxis_title="Nombre de coureurs",
        showlegend=False,
        template='plotly_dark'
    )

     # 9. Ajout d'un "sous-titre"
    if len(temps)=1
        texte_annotation = "\n".join([f"{k} : {v}" for k, v in temps_dict.items()])
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


def Viz_Radar_Triathlon(df, names_list):
    # 1. Identifier les courses et filtrer celles qui ont les colonnes nécessaires
    required_cols = ['swim', 'bike', 'run']
    # On ne garde que les courses qui ont au moins une valeur non nulle dans ces colonnes
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
        title_text="Analyse Multi-Courses (Uniquement courses avec Splits complets)",
        template='plotly_dark'
    )
    #return fig.show() pour notebook .ipynb
    return fig   #pour streamlit

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
# ---------------------------------------------------------------------------------------
# 🔹 Fonction de Filtre
# ---------------------------------------------------------------------------------------

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

def Filter_By_Race(df, race):
    """
    Filtre le DataFrame pour une ou plusieurs courses.
    'race' peut être un string "EDT23" ou une liste ["EDT23", "EDT25"].
    """
    #Extraction de l'année et filtrage
    if isinstance(race, list):
        # Si on passe une liste d'années
        mask = df['race_name'].isin(race)
    else:
        # Si on passe une seule année
        mask = df['race_name'] == race

    result = df[mask].reset_index(drop=True)

    if len(result) == 0:
        print(f"⚠️ Aucun résultat pour : {race}. Valeurs disponibles : {df['race_name'].unique()[:5]}")

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
    race_stats = df[mask_athletes].groupby('race_name')['name_key'].nunique()
    valid_races = race_stats[race_stats == num_required].index
    result = df[df['race_name'].isin(valid_races)].reset_index(drop=True)

    return result

# ---------------------------------------------------------------------------------------
# 🔹 Fonction de Calcul
# ---------------------------------------------------------------------------------------

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

