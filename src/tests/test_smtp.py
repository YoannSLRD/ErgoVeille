import smtplib
import ssl
import os
from dotenv import load_dotenv

# 1. Charger les secrets depuis le fichier .env
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

print(f"🔍 Tentative de connexion à {SMTP_HOST} sur le port {SMTP_PORT}...")
print(f"👤 Utilisateur : {SMTP_USER}")

try:
    # 2. Créer un contexte sécurisé (SSL)
    context = ssl.create_default_context()
    
    # 3. Se connecter au serveur
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ SUCCÈS ! Connexion établie. Hostinger accepte tes identifiants.")
        
except smtplib.SMTPAuthenticationError:
    print("❌ ERREUR D'AUTHENTIFICATION : Le serveur a refusé le mot de passe.")
    print("👉 Vérifie que tu as bien copié ton mot de passe Hostinger dans le fichier .env")
except Exception as e:
    print(f"❌ ERREUR RÉSEAU OU SERVEUR : {e}")