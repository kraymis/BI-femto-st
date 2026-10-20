# Architecture du dashboard BI

## Principes

La partie BI est isolée dans le package Python `src/bi/` et organisée par responsabilité. Les calculs métier ne dépendent pas de Streamlit, FastAPI ou d’une bibliothèque de visualisation. FastAPI orchestre les fonctions analytiques et ne retourne que des résultats agrégés ; React prend en charge la navigation, les filtres et la présentation. La configuration centrale des chemins se trouve dans `src/bi/config.py` et s’appuie sur `pathlib` ainsi que sur l’emplacement du module, pas sur le répertoire courant.

## Modules et dossiers

- `data/raw/` conserve les fichiers sources originaux sans modification.
- `data/interim/` accueillera les données intermédiaires issues des futurs traitements.
- `data/processed/` accueillera les données préparées pour l’analyse et les tableaux de bord.
- `src/bi/ingestion/` contient le chargement Excel en lecture seule et la validation des colonnes requises et facultatives.
- `src/bi/preprocessing/` contient la préparation explicite du modèle local de destinations géographiques, sans géocodage ni modification du classeur.
- `src/bi/analytics/` contient les décomptes distincts, les distributions catégorielles, les filtres, les tableaux croisés, les contrôles de complétude et les agrégations géographiques indépendantes de Streamlit.
- `src/bi/database/` accueillera les futurs modules de connexion et d’accès aux données stockées, si un stockage est retenu.
- `src/bi/utils/` accueillera les fonctions utilitaires partagées.
- `notebooks/` est destiné à l’exploration et à l’expérimentation.
- `dashboards/` contient les cinq pages Streamlit, maintenues comme référence fonctionnelle pendant la migration.
- `backend/app/api/v1/` regroupe les routes FastAPI et les dépendances de filtres communs. `schemas/` définit les contrats Pydantic ; `services/dashboard.py` charge les colonnes requises/facultatives et orchestre les fonctions `src/bi/analytics/`.
- `frontend/src/` contient l’application React + TypeScript, ses services HTTP typés, ses types partagés, les composants graphiques et les pages. Vite fournit le serveur de développement et le build.
- `tests/` contient les tests analytiques ainsi que les tests API basés sur des DataFrames et des référentiels géographiques synthétiques. `frontend/src/services/` teste la sérialisation des filtres de l’API.
- `docs/` contient la documentation technique, fonctionnelle et les décisions métier.

## Flux d’exécution

Le flux est : **classeur Excel en lecture seule → ingestion et validation du schéma → filtres partagés → fonctions analytiques existantes → schémas Pydantic agrégés → API FastAPI → visualisations React**. Streamlit suit le même chemin d’ingestion et réutilise les mêmes calculs métier. Le stockage éventuel reste à décider ; le classeur `data/raw/stages_cleaned2.xlsx` n’est ni corrigé ni remplacé.

Les routes JSON destinées aux pages sont `GET /api/v1/health`, `/filters/options`, `/overview`, `/temporal`, `/stages`, `/companies-geography` et `/quality`. Les paramètres catégoriels sont répétés pour représenter plusieurs sélections ; les paramètres `include_missing_*` expriment explicitement la sélection des valeurs absentes. Une sélection vide produit un résultat vide, sans réutiliser une réponse précédente.

Les réponses API n’exposent pas les lignes sources ni les identifiants étudiants. Les détails de destinations de `/companies-geography` comprennent toutefois, dans chaque destination publiée, les numéros de convention associés et les libellés du champ `entreprise` lorsqu’ils existent. Le seuil géographique est appliqué à ces détails comme aux autres vues. Les libellés d’entreprise restent exploratoires et ne sont pas harmonisés en entités juridiques. L’API n’a pas d’authentification et doit rester sur un réseau de confiance jusqu’à la mise en place d’un contrôle d’accès adapté. Aucun géocodage réseau n’est exécuté au lancement.

La préparation et la validation du référentiel géographique sont décrites dans `docs/geographie_stages.md`. Les tests backend peuvent être exécutés depuis la racine avec `python -m pytest tests -q` et `python -m unittest discover -s tests -q`. Les vérifications du frontend (`npm test`, `npm run lint`, `npm run build`) s’exécutent depuis `frontend/`.

## Intégration Hybrid RAG

L’intégration avec le système Hybrid RAG sera étudiée ultérieurement. Le présent socle ne contient aucune connexion ni logique RAG et maintient la partie BI clairement séparée. Aucun système Hybrid RAG existant n’a été trouvé dans le dossier de travail inspecté.
