import requests
import feedparser

# Différentes URLs possibles pour l'ANSM
ANSM_URLS = [
    "https://ansm.sante.fr/rss/actualites",
    "https://ansm.sante.fr/feed/actualites",
    "https://ansm.sante.fr/rss.xml",
    "https://ansm.sante.fr/feed.xml",
    "https://ansm.sante.fr/rss",
]

print("🔍 Test des différentes URLs ANSM")
print("=" * 70)

for url in ANSM_URLS:
    print(f"\n📡 URL : {url}")
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'ErgoVeille/1.0 (veille scientifique ergothérapie)'
        })
        
        if response.status_code == 200:
            print(f"   ✅ Connexion réussie (HTTP {response.status_code})")
            
            # Vérifions le type de contenu
            content_type = response.headers.get('Content-Type', 'Inconnu')
            print(f"   📄 Type de contenu : {content_type}")
            
            # Essayons de parser
            feed = feedparser.parse(response.content)
            
            if feed.entries:
                print(f"   📰 {len(feed.entries)} articles trouvés")
                print(f"   ✅ CE FLUX FONCTIONNE !")
                
                # Afficher le premier article
                if feed.entries:
                    titre = feed.entries[0].get('title', 'Sans titre')
                    print(f"      Exemple : {titre[:80]}...")
            else:
                print(f"   ⚠️  Flux vide ou non reconnu par feedparser")
                # Afficher un extrait du contenu pour diagnostic
                print(f"   🔍 Aperçu du contenu (200 premiers caractères) :")
                print(f"      {response.text[:200]}")
        else:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erreur : {type(e).__name__} : {e}")

print("\n" + "=" * 70)
print("Test terminé.")