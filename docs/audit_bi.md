# Audit des données de stages et cadrage du futur dashboard BI

**Date de l’audit :** 16 octobre 2026  
**Périmètre :** inspection en lecture seule du dépôt et du classeur présent dans `data/raw/`.  
**Confidentialité :** ce rapport ne reproduit aucune ligne du classeur, identité, adresse, adresse e-mail, titre de stage ou description.

## 1. Résumé exécutif

Le classeur audité contient **2 292 lignes et 24 colonnes**, sur une feuille visible. Il n’y a aucune ligne entièrement dupliquée ni colonne entièrement vide. La colonne de convention est renseignée et unique sur toutes les lignes. La colonne d’identifiant étudiant contient **1 419 identifiants distincts** ; plusieurs lignes peuvent donc concerner un même étudiant. Compter les lignes ou les conventions comme autant d’étudiants serait incorrect.

Les années académiques sont présentes sous sept libellés consécutifs, de 2020/2021 à 2026/2027 ; quatre lignes n’ont pas d’année. Les dates de début disponibles concordent avec l’une des deux années portées par leur libellé. La dernière année n’est vraisemblablement pas une période complète au vu de la date de modification du classeur et doit être signalée comme telle ou exclue des comparaisons de périodes complètes après confirmation métier.

Les deux colonnes de durée n’ont pas la même précision et doivent être arbitrées : `duree_totale_mois` est renseignée mais comporte 12 valeurs nulles au sens numérique (zéro), tandis que `duree_calculee_mois` manque sur 12 lignes. Sur les 2 280 lignes où elles sont comparables, leur différence absolue médiane est d’environ 0,08 mois. La seconde est presque identique au nombre de jours écoulés divisé par 30,4375 ; cela décrit son comportement observé, sans valider cette formule comme règle métier.

La nature du stage manque sur **19,76 %** des lignes. Le pays du lieu de stage manque sur **71,82 %**. Une analyse géographique nationale/internationale sur l’ensemble des stages n’est donc pas fiable sans règle explicite pour ces inconnues. Les champs de l’entreprise et ceux du lieu de stage sont distincts dans les données : ils ne doivent pas être substitués l’un à l’autre sans confirmation de leur sens.

**Le fichier attendu sous le nom `stages_cleaned.xlsx` n’existe pas dans le dépôt.** Un unique fichier Excel a été trouvé : `data/raw/stages_cleaned2.xlsx`. C’est ce fichier qui a été audité ; aucun fichier source original de référence ni autre version n’a été trouvé dans le périmètre inspecté.

Aucune page Streamlit, fonction métier, connexion ou opération de nettoyage n’a été développée. Le présent document est le seul fichier créé pour cette étape.

## 2. Dépôt et fichier analysé

### État du dépôt

L’arborescence existante est le socle BI déjà en place :

- `src/bi/` et ses sous-dossiers `ingestion/`, `preprocessing/`, `analytics/`, `database/` et `utils/` ne contiennent que les fichiers `__init__.py` et `config.py` prévus pour les étapes futures.
- `data/` comporte `raw/`, `interim/` et `processed/`.
- `notebooks/`, `dashboards/`, `tests/` et `docs/` ont chacun leur documentation de base.
- Aucun notebook, script de traitement, rapport d’audit antérieur ou code Hybrid RAG n’a été trouvé.
- Le dossier n’est pas un dépôt Git.
- `requirements.txt` déclare `pandas` et `openpyxl`. Ces deux paquets sont disponibles dans l’environnement inspecté ; Streamlit n’y est pas installé. Aucun paquet n’a été installé.

L’architecture BI existante a été conservée. Aucun autre module du PFE n’a été localisé dans le dossier de travail inspecté ; une éventuelle intégration à un Hybrid RAG situé ailleurs n’a pas pu être évaluée.

### Fichier effectivement audité

| Élément | Constat |
|---|---|
| Fichier | `data/raw/stages_cleaned2.xlsx` |
| Taille | 938 232 octets |
| Dernière modification du fichier, d’après le système de fichiers | 7 octobre 2026 |
| Feuilles | Une feuille visible, `Sheet1` |
| Dimensions Excel déclarées | 2 293 lignes par 24 colonnes, en-tête compris |
| Dimensions de données lues | 2 292 lignes par 24 colonnes |
| Formules Excel détectées | 0 |
| Cellules contenant littéralement `########` | 0 |

La lecture du classeur a été faite sans écriture. Les cellules non vides des trois colonnes de dates sont enregistrées comme dates Excel et interprétées comme dates par `pandas`. Cela n’exclut pas une mise en forme d’affichage inhabituelle dans un tableur, mais aucun `########` n’est stocké comme valeur.

## 3. Description réelle du jeu de données

Le classeur contient des champs correspondant à l’année académique, la convention, les dates de début, de fin et de soutenance, deux durées en mois, le type et la nature du stage, l’identifiant et les nom/prénom de l’étudiant, l’entreprise, le titre et le descriptif, l’adresse et la ville, des champs séparés pour l’entreprise et la ville du lieu de stage, un pays et deux champs de référent pédagogique.

Les noms de colonnes ci-dessous sont ceux lus dans le fichier. Les types indiqués sont les types inférés par `pandas` lors de l’audit, pas des types métier validés.

| Colonne | Type détecté | Manquants | % manquants |
|---|---:|---:|---:|
| `annee_academique` | texte (`object`) | 4 | 0,17 % |
| `n_convention_de_stage` | texte (`object`) | 0 | 0,00 % |
| `date_debut` | date/heure | 11 | 0,48 % |
| `date_fin` | date/heure | 12 | 0,52 % |
| `duree_totale_mois` | numérique décimal | 0 | 0,00 % |
| `type_de_stage` | texte (`object`) | 0 | 0,00 % |
| `nature_du_stage` | texte (`object`) | 453 | 19,76 % |
| `n_etudiant` | entier | 0 | 0,00 % |
| `nom_de_l_eleve` | texte (`object`) | 0 | 0,00 % |
| `prenom_de_l_eleve` | texte (`object`) | 0 | 0,00 % |
| `entreprise` | texte (`object`) | 32 | 1,40 % |
| `titre_du_stage` | texte (`object`) | 0 | 0,00 % |
| `descriptif_du_stage` | texte (`object`) | 12 | 0,52 % |
| `adresse` | texte (`object`) | 1 | 0,04 % |
| `code_postal` | texte (`object`) | 0 | 0,00 % |
| `ville` | texte (`object`) | 0 | 0,00 % |
| `entreprise_lieu_stage` | texte (`object`) | 1 747 | 76,22 % |
| `cp_lieu_stage` | texte (`object`) | 1 744 | 76,09 % |
| `ville_lieu_stage` | texte (`object`) | 1 744 | 76,09 % |
| `pays_lieu_stage` | texte (`object`) | 1 646 | 71,82 % |
| `date_soutenance` | date/heure | 704 | 30,72 % |
| `referent_pedagogique_mail` | texte (`object`) | 13 | 0,57 % |
| `referent_pedagogique_mail_1` | texte (`object`) | 13 | 0,57 % |
| `duree_calculee_mois` | numérique décimal | 12 | 0,52 % |

**Constats de typage :**

- Les années académiques, identifiants de convention, codes postaux et champs catégoriels sont lus comme texte. C’est cohérent avec la préservation de libellés et d’identifiants, sous réserve de leurs règles métier.
- Les dates sont lues comme dates Excel ; aucune valeur textuelle invalide n’a été observée dans ces colonnes.
- Les deux durées sont lues comme numériques.
- Aucun champ n’est entièrement vide.
- Les deux colonnes des référents portent des noms distincts, dont l’un se termine par `_1`. Elles contiennent des valeurs différentes sur les 2 279 lignes où elles sont toutes deux renseignées. Leur rôle respectif doit être précisé ; elles ne sont pas des colonnes identiques.
- Un marqueur de remplissage atypique a été repéré dans `cp_lieu_stage`. Il n’est pas reproduit ici et n’a pas été corrigé.

## 4. Résultats chiffrés de l’audit

### Années, types et natures

Les libellés d’année renseignés ont tous le format `AAAA/AAAA`, sont consécutifs et ne présentent pas de variante de casse ou d’espaces périphériques dans les colonnes catégorielles examinées. Il y a 4 années manquantes.

| Année académique | Lignes |
|---|---:|
| 2020/2021 | 360 |
| 2021/2022 | 369 |
| 2022/2023 | 375 |
| 2023/2024 | 379 |
| 2024/2025 | 350 |
| 2025/2026 | 355 |
| 2026/2027 | 100 |
| Année manquante | 4 |

Parmi les 2 281 lignes ayant à la fois une date de début et un libellé d’année valide, l’année de la date de début correspond à l’une des deux années du libellé. La période 2026/2027 apparaît encore en cours au regard de la date du fichier ; il faut confirmer sa complétude avant toute comparaison annuelle.

Répartition observée des types :

| Type | Lignes |
|---|---:|
| `PFE` | 963 |
| `SIB` | 562 |
| `SIA` | 530 |
| `MASTER` | 73 |
| `SNO` | 60 |
| `SD` | 51 |
| `PFE_MASTER` | 46 |
| `PFE_CPRO` | 7 |

Répartition observée des natures :

| Nature | Lignes |
|---|---:|
| `Stage en entreprise` | 1 525 |
| `Stage en laboratoire` | 243 |
| `Stage Plateforme SUPMICROTECH-ENSMM` | 52 |
| `Contrat de professionnalisation` | 18 |
| `Formation continue` | 1 |
| Nature manquante | 453 |

Il n’y a pas de valeur manquante pour `type_de_stage`. Les catégories rares, notamment une catégorie de type à 7 lignes et une catégorie de nature à 1 ligne, ne doivent pas être regroupées sans validation.

### Doublons, identifiants et unité observable

- **Doublons exacts de lignes : 0.**
- `n_convention_de_stage` : 2 292 valeurs renseignées et 2 292 valeurs distinctes ; aucune convention répétée dans le fichier.
- `n_etudiant` : 2 292 valeurs renseignées, 1 419 valeurs distinctes ; 778 identifiants apparaissent sur plusieurs lignes, 1 651 lignes appartiennent à un identifiant apparaissant plusieurs fois, avec un maximum de 4 lignes pour un même identifiant.
- `entreprise` : 2 260 valeurs renseignées et 1 105 libellés distincts selon l’égalité textuelle exacte.
- `titre_du_stage` : 2 292 valeurs renseignées et 2 071 libellés distincts. Un titre répété ne constitue pas à lui seul une preuve de doublon de stage.

La **ligne** est une unité observée. Elle correspond à une convention unique dans ce fichier, mais cela ne prouve pas qu’une convention équivaut toujours à un stage métier distinct. Pour les tableaux de bord, `n_convention_de_stage` peut servir provisoirement de proxy de décompte des conventions ; le nom « nombre de stages » requiert une confirmation métier. L’identifiant étudiant n’est pas une clé de ligne et un étudiant peut avoir plusieurs conventions ou stages.

### Dates et durées

| Mesure | `duree_totale_mois` | `duree_calculee_mois` |
|---|---:|---:|
| Valeurs manquantes | 0 | 12 |
| Valeurs égales à zéro | 12 | 0 |
| Valeurs négatives | 0 | 0 |
| Minimum | 0,00 | 0,033 |
| Médiane | 5,50 | 5,420 |
| 99e percentile | 7,00 | 6,899 |
| Maximum | 13,13 | 12,943 |
| Valeurs supérieures à 12 mois | 8 | 1 |

Les 2 280 lignes avec dates de début et de fin ont toutes une fin postérieure au début. L’écart observé va de 1 à 394 jours, avec une médiane de 165 jours ; une ligne dépasse 365 jours. Les 12 zéros de `duree_totale_mois` n’ont ni paire complète de dates ni valeur de `duree_calculee_mois` permettant de confirmer la durée.

Sur les 2 280 lignes comparables :

- La différence absolue médiane entre les deux colonnes de durée est de 0,0795 mois ; la différence maximale est de 0,1866 mois. 178 lignes dépassent 0,1 mois de différence et aucune ne dépasse 0,5 mois.
- `duree_calculee_mois` est presque égale à `(date_fin - date_debut).days / 30,4375` : différence absolue maximale observée d’environ 0,0011 mois.
- Les différences entre `duree_totale_mois` et la durée dérivée des jours sont du même ordre que celles entre les deux colonnes. Un arrondi à un chiffre après la virgule ne rend les colonnes égales que sur 504 lignes.

La règle de durée de référence ne peut pas être arrêtée sur ces seuls constats. Il faut décider si la mesure doit provenir d’une durée fournie, d’une durée recalculée à partir des dates, ou d’une convention de mois calendaires. Il faut aussi préciser le traitement des zéros, des valeurs supérieures à un an, des dates incomplètes et des périodes de plus de 12 mois.

Pour `date_soutenance`, 1 588 lignes ont une date renseignée : 704 sont manquantes. Parmi ces 1 588 dates, une est antérieure à `date_debut`, 222 sont comprises entre les dates de début et de fin, et 1 365 sont postérieures à `date_fin`. Une soutenance postérieure à la fin peut être attendue ; la valeur antérieure au début mérite une vérification. Une date absente ne permet pas de conclure qu’il n’y a pas eu de soutenance.

### Entreprises et géographie

- `entreprise` est renseignée sur 2 260 lignes et compte 1 105 libellés distincts exacts ; 32 lignes n’ont pas de valeur.
- `entreprise_lieu_stage` est renseignée sur 545 lignes et compte 392 libellés distincts.
- Ces champs sont tous deux renseignés sur 540 lignes ; les libellés ne sont pas identiques après retrait des espaces périphériques et comparaison sans casse dans 365 cas. Cela peut refléter deux notions (organisme d’accueil et lieu effectif), ou une incohérence ; il faut établir leur sémantique avant de choisir l’un pour les partenariats.
- `ville` est renseignée sur toutes les lignes et compte 852 valeurs distinctes ; `ville_lieu_stage` est renseignée sur 548 lignes et en compte 265. Lorsque les deux sont présentes, 380 des 548 paires de villes diffèrent textuellement après retrait des espaces périphériques et comparaison sans casse.
- `code_postal` est renseignée sur toutes les lignes ; `cp_lieu_stage` manque sur 1 744 lignes. Les deux champs diffèrent dans 403 des 548 lignes où ils sont tous deux renseignés.
- `pays_lieu_stage` est renseigné sur 646 lignes (30 libellés distincts). Parmi ces valeurs, 446 sont libellées exactement `FRANCE` après comparaison sans casse et 200 ont un autre libellé. Les 1 646 valeurs manquantes empêchent de calculer une part internationale représentative de tout le fichier sans une règle métier sur les inconnues.

Les catégories textuelles examinées ne présentent pas d’écart de nombre de modalités après retrait des espaces périphériques et comparaison sans casse. Cela ne garantit pas que les variantes de noms d’entreprise, villes ou pays sont résolues : les alias et différences de forme plus complexes ne sont pas des identités métier vérifiables à partir de ces champs seuls.

### Données personnelles et confidentialité

Le fichier contient des colonnes directement personnelles (identifiant, nom, prénom, e-mails de référents) et des champs potentiellement sensibles ou identifiants (adresse, titre et description de stage). Aucun échantillon de ligne ni contenu de ces champs n’est repris dans ce rapport. Ces colonnes ne doivent pas apparaître dans les vues générales destinées à la direction. La nécessité d’afficher des entreprises ou de petites catégories devra être évaluée, notamment pour éviter la ré-identification par petits effectifs.

## 5. Anomalies, réserves et limites

| Constat vérifié | Incidence potentielle | Recommandation, sans correction de la source |
|---|---|---|
| Le classeur attendu sous `stages_cleaned.xlsx` est absent ; seul `stages_cleaned2.xlsx` a été trouvé. | L’identité de la version finale et sa provenance ne sont pas confirmées. | Confirmer que `stages_cleaned2.xlsx` est bien la source approuvée et documenter sa provenance. |
| 4 années académiques manquantes ; 2026/2027 compte 100 lignes à la date du fichier. | Séries temporelles incomplètes ; la dernière année n’est probablement pas comparable à des années closes. | Afficher les manquants explicitement et confirmer le traitement de l’année en cours. |
| `nature_du_stage` manque sur 453 lignes. | Les distributions par nature sont incomplètes ; un filtre silencieux sous-estimerait le total. | Conserver une modalité « Non renseignée » distincte et afficher le dénominateur. |
| `pays_lieu_stage` manque sur 1 646 lignes ; ville/adresse principale et lieu effectif diffèrent souvent. | Les cartes, villes et taux de mobilité internationale peuvent être trompeurs. | Faire confirmer les champs de destination et définir la règle des pays inconnus avant de calculer des parts. |
| 12 durées enregistrées valent zéro, sans dates complètes ; les deux colonnes de durée diffèrent. | Moyennes et médianes peuvent être biaisées et la définition de mois n’est pas établie. | Décider de la colonne/règle de référence et du traitement des zéros avant publication. |
| Une date de soutenance est antérieure à la date de début. | Peut signaler une anomalie de saisie ou une sémantique de date différente. | Faire vérifier la ligne concernée par le propriétaire métier dans l’environnement de données, sans reproduire son identité dans les rapports. |
| Deux colonnes de référent ont 13 valeurs manquantes chacune et des valeurs différentes sur toutes les lignes comparables. | Le rôle de chacune n’est pas déductible de leur nom. | Confirmer s’il s’agit de rôles distincts et ne pas les exploiter dans le dashboard de direction. |
| Un marqueur atypique dans `cp_lieu_stage`. | Peut être compté comme un code postal et perturber les regroupements. | Définir une règle de validation/normalisation séparée et soumise à validation. |
| Aucun doublon exact ; une convention unique par ligne. | Les répétitions d’étudiants ne sont pas des doublons ; une convention n’est pas nécessairement une unité métier « stage ». | Garder séparés les décomptes de lignes, conventions, stages et étudiants jusqu’à validation de leurs définitions. |

L’audit n’a appliqué aucune correction, déduplication, normalisation, imputation ou suppression.

## 6. Unité d’analyse proposée

1. **Enregistrement observé :** une ligne du classeur.
2. **Convention :** une clé candidate solide pour identifier une ligne, car les 2 292 valeurs sont présentes et distinctes. Le rapport peut compter les conventions distinctes sans les assimiler à des étudiants.
3. **Stage :** proxy provisoire = une convention, uniquement si le métier confirme qu’une convention correspond à un stage unique et que les éventuels avenants ou conventions multiples sont traités correctement.
4. **Étudiant :** `n_etudiant` distinct, sous réserve que cet identifiant soit stable et unique à l’échelle temporelle du fichier. Il ne faut pas compter les lignes comme des étudiants.
5. **Entreprise :** libellé distinct de `entreprise` à ce stade, pas nécessairement entité juridique distincte. Une table d’alias ou un identifiant de référence nécessiterait une validation et une étape de préparation séparée.
6. **Lieu :** choisir entre informations d’organisme (`adresse`, `code_postal`, `ville`) et lieu effectif (`entreprise_lieu_stage`, `cp_lieu_stage`, `ville_lieu_stage`, `pays_lieu_stage`) après confirmation métier.

## 7. Faisabilité des KPI envisagés

Dans le tableau, « calculable sous réserve » signifie que le calcul technique est possible mais dépend d’une définition métier, d’une qualité insuffisante ou d’un dénominateur à rendre visible. Aucune valeur du rapport ne valide à elle seule le sens métier du KPI.

| KPI / question | Définition et formule envisagées | Champs et unité | Manquants, filtres et limites | Statut |
|---|---|---|---|---|
| Nombre de stages | `COUNT(DISTINCT n_convention_de_stage)` (2 292 conventions observées), à n’appeler « stages » qu’après validation de l’équivalence. | `n_convention_de_stage` ; convention. | Filtrable par année, type, nature, entreprise, pays si les règles sont approuvées. Quatre années manquantes ; conventions non égales à des étudiants. | Calculable sous réserve |
| Nombre d’étudiants distincts | `COUNT(DISTINCT n_etudiant)` (1 419). | `n_etudiant` ; identifiant étudiant. | L’identifiant est complet ; confirmer sa stabilité. Ne jamais afficher les identifiants ni noms en vue générale. | Calculable sous réserve |
| Entreprises d’accueil distinctes | `COUNT(DISTINCT entreprise)` sur les valeurs connues (1 105 libellés exacts). | `entreprise` ; libellé d’entreprise, pas entité normalisée. | 32 absents ; alias éventuels et rapprochement avec le lieu à valider. Modalité manquante explicite. | Calculable sous réserve |
| Évolution annuelle | Compter les conventions distinctes par `annee_academique`. | Convention + année académique. | Quatre années manquantes ; 2026/2027 en cours/partielle probable ; exclure ou distinguer période incomplète après décision. | Calculable sous réserve |
| Répartition par type | Compter les conventions distinctes par `type_de_stage`. | Convention + type. | Aucun type manquant ; catégories rares et significations institutionnelles à confirmer. | Calculable |
| Répartition par nature | Compter les conventions distinctes par `nature_du_stage`, avec modalité « Non renseignée ». | Convention + nature. | 453 natures manquantes ; toujours afficher la couverture et le total. | Calculable sous réserve |
| Durée moyenne / médiane | Moyenne et médiane d’une durée de référence approuvée, après définition du traitement des zéros et valeurs absentes. | `duree_totale_mois`, `duree_calculee_mois` ou dates ; convention. | 12 zéros sur la durée totale ; différences entre colonnes ; une période de 394 jours. Les résultats changent selon la règle choisie. | Calculable sous réserve |
| Durée par type/nature | Moyenne, médiane et distribution de la durée de référence par catégorie. | Durée + type/nature ; convention. | Même arbitrage de durée ; nature inconnue sur 19,76 % des lignes ; catégories rares. Afficher effectifs. | Calculable sous réserve |
| Entreprises accueillant le plus de stages | Nombre de conventions par libellé `entreprise`, tri décroissant. | Entreprise + convention. | 32 entreprises absentes ; les alias peuvent fragmenter le classement ; seuil d’affichage à valider pour les petits effectifs. | Calculable sous réserve |
| Récurrence d’une entreprise | Présenter deux mesures séparées : nombre de conventions par entreprise **et** nombre d’années académiques distinctes avec au moins une convention (`COUNT(DISTINCT annee_academique)`). | Entreprise, convention, année. | Ne pas appeler ces deux mesures indistinctement « récurrence » ; années manquantes, entreprise manquante, alias et période en cours. | Calculable sous réserve |
| Concentration des partenariats | Part des conventions attribuée aux N premiers libellés d’entreprise : conventions des N premiers / conventions associées à une entreprise connue. | Entreprise + convention. | Publier explicitement le dénominateur, le nombre d’entreprises sans libellé et l’effet des alias. | Calculable sous réserve |
| Répartition par pays / international | Effectifs par `pays_lieu_stage` ; part internationale sur pays renseigné = valeurs non assimilées à France / pays renseignés (200/646, soit environ 31 % des seuls pays renseignés). | Convention + pays du lieu effectif. | 1 646 pays absents ; ce taux conditionnel ne représente pas l’ensemble des conventions. Vérifier les libellés et décider comment présenter l’inconnu. | Calculable sous réserve |
| Répartition par ville | Compter les conventions par ville du lieu effectif après choix de `ville_lieu_stage` ou `ville`. | Convention + ville validée. | `ville_lieu_stage` manque sur 1 744 lignes ; `ville` a une couverture complète mais diffère fréquemment de la ville du lieu effectif. Ne pas cartographier avant validation et normalisation contrôlée. | Calculable sous réserve |
| Soutenances | Éventuellement suivre la couverture des dates de soutenance, séparément du nombre de soutenances. | `date_soutenance` ; convention. | 704 dates absentes ; absence ne signifie pas absence de soutenance ; une date précède le début du stage. | Calculable sous réserve |

Pour la récurrence, le dashboard devra distinguer les deux définitions : **volume de conventions** et **nombre d’années académiques actives**. Une entreprise ayant plusieurs stages la même année compte une seule année active dans la seconde mesure. Une année manquante n’est pas assimilée à une année distincte.

## 8. Proposition fonctionnelle du dashboard

Cette conception est préparatoire ; aucune page n’a été créée.

### Navigation

1. **Vue exécutive** : conventions/stages (libellé dépendant de la décision sur l’unité), étudiants distincts, entreprises référencées, évolution annuelle, type/nature et durée seulement après arbitrage.
2. **Entreprises d’accueil** : classement par conventions, évolution annuelle, nombre d’années actives, concentration. Distinguer les libellés d’entreprise des lieux effectifs.
3. **Mobilité géographique** : distribution pays, part internationale conditionnelle au pays renseigné, puis villes si leur rôle et leur qualité sont confirmés. Afficher les inconnues comme catégorie ou dans un indicateur de couverture.
4. **Analyse des stages** : types, natures, durées et évolutions temporelles, avec les modalités rares et manquantes visibles.

### Filtres et visualisations

- Prévoir des filtres globaux synchronisés : année académique, type, nature, entreprise et pays ; n’activer un filtre qu’après validation du champ correspondant.
- Chaque métrique doit préciser son champ, son dénominateur, l’effet des valeurs manquantes et le traitement de la période académique incomplète.
- Ne pas exclure silencieusement les valeurs manquantes : proposer une modalité « Non renseigné » ou un indicateur de couverture.
- Favoriser les cartes KPI, graphiques en barres et séries temporelles lisibles ; éviter les cartes géographiques tant que pays/villes ne sont pas suffisamment définis.
- Les vues générales n’affichent ni nom/prénom, ni numéro étudiant, ni adresse e-mail, ni adresse postale, ni titre/descriptif individuel.
- Évaluer une règle de seuil/suppression des petits effectifs avant d’afficher des répartitions fines, en particulier par entreprise.

Chaque visualisation devra répondre à une question de pilotage explicite. Aucun graphique NLP, analyse sémantique de descriptifs ou RAG ne relève de ce module.

## 9. Recommandations techniques pour Streamlit

- **Dépendances :** garder `pandas` et `openpyxl` pour l’import tabulaire. Ajouter `streamlit` dans les dépendances uniquement lorsque la décision de réaliser l’interface est validée. Aucun besoin actuel démontré pour une bibliothèque NLP, ML, base de données ou cartographie. Une bibliothèque de graphiques externe n’est pas nécessaire pour une première version utilisant les graphiques intégrés de Streamlit.
- **Lecture :** lire le fichier Excel depuis un chemin de configuration ancré au projet, contrôler la présence/ambiguïté des colonnes requises et signaler clairement les erreurs de fichier ou de schéma. Préserver les identifiants comme texte dans la future couche de chargement afin de ne pas altérer zéros initiaux ou formats.
- **Séparation :** réserver `src/bi/ingestion/` au chargement, `src/bi/preprocessing/` aux contrôles et transformations approuvés, `src/bi/analytics/` aux calculs purs des KPI, et `dashboards/` à l’interface. Les choix de calcul doivent être documentés et testés hors interface.
- **Filtres :** construire un jeu de données filtré unique par session pour que les KPI et graphiques partagent le même périmètre ; les modalités inconnues doivent rester explicites. Utiliser un état de session seulement pour la synchronisation d’interface.
- **Tests :** tester les formules d’indicateurs avec petits jeux d’essai synthétiques (identifiants anonymes), notamment données manquantes, conventions répétées éventuelles, valeurs inconnues, durée nulle, dates incohérentes et filtre sans résultat. Aucun jeu réel ne doit être copié dans les tests.
- **Cache :** envisager `st.cache_data` uniquement après décision sur le mode de déploiement et la sensibilité des données ; documenter l’invalidation au changement de fichier et éviter un cache partagé ou persistant non maîtrisé.
- **Confidentialité :** agrégats uniquement, absence de journalisation des valeurs individuelles et de transmission vers des services externes. Contrôler les petits effectifs et les informations exportables.
- **Évolution du PFE :** conserver l’interface indépendante des calculs et de la couche d’accès ; aucune base de données, API ou intégration Hybrid RAG n’est justifiée par cet audit.

## 10. Décisions métier à valider

1. `stages_cleaned2.xlsx` est-il la version approuvée, et où se trouve le fichier original ayant servi à son nettoyage ?
2. Une convention représente-t-elle toujours un stage distinct ? Comment traiter les avenants, renouvellements ou conventions multiples ?
3. `n_etudiant` est-il un identifiant stable et unique sur toute la période ?
4. Quelle colonne définit l’organisme d’accueil : `entreprise` ou `entreprise_lieu_stage` ? Le champ « entreprise » doit-il être rapproché d’une nomenclature d’entités ?
5. Quels champs décrivent le lieu effectif du stage : ville/pays/adresse principaux ou champs suffixés `_lieu_stage` ?
6. Quelle définition de durée faut-il retenir (valeur source, jours écoulés convertis en mois, mois calendaires) ? Comment traiter 0, les dates incomplètes et les durées supérieures à 12 mois ?
7. La nature manquante doit-elle rester inconnue ou peut-elle être renseignée ultérieurement à partir d’une source validée ?
8. La soutenance est-elle attendue après la fin du stage ? Quelle interprétation donner aux données préfin de stage ?
9. Quel doit être le comportement de l’année en cours dans les comparaisons et filtres ?
10. Quel seuil de confidentialité appliquer aux catégories et entreprises à faible effectif ?
11. À quoi correspondent `referent_pedagogique_mail` et `referent_pedagogique_mail_1`, et sont-ils hors périmètre du dashboard ?
12. Où se trouve le projet Hybrid RAG s’il est situé hors du dossier inspecté, et quelles frontières d’intégration doivent être respectées ?

## 11. Plan d’action priorisé

1. **Confirmer les sources** : version finale du classeur, provenance, propriétaire métier et éventuel fichier original.
2. **Valider le modèle de comptage** : ligne, convention, stage, étudiant et organisme d’accueil.
3. **Arbitrer les règles de données** : durée de référence, catégories, valeurs inconnues, lieux de stage, année courante et soutenance.
4. **Définir la confidentialité** : colonnes exclues, agrégation, seuils de faible effectif, accès et déploiement.
5. **Documenter les règles retenues** avant tout calcul destiné au dashboard.
6. **Ajouter des tests de calcul** sur des données synthétiques anonymisées.
7. **Ajouter Streamlit et réaliser l’interface** uniquement après les validations précédentes ; garder l’interface indépendante du cœur BI.
8. **Étudier l’intégration Hybrid RAG séparément**, après localisation du système existant et sans introduire de fonctionnalités NLP/RAG dans la BI.

