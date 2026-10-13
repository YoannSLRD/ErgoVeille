"""
Script de maintenance ErgoVeille (version 2).
Enrichit les articles PubMed avec :
- leur DOI (esummary, articleids)
- leur date de publication réelle (esummary, pubdate)
Relançable sans risque : les champs déjà remplis sont conservés.
"""
import json
import time
from datetime import datetime

from Bio import Entrez

DATA_PATH = "data/articles.json"
BATCH = 100

MOIS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_pubdate(valeur):
    """Convertit un pubdate PubMed ('2026 Oct 9', '2026 Oct', '2026') en ISO."""
    if not valeur:
        return ""
    parts = str(valeur).split()
    try:
        annee = int(parts[0])
    except (ValueError, IndexError):
        return ""
    mois, jour = 1, 1
    if len(parts) >= 2 and parts[1] in MOIS:
        mois = MOIS[parts[1]]
        if len(parts) >= 3:
            try:
                jour = int(parts[2])
            except ValueError:
                jour = 1
    try:
        return datetime(annee, mois, jour).isoformat()
    except ValueError:
        return ""


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    Entrez.email = "veille@ergoland.fr"
    Entrez.tool = "ErgoVeille"

    targets = [
        a for a in articles
        if a.get("source") == "PubMed"
        and str(a.get("pmid", "")).isdigit()
        and (not a.get("doi") or not a.get("date_publication"))
    ]
    print(f"🎯 {len(targets)} article(s) PubMed à enrichir (DOI et/ou date).")

    if not targets:
        print("✅ Rien à faire.")
        return

    pmids = [a["pmid"] for a in targets]
    doi_map = {}
    date_map = {}

    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i + BATCH]
        print(f"   🔎 Lot {i // BATCH + 1} : {len(batch)} PMID(s)...")
        try:
            handle = Entrez.esummary(db="pubmed", id=",".join(batch), retmode="json")
            data = json.load(handle)
            handle.close()

            result = data.get("result", {})
            for uid, rec in result.items():
                if uid == "uids":
                    continue
                for aid in rec.get("articleids", []):
                    if aid.get("idtype") == "doi":
                        doi_map[str(uid)] = aid.get("value", "")
                        break
                date_iso = parse_pubdate(rec.get("pubdate", ""))
                if date_iso:
                    date_map[str(uid)] = date_iso
        except Exception as e:
            print(f"   ❌ Erreur sur le lot : {e}")
        time.sleep(0.4)

    nb_doi = nb_date = 0
    for a in articles:
        pmid = str(a.get("pmid", ""))
        if a.get("source") != "PubMed" or not pmid.isdigit():
            continue
        if not a.get("doi") and pmid in doi_map and doi_map[pmid]:
            a["doi"] = doi_map[pmid]
            a["lien_doi"] = f"https://doi.org/{doi_map[pmid]}"
            nb_doi += 1
        if not a.get("date_publication") and pmid in date_map:
            a["date_publication"] = date_map[pmid]
            nb_date += 1

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

    print("💾 Enrichissement terminé :")
    print(f"   - {nb_doi} DOI ajouté(s)")
    print(f"   - {nb_date} date(s) de publication ajoutée(s)")


if __name__ == "__main__":
    main()