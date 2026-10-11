from Bio import Entrez
import json

# Configuration
Entrez.email = "veille@ergoland.fr"
Entrez.tool = "ErgoVeille_Debug"

# On prend le premier PMID de ta base
pmid_test = "42856067"

print(f"🔍 Téléchargement de l'article PMID {pmid_test}...")
handle = Entrez.efetch(db="pubmed", id=pmid_test, retmode="xml")
xml_data = Entrez.read(handle)
handle.close()

article = xml_data['PubmedArticle'][0]

# Affichons la structure
print("\n📋 Structure de l'article :")
print("=" * 60)

# Vérifions si PubmedData existe
if 'PubmedData' in article:
    print("✅ 'PubmedData' TROUVÉ")
    pubmed_data = article['PubmedData']
    
    # Vérifions si PublicationTypeList existe
    if 'PublicationTypeList' in pubmed_data:
        print("✅ 'PublicationTypeList' TROUVÉ")
        print(f"   Contenu : {pubmed_data['PublicationTypeList']}")
    else:
        print("❌ 'PublicationTypeList' ABSENT de PubmedData")
        print(f"   Clés disponibles dans PubmedData : {list(pubmed_data.keys())}")
else:
    print("❌ 'PubmedData' ABSENT de l'article")
    print(f"   Clés disponibles : {list(article.keys())}")

print("\n📄 Sauvegarde de la structure complète dans debug_output.json...")
with open('debug_output.json', 'w', encoding='utf-8') as f:
    # Convertir en string pour éviter les problèmes de sérialisation
    json.dump(str(article), f, ensure_ascii=False, indent=2)

print("✅ Fichier debug_output.json créé. Ouvre-le pour voir la structure complète.")