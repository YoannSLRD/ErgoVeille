"""
Tableau de bord ErgoVeille (Section 9 du cahier des charges).
Affiche les articles collectés avec filtres, tri et recherche.
"""

import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from src.newsletter.builder import score_article

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


def _valeur_date(article, champ):
    """Retourne la valeur brute d'un champ de date uniquement si elle est exploitable."""
    v = article.get(champ)
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    v = str(v).strip()
    return v or None


def get_publication_date(article):
    """
    Récupère la date de publication réelle d'un article.
    Priorité : date_publication (RSS/PubMed enrichi) > date_collecte > annee.
    Retourne une date "naive" (sans fuseau horaire).
    """
    for champ in ("date_publication", "date_collecte"):
        v = _valeur_date(article, champ)
        if v:
            dt = pd.to_datetime(v, errors="coerce")
            if dt is not pd.NaT:
                if dt.tzinfo is not None:
                    dt = dt.tz_localize(None)
                return dt

    annee = _valeur_date(article, "annee")
    if annee and annee.isdigit() and len(annee) == 4:
        return pd.to_datetime(f"{annee}-01-01", errors="coerce")

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
    # Remplace les valeurs manquantes (NaN) par None pour un affichage propre
    df = df.where(pd.notna(df), None)
    df["date_publication_dt"] = df.apply(get_publication_date, axis=1)
    df["score_pertinence"] = df.apply(score_article, axis=1)

    # --- Statistiques ---
    col1, col2, col3 = st.columns(3)
    col1.metric(label="📚 Articles collectés", value=len(df))

    sept_jours = datetime.now() - pd.Timedelta(days=7)
    df_recents = df[df["date_publication_dt"] >= sept_jours]
    col2.metric(label="✨ Nouveautés (7 jours)", value=len(df_recents))

    sources_uniques = df["source"].nunique() if "source" in df.columns else 0
    col3.metric(label="🏥 Sources surveillées", value=sources_uniques)

    if status and status.get("last_run"):
        try:
            last_run = pd.to_datetime(status["last_run"])
            st.caption(f"Dernière collecte réussie : {last_run.strftime('%d/%m/%Y à %H:%M')}")
        except Exception:
            pass

    st.markdown("---")

    # --- Sidebar : Filtres ---
    st.sidebar.header("🔍 Filtres et recherche")

    recherche = st.sidebar.text_input("Rechercher un article...", placeholder="Titre, auteur, résumé...")

    if "source" in df.columns:
        sources = sorted(df["source"].dropna().unique())
        source_choisie = st.sidebar.multiselect("Source", sources, default=sources)
    else:
        source_choisie = []

    if "tags" in df.columns:
        tous_tags = set()
        for tags in df["tags"].dropna():
            if isinstance(tags, list):
                tous_tags.update(tags)
        tags_choisis = st.sidebar.multiselect("Thème", sorted(tous_tags))
    else:
        tags_choisis = []

    if "type_etude" in df.columns:
        types = sorted(df["type_etude"].dropna().unique())
        type_choisi = st.sidebar.multiselect("Type d'étude", types)
    else:
        type_choisi = []

    # 🆕 Filtre par plage de dates de publication
    st.sidebar.subheader("📅 Date de publication")
    dates_valides = df["date_publication_dt"].dropna()
    plage = None
    if len(dates_valides) > 0:
        min_date = dates_valides.min().date()
        max_date = dates_valides.max().date()
        plage = st.sidebar.date_input(
            "Période",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    filtre_nouveaute = st.sidebar.checkbox("✨ Afficher uniquement les nouveautés (7 jours)", value=False)

    # 🆕 Tri
    tri = st.sidebar.selectbox(
        "Trier par",
        [
            "Date de publication (récent → ancien)",
            "Date de publication (ancien → récent)",
            "Pertinence (score expliqué)",
        ],
    )

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

    # 🆕 Application de la plage de dates (uniquement si les deux bornes sont choisies)
    if isinstance(plage, (tuple, list)) and len(plage) == 2:
        debut_plage = pd.Timestamp(plage[0])
        fin_plage = pd.Timestamp(plage[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtre = df_filtre[
            (df_filtre["date_publication_dt"] >= debut_plage) &
            (df_filtre["date_publication_dt"] <= fin_plage)
        ]

    if filtre_nouveaute:
        df_filtre = df_filtre[df_filtre["date_publication_dt"] >= sept_jours]

    # 🆕 Application du tri
    if tri == "Date de publication (récent → ancien)":
        df_filtre = df_filtre.sort_values("date_publication_dt", ascending=False, na_position="last")
    elif tri == "Date de publication (ancien → récent)":
        df_filtre = df_filtre.sort_values("date_publication_dt", ascending=True, na_position="last")
    else:
        df_filtre = df_filtre.sort_values("score_pertinence", ascending=False, na_position="last")

    st.sidebar.markdown(f"**{len(df_filtre)} article(s) affiché(s)** sur {len(df)}")

    # --- Affichage des articles ---
    st.subheader(f"📚 Articles ({len(df_filtre)})")

    for _, article in df_filtre.iterrows():
        with st.container():
            st.markdown(f"### {article.get('titre', 'Sans titre')}")

            # Métadonnées (vérification robuste contre None et chaînes vides)
            meta = []
            auteurs = article.get("auteurs")
            if auteurs and pd.notna(auteurs) and str(auteurs).strip():
                meta.append(f"👤 {auteurs}")
            revue = article.get("revue")
            if revue and pd.notna(revue) and str(revue).strip():
                meta.append(f"📰 {revue}")
            annee = article.get("annee")
            if annee and pd.notna(annee) and str(annee).strip():
                meta.append(f"📅 {annee}")
            source = article.get("source")
            if source and pd.notna(source) and str(source).strip():
                meta.append(f"🔗 {source}")
            if meta:
                st.caption(" | ".join(meta))

            # Badges
            badges = []
            type_etude = article.get("type_etude")
            if type_etude and pd.notna(type_etude) and str(type_etude).strip():
                badges.append(f"📋 {type_etude}")
            tags = article.get("tags")
            if tags and isinstance(tags, list):
                badges.extend([f"🏷️ {tag}" for tag in tags if tag and pd.notna(tag)])
            if badges:
                st.markdown(" ".join(badges))

            # Résumé
            resume = article.get("resume")
            if resume and pd.notna(resume) and str(resume).strip():
                resume_str = str(resume)
                st.markdown(resume_str[:400] + "..." if len(resume_str) > 400 else resume_str)

            # Liens (PubMed / source + DOI)
            liens = []
            lien = article.get("lien")
            if lien and pd.notna(lien) and str(lien).strip():
                libelle = "PubMed" if article.get("source") == "PubMed" else "Article original"
                liens.append(f"[🔗 {libelle}]({lien})")
            lien_doi = article.get("lien_doi")
            if lien_doi and pd.notna(lien_doi) and str(lien_doi).strip():
                liens.append(f"[📄 DOI]({lien_doi})")
            doi = article.get("doi")
            if doi and pd.notna(doi) and str(doi).strip():
                liens.append(f"**DOI:** `{doi}`")
            if liens:
                st.markdown(" | ".join(liens))

            st.markdown("---")


if __name__ == "__main__":
    main()