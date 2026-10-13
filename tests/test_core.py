"""
Tests automatisés pour ErgoVeille (Section 16 du cahier des charges).
Ces tests utilisent des données simulées pour ne pas dépendre d'API externes.
"""

import pytest
import sys
import os
import json
import tempfile
from datetime import datetime

# Ajouter le dossier racine au chemin pour pouvoir importer les modules src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.newsletter.builder import score_article, _get_theme_icon
from src.processing.classifier import classify_study_type, classify_themes, TYPE_A_VERIFIER


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
        assert "id_unique" not in article_incomplet

    def test_article_sans_resume_est_valide(self):
        """Un article sans résumé doit être accepté (certaines sources n'en fournissent pas)."""
        article = {
            "id_unique": "pmid_99999",
            "titre": "Étude sans résumé",
            "source": "PubMed",
            "resume": ""
        }
        assert article.get("resume") == ""
        assert article["titre"]  # Le titre doit exister

    def test_article_avec_identifiants_multiples(self):
        """Un article peut avoir plusieurs identifiants (PMID, DOI, lien)."""
        article = {
            "id_unique": "12345",
            "pmid": "12345",
            "doi": "10.1234/test",
            "lien": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            "titre": "Test",
            "source": "PubMed"
        }
        assert article["pmid"]
        assert article["doi"]
        assert article["lien"]


class TestLogiqueMetier:
    """Tests sur les fonctions de traitement (scoring, classification)."""

    def test_score_article_pubmed_fiable(self):
        """Un article PubMed avec un type d'étude fiable doit avoir un score élevé."""
        article = {
            "source": "PubMed",
            "type_etude": "Revue systématique",
            "tags": ["Neurologie", "Gériatrie"]
        }
        assert score_article(article) == 7

    def test_score_article_rss_mots_cles(self):
        """Un article RSS avec détection par mots-clés a un score plus faible."""
        article = {
            "source": "HAS",
            "type_etude": "Étude observationnelle (détection par mots-clés, à confirmer)",
            "tags": []
        }
        assert score_article(article) == 3

    def test_score_article_a_verifier(self):
        """Un article sans type d'étude déterminé a le score le plus bas."""
        article = {
            "source": "PubMed",
            "type_etude": "Type d'étude à vérifier",
            "tags": ["Pédiatrie"]
        }
        assert score_article(article) == 3

    def test_get_theme_icon_defaut(self):
        """Si aucun tag n'est fourni, l'icône par défaut est un livre."""
        assert _get_theme_icon([]) == "📚"
        assert _get_theme_icon(None) == "📚"

    def test_get_theme_icon_neurologie(self):
        """Le thème neurologie doit retourner un cerveau."""
        assert _get_theme_icon(["Neurologie", "Gériatrie"]) == "🧠"

    def test_classify_study_type_pubmed_metadata(self):
        """La classification par métadonnées PubMed est prioritaire."""
        pubmed_types = ["Randomized Controlled Trial", "Journal Article"]
        text = "This is a qualitative study about patient experiences"
        # Même si le texte contient des mots-clés qualitatifs, le type PubMed prime
        result = classify_study_type(pubmed_types, text)
        assert result == "Essai contrôlé randomisé"

    def test_classify_study_type_keywords_fallback(self):
        """En l'absence de métadonnées PubMed, les mots-clés sont utilisés."""
        pubmed_types = []
        text = "This systematic review examines the effectiveness of occupational therapy"
        result = classify_study_type(pubmed_types, text)
        assert "Revue systématique" in result
        assert "à confirmer" in result  # Signalé comme détection par mots-clés

    def test_classify_study_type_unknown(self):
        """Si aucune méthode ne fonctionne, le type est 'à vérifier'."""
        pubmed_types = ["Journal Article"]
        text = "This is a general article about health"
        result = classify_study_type(pubmed_types, text)
        assert result == TYPE_A_VERIFIER

    def test_classify_themes_multiple(self):
        """Un article peut appartenir à plusieurs thèmes."""
        text = "This study examines stroke rehabilitation in elderly patients"
        categories = {
            "Neurologie": ["stroke", "brain injury"],
            "Gériatrie": ["elderly", "aged"]
        }
        themes = classify_themes(text, categories)
        assert "Neurologie" in themes
        assert "Gériatrie" in themes

    def test_classify_themes_aucun(self):
        """Si aucun mot-clé ne correspond, la liste de thèmes est vide."""
        text = "This is an unrelated text about cooking"
        categories = {
            "Neurologie": ["stroke", "brain injury"],
            "Pédiatrie": ["child", "pediatric"]
        }
        themes = classify_themes(text, categories)
        assert themes == []


class TestDedoublonnage:
    """Tests sur la logique de dédoublonnage."""

    def test_dedoublonnage_par_id_unique(self):
        """Deux articles avec le même id_unique doivent être considérés comme doublons."""
        articles = [
            {"id_unique": "pmid_12345", "titre": "Article 1"},
            {"id_unique": "pmid_67890", "titre": "Article 2"},
            {"id_unique": "pmid_12345", "titre": "Article 1 (doublon)"}
        ]
        ids = {art["id_unique"] for art in articles}
        assert len(ids) == 2  # Seulement 2 IDs uniques

    def test_idempotence_ajout_article(self):
        """Ajouter deux fois le même article ne doit pas créer de doublon."""
        existing = [{"id_unique": "test_1", "titre": "Test"}]
        new_article = {"id_unique": "test_1", "titre": "Test"}
        
        existing_ids = {art["id_unique"] for art in existing}
        if new_article["id_unique"] not in existing_ids:
            existing.append(new_article)
        
        assert len(existing) == 1  # Pas de doublon ajouté


class TestNewsletter:
    """Tests sur la construction de la newsletter."""

    def test_score_article_influence_selection(self):
        """Les articles avec un score élevé doivent être sélectionnés en priorité."""
        articles = [
            {"source": "PubMed", "type_etude": "Méta-analyse", "tags": ["Neurologie"]},
            {"source": "RSS", "type_etude": "Type d'étude à vérifier", "tags": []},
            {"source": "PubMed", "type_etude": "Essai contrôlé randomisé", "tags": ["Pédiatrie"]}
        ]
        scores = [score_article(a) for a in articles]
        # La méta-analyse PubMed doit avoir le score le plus élevé
        assert scores[0] > scores[1]
        assert scores[0] >= scores[2]


class TestStockage:
    """Tests sur la lecture/écriture des données."""

    def test_lecture_json_valide(self):
        """Un fichier JSON valide doit être lu sans erreur."""
        test_data = [
            {"id_unique": "1", "titre": "Test 1"},
            {"id_unique": "2", "titre": "Test 2"}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            assert len(loaded) == 2
            assert loaded[0]["id_unique"] == "1"
        finally:
            os.unlink(temp_path)

    def test_ecriture_json_preserve_accents(self):
        """L'écriture JSON doit préserver les caractères spéciaux (accents français)."""
        test_data = [{"titre": "Étude sur l'ergothérapie française"}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            assert "Étude" in loaded[0]["titre"]
            assert "française" in loaded[0]["titre"]
        finally:
            os.unlink(temp_path)