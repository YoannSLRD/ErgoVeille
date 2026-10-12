"""
Tableau de bord ErgoVeille (Section 9 du cahier des charges).
Affiche les articles collectés avec filtres et recherche.
"""

import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="ErgoVeille",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_PATH = "data/articles.json"
STATUS_PATH = "data/collect_status.json"


def load_articles():
    """Charge les articles depuis le fichier JSON."""
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return []


def load_status():
    """Charge le statut de la dernière collecte."""
    if not os.path.exists(STATUS_PATH):
        return None
    try:
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_publication_date(article):
    """
    Récupère la date de publication réelle d'un article.
    Retourne une date "naive" (sans fuseau horaire) pour éviter les erreurs de comparaison.
    Priorité : date_publication (RSS) > date_collecte > annee (PubMed).
    """
    # 1. Date de publication explicite (articles RSS)
    if article.get("date_publication"):
        try:
            dt = pd.to_datetime(article["date_publication"], errors="coerce")
            # Retirer le fuseau horaire si présent
            if dt is not pd.NaT and dt.tzinfo is not None:
                dt = dt.tz_localize(None)
            return dt
        except Exception:
            pass
    
    # 2. Date de collecte (fallback)
    if article.get("date_collecte"):
        try:
            dt = pd.to_datetime(article["date_collecte"], errors="coerce")
            if dt is not pd.NaT and dt.tzinfo is not None:
                dt = dt.tz_localize(None)
            return dt
        except Exception:
            pass
    
    # 3. Année seulement (articles PubMed anciens)
    if article.get("annee"):
        try:
            annee = str(article["annee"])
            if annee.isdigit() and len(annee) == 4:
                return pd.to_datetime(f"{annee}-01-01", errors="coerce")
        except Exception:
            pass
    
    return pd.NaT


def main():
    # En-tête
    st.title("🧠 ErgoVeille")
    st.header("Tableau de bord de veille scientifique en ergothérapie")
    
    # Chargement des données
    articles = load_articles()
    status = load_status()
    
    if not articles:
        st.info("👋 Aucune donnée disponible. Lance la collecte avec `python main.py` pour commencer.")
        return
    
    # Conversion en DataFrame
    df = pd.DataFrame(articles)
    
    # Ajout de la colonne "date_publication_dt" basée sur la vraie date de publication
    df["date_publication_dt"] = df.apply(get_publication_date, axis=1)
    
    # --- Statistiques ---
    col1, col2, col3 = st.columns(3)
    col1.metric(label="📚 Articles collectés", value=len(df))
    
    # Nouveautés : articles dont la date de publication est dans les 7 derniers jours
    sept_jours = datetime.now() - pd.Timedelta(days=7)
    df_recents = df[df["date_publication_dt"] >= sept_jours]
    col2.metric(label="✨ Nouveautés (7 jours)", value=len(df_recents))
    
    # Sources uniques
    sources_uniques = df["source"].nunique() if "source" in df.columns else 0
    col3.metric(label="🏥 Sources surveillées", value=sources_uniques)
    
    # Date de dernière collecte réussie
    if status and status.get("last_run"):
        try:
            last_run = pd.to_datetime(status["last_run"])
            st.caption(f"Dernière collecte réussie : {last_run.strftime('%d/%m/%Y à %H:%M')}")
        except Exception:
            pass
    
    st.markdown("---")
    
    # --- Sidebar : Filtres ---
    st.sidebar.header(" Filtres et recherche")
    
    # Recherche textuelle
    recherche = st.sidebar.text_input("Rechercher un article...", placeholder="Titre, auteur, résumé...")
    
    # Filtre par source
    if "source" in df.columns:
        sources = sorted(df["source"].dropna().unique())
        source_choisie = st.sidebar.multiselect("Source", sources, default=sources)
    else:
        source_choisie = []
    
    # Filtre par thème (tags)
    if "tags" in df.columns:
        tous_tags = set()
        for tags in df["tags"].dropna():
            if isinstance(tags, list):
                tous_tags.update(tags)
        tags_choisis = st.sidebar.multiselect("Thème", sorted(tous_tags))
    else:
        tags_choisis = []
    
    # Filtre par type d'étude
    if "type_etude" in df.columns:
        types = sorted(df["type_etude"].dropna().unique())
        type_choisi = st.sidebar.multiselect("Type d'étude", types)
    else:
        type_choisi = []
    
    # Filtre par nouveauté (7 derniers jours)
    filtre_nouveaute = st.sidebar.checkbox("✨ Afficher uniquement les nouveautés (7 jours)", value=False)
    
    # --- Application des filtres ---
    df_filtre = df.copy()
    
    if recherche:
        recherche_lower = recherche.lower()
        mask = (
            df_filtre.get("titre", pd.Series(dtype=str)).str.lower().str.contains(recherche_lower, na=False) |
            df_filtre.get("resume", pd.Series(dtype=str)).str.lower().str.contains(recherche_lower, na=False) |
            df_filtre.get("auteurs", pd.Series(dtype=str)).str.lower().str.contains(recherche_lower, na=False)
        )
        df_filtre = df_filtre[mask]
    
    if source_choisie:
        df_filtre = df_filtre[df_filtre["source"].isin(source_choisie)]
    
    if tags_choisis:
        df_filtre = df_filtre[df_filtre["tags"].apply(lambda x: any(t in tags_choisis for t in x) if isinstance(x, list) else False)]
    
    if type_choisi:
        df_filtre = df_filtre[df_filtre["type_etude"].isin(type_choisi)]
    
    if filtre_nouveaute:
        df_filtre = df_filtre[df_filtre["date_publication_dt"] >= sept_jours]
    
    st.sidebar.markdown(f"**{len(df_filtre)} article(s) affiché(s)** sur {len(df)}")
    
    # --- Affichage des articles ---
    st.subheader(f" Articles ({len(df_filtre)})")
    
    for _, article in df_filtre.iterrows():
        with st.container():
            st.markdown(f"### {article.get('titre', 'Sans titre')}")
            
            # Métadonnées
            meta = []
            if article.get("auteurs"):
                meta.append(f"👤 {article['auteurs']}")
            if article.get("revue"):
                meta.append(f"📰 {article['revue']}")
            if article.get("annee"):
                meta.append(f"📅 {article['annee']}")
            if article.get("source"):
                meta.append(f"🔗 {article['source']}")
            if meta:
                st.caption(" | ".join(meta))
            
            # Badges
            badges = []
            if article.get("type_etude"):
                badges.append(f" {article['type_etude']}")
            if article.get("tags"):
                badges.extend([f"🏷️ {tag}" for tag in article["tags"]])
            if badges:
                st.markdown(" ".join(badges))
            
            # Résumé
            if article.get("resume"):
                st.markdown(article["resume"][:400] + "..." if len(article["resume"]) > 400 else article["resume"])
            
            # Lien
            if article.get("lien"):
                st.markdown(f"[🔗 Lire la publication originale]({article['lien']})")
            
            st.markdown("---")


if __name__ == "__main__":
    main()