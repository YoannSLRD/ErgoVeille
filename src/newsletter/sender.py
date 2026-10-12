"""
Module d'envoi de la newsletter ErgoVeille via SMTP.
Inclut des garde-fous stricts pour éviter les envois accidentels.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration SMTP (déjà testée en Phase 6)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "veille@ergoland.fr")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "ErgoVeille")

# Configuration de sécurité Newsletter
SEND_ENABLED = os.getenv("NEWSLETTER_SEND_ENABLED", "false").lower() == "true"
TEST_RECIPIENT = os.getenv("NEWSLETTER_TEST_RECIPIENT", "")

def send_test_newsletter(html_path: str, txt_path: str):
    """
    Envoie la newsletter en mode TEST uniquement.
    """
    if not SEND_ENABLED:
        print("❌ Envoi bloqué : NEWSLETTER_SEND_ENABLED est défini sur 'false' dans le .env")
        return False

    if not TEST_RECIPIENT or "@" not in TEST_RECIPIENT:
        print("❌ Envoi bloqué : NEWSLETTER_TEST_RECIPIENT n'est pas configuré correctement dans le .env")
        return False

    if not os.path.exists(html_path) or not os.path.exists(txt_path):
        print(f"❌ Erreur : Fichiers de newsletter introuvables ({html_path} ou {txt_path})")
        return False

    print(f"📤 Préparation de l'envoi de TEST vers : {TEST_RECIPIENT}")

    # 1. Lire le contenu des fichiers
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    with open(txt_path, "r", encoding="utf-8") as f:
        txt_content = f.read()

    # 2. Construire le message multipart (HTML + Texte)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[TEST] ErgoVeille — Votre veille scientifique et sanitaire"
    msg["From"] = f"{EMAIL_SENDER_NAME} <{EMAIL_SENDER}>"
    msg["To"] = TEST_RECIPIENT

    # Attacher la version texte (secours)
    part1 = MIMEText(txt_content, "plain", "utf-8")
    msg.attach(part1)

    # Attacher la version HTML (principale)
    part2 = MIMEText(html_content, "html", "utf-8")
    msg.attach(part2)

    # 3. Envoi via SMTP SSL (Hostinger)
    try:
        print(f"🔌 Connexion à {SMTP_HOST}:{SMTP_PORT}...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_SENDER, TEST_RECIPIENT, msg.as_string())
            
        print("✅ SUCCÈS ! L'e-mail de test a été envoyé avec succès.")
        print("💡 Vérifie ta boîte de réception (et le dossier Spam/Courrier indésirable).")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ ERREUR D'AUTHENTIFICATION : Le serveur a refusé le mot de passe.")
        print("👉 Vérifie ton mot de passe dans le fichier .env.")
        return False
    except Exception as e:
        print(f"❌ ERREUR D'ENVOI : {e}")
        return False