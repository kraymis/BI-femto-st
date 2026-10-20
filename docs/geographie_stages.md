# Analyse géographique des stages

## État et limites des données source

La source configurée reste `data/raw/stages_cleaned2.xlsx`, chargée en lecture
seule. Au moment de l’inspection, elle contenait 2 292 lignes :

| Champ | Valeurs renseignées | Interprétation retenue |
|---|---:|---|
| `ville_lieu_stage` | 548 / 2 292 (23,9 %) | Ville du lieu effectif, utilisée comme destination |
| `pays_lieu_stage` | 646 / 2 292 (28,2 %) | Pays du lieu effectif, utilisé pour distinguer les villes |
| `cp_lieu_stage` | 548 / 2 292 (23,9 %) | Code postal du lieu ; non utilisé en raison d’anomalies signalées dans l’audit |
| `entreprise_lieu_stage` | 545 / 2 292 (23,8 %) | Libellé du lieu/organisme, jamais traité comme une coordonnée |
| `ville` | 2 292 / 2 292 (100 %) | Champ général non substitué à la ville du lieu |
| `code_postal` | 2 292 / 2 292 (100 %) | Champ général non substitué au code postal du lieu |

`entreprise` et `entreprise_lieu_stage` ne sont pas fusionnés. Les colonnes
générales `ville` et `code_postal` ne sont pas utilisées : l’audit constate
qu’elles diffèrent souvent des champs du lieu effectif. La couverture limitée
des champs de lieu signifie que les destinations trouvées ne sont pas
nécessairement représentatives de tous les stages.

Le suffixe `_lieu_stage` en fait les champs les plus pertinents disponibles,
mais l’audit demande encore au métier de confirmer leur sens. Ce choix reste
provisoire et l’application l’indique avant les indicateurs géographiques.

## Coordonnées de l’établissement

- Nom : **SUPMICROTECH-ENSMM**.
- Adresse officielle : **26, rue de l’Épitaphe, CS 51813, 25030 Besançon Cedex, France**.
- Latitude : `47.250944`; longitude : `5.9942287`.
- Source et date de vérification : métadonnées géographiques de la page
  [Contact officielle de SUPMICROTECH](https://www.supmicrotech.fr/fr/contact),
  vérifiées le 17 octobre 2026.

Ces coordonnées fixes sont centralisées dans `src/bi/config.py`. Elles
représentent le point publié par l’établissement, pas une entrée d’accès précise.

## Référentiel local et préparation manuelle

Le tableau de bord ne géocode pas et n’effectue aucune requête réseau pour
résoudre des destinations. Aucun service externe n’est appelé et aucune donnée
du classeur n’est transmise.

Un modèle par couple ville+pays peut être généré explicitement :

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
.venv\Scripts\python.exe -m bi.preprocessing.geographic_reference
```

Le fichier produit est `data/interim/geographic_reference.csv`, ignoré par Git.
La commande refuse de remplacer un fichier existant ; utilisez `--overwrite`
uniquement après en avoir conservé une copie :

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location).Path 'src')
.venv\Scripts\python.exe -m bi.preprocessing.geographic_reference --overwrite
```

Le modèle contient les libellés géographiques source, les champs `city` et
`country` servant à la correspondance, une clé reproductible, des coordonnées
vides et le statut `pending`. Il ne contient ni ligne par convention, ni
identifiant étudiant, ni nom, e-mail, titre ou description de stage. Les clés
séparent les homonymes par pays ; seule la réduction des espaces est appliquée,
sans fusion par casse, accents, alias ou entreprise.

Compléter le CSV manuellement à partir de coordonnées vérifiables. Pour qu’une
destination soit utilisée, indiquer latitude, longitude, `status=located`,
`coordinate_source`, `verified_at` et `validated=true`. Les statuts utilisés
sont `pending`, `not_found`, `ambiguous` et `located` ; `resolved` est accepté
comme synonyme de `located`. Coordonnées invalides,
incomplètes ou non documentées restent non calculables. Il n’y a pas de
géocodage de masse intégré.

Un référentiel absent ou incomplet n’empêche pas le démarrage de l’application :
la page indique la préparation requise et distingue destination source
absente, destination hors référentiel, coordonnées à préparer, non localisée,
ambiguë, invalide ou non validée.

## Calcul et unité de compte

La distance est calculée localement par Haversine, avec un rayon terrestre
moyen de **6 371,0088 km**. La mesure porte le nom **« Distance estimée à vol
d’oiseau depuis SUPMICROTECH-ENSMM »**. Elle ne représente pas une distance
routière ni une distance exacte jusqu’à l’entreprise.

Les volumes sont des `COUNT(DISTINCT n_convention_de_stage)`. Les répétitions
de lignes ne doublent pas une convention dans une destination. Une convention
associée à plusieurs couples ville+pays est exclue des distances et signalée
comme ambiguë ; aucune destination n’est choisie arbitrairement. Les
pourcentages de couverture ont pour dénominateur les conventions distinctes du
périmètre filtré. Les parts par pays ont pour dénominateur les conventions avec
un pays renseigné et non ambigu ; les pays absents sont comptés séparément.

Les classes descriptives sont : moins de 25 km, 25 à moins de 100 km, 100 à
moins de 300 km et 300 km et plus. Les pourcentages de ces classes sont calculés
uniquement parmi les conventions localisées. Ces classes ne sont pas des
catégories officielles de l’école.

## Carte et confidentialité

La carte Streamlit utilise Folium `MarkerCluster` intégré par
`streamlit-folium` ; la carte React utilise Leaflet. Chaque marqueur correspond
à une destination agrégée. Les popups listent les numéros de convention
associés et, lorsque renseigné, la valeur du champ `entreprise` pour chaque
convention. Aucun identifiant étudiant n’est affiché. Les épingles de
destination sont dessinées en HTML/CSS par Leaflet (`DivIcon`) et ne dépendent
pas d’un fichier image externe. Les tuiles OpenStreetMap et les
ressources Leaflet/MarkerCluster chargées par Folium nécessitent un accès réseau ;
la carte peut donc ne pas s’afficher complètement hors réseau. Les coordonnées
du référentiel et les calculs de distance restent locaux, et les tableaux
agrégés restent disponibles si le fond cartographique ne charge pas.

Le seuil de confidentialité configuré est de **1 convention distincte par
destination**. Les destinations sous ce seuil sont toujours exclues sur le
plan descriptif, mais cette valeur doit être confirmée avec le propriétaire des
données avant toute diffusion institutionnelle. La valeur est centralisée dans
`GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION` dans `src/bi/config.py`. Les
protections contre les déductions par filtres répétés restent à valider avec le
responsable des données. La couverture agrégée et les statuts qualité restent
visibles.

L’API ne comporte pas d’authentification. Comme les popups exposent les
numéros de convention, le service doit rester sur un réseau de confiance tant
qu’un contrôle d’accès n’a pas été ajouté.

## Dépendances et commandes

Les dépendances de carte déclarées sont `folium>=0.20,<0.21` et
`streamlit-folium>=0.27.4,<0.28`. L’interface prévient si elles ne sont pas
installées.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run dashboards\app.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Les fonctions de préparation et d’agrégation sont également testables sans
Streamlit dans `src/bi/analytics/geography.py` et
`src/bi/preprocessing/geographic_reference.py`.
