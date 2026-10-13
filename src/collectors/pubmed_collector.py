"""
Collecteur PubMed pour ErgoVeille.
Interroge l'API officielle E-utilities avec PLUSIEURS requêtes thématiques,
configurables dans config/config.yaml (Section 5 du cahier des charges).
"""

import os
import json
import time
import yaml
from datetime import datetime, timedelta
from Bio import Entrez

CONFIG_PATH = 'config/config.yaml'
DATA_PATH = 'data/articles.json'


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_article(article, theme_nom, categories):
    """Transforme un article XML PubMed en dictionnaire normalisé."""
    medline = article['MedlineCitation']
    art_data = medline['Article']

    # Gestion robuste du PMID (peut être absent pour articles très récents)
    pmid = str(medline.get('PMID', ''))
    if not pmid:
        elocation = art_data.get('ELocationID', [])
        if elocation and len(elocation) > 0:
            pmid = f"no_pmid_{str(elocation[0])}"
        else:
            pmid = f"no_pmid_{datetime.now().timestamp()}"

    titre = art_data.get('ArticleTitle', 'Sans titre')

    auteurs_list = []
    if 'AuthorList' in art_data:
        for author in art_data['AuthorList']:
            if 'LastName' in author and 'ForeName' in author:
                auteurs_list.append(f"{author['LastName']} {author['ForeName']}")
    auteurs = ", ".join(auteurs_list) if auteurs_list else "Non spécifiés"

    journal = "Inconnue"
    annee = "Inconnue"
    if 'Journal' in art_data:
        journal = art_data['Journal'].get('Title', 'Inconnue')
        try:
            annee = art_data['Journal']['JournalIssue']['PubDate'].get('Year', 'Inconnue')
        except KeyError:
            pass

    resume = ""
    if 'Abstract' in art_data and 'AbstractText' in art_data['Abstract']:
        abs_text = art_data['Abstract']['AbstractText']
        if isinstance(abs_text, list):
            resume = " ".join(str(a) for a in abs_text)
        else:
            resume = str(abs_text)

    types_pubmed = []
    if 'PublicationTypeList' in art_data:
        types_pubmed = [str(pt) for pt in art_data['PublicationTypeList']]

    # 🆕 Extraction du DOI (identifiant permanent)
    doi = ""
    # Méthode 1 : ELocationID dans Article
    elocations = art_data.get('ELocationID', [])
    if isinstance(elocations, list):
        for eloc in elocations:
            if hasattr(eloc, 'attributes') and eloc.attributes.get('EIdType') == 'doi':
                doi = str(eloc)
                break
    elif isinstance(elocations, dict):
        if elocations.get('attributes', {}).get('EIdType') == 'doi':
            doi = str(elocations.get('data', ''))
    
    # Méthode 2 : ArticleIdList dans PubmedData (fallback)
    if not doi and 'PubmedData' in article:
        article_ids = article['PubmedData'].get('ArticleIdList', [])
        if isinstance(article_ids, list):
            for aid in article_ids:
                if hasattr(aid, 'attributes') and aid.attributes.get('IdType') == 'doi':
                    doi = str(aid)
                    break

    # Classification automatique par mots-clés
    tags = []
    texte = (titre + " " + resume).lower()
    for categorie, mots_cles in categories.items():
        for mot_cle in mots_cles:
            if mot_cle.lower() in texte:
                if categorie not in tags:
                    tags.append(categorie)
                break

    lien = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid.isdigit() else ""
    lien_doi = f"https://doi.org/{doi}" if doi else ""

    return {
        "pmid": pmid,
        "id_unique": pmid,
        "titre": titre,
        "auteurs": auteurs,
        "revue": journal,
        "annee": annee,
        "resume": resume,
        "types_pubmed": types_pubmed,
        "doi": doi,  # 🆕 Ajouté
        "tags": tags,
        "source": "PubMed",
        "theme": theme_nom,
        "date_collecte": datetime.now().isoformat(),
        "lien": lien,
        "lien_doi": lien_doi,  # 🆕 Ajouté
    }


def collect_and_save():
    config = load_config()
    pubmed_cfg = config['pubmed']
    requetes = config.get('requetes', [])
    categories = config.get('categories', {})

    Entrez.email = pubmed_cfg['email']
    Entrez.tool = pubmed_cfg['tool']

    days = pubmed_cfg.get('jours_retroactifs', 30)
    datetoday = datetime.now()
    datestart = datetoday - timedelta(days=days)
    mindate = datestart.strftime('%Y/%m/%d')
    maxdate = datetoday.strftime('%Y/%m/%d')

    print(f"📅 Période analysée : du {mindate} au {maxdate}")
    print(f"🔎 {len(requetes)} requête(s) thématique(s) à interroger.")

    nouveaux_articles = []
    bilan = {"requetes_ok": 0, "requetes_erreur": 0, "trouves": 0}

    for i, query_cfg in enumerate(requetes, 1):
        nom = query_cfg.get('nom', f'Requête {i}')
        termes = query_cfg.get('termes', '')
        retmax = int(query_cfg.get('retmax', pubmed_cfg.get('retmax', 25)))

        print(f"\n🔍 [{i}/{len(requetes)}] Thème : '{nom}'")
        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=termes,
                retmax=retmax,
                mindate=mindate,
                maxdate=maxdate,
                datetype="pdat"
            )
            record = Entrez.read(handle)
            handle.close()
            time.sleep(0.4)  # Respect du débit NCBI (3 requêtes/seconde max)

            id_list = record["IdList"]
            total = int(record["Count"])
            print(f"   📊 {total} article(s) au total, récupération de {len(id_list)}...")
            bilan["trouves"] += len(id_list)

            if not id_list:
                bilan["requetes_ok"] += 1
                continue

            handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
            xml_data = Entrez.read(handle)
            handle.close()
            time.sleep(0.4)

            for article in xml_data['PubmedArticle']:
                nouveaux_articles.append(extract_article(article, nom, categories))

            bilan["requetes_ok"] += 1

        except Exception as e:
            # Une requête en échec ne bloque pas les autres (Section 6)
            print(f"   ❌ Erreur sur la requête '{nom}' : {e}")
            bilan["requetes_erreur"] += 1

    # Sauvegarde + dédoublonnage (une seule fois pour toutes les requêtes)
    os.makedirs('data', exist_ok=True)
    existing_articles = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            existing_articles = json.load(f)

    for art in existing_articles:
        if 'id_unique' not in art:
            if 'pmid' in art:
                art['id_unique'] = art['pmid']
            elif 'lien' in art:
                art['id_unique'] = art['lien']
            else:
                art['id_unique'] = f"unknown_{hash(str(art))}"

    existing_ids = {art['id_unique'] for art in existing_articles}
    added = 0
    for art in nouveaux_articles:
        if art['id_unique'] not in existing_ids:
            existing_articles.append(art)
            existing_ids.add(art['id_unique'])
            added += 1

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing_articles, f, ensure_ascii=False, indent=4)

    ignored = len(nouveaux_articles) - added
    print("\n💾 Bilan de la collecte PubMed multi-requêtes :")
    print(f"   - Requêtes réussies : {bilan['requetes_ok']}/{len(requetes)}")
    print(f"   - Requêtes en erreur : {bilan['requetes_erreur']}")
    print(f"   - Articles analysés : {len(nouveaux_articles)}")
    print(f"   - NOUVEAUX ajoutés : {added}")
    print(f"   - Doublons ignorés : {ignored}")
    print(f"   - Total en base : {len(existing_articles)}")


if __name__ == "__main__":
    print("🚀 Démarrage du collecteur PubMed multi-requêtes...")
    collect_and_save()