"""
Construction de la newsletter ErgoVeille (Section 10 du cahier des charges).

Produit deux versions : HTML (principale) et texte (secours).
Modes :
- "preview" : génère des fichiers locaux, sans envoi et sans modifier l'état.
- "send"    : réservé au module d'envoi (étape 8.2), avec garde-fous.

CRITÈRES DE PERTINENCE (score_article) — documentés et modifiables ici :
+3 : type d'étude déterminé par les métadonnées officielles PubMed
+2 : type d'étude détecté par mots-clés (signalé "à confirmer")
+2 : publication scientifique (source PubMed) / +1 : actualité sanitaire
+1 : par thème clinique détecté (plafonné à 3)
Ce score sert UNIQUEMENT à ordonner l'affichage. Il ne qualifie jamais
la qualité méthodologique ni le niveau de preuve d'une publication.
"""

import html
import json
import os
from datetime import datetime, timedelta

import yaml

CONFIG_PATH = "config/config.yaml"
DATA_PATH = "data/articles.json"
STATE_PATH = "data/newsletter_state.json"
STATUS_PATH = "data/collect_status.json"
PREVIEW_HTML = "data/newsletter_preview.html"
PREVIEW_TXT = "data/newsletter_preview.txt"

TEAL = "#0E7C86"
DARK = "#14344F"

TYPES_FIABLES = {
    "Essai contrôlé randomisé", "Méta-analyse", "Revue systématique",
    "Recommandations professionnelles", "Essai clinique",
    "Étude observationnelle", "Étude qualitative",
    "Étude psychométrique / de validation", "Revue narrative",
}


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
    if type_etude in TYPES_FIABLES:
        score += 3
    elif type_etude.endswith("(détection par mots-clés, à confirmer)"):
        score += 2
    score += 2 if article.get("source") == "PubMed" else 1
    score += min(len(article.get("tags", [])), 3)
    return score


def limitations_text(article):
    """Limites et incertitudes affichées pour chaque article (Section 10.6)."""
    parties = []
    te = article.get("type_etude", "")
    if te == "Type d'étude à vérifier":
        parties.append("Type d'étude non déterminable automatiquement : à vérifier dans la publication originale.")
    elif te.endswith("(détection par mots-clés, à confirmer)"):
        parties.append("Type d'étude détecté par mots-clés : à confirmer dans la publication originale.")
    if article.get("source") == "PubMed":
        if not article.get("resume"):
            parties.append("Résumé non disponible : cette fiche repose uniquement sur les métadonnées.")
        else:
            parties.append("Présentation fondée uniquement sur le résumé bibliographique fourni par PubMed.")
    else:
        parties.append("Actualité institutionnelle : consulter le document original pour le détail et les limites.")
    return parties


def select_new_articles(articles, state):
    """Articles jamais envoyés (anti-répétition, Section 10)."""
    sent = set(state.get("sent_ids", []))
    return [a for a in articles if a.get("id_unique") not in sent]


def _card_html(a):
    te = html.escape(a.get("type_etude", "Type d'étude à vérifier"))
    tags = ", ".join(html.escape(t) for t in a.get("tags", [])) or "Thème non classé"
    resume = html.escape((a.get("resume") or "Résumé non disponible.")[:600])
    auteurs = html.escape(a.get("auteurs", "") or "Auteurs non disponibles")
    revue = html.escape(a.get("revue", "") or a.get("source", ""))
    annee = html.escape(str(a.get("annee", "")))
    lien = a.get("lien", "")
    lien_html = (
        f'<a href="{html.escape(lien, quote=True)}" style="color:{TEAL};font-weight:600;text-decoration:none;">'
        f'Lire la publication originale →</a>'
        if lien else '<span style="color:#8a97a5;">Lien original non disponible</span>'
    )
    limites = "".join(f"<li>{html.escape(p)}</li>" for p in limitations_text(a))
    return f"""
    <div style="border:1px solid #E1E8ED;border-left:4px solid {TEAL};border-radius:6px;padding:16px;margin-bottom:16px;">
      <p style="margin:0 0 6px;font-size:12px;color:{TEAL};font-weight:700;">{te} &nbsp;|&nbsp; {tags}</p>
      <h3 style="margin:0 0 6px;font-size:16px;color:{DARK};">{html.escape(a.get('titre', 'Sans titre'))}</h3>
      <p style="margin:0 0 8px;font-size:12px;color:#5b7285;">{auteurs} — {revue} {annee} — Source : {html.escape(a.get('source', ''))}</p>
      <p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:#33475b;">{resume}</p>
      <ul style="margin:0 0 10px;padding-left:18px;font-size:12px;color:#7a5c00;background:#FFF9EC;border-radius:4px;padding:8px 8px 8px 24px;">{limites}</ul>
      <p style="margin:0;font-size:13px;">{lien_html}</p>
    </div>"""


def build_newsletter(mode="preview"):
    cfg = load_config().get("newsletter", {})
    articles = _load_json(DATA_PATH, [])
    state = _load_json(STATE_PATH, {"sent_ids": [], "history": []})
    status = _load_json(STATUS_PATH, None)

    collect_ok = bool(status) and bool(status.get("global_ok"))

    if mode == "send" and not collect_ok:
        raise RuntimeError(
            "Refus d'envoi : la dernière collecte a échoué ou son statut est inconnu. "
            "Relancez 'python main.py' avant d'envoyer."
        )

    nouveaux = select_new_articles(articles, state)
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
    dashboard_url = cfg.get("dashboard_url", "http://localhost:8501")

    # ---------- Version HTML ----------
    h = []
    h.append(f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ErgoVeille — Votre veille hebdomadaire</title></head>
<body style="margin:0;padding:0;background-color:#F4F8F9;font-family:'Segoe UI',Arial,sans-serif;color:{DARK};">
<div style="max-width:640px;margin:0 auto;background:#ffffff;">
  <div style="background:{TEAL};color:#ffffff;padding:24px;">
    <h1 style="margin:0;font-size:24px;">ErgoVeille</h1>
    <p style="margin:4px 0 0;font-size:14px;">La veille scientifique et sanitaire en ergothérapie</p>
  </div>
  <div style="padding:24px;">
    <h2 style="color:{TEAL};font-size:20px;margin:0 0 4px;">Les dernières avancées en ergothérapie</h2>
    <p style="margin:0 0 16px;font-size:13px;color:#5b7285;">Période couverte : du {debut:%d/%m/%Y} au {now:%d/%m/%Y}</p>""")
    if mode == "preview":
        h.append('<p style="background:#E8F6F6;border-left:4px solid ' + TEAL + ';padding:10px;font-size:13px;">👁️ APERÇU LOCAL — aucun e-mail n\'a été envoyé.</p>')
    if not collect_ok:
        h.append('<p style="background:#FFF4E5;border-left:4px solid #E8A13D;padding:10px;font-size:13px;">⚠️ Alerte : la dernière collecte a partiellement échoué ou son statut est inconnu. Ce récapitulatif peut être incomplet.</p>')
    h.append(f"""
    <div style="background:#F4F8F9;border-radius:8px;padding:16px;margin-bottom:20px;">
      <h3 style="margin:0 0 8px;font-size:15px;color:{TEAL};">Cette semaine en bref</h3>
      <p style="margin:0;font-size:14px;">{len(scientifiques)} nouvelle(s) publication(s) scientifique(s) · {len(sanitaires)} actualité(s) sanitaire(s) française(s) · {len(selection_sci)} article(s) mis en avant.</p>
    </div>
    <h3 style="color:{DARK};font-size:16px;border-bottom:2px solid {TEAL};padding-bottom:6px;">Sélection d'articles scientifiques</h3>""")
    if selection_sci:
        h += [_card_html(a) for a in selection_sci]
    else:
        h.append('<p style="font-size:13px;color:#5b7285;">Aucune nouvelle publication scientifique cette semaine.</p>')
    h.append('<h3 style="color:%s;font-size:16px;border-bottom:2px solid %s;padding-bottom:6px;">Actualités sanitaires françaises</h3>' % (DARK, TEAL))
    if selection_san:
        h += [_card_html(a) for a in selection_san]
    else:
        h.append('<p style="font-size:13px;color:#5b7285;">Aucune nouvelle actualité sanitaire cette semaine.</p>')
    if autres_sci:
        h.append('<h3 style="color:%s;font-size:16px;border-bottom:2px solid %s;padding-bottom:6px;">Autres publications</h3>' % (DARK, TEAL))
        h += [_card_html(a) for a in autres_sci]
    h.append(f"""
    <div style="background:#E8F6F6;border-radius:8px;padding:14px;margin-top:20px;font-size:13px;">
      <strong>À retenir pour la pratique :</strong> cette veille est une aide à la réflexion
      et ne constitue ni une recommandation officielle ni une preuve d'efficacité.
      Consultez toujours les publications originales.
    </div>
    <p style="margin-top:16px;font-size:13px;">
      <a href="{html.escape(dashboard_url, quote=True)}" style="color:{TEAL};font-weight:600;">Ouvrir le tableau de bord ErgoVeille →</a>
    </p>
  </div>
  <div style="background:{DARK};color:#cfd8e3;padding:16px;font-size:12px;text-align:center;">
    ErgoVeille — veille automatisée · Envoyé par veille@ergoland.fr ·
    <a href="#" style="color:#cfd8e3;">Se désabonner</a>
  </div>
</div></body></html>""")
    html_out = "\n".join(h)

    # ---------- Version texte de secours ----------
    t = []
    t.append("ERGOVEILLE — VOTRE VEILLE HEBDOMADAIRE")
    t.append(f"Période couverte : du {debut:%d/%m/%Y} au {now:%d/%m/%Y}")
    t.append("=" * 60)
    if not collect_ok:
        t.append("ALERTE : dernière collecte partiellement échouée ou statut inconnu.")
    t.append(f"Cette semaine : {len(scientifiques)} publication(s) scientifique(s), {len(sanitaires)} actualité(s) sanitaire(s).")
    t.append("")
    t.append("SÉLECTION D'ARTICLES SCIENTIFIQUES")
    t.append("-" * 60)
    for a in selection_sci:
        t.append(f"* {a.get('titre', 'Sans titre')}")
        t.append(f"  Type d'étude : {a.get('type_etude', 'n/d')} | Thèmes : {', '.join(a.get('tags', [])) or 'n/d'}")
        t.append(f"  Source : {a.get('source', '')} | Lien : {a.get('lien', 'n/d')}")
        t.append("")
    t.append("ACTUALITÉS SANITAIRES FRANÇAISES")
    t.append("-" * 60)
    for a in selection_san:
        t.append(f"* {a.get('titre', 'Sans titre')}")
        t.append(f"  Source : {a.get('source', '')} | Lien : {a.get('lien', 'n/d')}")
        t.append("")
    t.append("AUTRES PUBLICATIONS")
    t.append("-" * 60)
    for a in autres_sci:
        t.append(f"* {a.get('titre', 'Sans titre')} | Lien : {a.get('lien', 'n/d')}")
    t.append("")
    t.append(f"Tableau de bord : {dashboard_url}")
    t.append("Aide à la réflexion, ni recommandation officielle ni preuve d'efficacité.")
    txt_out = "\n".join(t)

    with open(PREVIEW_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)
    with open(PREVIEW_TXT, "w", encoding="utf-8") as f:
        f.write(txt_out)

    print("📨 Newsletter générée (mode prévisualisation)")
    print(f"   Période : du {debut:%d/%m/%Y} au {now:%d/%m/%Y}")
    print(f"   Nouveautés scientifiques : {len(scientifiques)} (dont {len(selection_sci)} mises en avant)")
    print(f"   Actualités sanitaires : {len(sanitaires)} (dont {len(selection_san)} affichées)")
    print(f"   Autres publications : {len(autres_sci)}")
    print(f"   Statut de la dernière collecte : {'✅ OK' if collect_ok else '⚠️ inconnu ou en échec'}")
    print(f"   Fichiers créés : {PREVIEW_HTML} et {PREVIEW_TXT}")
    return {"html": PREVIEW_HTML, "txt": PREVIEW_TXT}


if __name__ == "__main__":
    build_newsletter(mode="preview")