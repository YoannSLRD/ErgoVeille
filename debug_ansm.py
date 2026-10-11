"""
Script de debug pour comprendre pourquoi l'ANSM ne retourne aucun article.
"""

import requests
import xml.etree.ElementTree as ET

url = "https://ansm.sante.fr/rss/actualites"

print("🔍 Debug du flux RSS ANSM")
print("=" * 70)

try:
    response = requests.get(url, timeout=15, headers={
        'User-Agent': 'ErgoVeille/1.0 (veille scientifique ergothérapie)'
    })
    
    print(f"✅ Connexion réussie (HTTP {response.status_code})")
    print(f"📄 Type de contenu : {response.headers.get('Content-Type', 'Inconnu')}")
    print(f"📏 Taille du contenu : {len(response.content)} octets")
    
    # Afficher les 500 premiers caractères du XML
    print("\n📋 Aperçu du XML (500 premiers caractères) :")
    print(response.text[:500])
    
    # Parser le XML
    print("\n🔍 Analyse de la structure XML :")
    root = ET.fromstring(response.content)
    
    print(f"   Racine : <{root.tag}>")
    print(f"   Attributs : {root.attrib}")
    
    # Chercher le channel
    channel = root.find('channel')
    if channel is not None:
        print(f"   ✅ <channel> trouvé")
        print(f"   Enfants de <channel> : {[child.tag for child in channel]}")
        
        # Chercher les items
        items = channel.findall('item')
        print(f"   📰 Nombre d'<item> trouvés : {len(items)}")
        
        if items:
            print("\n   Premier article :")
            first_item = items[0]
            for child in first_item:
                print(f"      <{child.tag}> : {child.text[:80] if child.text else '(vide)'}...")
        else:
            print("   ⚠️  Aucun <item> trouvé dans <channel>")
            print("   🔍 Tous les enfants de <channel> :")
            for child in channel:
                print(f"      <{child.tag}>")
    else:
        print("   ❌ <channel> non trouvé")
        print(f"   Enfants directs de la racine : {[child.tag for child in root]}")

except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)