"""
Script de sauvegarde automatique des données ErgoVeille.
Crée une copie horodatée du dossier data/ dans le dossier backups/.
Garde uniquement les 5 sauvegardes les plus récentes (rotation).
Conforme Section 16 du cahier des charges (robustesse et sauvegarde).
"""

import os
import shutil
from datetime import datetime

# Configuration
SOURCE_DIR = "data"
BACKUP_BASE_DIR = "backups"
MAX_BACKUPS = 5  # Nombre de sauvegardes à conserver


def main():
    print("=" * 60)
    print("️ SAUVEGARDE AUTOMATIQUE DES DONNÉES")
    print("=" * 60)

    # 1. Vérifier que le dossier source existe
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Erreur : Le dossier '{SOURCE_DIR}' est introuvable.")
        return

    # 2. Créer le dossier de backups s'il n'existe pas
    os.makedirs(BACKUP_BASE_DIR, exist_ok=True)

    # 3. Générer le nom du dossier de sauvegarde (avec date et heure)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"data_backup_{timestamp}"
    backup_path = os.path.join(BACKUP_BASE_DIR, backup_name)

    print(f"📂 Source : {os.path.abspath(SOURCE_DIR)}")
    print(f"💾 Destination : {os.path.abspath(backup_path)}")
    print(" Copie en cours...")

    try:
        # 4. Copier le dossier
        shutil.copytree(SOURCE_DIR, backup_path)
        print("✅ Copie réussie !")

        # 5. Calculer la taille de la sauvegarde
        total_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(backup_path)
            for filename in filenames
        )
        size_mb = total_size / (1024 * 1024)
        print(f"   📊 Taille : {size_mb:.2f} Mo")

    except Exception as e:
        print(f"❌ Échec de la copie : {e}")
        return

    # 6. Rotation : supprimer les anciennes sauvegardes si on dépasse la limite
    print(f"\n🧹 Nettoyage (conservation des {MAX_BACKUPS} dernières)...")
    
    # Lister tous les dossiers de backup et les trier par date (le nom contient la date)
    all_backups = sorted([
        d for d in os.listdir(BACKUP_BASE_DIR) 
        if d.startswith("data_backup_") and os.path.isdir(os.path.join(BACKUP_BASE_DIR, d))
    ])

    if len(all_backups) > MAX_BACKUPS:
        # Ceux à supprimer sont les plus anciens (au début de la liste triée)
        to_delete = all_backups[:-MAX_BACKUPS]
        for old_backup in to_delete:
            old_path = os.path.join(BACKUP_BASE_DIR, old_backup)
            try:
                shutil.rmtree(old_path)
                print(f"   🗑️ Supprimé : {old_backup}")
            except Exception as e:
                print(f"   ⚠️ Impossible de supprimer {old_backup} : {e}")
    else:
        print("   ℹ️ Aucune ancienne sauvegarde à supprimer.")

    print("\n" + "=" * 60)
    print("🎉 SAUVEGARDE TERMINÉE")
    print("=" * 60)


if __name__ == "__main__":
    main()