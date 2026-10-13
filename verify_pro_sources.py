"""
Script de vérification des sources professionnelles françaises pour ErgoVeille.
Teste l'existence et la validité des flux RSS candidats avant intégration.
Conforme à la Section 5 du cahier des charges : on ne présume jamais de l'existence d'un flux.
"""

import feedparser
import requests
from datetime import datetime

# Headers simulant un navigateur standard pour éviter les blocages antibot basiques (ex: 403)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36 ErgoVeille/1.0"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

# Sources candidates avec leurs URLs potentielles
CANDIDATES = [
    {
        "nom": "ANFE (Alliance Francophone des Ergothérapeutes)",
        "urls_a_tester": [
            "https://anfe.fr/feed/",
            "https://www.anfe.fr/feed/",
            "https://anfe.fr/rss",
            "https://anfe.fr/actualites/feed/",
        ],
        "site_officiel": "https://anfe.fr/",
    },
    {
        "nom": "CNSA (Caisse Nationale de Solidarité pour l'Autonomie)",
        "urls_a_tester": [
            "https://www.cnsa.fr/rss.xml",
            "https://www.cnsa.fr/feed",
            "https://www.cnsa.fr/actualites/rss.xml",
        ],
        "site_officiel": "https://www.cnsa.fr",
    },
    {
        "nom": "HAS (Haute Autorité de Santé - Publications)",
        "urls_a_tester": [
            "https://www.has-sante.fr/jcms/c_1725598/fr/flux-rss-publications",
            "https://www.has-sante.fr/jcms/c_1725596/fr/flux-rss-actualites",
        ],
        "site_officiel": "https://www.has-sante.fr",
    },
    {
        "nom": "Ministère de la Santé et de la Prévention",
        "urls_a_tester": [
            "https://sante.gouv.fr/spip.php?page=backend",
        ],
        "site_officiel": "https://sante.gouv.fr",
    },
    {
        "nom": "RFRE (Revue Francophone de Recherche en Ergothérapie)",
        "urls_a_tester": [
            "https://rfre.org/index.php/rfre/gateway/plugin/WebFeedGatewayPlugin/rss2",
            "https://rfre.org/index.php/rfre/gateway/plugin/WebFeedGatewayPlugin/atom",
            "https://rfre.org/index.php/rfre/feed/atom",
            "https://rfre.org/index.php/rfre/feed/rss",
            "https://rfre.org/feed",
            "https://rfre.org/rss",
        ],
        "site_officiel": "https://rfre.org",
    },
    {
        "nom": "SYNFEL (Syndicat National des Ergothérapeutes Libéraux)",
        "urls_a_tester": [
            "https://www.synfel-ergolib.fr/feed/",
            "https://www.synfel-ergolib.fr/rss",
            "https://www.synfel-ergolib.fr/actualites/feed/",
        ],
        "site_officiel": "https://www.synfel-ergolib.fr/",
    },
    {
        "nom": "Cochrane France / Library",
        "urls_a_tester": [
            "https://france.cochrane.org/fr/rss.xml",
            "https://france.cochrane.org/rss",
            "https://www.cochranelibrary.com/rss",
        ],
        "site_officiel": "https://france.cochrane.org",
    },
    {
        "nom": "SOFEC (Société Française d'Ergothérapie en Clinique)",
        "urls_a_tester": [
            "https://www.sofec.fr/feed/",
            "https://www.sofec.fr/rss",
        ],
        "site_officiel": "https://www.sofec.fr",
    },
]


def verifier_url(url):
    """Teste une URL et valide s'il s'agit réellement d'un flux XML/RSS/Atom."""
    try:
        response = requests.get(
            url,
            timeout=15,
            headers=HEADERS,
            allow_redirects=True,
        )

        content_type = response.headers.get("Content-Type", "").lower()
        resultat_base = {
            "url_finale": response.url,
            "type_contenu": content_type,
        }

        if response.status_code != 200:
            return {
                "ok": False,
                "raison": f"HTTP {response.status_code}",
                **resultat_base,
            }

        # Parsing du flux
        feed = feedparser.parse(response.content)

        # Vérification 1 : Rejet formel si la réponse est du HTML standard sans version RSS reconnue
        if "text/html" in content_type and not getattr(feed, "version", ""):
            return {
                "ok": False,
                "raison": "Réponse HTTP 200 mais contenu HTML classique (pas de XML/RSS)",
                **resultat_base,
            }

        # Vérification 2 : Présence d'articles ou d'un flux structuré
        nb_entries = len(feed.entries)
        titre_feed = feed.feed.get("title", "").strip()

        if not getattr(feed, "version", "") and nb_entries == 0:
            return {
                "ok": False,
                "raison": "Format non reconnu comme flux RSS/Atom valide",
                **resultat_base,
            }

        return {
            "ok": True,
            "nb_articles": nb_entries,
            "titre": titre_feed or "(flux sans titre)",
            "dernier_article": (
                feed.entries[0].get("title", "") if nb_entries > 0 else None
            ),
            **resultat_base,
        }

    except requests.exceptions.RequestException as e:
        return {
            "ok": False,
            "raison": f"Erreur réseau ({type(e).__name__}) : {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "raison": f"Erreur inattendue : {e}",
        }


def main():
    print("=" * 80)
    print("🔎 VÉRIFICATION DES SOURCES PROFESSIONNELLES FRANÇAISES")
    print(f"⏰ {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 80)
    print("Objectif : identifier les flux RSS réellement exploitables.\n")

    confirmes = []
    non_disponibles = []

    for source in CANDIDATES:
        nom = source["nom"]
        print(f"\n{'=' * 70}")
        print(f"🏛️  {nom}")
        print(f"   Site officiel : {source['site_officiel']}")
        print(f"   Test de {len(source['urls_a_tester'])} URL(s) candidate(s)...")

        flux_trouve = None
        for url in source["urls_a_tester"]:
            print(f"\n   🔍 {url}")
            resultat = verifier_url(url)

            if resultat["ok"]:
                print("      ✅ FLUX VALIDE !")
                print(f"         Titre du flux   : {resultat['titre']}")
                print(f"         Nombre d'items  : {resultat['nb_articles']}")
                if resultat["dernier_article"]:
                    print(f"         Dernier item    : {resultat['dernier_article'][:80]}")
                flux_trouve = {"url": url, "resultat": resultat}
                break  # Arrêt dès qu'un flux fonctionne pour cette source
            else:
                print(f"      ❌ {resultat['raison']}")

        if flux_trouve:
            confirmes.append({
                "nom": nom,
                "url": flux_trouve["url"],
                "nb_articles": flux_trouve["resultat"]["nb_articles"],
                "titre": flux_trouve["resultat"]["titre"],
            })
        else:
            non_disponibles.append(nom)

    # Bilan final
    print("\n" + "=" * 80)
    print("📊 BILAN DE LA VÉRIFICATION")
    print("=" * 80)

    print(f"\n✅ Flux RSS confirmés ({len(confirmes)}) :")
    if confirmes:
        for s in confirmes:
            print(f"   - {s['nom']}")
            print(f"     URL : {s['url']}")
            print(f"     Articles disponibles : {s['nb_articles']}")
    else:
        print("   (aucun)")

    print(f"\n⚠️ Sources sans flux RSS disponible ({len(non_disponibles)}) :")
    if non_disponibles:
        for nom in non_disponibles:
            print(f"   - {nom}")
    else:
        print("   (aucune)")

    print("\n💡 Recommandation :")
    if confirmes:
        print(f"   → Intégrer les {len(confirmes)} source(s) validée(s) dans config/config.yaml.")
    if non_disponibles:
        print(f"   → Pour les {len(non_disponibles)} source(s) sans flux, basculer vers PubMed ou une veille manuelle.")
    print("=" * 80)


if __name__ == "__main__":
    main()