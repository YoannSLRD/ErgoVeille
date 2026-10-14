"""
Script one-shot pour traduire l'historique des articles PubMed.
Utilise le module translator.py (DeepL + fallback MyMemory).
Sauvegarde la progression tous les 10 articles pour résister aux interruptions.
Conforme Section 16 du cahier des charges (robustesse).
"""

import json
import os
import time
from src.processing.translator import traduire_texte

DATA_PATH = "data/articles.json"
SAVE_INTERVAL = 10  # Sauvegarde tous les 10 articles


def is_valid_fr(text):
    """Vérifie si un champ de traduction est valide (pas None, pas 'nan', pas vide)."""
    if not text or text == "nan":
        return False
    if isinstance(text, float):  # Gère le cas où pandas a mis un NaN
        return False
    return True


def main():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Fichier {DATA_PATH} introuvable.")
        return

    print(f"📂 Chargement de {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Filtrer uniquement les articles PubMed
    pubmed_articles = [a for a in articles if a.get("source") == "PubMed"]
    print(f" {len(pubmed_articles)} articles PubMed trouvés dans la base.")

    # Identifier ceux qui n'ont pas encore été traduits
    to_translate = []
    for a in pubmed_articles:
        if not is_valid_fr(a.get("titre_fr")) or not is_valid_fr(a.get("resume_fr")):
            to_translate.append(a)

    print(f"🚀 {len(to_translate)} article(s) à traduire.")
    if not to_translate:
        print("✅ Tout l'historique est déjà traduit ! Rien à faire.")
        return

    # Garde-fou : confirmation explicite avant de consommer des tokens
    print("\n️  ATTENTION : Cette opération va consommer des tokens DeepL.")
    confirm = input("Pour confirmer, tapez exactement : OUI\n> ")
    if confirm != "OUI":
        print("❌ Opération annulée.")
        return

    print("\n🔄 Démarrage de la traduction de l'historique...")
    print("(Le script sauvegarde automatiquement tous les 10 articles.)\n")
    
    total = len(to_translate)
    
    for i, article in enumerate(to_translate):
        pmid = article.get("pmid", "inconnu")
        print(f"[{i+1}/{total}] PMID {pmid}...", end=" ")

        # 1. Traduction du titre
        if not is_valid_fr(article.get("titre_fr")):
            titre_en = article.get("titre", "")
            if len(titre_en.strip()) >= 10:
                article["titre_fr"] = traduire_texte(titre_en)
                time.sleep(0.3)  # Respect du débit API DeepL
            else:
                article["titre_fr"] = titre_en

        # 2. Traduction du résumé
        if not is_valid_fr(article.get("resume_fr")):
            resume_en = article.get("resume", "")
            if len(resume_en.strip()) >= 20:
                article["resume_fr"] = traduire_texte(resume_en)
                time.sleep(0.3)  # Respect du débit API DeepL
            else:
                article["resume_fr"] = resume_en
        
        print("✅")

        # 💾 Sauvegarde périodique (robustesse)
        if (i + 1) % SAVE_INTERVAL == 0:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=4)
            print(f"   💾 Sauvegarde intermédiaire effectuée ({i+1} articles traités).")

    #  Sauvegarde finale
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    
    print("\n" + "=" * 60)
    print("🎉 TRADUCTION DE L'HISTORIQUE TERMINÉE !")
    print(f"   - {total} articles traduits avec succès.")
    print(f"   - Fichier {DATA_PATH} mis à jour.")
    print("=" * 60)


if __name__ == "__main__":
    main()