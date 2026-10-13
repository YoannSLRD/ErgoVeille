"""
Collecteur RSS pour les sources sanitaires françaises.
Gère à la fois les flux standards (feedparser) et les flux nécessitant un parsing XML manuel.
"""

import os
import json
import yaml
import feedparser
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from src.processing.source_status import update_source_status

CONFIG_PATH = 'config/config.yaml'
DATA_PATH = 'data/articles.json'

def load_config():
    """Charge la configuration YAML."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_feedparser(url):
    """Parse un flux RSS standard avec feedparser."""
    feed = feedparser.parse(url)
    articles = []
    
    for entry in feed.entries:
        # Extraction de la date
        date_pub = None
        if hasattr(entry, 'published'):
            try:
                date_pub = parsedate_to_datetime(entry.published).isoformat()
            except:
                date_pub = entry.get('published', '')
        
        # Extraction du résumé (description ou summary)
        resume = entry.get('summary', entry.get('description', ''))
        # Nettoyage basique du HTML dans le résumé
        if resume:
            import re
            resume = re.sub('<[^<]+?>', '', resume)  # Supprime les balises HTML
            resume = resume.strip()
        
        articles.append({
            "titre": entry.get('title', 'Sans titre'),
            "lien": entry.get('link', ''),
            "resume": resume,
            "date_publication": date_pub,
            "date_collecte": datetime.now().isoformat(),
            "source": "RSS",
            "type_publication": "Actualité sanitaire",
        })
    
    return articles

def parse_xml_manual(url):
    """Parse manuellement un flux RSS XML (pour les flux non standards comme ANSM)."""
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'ErgoVeille/1.0 (veille scientifique ergothérapie; mailto:veille@ergoland.fr)'
        })
        response.raise_for_status()
        
        # Parser le XML
        root = ET.fromstring(response.content)
        articles = []
        
        # Chercher les items dans le channel
        channel = root.find('channel')
        if channel is None:
            return articles
        
        for item in channel.findall('item'):
            titre = item.findtext('title', 'Sans titre')
            lien = item.findtext('link', '')
            description = item.findtext('description', '')
            date_pub_str = item.findtext('pubDate', '')
            
            # Nettoyage du HTML dans la description
            if description:
                import re
                description = re.sub('<[^<]+?>', '', description)
                description = description.strip()
            
            # Parsing de la date
            date_pub = ''
            if date_pub_str:
                try:
                    date_pub = parsedate_to_datetime(date_pub_str).isoformat()
                except:
                    date_pub = date_pub_str
            
            articles.append({
                "titre": titre,
                "lien": lien,
                "resume": description,
                "date_publication": date_pub,
                "date_collecte": datetime.now().isoformat(),
                "source": "RSS",
                "type_publication": "Actualité sanitaire",
            })
        
        return articles
        
    except Exception as e:
        print(f"   ❌ Erreur lors du parsing XML manuel : {e}")
        return []

def collect_rss():
    """Collecte tous les flux RSS actifs."""
    config = load_config()
    rss_feeds = config.get('rss_feeds', [])
    
    print("📡 Démarrage de la collecte RSS")
    print("=" * 70)
    
    tous_les_articles = []
    bilan = {"trouves": 0, "ajoutes": 0, "erreurs": 0}
    
    for feed_config in rss_feeds:
        if not feed_config.get('actif', True):
            print(f"\n⏭️  Source '{feed_config['nom']}' désactivée")
            if 'note' in feed_config:
                print(f"   Note : {feed_config['note']}")
            continue
        
        print(f"\n📡 Source : {feed_config['nom']}")
        print(f"   URL : {feed_config['url']}")
        
        try:
            parser_type = feed_config.get('parser', 'feedparser')
            
            if parser_type == 'feedparser':
                articles = parse_feedparser(feed_config['url'])
            elif parser_type == 'xml_manual':
                articles = parse_xml_manual(feed_config['url'])
            else:
                print(f"   ❌ Parser inconnu : {parser_type}")
                bilan["erreurs"] += 1
                update_source_status(feed_config['nom'], False, 0, f"Parser inconnu : {parser_type}")
                continue
            
            print(f"   ✅ {len(articles)} articles récupérés")
            update_source_status(feed_config['nom'], True, len(articles), "")
            
            # Ajouter la source à chaque article
            for art in articles:
                art['source'] = feed_config['nom']
                art['id_source'] = art['lien']
                art['id_unique'] = art['lien']  # ✅ NOUVEAU : Identifiant universel
            
            tous_les_articles.extend(articles)
            bilan["trouves"] += len(articles)
            
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
            bilan["erreurs"] += 1
            update_source_status(feed_config['nom'], False, 0, str(e))
    
    # Sauvegarde dans la base de données
    if tous_les_articles:
        os.makedirs('data', exist_ok=True)
        
        existing_articles = []
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                existing_articles = json.load(f)
        
        # Dédoublonnage par lien
        existing_ids = {art.get('id_source') or art.get('lien') for art in existing_articles}
        
        for art in tous_les_articles:
            article_id = art.get('id_source') or art.get('lien')
            if article_id not in existing_ids:
                existing_articles.append(art)
                bilan["ajoutes"] += 1
        
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=4)
    
    print("\n" + "=" * 70)
    print(f"📊 Bilan RSS :")
    print(f"   - {bilan['trouves']} articles trouvés")
    print(f"   - {bilan['ajoutes']} nouveaux articles ajoutés")
    print(f"   - {bilan['erreurs']} erreurs rencontrées")
    print(f"   - Total en base : {len(existing_articles) if 'existing_articles' in locals() else 0} articles")

if __name__ == "__main__":
    collect_rss()