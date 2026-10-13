"""
Script principal d'orchestration ErgoVeille.
Coordonne la collecte PubMed, RSS, et la classification.
"""

import json
import os
from datetime import datetime

from src.collectors.pubmed_collector import collect_and_save as collect_pubmed
from src.collectors.rss_collector import collect_rss
from src.processing.classifier import reprocess_database
from src.processing.source_status import update_source_status

STATUS_PATH = "data/collect_status.json"


def main():
    print("=" * 80)
    print("🚀 ERGOVEILLE — Collecte automatisée")
    print(f"⏰ Démarré le : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 80)

    global_ok = True

    # ÉTAPE 1 : Collecte PubMed
    print("\n📚 ÉTAPE 1/3 : Collecte des articles scientifiques (PubMed)")
    try:
        resultat = collect_pubmed()
        update_source_status("PubMed", True, resultat.get("trouves", 0), "")
    except Exception as e:
        print(f"❌ Erreur lors de la collecte PubMed : {e}")
        update_source_status("PubMed", False, 0, str(e))
        global_ok = False

    # ÉTAPE 2 : Collecte RSS
    print("\n📡 ÉTAPE 2/3 : Collecte des actualités sanitaires (RSS)")
    try:
        collect_rss()
    except Exception as e:
        print(f"❌ Erreur lors de la collecte RSS : {e}")
        global_ok = False

    # ÉTAPE 3 : Classification
    print("\n🧠 ÉTAPE 3/3 : Classification des articles")
    try:
        reprocess_database()
    except Exception as e:
        print(f"❌ Erreur lors de la classification : {e}")
        global_ok = False

    # Statut global
    print("\n" + "=" * 80)
    print("🎉 COLLECTE TERMINÉE")
    print("   Statut global : ✅ OK" if global_ok else "   Statut global : ⚠️ ERREURS DÉTECTÉES")
    print(f"   Statut enregistré dans : {STATUS_PATH}")
    print(f"⏰ Terminé le : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 80)

    os.makedirs("data", exist_ok=True)
    status = {
        "last_run": datetime.now().isoformat(),
        "global_ok": global_ok,
    }
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()