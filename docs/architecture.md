# Architecture de la partie BI

## Principes

La partie BI est isolée dans le package Python `src/bi/` et organisée par responsabilité. Elle ne dépend pas d’une technologie particulière de visualisation. La configuration centrale des chemins se trouve dans `src/bi/config.py` et s’appuie sur `pathlib` ainsi que sur l’emplacement du module, pas sur le répertoire courant.

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
- `dashboards/` contient les cinq pages de l’interface Streamlit ; elle réutilise les fonctions analytiques sans les réimplémenter, utilise Plotly pour les graphiques et Folium/MarkerCluster pour la carte géographique lorsque le seuil de confidentialité sera approuvé.
- `tests/` accueillera les tests automatisés et `docs/` la documentation technique.

## Flux envisagé

Le flux prévu est : **fichier source → ingestion et validation du schéma → contrôles/transformations approuvés → analyses → tableau de bord**. Le stockage éventuel reste à décider. Le classeur de travail `data/raw/stages_cleaned2.xlsx` est chargé en lecture seule ; il n’est ni corrigé ni remplacé.

Les calculs analytiques sont indépendants de Streamlit. Les tests synthétiques se lancent depuis la racine avec `python -m unittest discover -s tests -v`. Les exports ne sont pas activés tant que la politique de petits effectifs n’est pas approuvée.

La préparation du référentiel géographique est décrite dans `docs/geographie_stages.md`. Le CSV local n’est pas généré au lancement de l’application.

## Intégration Hybrid RAG

L’intégration avec le système Hybrid RAG sera étudiée ultérieurement. Le présent socle ne contient aucune connexion ni logique RAG et maintient la partie BI clairement séparée. Aucun système Hybrid RAG existant n’a été trouvé dans le dossier de travail inspecté.
