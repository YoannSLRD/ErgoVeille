# Documentation des sources ErgoVeille

## Sources scientifiques

### PubMed (API E-utilities)

- **Mode de collecte** : API REST officielle via Biopython
- **Fréquence** : Hebdomadaire (configurable)
- **Limites** :
  - Maximum 3 requêtes/seconde (respecté)
  - Nécessite un email de contact (fourni)
  - `retmax` configurable (actuellement 50 articles par collecte)
- **Conditions** : Utilisation gratuite, respect des guidelines NCBI
- **Documentation** : https://www.ncbi.nlm.nih.gov/books/NBK25501/

---

## Sources sanitaires françaises

### HAS (Haute Autorité de Santé)

- **URL** : https://www.has-sante.fr/feed/Rss2.jsp?id=p_3082237
- **Mode de collecte** : Flux RSS 2.0 standard via `feedparser`
- **Fréquence** : 1-2 publications par semaine observées
- **Contenu** : Recommandations, certifications, évaluations
- **Limites** : Flux limité aux 50 derniers articles
- **Conditions** : Flux public, réutilisation autorisée

### ANSM (Agence nationale de sécurité du médicament)

- **URL** : https://ansm.sante.fr/rss/actualites
- **Mode de collecte** : Flux RSS 2.0 avec parser XML manuel
- **Fréquence** : Variable (flux parfois vide)
- **Contenu** : Actualités sur les médicaments, dispositifs médicaux, vigilance
- **Limites** : Le flux peut être vide certains jours (pas d'actualités)
- **Conditions** : Flux public, réutilisation autorisée
- **Note** : Collecte incrémentale active, capturera les publications dès leur mise en ligne

### Santé publique France - Actualités

- **URL** : https://www.santepubliquefrance.fr/rss/news/1008
- **Mode de collecte** : Flux RSS standard via `feedparser`
- **Fréquence** : Plusieurs publications par semaine
- **Contenu** : Actualités épidémiologiques, alertes sanitaires, études
- **Limites** : 30 derniers articles
- **Conditions** : Flux public, réutilisation autorisée

### Santé publique France - Communiqués de presse

- **URL** : https://www.santepubliquefrance.fr/rss/press-releases
- **Mode de collecte** : Flux RSS standard via `feedparser`
- **Fréquence** : Variable selon l'actualité
- **Contenu** : Communiqués officiels, points de situation
- **Limites** : 30 derniers communiqués
- **Conditions** : Flux public, réutilisation autorisée

---

## Sources non intégrées

### Santé publique France (URL principale)

- **URL testée** : https://www.santepubliquefrance.fr/rss/actualites
- **Statut** : ❌ Indisponible (HTTP 500)
- **Alternative** : Utilisation des flux `/news/1008` et `/press-releases` qui fonctionnent

---

## Respect des conditions d'utilisation

Toutes les sources intégrées respectent les principes suivants :

- ✅ Utilisation des API officielles ou flux RSS publics
- ✅ User-Agent identifiable : `ErgoVeille/1.0 (veille scientifique ergothérapie; mailto:veille@ergoland.fr)`
- ✅ Respect des limites de débit (délais entre requêtes)
- ✅ Pas de scraping agressif
- ✅ Collecte incrémentale (pas de re-téléchargement des articles déjà connus)
- ✅ Attribution de la source dans les métadonnées

## Mises à jour

Cette documentation sera mise à jour si :

- Une source change d'URL ou de format
- Une nouvelle source est intégrée
- Les conditions d'utilisation évoluent
