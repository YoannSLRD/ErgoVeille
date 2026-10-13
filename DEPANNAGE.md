# 🛠️ Guide de dépannage ErgoVeille

Ce document recense les erreurs fréquentes rencontrées lors de l'installation, de l'exécution et du déploiement d'ErgoVeille. Les solutions proposées doivent être adaptées à la version réelle du code et à la configuration du projet.

## 1. Erreur Git : « Updates were rejected because the remote contains work that you do not have locally »

**Cause possible :** la branche distante `main` contient des commits absents de la copie locale. Cela peut notamment arriver si GitHub Actions pousse des données pendant que tu travailles en local.

**Diagnostic :**

```bash
git status
git fetch origin
```

**Solution :** si ton répertoire de travail est propre, récupère les changements distants :

```bash
git pull --rebase origin main
```

Puis pousse tes changements :

```bash
git push origin main
```

Si Git signale des conflits, ouvre les fichiers concernés, résous les conflits puis poursuis le rebase avec :

```bash
git add <fichier-corrige>
git rebase --continue
```

Pour annuler un rebase en cours :

```bash
git rebase --abort
```

Ne lance pas `git push --force` sans comprendre les conséquences : tu pourrais écraser des commits distants. Si Git ouvre Vim pour un message de commit, appuie sur `Échap`, tape `:wq`, puis appuie sur `Entrée`.

## 2. Streamlit : `FileNotFoundError: data/articles.json`

**Causes possibles :**

- La collecte n'a pas encore été lancée.
- Le fichier n'a pas été généré à l'emplacement attendu.
- Le dossier de travail n'est pas la racine du projet.
- Le tableau de bord suppose que le fichier existe sans gérer son absence.

**Vérifications :**

Depuis la racine du projet, vérifie le dossier `data/` et son contenu. Puis, si le script principal est conçu pour effectuer la collecte :

```bash
python main.py
```

Vérifie ensuite que `data/articles.json` existe. Si le fichier est enregistré ailleurs, compare le chemin de sortie dans `main.py` avec le chemin lu dans `app.py`.

Relance le tableau de bord :

```bash
streamlit run app.py
```

Si l'erreur se produit sur Streamlit Community Cloud, assure-toi que les données sont effectivement disponibles dans l'environnement déployé. Un fichier présent uniquement sur ton ordinateur n'est pas automatiquement accessible dans le cloud.

## 3. La newsletter ne s'envoie pas

**Causes possibles :**

- Le mode d'envoi est désactivé.
- Le destinataire de test est absent ou invalide.
- Les variables SMTP sont incorrectes.
- Le fournisseur refuse l'authentification ou la connexion.
- Les options `--preview` ou `--send-test` ne sont pas implémentées dans la version actuelle du script.

**Vérifications :**

Consulte les noms de variables réellement utilisés dans le code et dans `.env.example`. Si le projet attend ces variables, la configuration peut ressembler à ceci :

```env
NEWSLETTER_SEND_ENABLED=true
NEWSLETTER_TEST_RECIPIENT=votre.email@exemple.com
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=votre.adresse@example.com
SMTP_PASSWORD=votre_mot_de_passe
```

Ces valeurs sont des exemples : remplace-les par les paramètres de ton fournisseur. Ne copie jamais un véritable mot de passe dans ce guide ni dans Git.

Pour prévisualiser la newsletter, si l'option est disponible :

```bash
python generate_newsletter.py --preview
```

Pour un envoi de test, si l'option est disponible :

```bash
python generate_newsletter.py --send-test
```

Vérifie les logs, le dossier de sortie et le destinataire avant tout envoi. Ne teste pas l'envoi sur une liste réelle tant que le mode test n'a pas été validé.

## 4. Erreur SMTP : authentification refusée ou connexion impossible

**Causes possibles :**

- Nom d'hôte SMTP incorrect.
- Port ou chiffrement incompatible avec le fournisseur.
- Identifiant ou mot de passe erroné.
- Authentification SMTP désactivée chez le fournisseur.
- Connexion sortante bloquée par le réseau ou l'hébergeur.

**Vérifications :**

- Confirme le nom d'hôte dans la documentation de ton fournisseur de messagerie.
- Le port `465` est généralement utilisé avec SSL implicite.
- Le port `587` est généralement utilisé avec STARTTLS.
- Vérifie si `SMTP_USER` doit être l'adresse complète de la boîte mail.
- Vérifie si le fournisseur exige un mot de passe d'application ou une autorisation spécifique.

Ne change pas le port au hasard : le code doit utiliser le mode de chiffrement correspondant. Consulte les messages d'erreur complets sans divulguer les mots de passe ni les jetons.

## 5. Erreur pytest : `ImportError: cannot import name ...`

**Causes possibles :**

- Une fonction a été renommée, déplacée ou supprimée.
- Le test importe un ancien nom.
- Une dépendance n'est pas installée.
- Les tests sont exécutés depuis un mauvais répertoire.
- Le code local et les tests ne correspondent pas à la même version.

**Étapes de diagnostic :**

1. Place-toi à la racine du dépôt.
2. Active l'environnement virtuel.
3. Vérifie que les dépendances sont installées :

   ```bash
   pip install -r requirements.txt
   ```

4. Lance les tests :

   ```bash
   pytest tests/ -v
   ```

5. Lis le chemin du module et le nom exact de la fonction mentionnés dans la trace d'erreur.

Si l'erreur concerne `_get_theme_icon`, vérifie si cette fonction existe dans `src/newsletter/builder.py` et si son nom correspond exactement à celui importé par les tests. Ne crée pas une fonction uniquement pour faire disparaître l'erreur : assure-toi qu'elle respecte le comportement attendu.

## 6. Le compteur « Nouveautés » affiche un nombre anormal

**Cause possible :** les dates comportent des fuseaux horaires, ou les dates sont analysées de façon incohérente. Une comparaison entre dates avec fuseau horaire et dates sans fuseau horaire peut provoquer des erreurs ou des résultats inattendus.

**Vérifications :**

- Vérifie le format des dates dans les données sources.
- Vérifie la fonction qui analyse les dates dans `app.py`.
- Vérifie que toutes les dates sont converties selon une convention cohérente avant comparaison.
- Teste le comportement avec des dates récentes, anciennes, manquantes et comportant un fuseau horaire.

Si le code utilise pandas, `tz_localize(None)` peut retirer l'information de fuseau horaire dans certains cas, mais cette opération ne doit pas être appliquée aveuglément : il faut d'abord déterminer si les dates sont déjà localisées et quel fuseau doit servir de référence.

Après correction, exécute les tests et compare le compteur avec un petit échantillon d'articles dont les dates sont connues.

## 7. GitHub Actions échoue lors de la sauvegarde des données

**Causes possibles :**

- Permissions d'écriture insuffisantes.
- Conflit avec un commit récent sur `main`.
- Erreur pendant la collecte.
- Chemin de fichier incorrect.
- Échec du commit ou du push automatique.

**Diagnostic :**

1. Ouvre le dépôt GitHub.
2. Va dans **Actions**.
3. Ouvre l'exécution en échec.
4. Repère la première étape qui échoue et lis ses logs.

Si l'erreur concerne les permissions, vérifie le paramètre `permissions` du workflow. Le workflow doit disposer des droits nécessaires, par exemple `contents: write`, uniquement si le script pousse réellement des modifications.

Si l'erreur concerne un conflit Git, récupère les changements distants et résous le conflit avant de pousser. Vérifie aussi que le workflow ne tente pas de versionner `.env`, des secrets ou des fichiers non prévus.

## 8. Streamlit Community Cloud affiche « Error » au déploiement

**Causes possibles :**

- Dépendance manquante.
- Erreur d'importation Python.
- Fichier principal absent ou chemin incorrect.
- Fichier de données non disponible.
- Variable de configuration absente.

**Solution :**

1. Ouvre les logs de l'application depuis l'interface Streamlit Community Cloud.
2. Identifie la première erreur Python utile dans la trace.
3. Vérifie que `app.py` est bien à l'emplacement configuré pour le déploiement.
4. Vérifie que `requirements.txt` contient les dépendances réellement importées par l'application.
5. Vérifie que les données nécessaires sont présentes ou accessibles dans l'environnement cloud.
6. Si l'application utilise des secrets, configure-les dans les paramètres de l'application et non dans un fichier public.

N'ajoute pas automatiquement des bibliothèques à `requirements.txt` sans vérifier qu'elles sont nécessaires au code.

## 9. Tous les articles affichent « Type d'étude à vérifier »

**Cause possible :** les métadonnées de type de publication ne sont pas extraites ou interprétées comme prévu, ou les publications récupérées ne contiennent pas ces métadonnées.

**Vérifications :**

- Ouvre `src/collectors/pubmed_collector.py`.
- Repère la fonction qui transforme la réponse XML PubMed en données d'article.
- Vérifie la structure réelle des données reçues et le chemin utilisé pour accéder aux types de publication.
- Vérifie que le classificateur reconnaît les valeurs renvoyées par le collecteur.
- Teste avec quelques réponses PubMed dont les métadonnées sont connues.

Ne modifie pas le chemin d'extraction en supposant qu'une clé particulière existe : la structure doit être confirmée dans la réponse XML analysée par le code.

Le signalement d'incertitude doit être conservé lorsque les données ne permettent pas une classification fiable.

## 10. Le workflow GitHub Actions ne se déclenche pas automatiquement

**Causes possibles :**

- Expression cron incorrecte.
- Workflow désactivé.
- Fichier YAML invalide.
- Modifications du workflow non présentes sur la branche attendue.
- Retard de planification côté GitHub.

**Vérifications :**

1. Ouvre `.github/workflows/collect.yml`.
2. Vérifie la section `on:` et l'expression cron.
3. Si la planification attendue est le lundi à 08:00 UTC, l'expression cron est :

   ```yaml
   schedule:
     - cron: "0 8 * * 1"
   ```

4. Vérifie que le workflow est présent sur la branche par défaut et qu'il n'est pas désactivé.
5. Consulte l'onglet **Actions**.
6. Si le workflow prend en charge `workflow_dispatch`, lance-le manuellement pour vérifier son fonctionnement.

Les exécutions planifiées peuvent subir des retards. Le lancement manuel ne prouve pas à lui seul que la planification automatique est correcte.

## 11. Les articles ne sont pas correctement classés ou des doublons apparaissent

**Causes possibles :**

- Les règles de classification ne couvrent pas les termes rencontrés.
- Les métadonnées des sources sont incomplètes.
- La clé de dédoublonnage est absente ou incohérente.
- Les données historiques ne suivent pas le format actuel.

**Vérifications :**

- Contrôle les champs d'identification des articles.
- Vérifie la stratégie de dédoublonnage utilisée pour PubMed et les flux RSS.
- Examine les catégories définies dans la configuration.
- Lance les tests existants après toute modification.
- Conserve les informations permettant d'identifier la source d'origine d'un article.

Ne supprime pas en masse les données existantes sans sauvegarde préalable.

## 12. Sauvegarder les données avant une modification importante

Avant de modifier le format des articles, les règles de classification ou le mécanisme de stockage :

1. Arrête les scripts qui écrivent dans les données.
2. Copie le dossier `data/` vers un emplacement de sauvegarde privé.
3. Vérifie que la copie contient bien les fichiers attendus.
4. Crée un commit Git des modifications de code déjà validées.
5. Effectue les changements et lance les tests.
6. Vérifie le résultat avant de remplacer les données de référence.

Ne place pas de secrets ou de données sensibles dans une sauvegarde versionnée sur un dépôt public.

---

## Informations utiles pour demander de l'aide

Pour signaler un problème, indique :

- Le système utilisé (Windows, Linux ou environnement cloud).
- La commande exécutée.
- Le message d'erreur complet, après suppression des secrets éventuels.
- L'étape concernée (collecte, tableau de bord, newsletter, tests ou déploiement).
- Les modifications récentes effectuées dans le projet.

Ne partage jamais de mot de passe SMTP, de jeton GitHub, de secret Streamlit ou d'autre identifiant confidentiel.

---

_Ce guide couvre les problèmes les plus courants susceptibles d'être rencontrés lors de l'utilisation d'ErgoVeille. Les chemins, options et variables doivent être vérifiés dans la version réelle du projet._
