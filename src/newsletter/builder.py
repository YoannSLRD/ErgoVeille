"""
Construction de la newsletter ErgoVeille (Section 10 du cahier des charges).

Direction artistique : Éditoriale, sobre, inspirée d'une revue scientifique professionnelle.
"""

import html
import json
import os
from datetime import datetime, timedelta
from src.processing.translator import traduire_texte, est_traduction_active

import yaml

CONFIG_PATH = "config/config.yaml"
DATA_PATH = "data/articles.json"
STATE_PATH = "data/newsletter_state.json"
STATUS_PATH = "data/collect_status.json"
TEMPLATE_PATH = "src/newsletter/template.html"
PREVIEW_HTML = "data/newsletter_preview.html"
PREVIEW_TXT = "data/newsletter_preview.txt"


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def score_article(article):
    """Score de pertinence explicable (voir docstring du module)."""
    score = 0
    type_etude = article.get("type_etude", "")
    if type_etude in {"Essai contrôlé randomisé", "Méta-analyse", "Revue systématique", "Recommandations professionnelles"}:
        score += 3
    elif type_etude.endswith("(détection par mots-clés, à confirmer)"):
        score += 2
    score += 2 if article.get("source") == "PubMed" else 1
    score += min(len(article.get("tags", [])), 3)
    return score


def _get_theme_icon(tags):
    """Retourne un emoji selon le thème principal."""
    if not tags:
        return "📚"
    tag_lower = tags[0].lower()
    icons = {
        "neurologie": "🧠",
        "pédiatrie": "👶",
        "gériatrie": "👴",
        "santé mentale": "💚",
        "handicap et technologie": "♿",
    }
    for theme, icon in icons.items():
        if theme in tag_lower:
            return icon
    return "📚"


def _card_html(a, traduire=False):
    """Génère une carte d'article avec traduction optionnelle."""
    te = html.escape(a.get("type_etude", "Type d'étude à vérifier"))
    tags = ", ".join(html.escape(t) for t in a.get("tags", [])) or "Thème non classé"
    
    # 🆕 Traduction du titre (uniquement pour PubMed, si activée)
    titre = a.get('titre', 'Sans titre')
    titre_traduit = None
    if traduire and a.get("source") == "PubMed" and len(titre.strip()) >= 10:
        from src.processing.translator import traduire_texte
        titre_traduit = traduire_texte(titre)
    
    # 🆕 Traduction du résumé
    resume = a.get("resume") or "Résumé non disponible."
    resume_traduit = None
    mention_traduction = ""
    if traduire and a.get("source") == "PubMed" and len(resume.strip()) >= 20:
        from src.processing.translator import traduire_texte
        resume_traduit = traduire_texte(resume)
        # N'ajouter la mention que si la traduction a réussi
        if resume_traduit and resume_traduit != resume:
            resume = resume_traduit
            mention_traduction = '<span style="font-size:9px;color:#78978A;font-style:italic;"> (traduction automatique)</span>'
    
    resume = html.escape(resume[:300])
    
    # Utiliser le titre traduit si disponible, sinon l'original
    titre_affiche = titre_traduit if titre_traduit and titre_traduit != titre else titre
    titre_affiche = html.escape(titre_affiche)
    
    auteurs = html.escape(a.get("auteurs", "") or "Auteurs non disponibles")
    revue = html.escape(a.get("revue", "") or a.get("source", ""))
    annee = html.escape(str(a.get("annee", "")))
    lien = a.get("lien", "")
    lien_safe = lien if lien.startswith("https://") else "#"
    
    return f"""
    <div class="article-card">
      <span class="article-badge">{te}</span>
      <h3 class="article-title">{titre_affiche}</h3>
      <p class="article-meta">{auteurs} &mdash; {revue} {annee} &mdash; {tags}</p>
      <p class="article-excerpt">{resume}...{mention_traduction}</p>
      <a href="{lien_safe}" class="article-button" target="_blank">Lire la publication <span>&rarr;</span></a>
    </div>"""


def build_newsletter(mode="preview", themes=None, suffixe=""):
    cfg = load_config().get("newsletter", {})
    articles = _load_json(DATA_PATH, [])
    state = _load_json(STATE_PATH, {"sent_ids": [], "history": []})
    status = _load_json(STATUS_PATH, None)

    collect_ok = bool(status) and bool(status.get("global_ok"))

    if mode == "send" and not collect_ok:
        raise RuntimeError(
            "Refus d'envoi : la dernière collecte a échoué ou son statut est inconnu."
        )

    # Filtrer les articles jamais envoyés
    sent_ids = set(state.get("sent_ids", []))
    nouveaux = [a for a in articles if a.get("id_unique") not in sent_ids]

    # 🆕 Personnalisation par thèmes (Section 10) :
    # si une liste de thèmes est fournie, ne conserver que les articles
    # portant au moins un de ces thèmes.
    if themes:
        nouveaux = [
            a for a in nouveaux
            if any(t in (a.get("tags") or []) for t in themes)
        ]
    
    scientifiques = sorted(
        [a for a in nouveaux if a.get("source") == "PubMed"],
        key=score_article, reverse=True)
    sanitaires = sorted(
        [a for a in nouveaux if a.get("source") != "PubMed"],
        key=lambda a: a.get("date_collecte", ""), reverse=True)

    max_sci = int(cfg.get("max_articles_scientifiques", 5))
    max_san = int(cfg.get("max_articles_sanitaires", 5))
    selection_sci = scientifiques[:max_sci]
    autres_sci = scientifiques[max_sci:]
    selection_san = sanitaires[:max_san]

    now = datetime.now()
    debut = now - timedelta(days=int(cfg.get("periode_jours", 7)))
    
    # Gestion intelligente du lien dashboard
    dashboard_url_cfg = cfg.get("dashboard_url", "http://localhost:8501")
    # Si c'est localhost, on met un lien neutre pour éviter la confusion sur mobile
    dashboard_url = "#" if "localhost" in dashboard_url_cfg else dashboard_url_cfg
    
    numero_semaine = now.isocalendar()[1]

    # Charger le template
    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ Template introuvable : {TEMPLATE_PATH}")
        print("💡 Assure-toi d'avoir créé src/newsletter/template.html avec le nouveau code.")
        return None

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Calcul corrigé du nombre de sélections (scientifiques + sanitaires)
    nb_selection = len(selection_sci) + len(selection_san)

    # Remplacer les placeholders
    html_out = template
    html_out = html_out.replace("{{DEBUT}}", debut.strftime("%d/%m/%Y"))
    html_out = html_out.replace("{{FIN}}", now.strftime("%d/%m/%Y"))
    html_out = html_out.replace("{{NUMERO}}", str(numero_semaine))
    html_out = html_out.replace("{{NB_SCIENTIFIQUES}}", str(len(scientifiques)))
    html_out = html_out.replace("{{NB_SANITAIRES}}", str(len(sanitaires)))
    html_out = html_out.replace("{{NB_SELECTION}}", str(nb_selection))
    html_out = html_out.replace("{{DASHBOARD_URL}}", dashboard_url)
    html_out = html_out.replace("{{DESABONNEMENT_URL}}", "#")
    html_out = html_out.replace("{{CONTACT_URL}}", "mailto:veille@ergoland.fr")

    # Générer les cartes d'articles
    # 🆕 Traduction activée ?
    traduire = est_traduction_active(load_config())
    
    articles_sci_html = "\n".join([_card_html(a, traduire=traduire) for a in selection_sci]) if selection_sci else '<p style="font-size:14px;color:#65716F;">Aucune nouvelle publication scientifique cette semaine.</p>'
    articles_san_html = "\n".join([_card_html(a, traduire=traduire) for a in selection_san]) if selection_san else '<p style="font-size:14px;color:#65716F;">Aucune nouvelle actualité sanitaire cette semaine.</p>'
    
    # Si on est en mode preview et qu'il n'y a pas de nouveaux articles, on en affiche quelques-uns anciens pour le test visuel
    if mode == "preview" and nb_selection == 0 and len(articles) > 0:
        articles_sci_html = "\n".join([_card_html(a) for a in scientifiques[:3]])
        articles_san_html = "\n".join([_card_html(a) for a in sanitaires[:2]])
        html_out = html_out.replace("Le regard de la semaine", "Le regard de la semaine (Mode Aperçu : anciens articles affichés)")

    html_out = html_out.replace("{{ARTICLES_SCIENTIFIQUES}}", articles_sci_html)
    html_out = html_out.replace("{{ARTICLES_SANITAIRES}}", articles_san_html)

    # Ajouter le bandeau APERÇU si mode preview
    if mode == "preview":
        preview_banner = '''
        <div style="background:#EAF0E9; border-left:3px solid #416F6B; padding:12px 16px; margin-bottom:24px; font-family:Arial, sans-serif; font-size:12px; color:#365F56;">
          👁️ <strong>APERÇU LOCAL</strong> — Aucun e-mail n'a été envoyé. Ce rendu est une simulation.
        </div>'''
        html_out = html_out.replace('<div class="content">', f'<div class="content">{preview_banner}')

    # Version texte de secours
    t = []
    t.append("ERGOVEILLE — VOTRE VEILLE SCIENTIFIQUE ET SANITAIRE")
    t.append(f"Édition n° {numero_semaine} | Période : du {debut:%d/%m/%Y} au {now:%d/%m/%Y}")
    t.append("=" * 70)
    t.append(f"Cette semaine : {len(scientifiques)} publication(s) scientifique(s), {len(sanitaires)} actualité(s) sanitaire(s).")
    t.append("")
    t.append("SÉLECTION SCIENTIFIQUE")
    t.append("-" * 70)
    for a in selection_sci:
        t.append(f"* {a.get('titre', 'Sans titre')}")
        t.append(f"  Type : {a.get('type_etude', 'n/d')} | Thèmes : {', '.join(a.get('tags', [])) or 'n/d'}")
        t.append(f"  Lien : {a.get('lien', 'n/d')}")
        t.append("")
    t.append("ACTUALITÉS SANITAIRES")
    t.append("-" * 70)
    for a in selection_san:
        t.append(f"* {a.get('titre', 'Sans titre')}")
        t.append(f"  Source : {a.get('source', '')} | Lien : {a.get('lien', 'n/d')}")
        t.append("")
    txt_out = "\n".join(t)

    # Sauvegarder
    os.makedirs("data", exist_ok=True)
    preview_html = PREVIEW_HTML if not suffixe else PREVIEW_HTML.replace(".html", f"{suffixe}.html")
    preview_txt = PREVIEW_TXT if not suffixe else PREVIEW_TXT.replace(".txt", f"{suffixe}.txt")
    with open(preview_html, "w", encoding="utf-8") as f:
        f.write(html_out)
    with open(preview_txt, "w", encoding="utf-8") as f:
        f.write(txt_out)

    mode_label = "prévisualisation" if mode == "preview" else "envoi réel"
    print(f"📨 Newsletter générée (mode {mode_label})")
    print(f"   Période : du {debut:%d/%m/%Y} au {now:%d/%m/%Y}")
    print(f"   Nouveautés scientifiques : {len(scientifiques)} (dont {len(selection_sci)} mises en avant)")
    print(f"   Actualités sanitaires : {len(sanitaires)} (dont {len(selection_san)} affichées)")
    print(f"   Total contenus sélectionnés : {nb_selection}")
    print(f"   Statut de la dernière collecte : {'✅ OK' if collect_ok else '⚠️ inconnu ou en échec'}")
    print(f"   Fichiers créés : {preview_html} et {preview_txt}")
    return {"html": preview_html, "txt": preview_txt}


if __name__ == "__main__":
    build_newsletter(mode="preview")