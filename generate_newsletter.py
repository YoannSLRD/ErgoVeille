"""Point d'entrée manuel et automatique de la newsletter ErgoVeille."""
import argparse
import os
import yaml

from src.newsletter.builder import build_newsletter
from src.newsletter.sender import send_test_newsletter, send_to_subscriber

PREVIEW_HTML = "data/newsletter_preview.html"
PREVIEW_TXT = "data/newsletter_preview.txt"
ABONNES_PATH = "config/abonnes.yaml"


def load_abonnes():
    """Charge la liste des abonnés depuis config/abonnes.yaml."""
    if not os.path.exists(ABONNES_PATH):
        print(f"❌ Fichier {ABONNES_PATH} introuvable.")
        return []
    
    with open(ABONNES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("abonnes", [])


def send_all_newsletters(auto_mode=False):
    """
    Génère et envoie la newsletter à tous les abonnés actifs.
    
    Args:
        auto_mode: si True, pas de confirmation interactive (pour GitHub Actions)
    """
    print("=" * 70)
    print("🚀 MODE ENVOI MULTI-ABONNÉS" + (" (AUTO)" if auto_mode else ""))
    print("=" * 70)
    
    abonnes = load_abonnes()
    if not abonnes:
        print("❌ Aucun abonné trouvé dans config/abonnes.yaml")
        return
    
    # Filtrer les abonnés actifs
    actifs = [a for a in abonnes if a.get("actif", False)]
    if not actifs:
        print("❌ Aucun abonné actif trouvé (actif: true)")
        return
    
    print(f"\n📋 {len(actifs)} abonné(s) actif(s) détecté(s) :")
    for i, ab in enumerate(actifs, 1):
        themes_str = ", ".join(ab.get("themes", [])) if ab.get("themes") else "tous les thèmes"
        print(f"   {i}. {ab['nom']} <{ab['email']}> — Thèmes : {themes_str}")
    
    # Confirmation interactive UNIQUEMENT en mode manuel
    if not auto_mode:
        print("\n" + "=" * 70)
        print("⚠️  ATTENTION : Vous êtes sur le point d'envoyer des e-mails réels.")
        print("=" * 70)
        confirmation = input("Pour confirmer, tapez exactement : OUI\n> ")
        
        if confirmation != "OUI":
            print("❌ Envoi annulé.")
            return
    else:
        print("\n✅ Mode auto : confirmation sautée (garde-fou GitHub Actions actif)")
    
    print("\n🚀 Démarrage de l'envoi...\n")
    
    # Boucle d'envoi
    succes = 0
    echecs = 0
    
    for ab in actifs:
        print(f"\n{'=' * 70}")
        print(f"📧 Traitement de : {ab['nom']} <{ab['email']}>")
        print(f"{'=' * 70}")
        
        # Générer la newsletter personnalisée
        themes = ab.get("themes", [])
        suffixe = f"_{ab['nom'].lower().replace(' ', '_')}"
        
        result = build_newsletter(mode="preview", themes=themes, suffixe=suffixe)
        
        if not result:
            print(f"❌ Échec de la génération pour {ab['nom']}")
            echecs += 1
            continue
        
        # Envoyer
        success = send_to_subscriber(ab, result["html"], result["txt"])
        
        if success:
            succes += 1
        else:
            echecs += 1
    
    # Bilan final
    print("\n" + "=" * 70)
    print("📊 BILAN DE L'ENVOI MULTI-ABONNÉS")
    print("=" * 70)
    print(f"✅ Envois réussis : {succes}/{len(actifs)}")
    print(f"❌ Envois échoués : {echecs}/{len(actifs)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Génère et/ou envoie la newsletter ErgoVeille.")
    parser.add_argument("--preview", action="store_true", 
                        help="Génère un aperçu local (HTML + texte) sans aucun envoi.")
    parser.add_argument("--send-test", action="store_true", 
                        help="Génère la newsletter et l'envoie en mode TEST à l'adresse configurée.")
    parser.add_argument("--send-all", action="store_true",
                        help="Génère et envoie la newsletter à tous les abonnés actifs (avec confirmation interactive).")
    parser.add_argument("--send-all-auto", action="store_true",
                        help="Génère et envoie la newsletter à tous les abonnés actifs (SANS confirmation, pour GitHub Actions).")
    args = parser.parse_args()

    if args.preview:
        build_newsletter(mode="preview")
        
    elif args.send_test:
        print("🚀 Mode TEST activé : Génération + Envoi unique")
        print("-" * 60)
        build_newsletter(mode="preview")
        print("-" * 60)
        send_test_newsletter(PREVIEW_HTML, PREVIEW_TXT)
        
    elif args.send_all:
        send_all_newsletters(auto_mode=False)
    
    elif args.send_all_auto:
        send_all_newsletters(auto_mode=True)
        
    else:
        print("ℹ️ Utilisation :")
        print("   python generate_newsletter.py --preview        (Aperçu local uniquement)")
        print("   python generate_newsletter.py --send-test      (Aperçu + Envoi de test)")
        print("   python generate_newsletter.py --send-all       (Envoi multi-abonnés, confirmation interactive)")
        print("   python generate_newsletter.py --send-all-auto  (Envoi multi-abonnés, mode automatique)")

if __name__ == "__main__":
    main()