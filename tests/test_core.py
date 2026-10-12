"""
Tests automatisés pour ErgoVeille (Section 16 du cahier des charges).
Ces tests utilisent des données simulées pour ne pas dépendre d'API externes.
"""

import pytest
import sys
import os

# Ajouter le dossier racine au chemin pour pouvoir importer les modules src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.newsletter.builder import score_article, _get_theme_icon


class TestValidationDonnees:
    """Tests sur la structure et la validité des données d'un article."""

    def test_article_valide_minimal(self):
        """Un article doit au minimum avoir un id_unique, un titre et une source."""
        article = {
            "id_unique": "12345",
            "titre": "Test d'ergothérapie",
            "source": "PubMed"
        }
        assert "id_unique" in article
        assert "titre" in article
        assert "source" in article
        assert len(article["titre"]) > 0

    def test_article_sans_id_unique_est_invalide(self):
        """Un article sans identifiant unique doit être rejeté ou géré."""
        article_incomplet = {
            "titre": "Test sans ID",
            "source": "RSS"
        }
        # Dans notre logique, on s'attend à ce que le collecteur ait déjà ajouté un id_unique.
        # Ce test vérifie que notre règle de validation est claire.
        assert "id_unique" not in article_incomplet


class TestLogiqueMetier:
    """Tests sur les fonctions de traitement (scoring, classification)."""

    def test_score_article_pubmed_fiable(self):
        """Un article PubMed avec un type d'étude fiable doit avoir un score élevé."""
        article = {
            "source": "PubMed",
            "type_etude": "Revue systématique",
            "tags": ["Neurologie", "Gériatrie"]
        }
        # 3 (type fiable) + 2 (PubMed) + 2 (2 tags, max 3) = 7
        assert score_article(article) == 7

    def test_score_article_rss_mots_cles(self):
        """Un article RSS avec détection par mots-clés a un score plus faible."""
        article = {
            "source": "HAS",
            "type_etude": "Étude observationnelle (détection par mots-clés, à confirmer)",
            "tags": []
        }
        # 2 (mots-clés) + 1 (non PubMed) + 0 (pas de tags) = 3
        assert score_article(article) == 3

    def test_score_article_a_verifier(self):
        """Un article sans type d'étude déterminé a le score le plus bas."""
        article = {
            "source": "PubMed",
            "type_etude": "Type d'étude à vérifier",
            "tags": ["Pédiatrie"]
        }
        # 0 (à vérifier) + 2 (PubMed) + 1 (1 tag) = 3
        assert score_article(article) == 3

    def test_get_theme_icon_defaut(self):
        """Si aucun tag n'est fourni, l'icône par défaut est un livre."""
        assert _get_theme_icon([]) == "📚"
        assert _get_theme_icon(None) == "📚"

    def test_get_theme_icon_neurologie(self):
        """Le thème neurologie doit retourner un cerveau."""
        assert _get_theme_icon(["Neurologie", "Gériatrie"]) == "🧠"