"""
Script maître ErgoVeille
Orchestre la collecte scientifique (PubMed) et sanitaire (RSS), puis applique la classification.
"""

import sys
from datetime import datetime

def main():
    print("=" * 80)
    print("🚀 ERGOVEILLE — Collecte automatisée")
    print(f"⏰ Démarré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Étape 1 : Collecte PubMed
    print("\n" + "=" * 80)
    print("📚 ÉTAPE 1/3 : Collecte des articles scientifiques (PubMed)")
    print("=" * 80)
    try:
        from src.collectors.pubmed_collector import collect_and_save
        collect_and_save()
        print("✅ Collecte PubMed terminée avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la collecte PubMed : {e}")
        print("⚠️  La collecte RSS continue malgré cette erreur")
    
    # Étape 2 : Collecte RSS
    print("\n" + "=" * 80)
    print("📡 ÉTAPE 2/3 : Collecte des actualités sanitaires (RSS)")
    print("=" * 80)
    try:
        from src.collectors.rss_collector import collect_rss
        collect_rss()
        print("✅ Collecte RSS terminée avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la collecte RSS : {e}")
        print("⚠️  La classification continue malgré cette erreur")
    
    # Étape 3 : Classification
    print("\n" + "=" * 80)
    print("🧠 ÉTAPE 3/3 : Classification des articles")
    print("=" * 80)
    try:
        from src.processing.classifier import reprocess_database
        reprocess_database()
        print("✅ Classification terminée avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la classification : {e}")
    
    # Bilan final
    print("\n" + "=" * 80)
    print("🎉 COLLECTE TERMINÉE")
    print("=" * 80)
    print(f"⏰ Terminé le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Pour voir les résultats, lancez : streamlit run app.py")

if __name__ == "__main__":
    main()