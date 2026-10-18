# Validation de l’interface BI V2

## Périmètre implémenté

Le dashboard Streamlit expose cinq pages :

1. **Vue d’ensemble** — conventions distinctes, étudiants distincts, années et types renseignés, répartitions agrégées.
2. **Analyse temporelle** — conventions par année, composition par type et tableau croisé année × type.
3. **Analyse des stages** — classements agrégés, recherche de catégories et tableau croisé type × nature.
4. **Entreprises et géographie** — explorations descriptives des libellés d’entreprise et des pays, accompagnées de leur couverture.
5. **Qualité des données** — couverture complète et filtrée, comparaison de couverture par année et avertissements descriptifs.

Les filtres Année académique, Type de stage et Nature du stage sont communs aux cinq pages et conservés dans l’état de session Streamlit. Les valeurs absentes sont une modalité explicite distincte des libellés source. Les sélections vides affichent un état vide.

## Définitions et garde-fous

- Le volume est un nombre de **conventions distinctes**, non un nombre de stages validé.
- Les décomptes d’étudiants sont distincts ; les identifiants ne sont jamais affichés.
- Les tableaux croisés dédupliquent les conventions répétées dans une même cellule et signalent les conventions portant plusieurs modalités distinctes, pour éviter des totaux trompeurs.
- Les pourcentages des tableaux croisés sont calculés par ligne ; le dénominateur est explicité dans l’interface.
- Les valeurs manquantes des champs catégoriels restent visibles sous « Non renseigné », avec un libellé ajusté si cette valeur existe déjà comme modalité source.
- Les pourcentages de couverture ont pour dénominateur le nombre de lignes du périmètre concerné.
- Les périodes récentes peuvent être incomplètes. Aucune comparaison de périodes n’est implémentée.
- Aucun KPI de durée n’est publié.
- `entreprise` et `entreprise_lieu_stage`, ainsi que les champs généraux et suffixés de géographie, ne sont pas fusionnés. Ces pages restent exploratoires.

## Confidentialité

Les tableaux et graphiques ne présentent que des agrégats ; aucun tableau de lignes ni identifiant, e-mail, adresse, titre ou description individuelle n’est affiché. Aucun téléchargement de source ou export agrégé n’est disponible.

La documentation ne fixe pas de seuil approuvé pour les petits effectifs. En conséquence, les détails d’entreprise et de pays sont explicitement présentés comme exploratoires et l’application n’autorise aucun export. Avant diffusion élargie, le seuil et les règles de protection contre les déductions par filtres devront être validés.

## Dépendances et commandes

`requirements.txt` déclare `pandas`, `openpyxl`, `streamlit`, `plotly>=6.0,<7`, `folium>=0.20,<0.21` et `streamlit-folium>=0.27.4,<0.28`. La carte utilise `folium.plugins.MarkerCluster`. Aucun paquet n’est installé automatiquement par le projet.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run dashboards/app.py
python -m unittest discover -s tests -v
```

Pour générer le modèle géographique sous PowerShell, depuis la racine :

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
.venv\Scripts\python.exe -m bi.preprocessing.geographic_reference
```

## État des validations

- `python -B -m unittest discover -s tests -v` : **41 tests réussis**, dont 17 nouveaux tests géographiques synthétiques.
- Vérification AST : syntaxe valide pour les 18 modules et fichiers de test Python examinés.
- Streamlit AppTest : les cinq pages s’exécutent sans exception ; les filtres globaux sont conservés lors de la navigation, actualisent les KPI et affichent un état vide explicite. La page géographique a aussi été vérifiée sans référentiel et avec un référentiel synthétique incomplet.
- Démarrage local Streamlit : le point de santé et la page d’accueil ont répondu HTTP 200 après l’ajout géographique.
- Le classeur configuré était présent et ses agrégations ont été calculées en lecture seule (2 292 lignes, 24 colonnes ; 2 292 conventions et 1 419 étudiants distincts). Aucun enregistrement individuel n’a été imprimé.
- La source contient 265 couples ville+pays distincts dans un modèle construit en mémoire. Le modèle réel n’a pas été écrit ; aucune coordonnée de destination n’a encore été validée.
- L’adresse et les coordonnées fixes de l’école ont été vérifiées sur les métadonnées de sa page officielle le 17 octobre 2026.
- Plotly 6.9.0 est installé dans l’environnement vérifié. Folium et `streamlit-folium` ne le sont pas ; la dépendance cartographique est déclarée, mais la carte n’a pas été rendue ou vérifiée dans un navigateur.
- Le sens métier des champs suffixés `_lieu_stage` reste à confirmer avec le propriétaire des données. Le seuil de 5 conventions par destination a été choisi et configuré ; l’approbation institutionnelle et les protections contre les déductions par filtres répétés restent à confirmer avant diffusion.
- Le classeur source n’a fait l’objet d’aucune écriture ; son SHA-256 est resté identique à celui mesuré avant l’implémentation.
