"""
Collecteur PubMed pour ErgoVeille.
Récupère les articles scientifiques via l'API E-utilities de PubMed.
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from Bio import Entrez

def collect_and_save():
    # 1. Charger la configuration
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        print(f"❌ Erreur : Le fichier {config_path} est introuvable.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    pubmed_cfg = config['pubmed']
    query_cfg = config['requetes'][0] 
    categories = config.get('categories', {})
    
    # 2. Configurer l'API PubMed
    Entrez.email = pubmed_cfg['email']
    Entrez.tool = pubmed_cfg['tool']
    
    # 3. Préparer les dates
    days = pubmed_cfg.get('jours_retroactifs', 30)
    datetoday = datetime.now()
    datestart = datetoday - timedelta(days=days)
    
    mindate = datestart.strftime('%Y/%m/%d')
    maxdate = datetoday.strftime('%Y/%m/%d')
    
    print(f"🔍 Interrogation de PubMed pour le thème : '{query_cfg['nom']}'")
    print(f"📅 Période analysée : du {mindate} au {maxdate}")
    
    try:
        # 4. ESearch
        handle = Entrez.esearch(
            db="pubmed", 
            term=query_cfg['termes'], 
            retmax=pubmed_cfg['retmax'],
            mindate=mindate,
            maxdate=maxdate,
            datetype="pdat"
        )
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        total_count = int(record["Count"])
        print(f"📊 {total_count} articles trouvés au total. Récupération des {len(id_list)} plus récents...")
        
        if not id_list:
            print("✅ Aucun nouvel article trouvé pour cette période.")
            return
            
        # 5. EFetch
        handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
        xml_data = Entrez.read(handle)
        handle.close()
        
        # 6. Extraction et Classification
        nouveaux_articles = []
        for article in xml_data['PubmedArticle']:
            medline = article['MedlineCitation']
            art_data = medline['Article']
            
            # 🛡️ Gestion robuste du PMID (peut être absent pour articles très récents)
            pmid = str(medline.get('PMID', ''))
            if not pmid:
                elocation = art_data.get('ELocationID', [])
                if elocation and len(elocation) > 0:
                    pmid = f"no_pmid_{str(elocation[0])}"
                else:
                    pmid = f"no_pmid_{datetime.now().timestamp()}"
                print(f"   ⚠️  Article sans PMID, ID alternatif : {pmid}")
            
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
            
            # Extraction des PublicationTypes
            types_pubmed = []
            if 'PublicationTypeList' in art_data:
                types_pubmed = [str(pt) for pt in art_data['PublicationTypeList']]
            
            # Classification automatique par mots-clés
            tags = []
            texte_a_analyser = (titre + " " + resume).lower()
            for categorie, mots_cles in categories.items():
                for mot_cle in mots_cles:
                    if mot_cle.lower() in texte_a_analyser:
                        if categorie not in tags:
                            tags.append(categorie)
                        break
            
            lien_pubmed = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid.isdigit() else ""
            
            nouveaux_articles.append({
                "pmid": pmid,
                "id_unique": pmid,  # ✅ Identifiant universel
                "titre": titre,
                "auteurs": auteurs,
                "revue": journal,
                "annee": annee,
                "resume": resume,
                "types_pubmed": types_pubmed,
                "tags": tags,
                "source": "PubMed",
                "theme": query_cfg['nom'],
                "date_collecte": datetime.now().isoformat(),
                "lien": lien_pubmed
            })
            
        # 7. Sauvegarde et Dédoublonnage
        os.makedirs('data', exist_ok=True)
        filepath = 'data/articles.json'
        
        existing_articles = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        
        # 🛡️ CORRECTION : Migration des anciens articles sans id_unique
        for art in existing_articles:
            if 'id_unique' not in art:
                if 'pmid' in art:
                    art['id_unique'] = art['pmid']
                elif 'lien' in art:
                    art['id_unique'] = art['lien']
                else:
                    art['id_unique'] = f"unknown_{hash(str(art))}"
        
        # ✅ Dédoublonnage par id_unique (fonctionne pour PubMed ET RSS)
        existing_ids = {art['id_unique'] for art in existing_articles}
        added_count = 0
        
        for art in nouveaux_articles:
            if art['id_unique'] not in existing_ids:
                existing_articles.append(art)
                added_count += 1
                
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=4)
            
        # Bilan précis
        ignored_count = len(nouveaux_articles) - added_count
        print(f"💾 Bilan de la collecte :")
        print(f"   - {len(nouveaux_articles)} articles analysés dans le lot.")
        print(f"   - {added_count} NOUVEAUX articles ajoutés à ta base.")
        print(f"   - {ignored_count} articles déjà connus (doublons ignorés).")
        print(f"   - Total en base : {len(existing_articles)} articles.")
        print(f"✅ Sauvegarde et classification réussies dans {filepath}")

    except Exception as e:
        print(f"❌ Erreur lors de la collecte PubMed : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Démarrage du collecteur ErgoVeille (Mode Classifié)...")
    collect_and_save()