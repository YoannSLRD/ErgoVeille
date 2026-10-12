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


def main():
    # En-tête
    st.title("🧠 ErgoVeille")
    st.header("Tableau de bord de veille scientifique en ergothérapie")
    
    # Chargement des données
    articles = load_articles()
    
    if not articles:
        st.info("👋 Aucune donnée disponible. Lance la collecte avec `python main.py` pour commencer.")
        return
    
    # Conversion en DataFrame pour faciliter les filtres
    df = pd.DataFrame(articles)
    
    # --- Statistiques ---
    col1, col2, col3 = st.columns(3)
    col1.metric(label="📚 Articles collectés", value=len(df))
    
    # Nouveautés (7 derniers jours)
    if "date_collecte" in df.columns:
        df["date_collecte_dt"] = pd.to_datetime(df["date_collecte"], errors="coerce")
        sept_jours = datetime.now() - pd.Timedelta(days=7)
        nouveaux = df[df["date_collecte_dt"] >= sept_jours]
        col2.metric(label="✨ Nouveautés (7 jours)", value=len(nouveaux))
    else:
        col2.metric(label="✨ Nouveautés (7 jours)", value=0)
    
    # Sources uniques
    sources_uniques = df["source"].nunique() if "source" in df.columns else 0
    col3.metric(label="🏥 Sources surveillées", value=sources_uniques)
    
    st.markdown("---")
    
    # --- Sidebar : Filtres ---
    st.sidebar.header("🔍 Filtres et recherche")
    
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
    
    # --- Application des filtres ---
    df_filtre = df.copy()
    
    if recherche:
        recherche_lower = recherche.lower()
        mask = (
            df_filtre.get("titre", "").str.lower().str.contains(recherche_lower, na=False) |
            df_filtre.get("resume", "").str.lower().str.contains(recherche_lower, na=False) |
            df_filtre.get("auteurs", "").str.lower().str.contains(recherche_lower, na=False)
        )
        df_filtre = df_filtre[mask]
    
    if source_choisie:
        df_filtre = df_filtre[df_filtre["source"].isin(source_choisie)]
    
    if tags_choisis:
        df_filtre = df_filtre[df_filtre["tags"].apply(lambda x: any(t in tags_choisis for t in x) if isinstance(x, list) else False)]
    
    if type_choisi:
        df_filtre = df_filtre[df_filtre["type_etude"].isin(type_choisi)]
    
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
                badges.append(f"📋 {article['type_etude']}")
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