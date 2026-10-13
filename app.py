"""
Tableau de bord ErgoVeille (Section 9 du cahier des charges).
Deux onglets : Accueil (synthèse) et Bibliothèque (recherche complète).
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
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return []


def load_status():
    if not os.path.exists(STATUS_PATH):
        return None
    try:
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _valeur_date(article, champ):
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
    """Récupère la date de publication réelle d'un article."""
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


def est_rempli(v):
    """Vérifie qu'une valeur est exploitable (non None, non NaN, non vide)."""
    if v is None:
        return False
    try:
        if pd.isna(v):
            return False
    except (TypeError, ValueError):
        pass
    return bool(str(v).strip())


def construire_df(articles):
    df = pd.DataFrame(articles)
    df = df.where(pd.notna(df), None)
    df["date_publication_dt"] = df.apply(get_publication_date, axis=1)
    df["score_pertinence"] = df.apply(score_article, axis=1)
    return df


def afficher_article(article):
    """Affiche une carte d'article formatée."""
    st.markdown(f"### {article.get('titre', 'Sans titre')}")

    meta = []
    for champ, emoji in [("auteurs", "👤"), ("revue", "📰"), ("annee", "📅"), ("source", "🔗")]:
        v = article.get(champ)
        if est_rempli(v):
            meta.append(f"{emoji} {v}")
    if meta:
        st.caption(" | ".join(meta))

    badges = []
    te = article.get("type_etude")
    if est_rempli(te):
        badges.append(f"📋 {te}")
    tags = article.get("tags")
    if tags and isinstance(tags, list):
        badges.extend([f"🏷️ {t}" for t in tags if est_rempli(t)])
    if badges:
        st.markdown(" ".join(badges))

    resume = article.get("resume")
    if est_rempli(resume):
        r = str(resume)
        st.markdown(r[:400] + "..." if len(r) > 400 else r)

    liens = []
    lien = article.get("lien")
    if est_rempli(lien):
        libelle = "PubMed" if article.get("source") == "PubMed" else "Article original"
        liens.append(f"[🔗 {libelle}]({lien})")
    lien_doi = article.get("lien_doi")
    if est_rempli(lien_doi):
        liens.append(f"[📄 DOI]({lien_doi})")
    doi = article.get("doi")
    if est_rempli(doi):
        liens.append(f"**DOI:** `{doi}`")
    if liens:
        st.markdown(" | ".join(liens))

    st.markdown("---")


def main():
    st.title("🧠 ErgoVeille")
    st.header("Tableau de bord de veille scientifique en ergothérapie")

    articles = load_articles()
    status = load_status()

    if not articles:
        st.info("👋 Aucune donnée disponible. Lance `python main.py` pour commencer.")
        return

    df = construire_df(articles)

    # --- Statistiques globales (toujours visibles) ---
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

    # --- Onglets : Accueil / Bibliothèque ---
    tab_accueil, tab_biblio, tab_sources = st.tabs(["🏠 Accueil", "📚 Bibliothèque", "📡 Sources"])

    with tab_accueil:
        st.subheader("🎯 Répartition par thèmes cliniques")
        # Compter les tags (un article peut avoir plusieurs thèmes)
        compteurs = {}
        for tags in df["tags"].dropna():
            if isinstance(tags, list):
                for t in tags:
                    if est_rempli(t):
                        compteurs[t] = compteurs.get(t, 0) + 1
        if compteurs:
            df_themes = (
                pd.DataFrame(list(compteurs.items()), columns=["Thème", "Nombre"])
                .sort_values("Nombre", ascending=True)
            )
            st.bar_chart(df_themes.set_index("Thème"))
            st.caption("Un article peut appartenir à plusieurs thèmes.")
        else:
            st.info("Aucun thème classé pour le moment.")

        st.markdown("---")

        st.subheader("⭐ Publications importantes de la semaine")
        st.caption(
            "Sélection basée sur le score de pertinence documenté "
            "(type d'étude + source + thèmes). Ce score n'est pas un niveau de preuve."
        )
        top = df_recents.sort_values("score_pertinence", ascending=False, na_position="last").head(5)
        if len(top) == 0:
            st.info("Aucune publication importante cette semaine.")
        else:
            for _, a in top.iterrows():
                with st.container():
                    afficher_article(a.to_dict())

        st.markdown("---")

        st.subheader("📰 Dernières actualités sanitaires françaises")
        actu_fr = df[
            df["source"].isin(["HAS (Haute Autorité de Santé)", "Santé publique France - Actualités",
                               "Santé publique France - Communiqués", "ANSM (Actualités)"])
        ].sort_values("date_publication_dt", ascending=False, na_position="last").head(3)
        if len(actu_fr) == 0:
            st.info("Aucune actualité sanitaire française récente.")
        else:
            for _, a in actu_fr.iterrows():
                with st.container():
                    afficher_article(a.to_dict())

    with tab_biblio:
        # --- Sidebar : Filtres (dans l'onglet Bibliothèque) ---
        st.sidebar.header("🔍 Filtres et recherche")

        recherche = st.sidebar.text_input("Rechercher un article...", placeholder="Titre, auteur, résumé...")

        sources = sorted(df["source"].dropna().unique()) if "source" in df.columns else []
        source_choisie = st.sidebar.multiselect("Source", sources, default=sources) if sources else []

        tous_tags = set()
        if "tags" in df.columns:
            for tags in df["tags"].dropna():
                if isinstance(tags, list):
                    tous_tags.update(t for t in tags if est_rempli(t))
        tags_choisis = st.sidebar.multiselect("Thème", sorted(tous_tags))

        types = sorted(df["type_etude"].dropna().unique()) if "type_etude" in df.columns else []
        type_choisi = st.sidebar.multiselect("Type d'étude", types) if types else []

        st.sidebar.subheader("📅 Date de publication")
        dates_valides = df["date_publication_dt"].dropna()
        plage = None
        if len(dates_valides) > 0:
            min_date = dates_valides.min().date()
            max_date = dates_valides.max().date()
            plage = st.sidebar.date_input(
                "Période (AAAA/MM/JJ)",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="Format : année/mois/jour (contrainte Streamlit)"
            )

        filtre_nouveaute = st.sidebar.checkbox("✨ Nouveautés (7 jours)", value=False)

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
            r = recherche.lower()
            mask = (
                df_filtre.get("titre", pd.Series(dtype=str)).str.lower().str.contains(r, na=False) |
                df_filtre.get("resume", pd.Series(dtype=str)).str.lower().str.contains(r, na=False) |
                df_filtre.get("auteurs", pd.Series(dtype=str)).str.lower().str.contains(r, na=False)
            )
            df_filtre = df_filtre[mask]
        if source_choisie:
            df_filtre = df_filtre[df_filtre["source"].isin(source_choisie)]
        if tags_choisis:
            df_filtre = df_filtre[df_filtre["tags"].apply(
                lambda x: any(t in tags_choisis for t in x) if isinstance(x, list) else False)]
        if type_choisi:
            df_filtre = df_filtre[df_filtre["type_etude"].isin(type_choisi)]
        if isinstance(plage, (tuple, list)) and len(plage) == 2:
            debut_plage = pd.Timestamp(plage[0])
            fin_plage = pd.Timestamp(plage[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_filtre = df_filtre[
                (df_filtre["date_publication_dt"] >= debut_plage) &
                (df_filtre["date_publication_dt"] <= fin_plage)
            ]
        if filtre_nouveaute:
            df_filtre = df_filtre[df_filtre["date_publication_dt"] >= sept_jours]

        # Tri
        if tri == "Date de publication (récent → ancien)":
            df_filtre = df_filtre.sort_values("date_publication_dt", ascending=False, na_position="last")
        elif tri == "Date de publication (ancien → récent)":
            df_filtre = df_filtre.sort_values("date_publication_dt", ascending=True, na_position="last")
        else:
            df_filtre = df_filtre.sort_values("score_pertinence", ascending=False, na_position="last")

        st.sidebar.markdown(f"**{len(df_filtre)} article(s) affiché(s)** sur {len(df)}")

        # 🆕 Export CSV des publications filtrées (Section 9)
        colonnes_export = [
            "titre", "auteurs", "revue", "annee", "source", "theme",
            "type_etude", "tags", "doi", "lien", "lien_doi",
            "date_publication", "date_collecte",
        ]
        df_export = df_filtre.copy()
        if "tags" in df_export.columns:
            df_export["tags"] = df_export["tags"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else ""
            )
        df_export = df_export[[c for c in colonnes_export if c in df_export.columns]]
        csv_bytes = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Exporter les publications filtrées en CSV",
            data=csv_bytes,
            file_name=f"ergoveille_export_{datetime.now():%Y-%m-%d}.csv",
            mime="text/csv",
            help="Séparateur point-virgule et encodage UTF-8 BOM : compatible Excel français.",
        )

        st.subheader(f"📚 Articles ({len(df_filtre)})")
        for _, a in df_filtre.iterrows():
            with st.container():
                afficher_article(a.to_dict())


    with tab_sources:
        st.subheader("📡 État des sources surveillées")
        st.caption("Historique des collectes pour chaque source (PubMed et flux RSS).")
        
        # Charger le statut des sources
        sources_status_path = "data/sources_status.json"
        if not os.path.exists(sources_status_path):
            st.warning("Aucune donnée de statut disponible. Lance `python main.py` pour initialiser.")
        else:
            try:
                with open(sources_status_path, "r", encoding="utf-8") as f:
                    sources_status = json.load(f)
                
                if not sources_status:
                    st.info("Aucune source enregistrée pour le moment.")
                else:
                    # Construire un DataFrame pour affichage tableau
                    rows = []
                    for source_name, data in sources_status.items():
                        derniere_tentative = data.get("derniere_tentative", "Jamais")
                        if derniere_tentative != "Jamais":
                            try:
                                dt = pd.to_datetime(derniere_tentative)
                                derniere_tentative = dt.strftime("%d/%m/%Y %H:%M")
                            except Exception:
                                pass
                        
                        derniere_reussite = data.get("derniere_reussite", "Jamais")
                        if derniere_reussite != "Jamais":
                            try:
                                dt = pd.to_datetime(derniere_reussite)
                                derniere_reussite = dt.strftime("%d/%m/%Y %H:%M")
                            except Exception:
                                pass
                        
                        statut = data.get("dernier_statut", "Inconnu")
                        statut_display = "✅ OK" if statut == "OK" else "❌ Erreur"
                        
                        nb_articles = data.get("dernier_nb_articles", 0)
                        message_erreur = data.get("dernier_message_erreur", "")
                        
                        rows.append({
                            "Source": source_name,
                            "Dernière tentative": derniere_tentative,
                            "Dernière réussite": derniere_reussite,
                            "Nb articles": nb_articles,
                            "Statut": statut_display,
                            "Message d'erreur": message_erreur if message_erreur else "",
                        })
                    
                    df_sources = pd.DataFrame(rows)
                    st.dataframe(df_sources, width='stretch', hide_index=True)
                    
                    # Statistiques globales
                    nb_sources = len(sources_status)
                    nb_ok = sum(1 for d in sources_status.values() if d.get("dernier_statut") == "OK")
                    st.caption(f"**{nb_ok}/{nb_sources} sources** en statut OK lors de la dernière collecte.")
                    
            except Exception as e:
                st.error(f"Erreur lors du chargement du statut des sources : {e}")


if __name__ == "__main__":
    main()