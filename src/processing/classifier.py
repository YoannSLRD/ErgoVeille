"""Module de classification ErgoVeille (Section 7 du cahier des charges).

Responsabilités :
- Classifier chaque article par thème clinique (mots-clés configurables).
- Déterminer le type d'étude :
    1. D'après les métadonnées officielles PubMed (PublicationType) : fiable.
    2. À défaut, par mots-clés titre/résumé : signalé comme "à confirmer".
    3. Sinon : catégorie "Type d'étude à vérifier" (on n'invente jamais).

Rappel méthodologique : le type d'étude n'est PAS un niveau de preuve.
"""

import json
import os
from collections import Counter

import yaml
from Bio import Entrez

CONFIG_PATH = "config/config.yaml"
DATA_PATH = "data/articles.json"

# Métadonnées officielles PubMed -> nos catégories.
# L'ordre du dictionnaire définit la priorité (du plus précis au plus général).
PUBMED_TYPE_MAP = {
    "Randomized Controlled Trial": "Essai contrôlé randomisé",
    "Meta-Analysis": "Méta-analyse",
    "Systematic Review": "Revue systématique",
    "Practice Guideline": "Recommandations professionnelles",
    "Clinical Trial": "Essai clinique",
    "Observational Study": "Étude observationnelle",
    "Qualitative Research": "Étude qualitative",
    "Validation Study": "Étude psychométrique / de validation",
    "Review": "Revue narrative",
}

# Mots-clés de repli (titre + résumé). Détection PROBABLE, jamais certaine.
KEYWORD_TYPE_MAP = {
    "Essai contrôlé randomisé": ["randomized controlled trial", "randomised controlled trial"],
    "Méta-analyse": ["meta-analysis", "meta analysis"],
    "Revue systématique": ["systematic review"],
    "Recommandations professionnelles": ["clinical practice guideline", "consensus statement"],
    "Étude qualitative": ["qualitative study", "qualitative research", "focus group", "semi-structured interviews"],
    "Étude psychométrique / de validation": ["psychometric", "validation study", "test-retest reliability", "internal consistency"],
    "Étude observationnelle": ["cross-sectional", "cohort study", "case-control"],
}

TYPE_A_VERIFIER = "Type d'étude à vérifier"


def load_config():
    """Charge la feuille de mission YAML."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def classify_themes(text, categories):
    """Retourne les thèmes cliniques détectés dans un texte."""
    text = text.lower()
    return [
        theme
        for theme, keywords in categories.items()
        if any(kw.lower() in text for kw in keywords)
    ]


def classify_study_type(pubmed_types, text):
    """Détermine le type d'étude d'un article (voir docstring du module)."""
    type_set = set(pubmed_types or [])
    for pubmed_label, notre_label in PUBMED_TYPE_MAP.items():
        if pubmed_label in type_set:
            return notre_label

    text = text.lower()
    for notre_label, keywords in KEYWORD_TYPE_MAP.items():
        if any(kw in text for kw in keywords):
            return f"{notre_label} (détection par mots-clés, à confirmer)"

    return TYPE_A_VERIFIER


def classify_article(article, categories):
    """Met à jour les champs 'tags' et 'type_etude' d'un article."""
    text = f"{article.get('titre', '')} {article.get('resume', '')}"
    article["tags"] = classify_themes(text, categories)
    article["type_etude"] = classify_study_type(article.get("types_pubmed"), text)
    return article


def fetch_missing_pubmed_types(articles):
    """Complète en UNE seule requête groupée les métadonnées manquantes."""
    missing = [a["pmid"] for a in articles if "types_pubmed" not in a or not a["types_pubmed"]]
    if not missing:
        return articles

    print(f"📥 Récupération des métadonnées PubMed pour {len(missing)} articles...")
    handle = Entrez.efetch(db="pubmed", id=",".join(missing), retmode="xml")
    xml_data = Entrez.read(handle)
    handle.close()

    types_par_pmid = {}
    for art in xml_data["PubmedArticle"]:
        pmid = str(art["MedlineCitation"]["PMID"])
        types = []
        # 🧠 CORRECTION : Chercher dans Article, pas dans PubmedData
        article_data = art["MedlineCitation"]["Article"]
        if "PublicationTypeList" in article_data:
            types = [str(pt) for pt in article_data["PublicationTypeList"]]
        types_par_pmid[pmid] = types

    for a in articles:
        if a["pmid"] in types_par_pmid:
            a["types_pubmed"] = types_par_pmid[a["pmid"]]
    return articles


def reprocess_database():
    """Retraite toute la base locale : thèmes + types d'étude, sans rien effacer."""
    config = load_config()
    categories = config.get("categories", {})
    Entrez.email = config["pubmed"]["email"]
    Entrez.tool = config["pubmed"]["tool"]

    if not os.path.exists(DATA_PATH):
        print(f"❌ Base introuvable : {DATA_PATH}. Lance d'abord une collecte.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    articles = fetch_missing_pubmed_types(articles)
    for article in articles:
        classify_article(article, categories)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    repartition = Counter(a["type_etude"] for a in articles)
    print(f"✅ Base retraitée : {len(articles)} articles classifiés.")
    print("📊 Répartition par type d'étude :")
    for label, count in repartition.most_common():
        print(f"   - {label} : {count}")


if __name__ == "__main__":
    print("🧠 Retraitement de la base locale (classification Section 7)...")
    reprocess_database()