# 🧠 ErgoVeille

**Veille scientifique et sanitaire automatisée pour l'ergothérapie.**

ErgoVeille est une application Python open-source qui collecte, classe et diffuse automatiquement les dernières publications scientifiques issues de PubMed et les actualités sanitaires françaises publiées par la Haute Autorité de Santé (HAS), Santé publique France et l'Agence nationale de sécurité du médicament et des produits de santé (ANSM).

L'objectif est de faciliter la veille professionnelle des ergothérapeutes en centralisant les informations pertinentes pour leur pratique clinique.

## ✨ Fonctionnalités

- **Collecte automatisée** : exécution hebdomadaire via GitHub Actions ou lancement manuel.
- **Dédoublonnage intelligent** : identification des doublons grâce aux identifiants uniques, notamment le PMID pour PubMed et l'URL pour les flux RSS.
- **Classification automatique** : classement des publications par thème clinique (neurologie, pédiatrie, gériatrie, etc.) et par type d'étude, avec signalement explicite des incertitudes.
- **Tableau de bord web** : interface Streamlit responsive avec recherche textuelle, filtres multiples, export CSV et mode sombre/clair.
- **Traduction automatique** : titres et résumés PubMed traduits de l'anglais vers le français (DeepL Free API + fallback MyMemory), stockés pour éviter la re-consommation de tokens.
- **Newsletter hebdomadaire** : génération de newsletters HTML et TXT, avec prévisualisation, envoi par SMTP et personnalisation par abonné (filtrage par thèmes).
- **Design éditorial** : newsletter au format magazine scientifique (palette bleu nuit, ivoire, vert sauge).
- **Score de pertinence explicable** : classement basé sur le type d'étude, la source et les thèmes (documenté et modifiable).
- **Sauvegarde automatique** : script de backup des données avec rotation (conservation des 5 dernières sauvegardes).
- **Tests automatisés** : vérification du fonctionnement du code à l'aide de pytest.
- **Coût de fonctionnement cible : 0 €/mois** : utilisation des offres gratuites de GitHub Actions, Streamlit Community Cloud, DeepL Free API (500 000 caractères/mois) et MyMemory.

## Sources utilisées

### Publications scientifiques

- **PubMed** : recherche de publications scientifiques à l'aide de l'API officielle E-utilities.

### Actualités sanitaires françaises

- **Haute Autorité de Santé (HAS)** : recommandations, évaluations et publications institutionnelles.
- **Santé publique France** : actualités, rapports et données de santé publique.
- **Agence nationale de sécurité du médicament et des produits de santé (ANSM)** : informations de sécurité, alertes et actualités relatives aux produits de santé.
- **ANFE (Alliance Francophone des Ergothérapeutes)** : actualités professionnelles et annonces.
- **CNSA (Caisse Nationale de Solidarité pour l'Autonomie)** : actualités sur l'autonomie, le handicap et le médico-social.

Les actualités sanitaires sont collectées à partir des flux RSS configurés dans l'application.

**Sources testées mais non disponibles en RSS** (vérifié le 2026-10-13) :

- **SYNFEL (Syndicat National des Ergothérapeutes Libéraux)** : pas de flux RSS détecté.
- **RFRE (Revue Francophone de Recherche en Ergothérapie)** : pas de flux RSS détecté.
- **SOFEC (Société Française d'Ergothérapie en Clinique)** : pas de flux RSS détecté.
- **Cochrane France** : pas de flux RSS français détecté.
- **Ministère de la Santé** : pas de flux RSS détecté.

Pour ces sources, une veille manuelle assistée peut être envisagée si nécessaire.

## 🏗️ Architecture du projet

```text
ErgoVeille/
├── .github/
│   └── workflows/
│       ├── collect.yml
│       └── newsletter.yml
├── config/
│   ├── abonnes.yaml
│   └── config.yaml
├── scripts/
│   └── backup_data.py
├── src/
│   ├── __init__.py
│   ├── collectors/
│   ├── newsletter/
│   ├── processing/
│   ├── storage/
│   └── tests/
│       └── test_smtp.py
├── tests/
│   └── test_core.py
├── data/
│   ├── articles.json
│   ├── collect_status.json
│   └── sources_status.json
├── backups/                     # Non versionné
├── .env                         # Non versionné
├── .env.example
├── .gitignore
├── app.py
├── main.py
├── generate_newsletter.py
├── traduire_historique.py
├── enrich_doi.py
├── verify_pro_sources.py
├── requirements.txt
├── README.md
├── DEPANNAGE.md
└── SOURCES.md
```

## ⚙️ Prérequis et installation locale

### 1. Prérequis

- Python 3.10 ou version compatible.
- Git.
- Visual Studio Code (recommandé).
- Un compte GitHub.
- Un compte Streamlit Community Cloud (optionnel, pour l'hébergement).
- Un compte DeepL Free API (optionnel, pour améliorer la qualité des traductions).

### 2. Cloner le dépôt

```bash
git clone https://github.com/YoannSLRD/ErgoVeille.git
cd ErgoVeille
```

### 3. Créer un environnement virtuel

Sous Windows (PowerShell) :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Si l'activation est bloquée, utilise l'invite de commandes :

```bat
venv\Scripts\activate.bat
```

### 4. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurer les variables d'environnement

Copie le fichier d'exemple :

```powershell
Copy-Item .env.example .env
```

Édite `.env` et renseigne les paramètres SMTP. Ajoute éventuellement ta clé DeepL :

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=votre.adresse@example.com
SMTP_PASSWORD=votre_mot_de_passe
EMAIL_SENDER=veille@exemple.com
EMAIL_SENDER_NAME=ErgoVeille
NEWSLETTER_SEND_ENABLED=false
DEEPL_API_KEY=votre_cle_deepl:fx
```

**Sécurité :** ne publie jamais `.env`, tes mots de passe ou tes clés API sur GitHub. Vérifie que `.env` est bien exclu dans `.gitignore`.

## 🚀 Lancement de l'application

### Lancer une collecte manuelle

```bash
python main.py
```

Le script affiche un bilan de collecte (articles trouvés, ajoutés, doublons ignorés).

### Lancer le tableau de bord

```bash
streamlit run app.py
```

Ouvre l'adresse affichée (généralement `http://localhost:8501`).

**Mode sombre :** clique sur l'icône 🌙 en haut à droite pour basculer entre mode clair et sombre.

**Traduction :** coche la case "🇫 Afficher les titres et résumés en français" pour afficher les traductions stockées.

### Prévisualiser la newsletter

```bash
python generate_newsletter.py --preview
```

### Envoyer une newsletter de test

```bash
python generate_newsletter.py --send-test
```

### Envoyer la newsletter à tous les abonnés

```bash
python generate_newsletter.py --send-all
```

La commande demande une confirmation interactive (`OUI`) avant envoi.

### Configuration des abonnés

Édite `config/abonnes.yaml` :

```yaml
abonnes:
  - nom: "Yoann"
    email: "monadressemail@ergoland.fr"
    themes: [] # [] = tous les thèmes
    actif: true

  - nom: "Collègue pédiatrie"
    email: "collegue@exemple.fr"
    themes: ["Pédiatrie"] # ne reçoit que ce thème
    actif: true
```

### Traduire l'historique des articles

Pour traduire tous les articles PubMed déjà collectés qui n'ont pas encore de traduction :

```bash
python traduire_historique.py
```

Le script utilise DeepL (si la clé est configurée) avec fallback automatique sur MyMemory. Il sauvegarde la progression tous les 10 articles et peut être interrompu puis relancé sans retraduire les articles déjà traités.

### Sauvegarder les données

Avant une modification importante :

```bash
python scripts/backup_data.py
```

Les sauvegardes sont stockées dans `backups/` avec un timestamp. Les 5 sauvegardes les plus récentes sont conservées automatiquement.

### Exécuter les tests automatisés

```bash
pytest tests/ -v
```

## 📰 Fonctionnement de la veille

1. **Collecte** : récupération des publications (PubMed) et actualités (RSS).
2. **Normalisation** : harmonisation des métadonnées.
3. **Dédoublonnage** : identification des publications déjà présentes.
4. **Classification** : attribution de thèmes et type d'étude.
5. **Scoring** : calcul d'un score de pertinence explicable.
6. **Traduction** : traduction des titres et résumés PubMed (une seule fois, stockée).
7. **Sauvegarde** : enregistrement dans `data/articles.json`.
8. **Consultation** : via le tableau de bord Streamlit.
9. **Newsletter** : génération et envoi aux abonnés actifs.

## 🌐 Déploiement

### 1. Tableau de bord Streamlit Community Cloud

1. Publie le dépôt sur GitHub.
2. Connecte-toi à Streamlit Community Cloud.
3. Crée une nouvelle application en sélectionnant le dépôt.
4. Branche : `main`, fichier principal : `app.py`.
5. Configure les secrets nécessaires.

**Note :** le tableau de bord lit `data/articles.json`. Ce fichier doit être présent dans le dépôt ou généré par le workflow de collecte.

### 2. Automatisation avec GitHub Actions

Deux workflows sont configurés :

- **`collect.yml`** : collecte automatique chaque lundi à 08:00 UTC.
- **`newsletter.yml`** : envoi automatique de la newsletter chaque lundi à 09:00 UTC (1 heure après la collecte).

Les deux workflows peuvent être lancés manuellement via l'onglet **Actions** de GitHub.

### 3. Secrets GitHub requis

Dans **Settings → Secrets and variables → Actions**, configure :

| Secret              | Description                                    |
| ------------------- | ---------------------------------------------- |
| `SMTP_HOST`         | Serveur SMTP (ex: `smtp.hostinger.com`)        |
| `SMTP_PORT`         | Port (ex: `465`)                               |
| `SMTP_USER`         | Adresse email expéditrice                      |
| `SMTP_PASSWORD`     | Mot de passe SMTP                              |
| `EMAIL_SENDER`      | Adresse email affichée                         |
| `EMAIL_SENDER_NAME` | Nom affiché (ex: `ErgoVeille`)                 |
| `DEEPL_API_KEY`     | Clé API DeepL (optionnelle, format `xxxxx:fx`) |

Et dans l'onglet **Variables** :

| Variable                 | Valeur par défaut | Description                                     |
| ------------------------ | ----------------- | ----------------------------------------------- |
| `ENABLE_AUTO_NEWSLETTER` | `false`           | Passe à `true` pour activer l'envoi automatique |

## ⚠️ Limites et considérations

### Classification

La classification automatique facilite la recherche mais ne remplace pas une analyse critique. La mention « à confirmer » est conservée lorsque le type d'étude est incertain. **Le type d'étude ne constitue pas un niveau de preuve scientifique.**

### Traduction

Les traductions sont fournies à titre indicatif. La mention « traduction automatique » est obligatoire. Consultez toujours la source originale pour les détails méthodologiques.

### Score de pertinence

Le score dépend des règles de pondération et des métadonnées disponibles. Il ne remplace ni la lecture critique ni l'évaluation méthodologique.

### Couverture documentaire

L'absence d'une publication dans ErgoVeille ne signifie pas qu'aucune publication pertinente n'existe.

### Quotas et disponibilité

- **PubMed** : respecte les conditions d'utilisation de l'API E-utilities.
- **DeepL Free API** : 500 000 caractères/mois (environ 1300 articles). Au-delà, bascule automatique sur MyMemory.
- **MyMemory** : fallback gratuit, qualité correcte, limite journalière.
- **GitHub Actions** : quotas gratuits mensuels (2000 minutes/mois).
- **Streamlit Community Cloud** : quotas gratuits avec limitations.

### Coût de fonctionnement

L'objectif est de fonctionner sans coût mensuel. Cette gratuité dépend des conditions commerciales et des quotas des services tiers.

## 🛠️ Dépannage

Consulte [DEPANNAGE.md](DEPANNAGE.md) pour les solutions aux erreurs courantes :

- Conflits Git lors d'un `git push`.
- Erreurs de lecture de `data/articles.json`.
- Problèmes d'envoi de newsletter.
- Erreurs d'importation Python et tests pytest.
- Échecs de GitHub Actions.
- Erreurs de déploiement Streamlit.
- Quota DeepL dépassé (bascule automatique sur MyMemory).
- Mode sombre non appliqué (cache du navigateur).

## ✅ Checklist de mise en production

- [ ] `.env` configuré et exclu de Git.
- [ ] `python main.py` s'exécute sans erreur.
- [ ] `data/articles.json` est créé ou mis à jour.
- [ ] `streamlit run app.py` affiche le tableau de bord.
- [ ] `python generate_newsletter.py --preview` fonctionne.
- [ ] L'envoi de test est vérifié.
- [ ] `pytest tests/ -v` passe avec succès.
- [ ] GitHub Actions configuré et vérifié.
- [ ] Secrets GitHub ajoutés.
- [ ] Variable `ENABLE_AUTO_NEWSLETTER` configurée.
- [ ] `README.md` et `DEPANNAGE.md` à jour.

## 🤝 Contribution

1. Active l'environnement virtuel.
2. Exécute les tests : `pytest tests/ -v`.
3. Vérifie que les secrets ne sont pas ajoutés au dépôt.
4. Documente les changements.
5. Soumets via un commit ou une pull request.

## 📄 Licence

La licence du projet doit être précisée dans un fichier `LICENSE`. Ne considère pas le projet comme distribué sous une licence particulière tant que celle-ci n'a pas été explicitement choisie.

---

_ErgoVeille — faciliter la veille scientifique et sanitaire au service de la pratique en ergothérapie._
