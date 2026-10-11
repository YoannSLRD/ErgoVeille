import feedparser
import requests
from datetime import datetime

# Liste des flux RSS à tester
RSS_FEEDS = {
    "HAS (Haute Autorité de Santé)": "https://www.has-sante.fr/feed/Rss2.jsp?id=p_3082237",
    "ANSM (Actualités)": "https://ansm.sante.fr/rss/actualites",
    "Santé publique France": "https://www.santepubliquefrance.fr/rss/actualites",
}

print("🔍 Test des flux RSS sanitaires français")
print("=" * 70)

for source_name, feed_url in RSS_FEEDS.items():
    print(f"\n📡 Source : {source_name}")
    print(f"   URL : {feed_url}")
    
    try:
        # Test de connexion
        response = requests.get(feed_url, timeout=10, headers={
            'User-Agent': 'ErgoVeille/1.0 (veille scientifique ergothérapie)'
        })
        
        if response.status_code == 200:
            print(f"   ✅ Connexion réussie (HTTP {response.status_code})")
            

            # Diagnostic du contenu reçu
            print(f"   Content-Type : {response.headers.get('Content-Type')}")
            print(f"   Taille : {len(response.content)} octets")
            print(f"   Début de la réponse : {response.text[:250]!r}")

            # Analyse du flux
            feed = feedparser.parse(response.content)

            print(f"   Version du flux : {feed.version or 'Non reconnue'}")
            print(f"   Entrées trouvées : {len(feed.entries)}")
            print(f"   Erreur de parsing : {feed.get('bozo', False)}")

            if feed.get("bozo"):
                print(f"   Détail : {feed.get('bozo_exception')}")

            if feed.entries:
                for i, entry in enumerate(feed.entries[:3], 1):
                    titre = entry.get("title", "Sans titre")
                    date = entry.get("published", "Date inconnue")
                    print(f"      {i}. {titre[:80]}")
                    print(f"         Date : {date}")
            else:
                print("   ⚠️ Aucune entrée exploitable.")
        else:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout (le serveur ne répond pas)")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur de connexion")
    except Exception as e:
        print(f"   ❌ Erreur : {type(e).__name__} : {e}")

print("\n" + "=" * 70)
print("Test terminé.")