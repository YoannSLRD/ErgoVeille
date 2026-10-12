"""
Script maître ErgoVeille.
Orchestre : collecte PubMed -> collecte RSS -> classification -> statut de collecte.
"""
import json
import os
from datetime import datetime

STATUS_PATH = "data/collect_status.json"


def main():
    print("=" * 80)
    print("🚀 ERGOVEILLE — Collecte automatisée")
    print(f"⏰ Démarré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    status = {"last_run": datetime.now().isoformat(), "sources": {}, "global_ok": True}

    print("\n📚 ÉTAPE 1/3 : Collecte des articles scientifiques (PubMed)")
    try:
        from src.collectors.pubmed_collector import collect_and_save
        collect_and_save()
        status["sources"]["PubMed"] = {"ok": True, "erreur": None}
    except Exception as e:
        status["sources"]["PubMed"] = {"ok": False, "erreur": str(e)}
        status["global_ok"] = False
        print(f"❌ Erreur lors de la collecte PubMed : {e}")

    print("\n📡 ÉTAPE 2/3 : Collecte des actualités sanitaires (RSS)")
    try:
        from src.collectors.rss_collector import collect_rss
        collect_rss()
        status["sources"]["RSS"] = {"ok": True, "erreur": None}
    except Exception as e:
        status["sources"]["RSS"] = {"ok": False, "erreur": str(e)}
        status["global_ok"] = False
        print(f"❌ Erreur lors de la collecte RSS : {e}")

    print("\n🧠 ÉTAPE 3/3 : Classification des articles")
    try:
        from src.processing.classifier import reprocess_database
        reprocess_database()
        status["sources"]["Classification"] = {"ok": True, "erreur": None}
    except Exception as e:
        status["sources"]["Classification"] = {"ok": False, "erreur": str(e)}
        status["global_ok"] = False
        print(f"❌ Erreur lors de la classification : {e}")

    os.makedirs("data", exist_ok=True)
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("🎉 COLLECTE TERMINÉE")
    print(f"   Statut global : {'✅ OK' if status['global_ok'] else '⚠️ ERREURS DÉTECTÉES'}")
    print(f"   Statut enregistré dans : {STATUS_PATH}")
    print(f"⏰ Terminé le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()