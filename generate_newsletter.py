"""Point d'entrée manuel de la newsletter ErgoVeille."""
import argparse
import os

from src.newsletter.builder import build_newsletter
from src.newsletter.sender import send_test_newsletter

PREVIEW_HTML = "data/newsletter_preview.html"
PREVIEW_TXT = "data/newsletter_preview.txt"

def main():
    parser = argparse.ArgumentParser(description="Génère et/ou envoie la newsletter ErgoVeille.")
    parser.add_argument("--preview", action="store_true", help="Génère un aperçu local (HTML + texte) sans aucun envoi.")
    parser.add_argument("--send-test", action="store_true", help="Génère la newsletter et l'envoie en mode TEST à l'adresse configurée.")
    args = parser.parse_args()

    if args.preview:
        build_newsletter(mode="preview")
        
    elif args.send_test:
        print("🚀 Mode TEST activé : Génération + Envoi unique")
        print("-" * 60)
        # 1. Générer d'abord
        build_newsletter(mode="preview")
        print("-" * 60)
        # 2. Envoyer
        send_test_newsletter(PREVIEW_HTML, PREVIEW_TXT)
        
    else:
        print("ℹ️ Utilisation :")
        print("   python generate_newsletter.py --preview      (Aperçu local uniquement)")
        print("   python generate_newsletter.py --send-test    (Aperçu + Envoi de test)")

if __name__ == "__main__":
    main()