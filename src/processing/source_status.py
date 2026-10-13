"""
Module de gestion du statut des sources ErgoVeille.
Enregistre les résultats de chaque collecte par source dans un fichier JSON.
"""

import json
import os
from datetime import datetime

STATUS_PATH = "data/sources_status.json"


def update_source_status(source_name: str, success: bool, nb_articles: int = 0, error_message: str = ""):
    """
    Met à jour le statut d'une source dans le fichier sources_status.json.
    
    Args:
        source_name: Nom de la source (ex: "PubMed", "HAS (Haute Autorité de Santé)")
        success: True si la collecte a réussi, False sinon
        nb_articles: Nombre d'articles collectés lors de cette tentative
        error_message: Message d'erreur si échec
    """
    os.makedirs("data", exist_ok=True)
    
    # Charger le statut existant
    status = {}
    if os.path.exists(STATUS_PATH):
        try:
            with open(STATUS_PATH, "r", encoding="utf-8") as f:
                status = json.load(f)
        except Exception:
            status = {}
    
    now_iso = datetime.now().isoformat()
    
    if source_name not in status:
        status[source_name] = {
            "premiere_collecte": now_iso,
            "total_articles": 0,
        }
    
    # Mise à jour
    status[source_name]["derniere_tentative"] = now_iso
    status[source_name]["dernier_statut"] = "OK" if success else "Erreur"
    status[source_name]["dernier_nb_articles"] = nb_articles
    
    if success:
        status[source_name]["derniere_reussite"] = now_iso
        status[source_name]["dernier_message_erreur"] = ""
        status[source_name]["nb_tentatives_reussies"] = status[source_name].get("nb_tentatives_reussies", 0) + 1
    else:
        status[source_name]["dernier_message_erreur"] = error_message
        status[source_name]["nb_tentatives_echouees"] = status[source_name].get("nb_tentatives_echouees", 0) + 1
    
    # Sauvegarder
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)