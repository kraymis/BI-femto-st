# Dashboard BI

L’application Streamlit comporte cinq pages : Vue d’ensemble, Analyse temporelle, Analyse des stages, Entreprises et géographie, et Qualité des données. Les indicateurs utilisent les fonctions de `src/bi/analytics/` et les données sont chargées via `src/bi/ingestion/`.

Depuis la racine du projet, après installation des dépendances du projet :

```powershell
python -m streamlit run dashboards/app.py
```

L’application charge `data/raw/stages_cleaned2.xlsx` en lecture seule. Elle n’affiche aucun enregistrement individuel et ne propose ni téléchargement de la source ni export agrégé. Les analyses d’entreprise et de géographie sont exploratoires ; les colonnes de lieu ne sont pas assimilées entre elles. La politique de protection des petits effectifs reste à valider.

Les coordonnées de destination se préparent séparément avec `python -m bi.preprocessing.geographic_reference`. La carte et les ventilations fines restent désactivées tant qu’un seuil de confidentialité n’est pas approuvé. Voir [`docs/geographie_stages.md`](../docs/geographie_stages.md).
