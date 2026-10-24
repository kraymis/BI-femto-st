# Cahier fonctionnel — Dashboard BI des stages

**Version :** 1.0 — proposition de cadrage  
**Référence des constats :** [`audit_bi.md`](./audit_bi.md)  
**Statut :** cahier de fonctionnalités proposé ; les décisions métier signalées ci-dessous restent à valider avant d’interpréter certains indicateurs comme des mesures officielles.

## 1. Présentation et objectifs

Le module BI a pour objectif d’aider la direction de l’école à piloter l’activité des stages à partir d’indicateurs descriptifs, agrégés et compréhensibles. Il doit permettre d’examiner les volumes de conventions, leur évolution, les types et natures de stage, les entreprises d’accueil et, lorsque les données le permettent, la mobilité géographique et les durées.

Ce document décrit les fonctionnalités à réaliser ultérieurement avec Python et Streamlit. Il ne constitue pas une autorisation de modifier les données ni de trancher les définitions métier en attente.

## 2. Public cible et besoins de pilotage

| Public | Besoin |
|---|---|
| Direction de l’école | Vue synthétique des volumes, tendances et limites de fiabilité. |
| Responsables de formation ou des stages, selon les droits qui seront définis | Exploration agrégée par année, type, nature et organisme d’accueil. |
| Responsable des données | Comprendre la couverture, les valeurs inconnues et les avertissements accompagnant les mesures. |

L’interface est destinée principalement à un usage sur ordinateur. Elle doit être entièrement rédigée en français, utiliser des libellés explicites et expliquer les dénominateurs des pourcentages. Les vues générales restent agrégées ; une recherche distincte et paginée des conventions expose uniquement les champs autorisés par le propriétaire des données.

## 3. Périmètre fonctionnel et exclusions

### Inclus dans le cadrage

- Import contrôlé du classeur approuvé, sans transformation implicite.
- Mesures descriptives au niveau agrégé et filtres partagés.
- Recherche multicritère paginée des conventions, indépendante des filtres globaux, limitée aux champs sélectionnés et autorisés.
- Indicateurs de couverture et avertissements de qualité.
- Pages de synthèse, partenariats, géographie et composition des stages.
- Comparaisons de périodes après traitement des années incomplètes.
- Exports agrégés, si les règles de confidentialité sont validées.

### Exclus

- Tout nettoyage automatique, déduplication, imputation ou harmonisation non approuvée.
- Exposition de champs individuels hors de la recherche de conventions autorisée ; notamment les courriels, adresses et descriptions détaillées.
- NLP, analyse sémantique des descriptions, RAG, IA générative et prédiction.
- Base de données, API, service externe, carte géographique ou infrastructure supplémentaire sans besoin démontré.
- Génération automatique d’interprétations ou de recommandations métier.
- Développement du dashboard dans cette étape de cadrage.

## 4. Référentiel de données et hypothèses

Le classeur inspecté est `data/raw/stages_cleaned2.xlsx`, et non `stages_cleaned.xlsx`. L’audit décrit une feuille et 2 292 lignes par 24 colonnes, 2 292 numéros de convention distincts et 1 419 identifiants étudiants distincts. Il ne confirme pas qu’une convention représente toujours un stage métier.

Les champs structurants considérés par ce cahier sont :

- Période : `annee_academique`.
- Convention : `n_convention_de_stage`.
- Étudiant : `n_etudiant`.
- Catégories : `type_de_stage`, `nature_du_stage`.
- Organisme : `entreprise`, et séparément `entreprise_lieu_stage`.
- Localisation : `ville`, `code_postal`, et séparément `ville_lieu_stage`, `cp_lieu_stage`, `pays_lieu_stage`.
- Dates : `date_debut`, `date_fin`, `date_soutenance`.
- Durées : `duree_totale_mois`, `duree_calculee_mois`.

Le fichier attendu `stages_cleaned.xlsx` est absent du dépôt inspecté. La validation du nom et de la provenance du classeur audité est un préalable à la mise en production.

### Statuts de validation employés

- **Défini techniquement :** la colonne est présente et la formule peut être implémentée sans choisir une définition métier encore inconnue.
- **Proposé :** comportement recommandé, soumis à validation du responsable métier.
- **Conditionnel / bloqué :** ne pas publier la mesure avant la décision indiquée.

## 5. Navigation et organisation des pages

Navigation latérale ou équivalente, avec des libellés français stables :

1. **Vue exécutive**
2. **Entreprises et partenariats**
3. **Mobilité géographique**
4. **Analyse des stages**
5. **Qualité des données** — panneau ou page distincte selon les essais d’usage ; les avertissements essentiels restent visibles sur les autres pages.
6. **Comparaison de périodes** — page ou mode spécialisé, après validation des périodes comparables.

Les contrôles partagés apparaissent au même endroit et ont les mêmes libellés sur chaque page. Les indicateurs sensibles à une définition non validée affichent un état « À valider » ou restent absents, plutôt que d’être présentés comme fiables.

## 6. Description détaillée des fonctionnalités

### A. Vue exécutive

**Besoin :** répondre rapidement à « combien de conventions avons-nous, quelle est la tendance, et quelles réserves faut-il garder à l’esprit ? »

Fonctionnalités :

- Présenter le nombre de conventions distinctes.
- Présenter le nombre d’étudiants distincts, avec une note indiquant qu’un étudiant peut avoir plusieurs conventions.
- Présenter le nombre de libellés d’entreprise distincts renseignés, en le distinguant explicitement du nombre d’entités juridiques.
- Présenter la durée moyenne/médiane uniquement après décision sur la règle de durée.
- Montrer l’évolution annuelle des conventions et identifier une période partielle.
- Résumer les répartitions par type et nature, sans regroupement automatique des catégories rares.
- Afficher les taux de couverture des champs qui conditionnent les KPI visibles.

**Critères d’acceptation :**

1. Le total affiché est défini comme un nombre de conventions distinctes, sauf validation formelle du terme « stages ».
2. Les KPI et graphiques de cette page répondent au même ensemble de filtres.
3. Les valeurs manquantes restent visibles ou sont accompagnées d’un effectif de non-renseignés et d’un dénominateur explicite.
4. Une durée n’est pas affichée comme indicateur officiel avant validation de sa formule et du traitement des zéros.
5. La page identifie visuellement une année incomplète/à confirmer et n’en fait pas une comparaison annuelle normale sans avertissement.

### B. Entreprises et partenariats

**Besoin :** comprendre le volume des conventions associé aux libellés d’accueil et la continuité des collaborations.

Fonctionnalités :

- Classement des libellés `entreprise` selon le nombre de conventions.
- Évolution annuelle des conventions associées aux libellés sélectionnés.
- Nombre d’années académiques distinctes actives par entreprise.
- Comparaison du volume de conventions avec le nombre d’années actives.
- Part des conventions couvertes par les N principaux libellés et distribution cumulée, après validation de la confidentialité.
- Évolution annuelle du nombre de libellés d’entreprise distincts observés.
- Affichage des valeurs manquantes comme « Entreprise non renseignée », hors classement des libellés.

Le classement s’appuie provisoirement sur `entreprise`, non sur `entreprise_lieu_stage`. Les libellés ne sont pas assimilés à des organisations juridiques distinctes. Les alias peuvent fragmenter le classement et les variations d’un nom ne seront pas résolues automatiquement.

**Critères d’acceptation :**

1. Le tableau et le graphique de classement utilisent `COUNT(DISTINCT n_convention_de_stage)` par libellé d’entreprise.
2. Le nombre de conventions et le nombre d’années actives sont nommés et présentés comme deux mesures distinctes.
3. Une entreprise ne compte qu’une fois par année académique pour la mesure « années actives », même si elle a plusieurs conventions cette année-là.
4. Les lignes sans entreprise contribuent au total général mais pas au nombre d’entreprises connues ; cette exclusion est expliquée.
5. Tout classement par petit effectif respecte le seuil de confidentialité validé avant publication.
6. Aucun rapprochement automatique entre `entreprise` et `entreprise_lieu_stage` n’est effectué.

### C. Mobilité géographique

**Besoin :** explorer la destination des stages sans masquer que la localisation est très incomplète.

Fonctionnalités initiales défendables :

- Indiquer la couverture de `pays_lieu_stage` et les champs de localisation apparentés.
- Afficher, sous réserve de validation des champs, les effectifs par pays uniquement parmi les pays renseignés.
- Afficher séparément la part France / autres pays **parmi les seuls pays renseignés**.
- Montrer le nombre et la part des pays non renseignés.
- Reporter les comparaisons temporelles de mobilité jusqu’à validation du champ de destination et du traitement des inconnus.
- Différer les classements par ville ou la carte tant que le lieu effectif n’est pas confirmé et les données jugées suffisantes.

Les 200 libellés de pays autres que France sur 646 pays renseignés ne donnent pas une part de l’ensemble des conventions : 1 646 pays sont absents. La part calculée sur les seules valeurs connues doit toujours être étiquetée « parmi les pays renseignés ».

**Critères d’acceptation :**

1. Tout pourcentage de pays affiche dans son libellé ou sa note son dénominateur : pays renseignés ou ensemble des conventions.
2. Tant qu’aucune règle ne permet d’attribuer un pays aux valeurs absentes, l’application ne présente pas un taux international sur tout le fichier.
3. Les champs `ville` / `ville_lieu_stage` et `entreprise` / `entreprise_lieu_stage` ne sont pas substitués l’un à l’autre implicitement.
4. Une carte ne peut être activée qu’après validation des colonnes de destination, de la normalisation géographique et du traitement des valeurs absentes.
5. Le filtre pays propose une modalité « Non renseigné » ; son périmètre est cohérent avec les autres composants.

### D. Analyse des stages

**Besoin :** étudier la composition par type/nature et les durées avec leurs limites.

Fonctionnalités :

- Répartition par type, puis évolution selon l’année académique.
- Répartition par nature, avec les 453 valeurs absentes visibles.
- Tableau croisé année × type/nature, si lisible et utile au pilotage.
- Distribution de durée et résumé moyenne/médiane par type/nature uniquement après validation du référentiel de durée.
- Signalement descriptif des valeurs atypiques, sans les corriger ni les supprimer.
- Affichage de la taille d’échantillon avec les statistiques de durée.

**Critères d’acceptation :**

1. Les catégories observées sont reproduites sans regroupement ni renommage automatique.
2. Le filtre de nature conserve la possibilité de sélectionner « Non renseignée » et les totaux indiquent le périmètre restant.
3. Toute statistique de durée utilise une unique règle documentée et approuvée ; les valeurs rejetées ou exclues sont comptées dans l’indicateur de couverture.
4. Les valeurs extrêmes sont signalées selon une règle descriptive à définir et ne sont jamais supprimées silencieusement.
5. Un graphique catégorie × année ne confond pas les années absentes avec une catégorie métier.

### E. Filtres globaux synchronisés

Fonctionnalités :

- Multi-sélection d’années, types, natures, entreprises et pays, sous réserve de fiabilité des champs.
- Commande de réinitialisation ramenant chaque filtre à son état initial documenté.
- Choix explicite d’inclure/exclure les valeurs non renseignées pour chaque filtre pertinent ; le comportement initial recommandé est de les inclure dans le périmètre général et de les exposer comme catégorie.
- Message « Aucun résultat pour cette sélection » si les filtres ne laissent aucune convention.
- Synchronisation des filtres entre pages sans divergence de périmètre.
- Contrôles propres à une page, tels que Top N ou période de comparaison, ne modifient pas les autres pages.

**Critères d’acceptation :**

1. Après modification d’un filtre, tous les KPI et graphiques concernés d’une page utilisent le même jeu filtré.
2. Un filtre sélectionné reste identique lors du changement de page, sauf contrôle explicitement propre à la page.
3. La commande de réinitialisation remet chaque filtre à sa sélection initiale et actualise toutes les vues.
4. Les valeurs inconnues peuvent être incluses ou exclues intentionnellement ; elles ne sont jamais retirées par un comportement caché.
5. Une sélection vide ne produit ni exception non gérée ni chiffres anciens : elle affiche un état vide explicite.
6. Une combinaison de filtres partielle ne change pas le dénominateur d’un pourcentage sans l’indiquer.

### F. Comparaison de périodes

Fonctionnalités proposées pour une version ultérieure :

- Sélection de deux années ou deux ensembles d’années académiques disjoints.
- Mesures comparées : conventions, étudiants distincts, catégories et libellés d’entreprises actives.
- Affichage de l’écart absolu `valeur_période_B - valeur_période_A`.
- Affichage de l’évolution relative `(B - A) / A × 100` seulement si `A != 0`.
- Comparaison des durées seulement après validation de la définition et de l’éligibilité des années.
- Application identique des filtres type, nature, entreprise et localisation aux deux périodes.

**Traitement des cas particuliers :**

- Si la période de référence vaut zéro, l’évolution en pourcentage est « Non calculable (référence nulle) » ; ne pas afficher l’infini ni un pourcentage fabriqué.
- Une année manquante n’est pas une période d’effectif nul.
- Une année incomplète ne se compare pas à une période complète sans avertissement et validation d’une comparaison à périmètre de dates équivalent.
- Le sélecteur d’années propre à cette page remplace le filtre global d’année ; les autres filtres communs restent appliqués aux deux périodes.

**Critères d’acceptation :**

1. Les valeurs absolues A, B et l’écart sont consultables, avec les filtres communs identiques.
2. Si A est nul, l’écart relatif est absent et remplacé par un message explicatif.
3. Une période incomplète est signalée avant et pendant l’affichage du résultat.
4. Les catégories absentes restent visibles dans les répartitions comparées ou sont quantifiées dans leur couverture.

### G. Qualité et fiabilité des données

La page ou le panneau qualité informe l’utilisateur ; il ne modifie pas les données.

Indicateurs recommandés :

- Nombre total de lignes et conventions du fichier chargé.
- Disponibilité / présence de `annee_academique`, dates, nature, entreprise, pays et durées.
- Nombre et pourcentage de valeurs manquantes pour les champs essentiels.
- Couverture géographique parmi l’ensemble du périmètre courant.
- Durées nulles et plages observées, dès que le choix de durée est explicité.
- Avertissements de schéma (fichier absent, colonne obligatoire absente, fichier illisible) et de période incomplète.
- Marqueurs atypiques et incohérences décrits dans l’audit, sous forme agrégée seulement.

**Critères d’acceptation :**

1. Les pourcentages de couverture utilisent le nombre de lignes du périmètre courant comme dénominateur et indiquent le numérateur/dénominateur.
2. Un indicateur de qualité ne modifie ni ne masque une donnée source.
3. Les avertissements associés à un KPI sont accessibles au même endroit que ce KPI.
4. Aucun détail de ligne ne sert à illustrer une anomalie dans l’interface générale.
5. Une colonne attendue absente produit une erreur compréhensible et bloque seulement les indicateurs qui en dépendent ; elle ne provoque pas un faux zéro.

### H. Export des résultats agrégés

Extension possible après validation de la confidentialité :

- Export CSV UTF-8 des tableaux agrégés filtrés et des résultats de comparaison.
- Export des KPI sélectionnés avec libellés, unité, périmètre, date de production et notes de qualité.
- Éventuel format XLSX seulement si un besoin utilisateur est confirmé ; aucun export de source brute.

Champs exportables : catégories validées (année, type, nature, entreprise ou pays selon décision), effectifs agrégés et pourcentages documentés. Sont exclus : noms/prénoms, identifiants étudiants, e-mails, adresses, convention individuelle, titres et descriptions individuelles.

**Critères d’acceptation :**

1. Le fichier exporté correspond exactement aux filtres et à la page affichée.
2. Aucun enregistrement individuel ou champ interdit ne figure dans le fichier.
3. Le dénominateur, les modalités inconnues et les avertissements requis accompagnent chaque taux exporté.
4. Les agrégats sous le seuil de confidentialité approuvé sont supprimés ou regroupés conformément à la règle validée.
5. Un export vide ou refusé pour confidentialité affiche un message explicite.

### I. Rapport de synthèse — extension

Un rapport périodique peut être étudié après stabilisation des KPI. La première version ne génère aucun texte interprétatif automatique. Un éventuel rapport ultérieur peut présenter des tableaux et variations calculés, accompagnés des avertissements et de la période choisie.

**Critères d’acceptation de l’extension :**

1. Chaque valeur du rapport est traçable à un KPI, une formule et un périmètre.
2. Les commentaires descriptifs ne sont publiés qu’avec une règle explicite et une validation humaine.
3. Aucune génération par IA ou interprétation sémantique n’est ajoutée.

## 7. Catalogue des KPI

Le décompte général est provisoirement exprimé en **conventions distinctes**. Les formules s’appliquent au périmètre filtré, sauf indication contraire. Les nombres de référence ci-dessous sont des constats de l’audit, pas des résultats garantis après filtres.

| KPI | Définition / formule | Colonnes | Dénominateur et manquants | Statut et affichage |
|---|---|---|---|---|
| Conventions distinctes | `COUNT(DISTINCT n_convention_de_stage)` | `n_convention_de_stage` | Nombre de lignes filtrées ; convention complète et unique dans l’audit. | Défini techniquement ; carte KPI « Conventions ». |
| Nombre de stages | Même formule seulement si une convention équivaut à un stage distinct. | Convention et éventuels identifiants métier à confirmer | Dépend de la définition métier. | Bloqué ; ne pas afficher sous ce nom avant validation. |
| Étudiants distincts | `COUNT(DISTINCT n_etudiant)` dans le périmètre filtré. | `n_etudiant` | Une valeur par étudiant distinct ; ne pas additionner des décomptes de sous-groupes qui se chevauchent. | Proposé ; carte avec mention « étudiants distincts ». Identifiant jamais affiché. |
| Entreprises distinctes | `COUNT(DISTINCT entreprise)` parmi les valeurs renseignées. | `entreprise` | Exclut du décompte les 32 valeurs absentes du jeu audité ; afficher séparément les conventions sans entreprise. | Conditionnel ; nommer « libellés d’entreprise distincts ». |
| Volume annuel | Nombre distinct de conventions par `annee_academique`. | Convention, année | Les quatre années absentes sont exposées à part ; année partielle signalée. | Proposé ; série temporelle ou barres. |
| Volume par type | Nombre distinct de conventions par type. | Convention, `type_de_stage` | Pas de type manquant observé à l’audit ; catégories conservées telles quelles. | Défini techniquement ; barres avec effectifs. |
| Volume par nature | Nombre distinct de conventions par nature, y compris « Non renseignée ». | Convention, `nature_du_stage` | Couverture connue : 1 839/2 292 dans le jeu complet observé ; filtre doit rendre le dénominateur explicite. | Proposé ; barres empilées ou barres simples. |
| Durée moyenne et médiane | Agrégats sur une seule mesure de durée officiellement validée et des lignes admissibles. | Colonne de durée décidée ou dates | Publier le nombre admissible et les exclusions ; traitement des zéros à décider. | Bloqué jusqu’à arbitrage ; afficher moyenne et médiane ensemble avec unité et effectif. |
| Années actives d’une entreprise | `COUNT(DISTINCT annee_academique)` par libellé connu, pour les années valides. | Entreprise, année | Exclut années et entreprises non renseignées ; avertir sur période incomplète et alias. | Conditionnel ; colonne de tableau distincte du volume. |
| Entreprises actives par année | `COUNT(DISTINCT entreprise)` par année. | Entreprise, année | Exclut entreprises absentes et alias non rapprochés. | Conditionnel ; série ou tableau. |
| Concentration Top N | `conventions des N premiers libellés / conventions ayant une entreprise renseignée × 100`. | Convention, entreprise | Dénominateur nommé ; ne pas le confondre avec l’ensemble des conventions. N à sélectionner, seuil de confidentialité à valider. | Conditionnel ; carte/barre cumulative. |
| Répartition parmi pays renseignés | Conventions de chaque pays / conventions ayant un pays renseigné × 100. | Convention, `pays_lieu_stage` | Dénominateur = pays renseignés ; afficher aussi les conventions sans pays. | Conditionnel ; titre explicite « parmi les lieux renseignés ». |
| Part internationale parmi pays connus | Conventions avec un pays renseigné classé hors France / conventions dont le pays est renseigné × 100. | Convention, `pays_lieu_stage` | Dans l’audit, 200/646 pays connus ne sont pas France ; cette fraction ne représente pas tous les stages. Classification des libellés à valider. | Conditionnel ; ne pas appeler « part sur l’ensemble ». |
| Couverture d’un champ | Nombre de lignes avec valeur non manquante / nombre de lignes du périmètre × 100. | Champ contrôlé | Denominateur = lignes filtrées ; toute modalité inconnue est explicitement comptée. | Défini techniquement ; cartes/tables qualité. |
| Écart absolu période | `valeur_B - valeur_A`. | Champs du KPI et période | Périmètres A et B identiques pour les filtres non temporels. | Proposé ; comparaison. |
| Évolution relative période | `(valeur_B - valeur_A) / valeur_A × 100`, seulement si A > 0. | Champs du KPI et période | A nul : non calculable ; données manquantes ≠ zéro. | Proposé ; pourcentage ou libellé non calculable. |

Les effectifs de conventions d’un type ou d’une nature sont calculés dans leur propre catégorie. Les étudiants distincts ne sont pas additifs par catégorie si un étudiant est présent dans plusieurs catégories ou années.

## 8. Catalogue des graphiques et tableaux

| Vue | Graphique / tableau | Question métier à laquelle il répond | Prérequis et garde-fous |
|---|---|---|---|
| Exécutive | Cartes KPI : conventions, étudiants distincts, libellés d’entreprise, couverture | Quel est l’ordre de grandeur et quelle est la complétude ? | Définitions et libellés explicites ; aucun identifiant. |
| Exécutive | Barres du volume par année | Comment le volume évolue-t-il dans le temps ? | Année manquante séparée ; période partielle annotée. |
| Exécutive | Barres type / nature | Quelle est la composition observée ? | Nature inconnue visible ; catégories non regroupées. |
| Entreprises | Tableau triable des entreprises et conventions | Quels libellés représentent le plus de conventions ? | Nom d’entreprise validé ; seuil de confidentialité et alias. |
| Entreprises | Barres années actives vs conventions | Volume et durée de la relation racontent-ils des choses différentes ? | Les deux métriques sont séparées, pas un score combiné. |
| Entreprises | Série annuelle des libellés distincts / conventions | Comment les partenariats référencés évoluent-ils ? | Années complètes comparables ; alias non résolus signalés. |
| Géographie | Tableau/barres par pays renseigné | Où sont localisés les stages dont le pays est connu ? | Titre et dénominateur précisent « pays renseigné ». |
| Géographie | Indicateur de couverture géographique | Quelle fraction du périmètre a une localisation exploitable ? | Champs suffixés validés ; taux sur toutes les conventions filtrées. |
| Analyse | Barres type/nature par année | La composition des conventions change-t-elle selon l’année ? | Effectifs visibles, période partielle signalée, inconnus inclus. |
| Analyse | Histogramme ou boîte à moustaches de durée | Quelle est la distribution des durées ? | À différer jusqu’à validation de la durée ; pas de suppression des valeurs atypiques. |
| Comparaison | Tableau A, B, écart absolu, évolution relative | Quelle différence entre deux périodes comparables ? | Dénominateurs alignés ; zéro et période incomplète traités explicitement. |
| Qualité | Tableau de couverture par champ | Quelles limites affectent les résultats ? | Aucun contenu individuel ; compte, taux et périmètre. |

Une carte, un nuage de mots, un graphique fondé sur les descriptions ou une visualisation sans question de pilotage définie n’est pas retenu pour la V1.

## 9. Matrice des filtres globaux par page

**Légende :** `Oui` = filtre à proposer lorsque la colonne est validée ; `Conditionnel` = différé tant que la définition/qualité n’est pas validée ; `Non` = ne s’applique pas à cette vue ou serait trompeur.

| Filtre partagé | Exécutive | Entreprises | Géographie | Analyse | Qualité | Comparaison |
|---|---:|---:|---:|---:|---:|---:|
| Année académique | Oui, avec année incomplète signalée | Oui | Conditionnel selon couverture pays | Oui | Oui, pour qualité du périmètre | Deux sélecteurs dédiés remplacent le filtre global d’année |
| Type de stage | Oui | Oui | Oui, pour les pays renseignés | Oui | Oui, si l’analyse de couverture par catégorie est demandée | Oui, appliqué identiquement aux deux périodes |
| Nature du stage | Oui, avec inconnu explicite | Oui | Oui, sous réserve | Oui, avec inconnu explicite | Oui | Oui, appliquée identiquement aux deux périodes |
| Entreprise d’accueil | Conditionnel à la définition de `entreprise` | Oui, libellé exact approuvé | Conditionnel ; risque de petit effectif | Conditionnel | Conditionnel | Oui, sous réserve de confidentialité |
| Pays du lieu de stage | Conditionnel ; dénominateur connu visible | Conditionnel | Oui parmi les pays connus et modalité inconnue | Conditionnel | Oui pour le taux de couverture | Conditionnel, règle de pays identique pour les deux périodes |

### Règles communes de filtre

- Sélections multiples autorisées ; un filtre sans sélection restrictive signifie « toutes les modalités », y compris les valeurs manquantes dans le périmètre général.
- Les modalités inconnues sont affichées comme `Non renseigné`, sans confondre cette étiquette d’affichage avec une valeur source.
- L’utilisateur peut exclure explicitement les inconnues ; l’interface rappelle alors que le dénominateur est réduit.
- Les contrôles d’une page (Top N, mesure choisie, A/B) ne deviennent pas des filtres globaux.
- Le filtre période de la page de comparaison est spécialisé : les critères année A et année B sont appliqués de façon disjointe ; les filtres non temporels sont communs.
- En cas de zéro ligne après filtrage, afficher une explication, une action de réinitialisation et aucun KPI issu d’un état antérieur.

## 10. Règles de calcul et valeurs manquantes

1. **Périmètre de base :** conserver toutes les lignes lues ; ne pas dédupliquer ou corriger à la volée. Pour les volumes de conventions, compter les valeurs distinctes de `n_convention_de_stage`.
2. **Valeurs absentes :** les distinguer des zéros et des catégories légitimes. Toujours préciser si une formule exclut des valeurs absentes.
3. **Pourcentages :** afficher numérateur, dénominateur et filtre. Ne jamais utiliser comme dénominateur implicite le nombre de valeurs connues sans le signaler.
4. **Durées :** aucun choix de référence n’est acquis. Options à arbitrer : durée source `duree_totale_mois`, durée `duree_calculee_mois`, calcul à partir des dates selon une convention définie (jours/30,4375 ou mois calendaires). Le comportement observé de `duree_calculee_mois` ne constitue pas une approbation métier.
5. **Durée nulle / extrême :** conserver et signaler ; décider si zéro signifie réellement une durée nulle, une donnée absente ou une autre convention. Ne pas exclure les durées de plus de 12 mois automatiquement.
6. **Années académiques :** considérer les libellés conformes et les dates comme vérification de plausibilité ; une année absente demeure inconnue. Confirmer si 2026/2027 est complète avant comparaison.
7. **Entreprise :** utiliser provisoirement le libellé exact, sans rapprochement d’alias et sans substitution par le champ de lieu. Une normalisation future requiert une table de correspondance approuvée.
8. **Pays :** classification France/autre pays requiert validation des valeurs et du champ de destination. Les pays absents restent inconnus, jamais assimilés à France ou à l’étranger.
9. **Soutenances :** l’absence de date ne prouve pas l’absence de soutenance ; les indicateurs de couverture sont préférables à un décompte des soutenances sans définition validée.
10. **Filtres :** tous les composants d’une page partagent le même jeu filtré ; les mesures calculées sur un sous-ensemble connu affichent leur couverture.
11. **Comparaisons :** aucune donnée manquante ne devient un zéro ; la variation relative pour une référence nulle est non calculable.
12. **Anomalies :** l’interface décrit leur fréquence agrégée, ne modifie aucune valeur et ne déclenche aucun nettoyage.

## 11. Registre des décisions métier

| Décision à prendre | Options possibles | Incidence sur les KPI | Recommandation provisoire | Validation requise |
|---|---|---|---|---|
| Le fichier de référence | Confirmer `stages_cleaned2.xlsx` ; fournir une version finale/originale différente | Toutes les mesures peuvent changer si la version n’est pas celle attendue | Bloquer le déploiement avant confirmation de provenance | Propriétaire des données |
| Convention = stage ? | Toujours équivalent ; équivalent avec exceptions ; unités distinctes | Nom et interprétation du KPI principal | Présenter le nombre de conventions, pas de stages, en attendant | Responsable métier des stages |
| Identifiant étudiant | `n_etudiant` stable ; périmètre à restreindre ; autre clé | Nombre d’étudiants distincts et filtres temporels | Compter les identifiants distincts seulement après confirmation de stabilité | Responsable des données |
| Entreprise d’accueil | `entreprise` ; `entreprise_lieu_stage` ; source de référence externe approuvée | Classement, récurrence, concentration | Ne pas combiner les deux ; utiliser `entreprise` uniquement avec avertissement provisoire | Service des stages |
| Identité d’une entreprise | Libellé exact ; alias approuvés ; identifiant officiel | Nombre d’entreprises, classement, récurrence | Garder les libellés exacts et les appeler « libellés » | Responsable des partenariats |
| Lieu du stage | Champs généraux ; champs suffixés `_lieu_stage` ; combinaison validée | Répartition géographique et international | Différer les KPI de destination hors couverture | Service des stages |
| Durée de référence | Durée source ; durée calculée ; intervalle de dates en mois calendaires ou jours/30,4375 | Moyenne, médiane, distributions | Ne pas publier les KPI de durée avant décision | Responsable pédagogique/métier |
| Durée nulle et valeurs extrêmes | Inclure, exclure, ou marquer non valide selon règle approuvée | Statistiques de durée et couverture | Ne pas supprimer ; exposer le compte affecté | Responsable métier des stages |
| Nature absente | Modalité inconnue ; source autorisée pour compléter ultérieurement | Distributions et filtres de nature | Garder inconnue et afficher la couverture | Responsable des données |
| Part internationale | Sur pays renseigné seulement ; sur toutes les conventions après règle d’inférence approuvée | Dénominateur et niveau de représentativité | Version initiale conditionnelle parmi les pays renseignés uniquement | Direction / responsable des stages |
| Année 2026/2027 | Afficher en cours ; exclure des comparaisons ; comparaison à date équivalente | Tendances et taux d’évolution | L’annoter comme potentiellement partielle | Direction |
| Date de soutenance | Utiliser comme couverture ; la relier à la fin du stage selon règle | KPI de soutenance et cohérence chronologique | Ne pas assimiler date absente à absence de soutenance | Responsable pédagogique |
| Petits effectifs | Seuil k, regroupement, suppression ou restriction d’accès | Classements, exports, croisements filtrés | Aucun seuil arbitraire ; définir une politique avant publication | Délégué protection des données / direction |
| Rôles des colonnes de référent | Deux rôles distincts ; doublon de source ; champs hors périmètre | Tout indicateur de supervision | Exclure des vues générales jusqu’à clarification | Responsable des stages |
| Déploiement et accès | Local/interne ; espace authentifié ; autres modalités institutionnelles | Cache, exports, accès et journalisation | Décider avant mise en service ; pas de service externe par défaut | Équipe informatique et DPO |

## 12. Règles de confidentialité

- Ne pas afficher dans les pages générales ni les exports : nom, prénom, identifiant étudiant, e-mail, adresse postale, numéro individuel de convention, titre et description détaillés d’un stage.
- Ne pas offrir de drill-through vers une ligne source ou de téléchargement du classeur.
- Limiter l’application aux résultats agrégés ; aucune ligne individuelle ne doit apparaître dans les journaux, les messages d’erreur ou les exemples.
- Ne transmettre aucune donnée à un service externe.
- Définir un seuil minimal d’effectif pour les tableaux détaillés, catégories rares, entreprises et combinaisons de filtres ; tant qu’il n’est pas décidé, différer les sorties à risque plutôt que choisir un seuil.
- Considérer les filtres combinés comme un risque : une catégorie suffisamment grande isolément peut devenir identifiable après plusieurs filtres.
- Ne pas confondre agrégation et anonymisation garantie. L’accès, l’hébergement, les exports et la rétention du cache doivent être revus par les responsables compétents.
- Les noms d’entreprises ne sont pas des données étudiantes, mais peuvent révéler un partenariat ou une affectation rare ; appliquer le contrôle des petits effectifs.

## 13. Architecture technique cible

L’architecture déjà présente est conservée :

| Emplacement existant | Responsabilité cible | Dépendance / résultat |
|---|---|---|
| `src/bi/config.py` | Chemins de projet et de données ancrés au package ; pas de chemin machine codé en dur. | Utilisé par le chargement. |
| `src/bi/ingestion/` | Charger le fichier approuvé et vérifier son accessibilité, sa feuille et son schéma attendu. Aucune correction de valeurs. | Produit une représentation tabulaire validée ou une erreur explicite. |
| `src/bi/preprocessing/` | Contrôles de qualité et transformations seulement après approbation documentée. | Ne doit pas modifier l’original ; transformations traçables hors source. |
| `src/bi/analytics/` | Fonctions pures de calcul des KPI et comparaisons, sans dépendance à Streamlit. | Reçoit le périmètre tabulaire et les règles approuvées. |
| `src/bi/utils/` | Petits utilitaires partagés réellement nécessaires. | Pas de couche abstraite prématurée. |
| `dashboards/` | Interface Streamlit, navigation, filtres, état de session, rendus et avertissements. | Appelle ingestion/analytics, ne contient pas les règles métier dupliquées. |
| `tests/` | Tests des formules, filtres, manquants, erreurs de schéma et cas limites. | Jeux synthétiques anonymisés seulement. |
| `docs/` | Règles métier, audit, cahier fonctionnel et décisions de calcul. | Source de vérité pour les définitions. |

Flux cible : fichier autorisé → ingestion/contrôle de schéma → contrôles et préparations expressément approuvés → calculs BI → filtres/présentation Streamlit → export agrégé éventuel.

Le projet déclare actuellement `pandas` et `openpyxl`. Streamlit n’est pas déclaré dans `requirements.txt` et n’est pas installé dans l’environnement inspecté. Il pourra être ajouté comme dépendance lors de l’étape de développement, après décision. Une bibliothèque graphique supplémentaire n’est pas nécessaire pour le premier périmètre. Aucun stockage, API, NLP ou lien Hybrid RAG n’est proposé.

## 14. Critères d’acceptation transversaux

| ID | Critère vérifiable |
|---|---|
| AC-01 | L’application signale explicitement l’absence ou l’illisibilité du fichier source et n’affiche aucun zéro de réussite par défaut. |
| AC-02 | Une colonne obligatoire absente bloque les mesures qui en dépendent et affiche le nom technique attendu ainsi qu’un message en français. |
| AC-03 | Le nombre de conventions est calculé par identifiants de convention distincts et ne sert pas de nombre d’étudiants. |
| AC-04 | Un filtre global modifié met à jour toutes les pages et tous les composants concernés avec les mêmes règles de périmètre. |
| AC-05 | Les valeurs inconnues ne sont jamais assimilées implicitement à zéro, France, une catégorie connue ou une période sans activité. |
| AC-06 | Chaque pourcentage expose son dénominateur et permet d’identifier la part de données manquantes. |
| AC-07 | Les années académiques incomplètes ou non comparables sont annotées ; elles ne sont pas mises en comparaison silencieuse avec une année close. |
| AC-08 | Les KPI de durée restent masqués ou marqués « à valider » avant adoption d’une définition métier écrite. |
| AC-09 | Les vues agrégées et exports n’exposent aucun identifiant étudiant, e-mail, adresse ou description individuelle de stage. L’exception est la recherche paginée de conventions, qui expose les noms/prénoms et identifiants étudiants limités et autorisés par le propriétaire des données. Les popups géographiques peuvent afficher les numéros de convention et libellés `entreprise` associés à une destination publiée ; l’API doit rester sur un réseau de confiance tant qu’elle n’est pas authentifiée. |
| AC-10 | Les petits effectifs et croisements sont bloqués ou protégés selon le seuil approuvé ; sans seuil, l’export détaillé n’est pas activé. |
| AC-11 | Aucune opération de nettoyage, déduplication ou écriture n’est appliquée au classeur brut par l’application. |
| AC-12 | Une sélection sans résultat affiche un état vide explicite et ne laisse pas visibles des résultats obsolètes. |
| AC-13 | Les erreurs techniques sont signalées en français sans exposer de contenu de ligne ou de valeur personnelle. |
| AC-14 | Les fonctions de calcul sont testables sans démarrer Streamlit et ne dépendent pas de l’état de l’interface. |

## 15. Stratégie de tests

Les jeux de test doivent être petits, synthétiques et anonymisés ; aucune ligne du classeur réel n’est copiée.

| Niveau | Cas à couvrir |
|---|---|
| Tests unitaires des KPI | Convention répétée ou manquante, étudiant multi-convention, entreprise absente, modalité inconnue, catégories rares, dénominateur nul. |
| Tests de durée | Durées différentes, zéro, valeur extrême, date manquante, fin antérieure au début, dates valides et règle de conversion décidée. |
| Tests des filtres | Une valeur, plusieurs valeurs, « Non renseigné », combinaison sans résultat, réinitialisation, synchronisation entre pages. |
| Tests de comparaison | Écart positif/négatif/nul, référence zéro, période manquante, période incomplète et filtres communs. |
| Tests d’ingestion | Fichier absent, feuille absente, extension/format illisible, colonnes manquantes, colonnes inattendues, lecture en lecture seule. |
| Tests d’interface | Libellés français, affichage des avertissements, absence de données personnelles dans les pages et exports, état vide. |
| Tests d’export | Égalité au tableau filtré, encodage, colonnes autorisées, protection contre petits effectifs, aucune ligne individuelle. |

La validation visuelle et métier des résultats doit utiliser les définitions approuvées et des agrégats de contrôle, et non des captures contenant des informations nominatives.

## 16. Priorisation : V1, V2 et extensions

### V1 — socle fiable et agrégé

- Chargement contrôlé du classeur et erreurs explicites.
- Navigation en français.
- Filtres synchronisés année/type/nature uniquement après validation des règles ; gestion visible des inconnues.
- Vue exécutive avec conventions distinctes, étudiants distincts, couverture, volumes annuels annotés et répartitions par type/nature.
- Page qualité de données.
- Tests unitaires de calcul et de filtres.
- Pas de KPI de durée officiel, de carte, d’export détaillé ou de réconciliation d’entreprise avant décisions correspondantes.

### V2 — exploration partenariats et périodes

Après validation des champs et de la confidentialité :

- Classement d’entreprises par volume de conventions.
- Mesure séparée du nombre d’années actives.
- Concentration et évolution des partenariats.
- Comparaison de deux périodes comparables.
- Mobilité par pays parmi les pays renseignés, avec dénominateur et couverture affichés.
- Mesures de durée après validation et tests métier.
- Export strictement agrégé si les seuils de confidentialité sont fixés.

### Extensions

- Analyse par ville ou carte si la qualité et la sémantique de la géographie le justifient.
- Rapport périodique de synthèse sans génération automatique d’interprétation.
- Harmonisation des alias d’entreprise et de géographie uniquement avec référentiel approuvé.
- Intégration éventuelle à Hybrid RAG, étudiée séparément et sans introduire NLP/RAG dans le module BI.

## 17. Plan d’implémentation proposé

1. **Valider les préalables métier et confidentialité** du registre de décisions, notamment source, unité d’analyse, entreprise, durée, géographie, périodes et seuil de petits effectifs.
2. **Stabiliser les contrats de données** : fichier autorisé, colonnes requises/optionnelles, types attendus, erreurs de chargement et protection de la source.
3. **Implémenter l’ingestion et les contrôles** dans les modules existants, sans correction automatique ; tester les erreurs de schéma et les manquants.
4. **Implémenter les calculs indépendants de l’interface** pour les KPI V1 et écrire leurs tests synthétiques.
5. **Construire l’interface V1** : navigation, filtres synchronisés, vue exécutive, qualité et états d’erreur/absence de résultat.
6. **Valider les agrégats** avec le responsable métier, contrôler les dénominateurs, la période partielle et la confidentialité.
7. **Développer les pages V2** de partenariats, comparaison et mobilité selon les décisions validées ; ajouter les KPI de durée seulement après arbitrage.
8. **Ajouter les exports agrégés** lorsque la politique de petits effectifs, d’accès et de rétention est approuvée.
9. **Évaluer les extensions** selon leur valeur de pilotage et les contraintes de déploiement, sans élargir le périmètre à du NLP/RAG.

**État à ce jour :** ce cahier fonctionnel est un livrable de cadrage. Le dashboard n’a pas été développé, aucune dépendance n’a été modifiée et aucun traitement du classeur n’a été exécuté dans le cadre de cette étape.
