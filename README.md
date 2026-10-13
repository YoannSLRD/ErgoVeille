# 🧠 ErgoVeille

**Veille scientifique et sanitaire automatisée pour l'ergothérapie.**

ErgoVeille est une application Python open-source qui collecte, classe et diffuse automatiquement les dernières publications scientifiques issues de PubMed et les actualités sanitaires françaises publiées par la Haute Autorité de Santé (HAS), Santé publique France et l'Agence nationale de sécurité du médicament et des produits de santé (ANSM).

L'objectif est de faciliter la veille professionnelle des ergothérapeutes en centralisant les informations pertinentes pour leur pratique clinique.

## ✨ Fonctionnalités

- **Collecte automatisée** : exécution hebdomadaire via GitHub Actions ou lancement manuel.
- **Dédoublonnage intelligent** : identification des doublons grâce aux identifiants uniques, notamment le PMID pour PubMed et l'URL pour les flux RSS.
- **Classification automatique** : classement des publications par thème clinique (neurologie, pédiatrie, gériatrie, etc.) et par type d'étude, avec signalement explicite des incertitudes.
- **Tableau de bord web** : interface Streamlit responsive avec recherche textuelle, filtres multiples et export des données.
- **Newsletter hebdomadaire** : génération de newsletters aux formats HTML et TXT, avec prévisualisation et envoi par SMTP.
- **Design éditorial** : newsletter au format magazine scientifique (palette bleu nuit, ivoire, vert sauge).
- **Score de pertinence explicable** : classement basé sur le type d'étude, la source et les thèmes (documenté et modifiable).
- **Automatisation du traitement** : orchestration des collectes, du traitement des publications et de la sauvegarde des données.
- **Tests automatisés** : vérification du fonctionnement du code à l'aide de pytest.
- **Coût de fonctionnement cible : 0 €/mois** : utilisation des offres gratuites de GitHub Actions et Streamlit Community Cloud, dans la limite de leurs quotas.

## 📚 Sources utilisées

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
├── app.py                      # Point d'entrée du tableau de bord Streamlit
├── main.py                     # Orchestration de la collecte et du traitement
├── generate_newsletter.py      # Génération et envoi de la newsletter
├── requirements.txt            # Dépendances Python
├── config/
│   └── config.yaml             # Configuration des requêtes, catégories et flux RSS
├── src/
│   ├── collectors/             # Collecteurs PubMed et RSS
│   ├── processing/             # Classification et dédoublonnage
│   └── newsletter/             # Construction et envoi de la newsletter
├── data/                       # Articles et données de suivi
├── tests/                      # Tests automatisés avec pytest
├── .github/
│   └── workflows/
│       └── collect.yml         # Automatisation GitHub Actions
├── .env.example                # Exemple de configuration des variables secrètes
├── .env                        # Variables d'environnement locales, non versionnées
├── README.md                   # Documentation principale
└── DEPANNAGE.md                # Guide de dépannage
```

L'arborescence ci-dessus décrit l'organisation attendue du projet. Certains fichiers ou sous-dossiers peuvent varier selon la version réellement présente dans le dépôt.

## ⚙️ Prérequis et installation locale

### 1. Prérequis

Avant de commencer, installe les outils suivants :

- Python 3.10 ou une version compatible avec les dépendances du projet.
- Git.
- Visual Studio Code, facultatif mais recommandé.
- Un compte GitHub pour accéder au dépôt et utiliser GitHub Actions.
- Un compte Streamlit Community Cloud si tu souhaites héberger le tableau de bord.

### 2. Cloner le dépôt

Dans un terminal, exécute :

```bash
git clone https://github.com/YoannSLRD/ErgoVeille.git
cd ErgoVeille
```

### 3. Créer un environnement virtuel

Sous Windows :

```powershell
python -m venv venv
```

Active ensuite l'environnement virtuel dans PowerShell :

```powershell
.\venv\Scripts\Activate.ps1
```

Si l'activation est bloquée par la politique d'exécution de PowerShell, tu peux utiliser l'invite de commandes Windows :

```bat
venv\Scripts\activate.bat
```

### 4. Installer les dépendances

Une fois l'environnement virtuel activé :

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurer les variables d'environnement

Si le fichier `.env.example` existe, copie-le vers `.env`, puis renseigne les paramètres nécessaires à ton installation.

Sous PowerShell :

```powershell
Copy-Item .env.example .env
```

Les paramètres SMTP doivent correspondre à ton fournisseur de messagerie. Vérifie également les noms exacts des variables attendues par le code.

**Sécurité :** ne publie jamais ton fichier `.env`, tes mots de passe SMTP ou tes jetons d'accès sur GitHub.

Vérifie que `.env` est exclu de Git dans `.gitignore` et que les fichiers locaux contenant des informations sensibles ne sont pas ajoutés au dépôt.

## 🚀 Lancement de l'application

### Lancer une collecte manuelle

Depuis la racine du projet et avec l'environnement virtuel activé :

```bash
python main.py
```

**Résultat attendu :** le script doit afficher un bilan de collecte et de traitement. Le nombre d'articles varie selon les sources, les requêtes, la date et les réponses des services ; aucun nombre fixe n'est garanti. Vérifie que `data/articles.json` a été créé ou mis à jour si c'est le fichier de sortie prévu par ta version du projet.

### Lancer le tableau de bord

```bash
streamlit run app.py
```

Streamlit affiche ensuite l'adresse locale à ouvrir dans ton navigateur (généralement `http://localhost:8501`).

Si le tableau de bord dépend du fichier `data/articles.json`, vérifie que ce fichier existe et qu'il a été généré par une collecte préalable.

### Prévisualiser la newsletter

```bash
python generate_newsletter.py --preview
```

Si l'option `--preview` est prise en charge par le script, elle permet de générer une prévisualisation. Les noms et emplacements des fichiers produits dépendent de l'implémentation de la version installée.

### Envoyer une newsletter de test

```bash
python generate_newsletter.py --send-test
```

Avant de lancer cette commande, vérifie que :

- `NEWSLETTER_SEND_ENABLED=true` est configuré si le code utilise cette variable.
- `NEWSLETTER_TEST_RECIPIENT` contient une adresse e-mail valide si cette variable est utilisée.
- Les paramètres SMTP sont corrects.
- Le mode test envoie bien uniquement au destinataire prévu.

### Envoyer la newsletter à tous les abonnés

```bash
python generate_newsletter.py --send-all
```

Cette commande :
1. Lit la liste des abonnés dans `config/abonnes.yaml`
2. Génère une newsletter personnalisée pour chaque abonné actif (filtrée par ses thèmes)
3. Demande une confirmation explicite avant envoi (taper `OUI`)
4. Envoie les newsletters une par une

**Configuration des abonnés** : édite `config/abonnes.yaml` pour ajouter ou modifier des abonnés :

```yaml
abonnes:
  - nom: "Yoann"
    email: "veille@ergoland.fr"
    themes: []              # [] = tous les thèmes
    actif: true

  - nom: "Collègue pédiatrie"
    email: "collegue@exemple.fr"
    themes: ["Pédiatrie"]   # ne reçoit que ce thème
    actif: true
```

**Sécurité** :
- L'envoi nécessite `NEWSLETTER_SEND_ENABLED=true` dans `.env`
- Une confirmation interactive (`OUI`) est demandée avant tout envoi
- Les erreurs d'envoi sont isolées (un échec n'arrête pas la boucle)

### Exécuter les tests automatisés

```bash
pytest tests/ -v
```

Les tests permettent de détecter les régressions et de vérifier les fonctionnalités couvertes par la suite de tests. Le nombre de tests peut évoluer au fil des modifications.

## 📰 Fonctionnement de la veille

Le processus général repose sur plusieurs étapes :

1. **Collecte** : récupération des publications scientifiques et des actualités sanitaires à partir des sources configurées.
2. **Normalisation** : harmonisation des informations récupérées afin de faciliter leur traitement.
3. **Dédoublonnage** : identification des publications déjà présentes dans les données.
4. **Classification** : attribution de catégories thématiques et, lorsque cela est possible, d'un type d'étude.
5. **Scoring** : calcul éventuel d'un score de pertinence à partir des critères implémentés dans le projet.
6. **Sauvegarde** : enregistrement des données selon le mécanisme prévu par le projet.
7. **Consultation** : exploration des résultats depuis le tableau de bord Streamlit.
8. **Newsletter** : génération d'un récapitulatif périodique et envoi si la configuration l'autorise.

Les catégories, les requêtes PubMed et les flux RSS sont définis par la configuration du projet, notamment dans `config/config.yaml` si ce fichier est bien utilisé par la version installée.

## 🌐 Déploiement

### 1. Tableau de bord Streamlit Community Cloud

Le tableau de bord peut être hébergé sur Streamlit Community Cloud, sous réserve des conditions et quotas applicables.

Procédure générale :

1. Publie le dépôt sur GitHub.
2. Connecte-toi à Streamlit Community Cloud.
3. Crée une nouvelle application en sélectionnant le dépôt GitHub.
4. Sélectionne la branche à déployer, généralement `main`.
5. Indique `app.py` comme fichier principal.
6. Configure les éventuels secrets et paramètres nécessaires.
7. Lance le déploiement et consulte les logs en cas d'erreur.

**Point de vigilance :** le déploiement Streamlit ne garantit pas à lui seul la disponibilité des données. Si l'application lit `data/articles.json`, ce fichier doit être présent dans le déploiement ou accessible par le mécanisme de stockage réellement utilisé.

### 2. Automatisation avec GitHub Actions

Le fichier `.github/workflows/collect.yml` peut définir une collecte planifiée et une exécution manuelle. Vérifie sa configuration réelle avant de considérer les horaires ou le comportement ci-dessous comme garantis.

Pour vérifier l'automatisation :

1. Ouvre le dépôt sur GitHub.
2. Accède à l'onglet **Actions**.
3. Sélectionne le workflow de collecte.
4. Vérifie son historique d'exécution et les éventuels messages d'erreur.
5. Si le workflow permet un lancement manuel, utilise **Run workflow**.

Si la planification est configurée avec `cron: '0 8 * * 1'`, elle correspond au lundi à 08:00 UTC. Cela correspond généralement à 09:00 en France en hiver et à 10:00 en été.

Si le workflow pousse des données sur `main`, vérifie ses permissions, sa stratégie de commit et les risques de conflit avec les modifications effectuées en local.

### 3. Sauvegarde des données

Les données peuvent être stockées dans le dossier `data/`, selon l'implémentation du projet.

Pour éviter toute perte :

- Sauvegarde régulièrement les données utiles.
- Vérifie que les données générées par GitHub Actions sont bien conservées si le workflow les versionne.
- Ne sauvegarde pas les secrets dans un dépôt public.
- Documente toute modification du mécanisme de stockage.

## ⚠️ Limites et considérations

### Classification des publications

La classification automatique facilite la recherche et le tri des publications, mais elle ne remplace pas une analyse critique de la littérature.

Lorsque les métadonnées sont insuffisantes, le type d'étude peut être incertain. Si le programme utilise la mention « à confirmer », celle-ci doit être conservée afin d'éviter de présenter une classification incertaine comme un résultat vérifié.

**Le type d'étude ne constitue pas, à lui seul, un niveau de preuve scientifique.**

### Score de pertinence

Un score de pertinence peut aider à prioriser les articles selon les critères programmés. Il dépend toutefois des règles de pondération et des métadonnées disponibles. Il ne remplace ni la lecture critique ni l'évaluation méthodologique d'une étude.

### Couverture documentaire

La couverture de la veille dépend des requêtes PubMed, des flux RSS disponibles, des métadonnées fournies et des règles de classification.

L'absence d'une publication dans ErgoVeille ne signifie donc pas qu'aucune publication pertinente n'existe.

### Données de santé et confidentialité

Le projet est destiné à la veille documentaire et non à la gestion de dossiers patients.

N'intègre pas de données directement identifiables de patients aux collectes, aux exports ou aux newsletters. Les obligations applicables en matière de protection des données doivent être vérifiées en fonction des données effectivement traitées, des services utilisés et de leur configuration.

### Quotas et disponibilité

Les services tiers peuvent imposer des limites d'exécution, de stockage ou de disponibilité.

Pour PubMed, respecte les conditions d'utilisation de l'API E-utilities et les limites de débit applicables. Une clé API peut modifier les limites autorisées.

Pour la newsletter, les limites dépendent du fournisseur SMTP utilisé.

### Coût de fonctionnement

L'objectif est de fonctionner sans coût mensuel grâce aux offres gratuites disponibles. Cette gratuité dépend néanmoins des conditions commerciales, des quotas et de l'évolution des services tiers.

## 🛠️ Dépannage et sauvegarde

Consulte le fichier [DEPANNAGE.md](DEPANNAGE.md) pour retrouver les solutions aux erreurs courantes, notamment :

- Les conflits Git lors d'un `git push`.
- Les erreurs de lecture du fichier `data/articles.json`.
- Les problèmes d'envoi de newsletter.
- Les erreurs d'importation Python et les tests pytest.
- Les échecs d'exécution de GitHub Actions.
- Les erreurs de déploiement sur Streamlit Community Cloud.

## ✅ Checklist de mise en production

Avant de considérer le projet comme opérationnel, vérifie les points suivants :

- [ ] Le fichier `.env` est configuré avec les paramètres nécessaires.
- [ ] Le fichier `.env` est exclu de Git et n'a jamais été publié avec des secrets.
- [ ] `python main.py` s'exécute sans erreur.
- [ ] Les données attendues sont créées ou mises à jour.
- [ ] `streamlit run app.py` affiche le tableau de bord.
- [ ] `python generate_newsletter.py --preview` fonctionne si cette option est implémentée.
- [ ] L'envoi de test est vérifié sans risque d'envoi massif.
- [ ] `pytest tests/ -v` passe avec succès.
- [ ] GitHub Actions est configuré et son exécution est vérifiée dans les logs.
- [ ] Le tableau de bord Streamlit Community Cloud est déployé et accessible, si utilisé.
- [ ] Le fichier `README.md` est complet et à jour.
- [ ] Le fichier `DEPANNAGE.md` existe et documente les erreurs courantes.

## 🤝 Contribution

Les contributions permettant d'améliorer la pertinence de la veille, la robustesse du traitement ou l'expérience utilisateur sont les bienvenues.

Avant de proposer une modification :

1. Vérifie que l'environnement virtuel est activé.
2. Exécute les tests automatisés.
3. Vérifie que les secrets et fichiers locaux ne sont pas ajoutés au dépôt.
4. Documente les changements apportés à la configuration.
5. Soumets tes modifications via un commit ou une pull request.

## 📄 Licence

La licence du projet doit être précisée dans le dépôt, par exemple à l'aide d'un fichier `LICENSE`.

Ne considère pas le projet comme distribué sous une licence particulière tant que celle-ci n'a pas été explicitement choisie et publiée.

---

_ErgoVeille — faciliter la veille scientifique et sanitaire au service de la pratique en ergothérapie._
