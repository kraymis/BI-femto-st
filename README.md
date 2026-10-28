# Système d’information intelligent — BI des stages

Cette partie du projet de fin d’études « Système d’information intelligent pour le pilotage et l’exploration des données d’une école d’ingénieurs » fournit un tableau de bord de Business Intelligence consacré aux conventions de stage.

## Objectifs de la partie BI

Le dashboard comprend cinq pages : Vue d’ensemble, Analyse temporelle, Analyse des stages, Entreprises et géographie, et Qualité des données. L’interface React consomme les agrégats calculés par FastAPI ; Streamlit reste disponible comme référence fonctionnelle pendant la migration. Les deux applications lisent les mêmes données et ne les modifient pas. La Vue d’ensemble propose également une recherche structurée et paginée des conventions, indépendante des filtres globaux.

Les KPI continuent de compter les conventions distinctes, sans les assimiler à un nombre de stages validé. Les endpoints analytiques renvoient des agrégats ; l’endpoint de recherche de conventions renvoie une page limitée de champs, dont le nom, le prénom et l’identifiant étudiant, conformément à l’autorisation explicite du propriétaire des données. Les popups de la carte affichent les numéros de convention associés à chaque destination et, lorsque renseigné, le champ `entreprise` correspondant. L’API ne dispose pas d’authentification : ne l’exposez pas à un réseau non autorisé. Les détails géographiques respectent le seuil configuré dans `src/bi/config.py`.

## Prérequis

- Python 3.10 ou ultérieur.
- `pip`, fourni avec les installations Python usuelles.
- Node.js `^20.19.0` ou `>=22.12.0` et npm pour le frontend React.

## Installation

Depuis la racine du projet, créez un environnement virtuel :

```powershell
python -m venv .venv
```

Activez-le sous PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

Sous macOS ou Linux, l’activation se fait avec :

```bash
source .venv/bin/activate
```

Installez les dépendances de base :

```bash
python -m pip install -r requirements.txt
```

## Organisation

- `data/` : emplacements des données brutes, intermédiaires et préparées. Les sources locales peuvent contenir des données personnelles : ne les versionnez pas sans validation. Pour ce déploiement, le classeur et le référentiel géographique ont été confirmés fictifs et approuvés pour publication.
- `notebooks/` : futurs travaux exploratoires et expérimentations.
- `src/bi/` : package Python de la partie BI, organisé par responsabilité.
- `dashboards/` : interface Streamlit.
- `backend/app/` : routes FastAPI, schémas Pydantic et orchestration des agrégats existants.
- `frontend/` : application React + TypeScript construite avec Vite.
- `tests/` : tests synthétiques des fonctions analytiques et d’ingestion.
- `docs/` : documentation technique et décisions d’architecture.

Les responsabilités restent séparées : `src/bi/analytics/` porte les calculs métier, FastAPI réutilise ces fonctions pour les agrégats et expose séparément les champs limités de la recherche de conventions, et React s’occupe de la navigation, des filtres et de leur présentation. Le détail des modules figure dans [`docs/architecture.md`](docs/architecture.md). Les chemins applicatifs sont définis dans `src/bi/config.py` relativement à l’emplacement du module.

## Lancement

Après activation de l’environnement virtuel et installation des dépendances, l’application Streamlit reste exécutable depuis la racine du dépôt :

```powershell
python -m streamlit run dashboards/app.py
```

### Dashboard React + API FastAPI

Les serveurs sont indépendants. Dans un premier terminal, depuis la racine du projet, installez les dépendances Python puis démarrez l’API :

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Dans un second terminal, installez les dépendances du frontend et lancez Vite :

```powershell
cd frontend
npm install
npm run dev
```

Le dashboard React est accessible sur `http://localhost:5173`. L’API est accessible sur `http://localhost:8000` et sa documentation interactive sur `http://localhost:8000/docs`. Pour utiliser une autre URL d’API en développement, créez `frontend/.env.local` à partir de `frontend/.env.example` et définissez `VITE_API_BASE_URL`. Le CORS de développement autorise uniquement les origines Vite locales `localhost:5173` et `127.0.0.1:5173`.

Routes de lecture :

- `GET /api/v1/health` — état de l’application.
- `GET /api/v1/filters/options` — options réelles, valeurs manquantes comprises.
- `GET /api/v1/overview` — KPI et répartitions de la vue d’ensemble.
- `GET /api/v1/temporal` — séries annuelles et croisement année × type.
- `GET /api/v1/stages` — répartitions type/nature et croisement type × nature.
- `GET /api/v1/companies-geography` — couverture entreprise/géographie et détails géographiques publiables.
- `GET /api/v1/quality` — couverture globale, filtrée et par année, et alertes.
- `GET /api/v1/conventions/search/options` — champs disponibles et options catégorielles de recherche.
- `POST /api/v1/conventions/search` — recherche multicritère indépendante des filtres globaux, paginée côté serveur.

La recherche renvoie les champs d’identification étudiant (`n_etudiant`, nom et prénom) après autorisation explicite du propriétaire des données. L’API n’a pas d’authentification : le déploiement doit rester réservé à un environnement approuvé pour ces données. Le classeur courant ne contient pas d’identifiant de sujet PFE (`id_sujet_pfe`), ce critère n’est donc pas proposé. Les résultats sont limités aux colonnes utiles de la recherche ; les courriels, adresses et descriptions de stage ne sont pas renvoyés.

Les trois filtres globaux utilisent des paramètres de requête répétés, par exemple `?academic_years=2024%2F2025&stage_types=PFE`. `include_missing_year`, `include_missing_type` et `include_missing_nature` sélectionnent explicitement les valeurs absentes. Un paramètre de catégorie omis avec son booléen omis ne restreint pas cette catégorie ; fournir `include_missing_*=false` sans valeur catégorielle sélectionnée produit un résultat vide.

Pour lancer les tests :

```powershell
python -m unittest discover -s tests -v
python -m pytest tests -v
```

Depuis `frontend/`, les tests du service API, le lint et le build de production s’exécutent avec :

```powershell
npm test
npm run lint
npm run build
```

Streamlit n’est pas supprimé et reste la référence fonctionnelle historique jusqu’à validation métier complète. Consultez [`docs/audit_bi.md`](docs/audit_bi.md), [`docs/cahier_fonctionnel_bi.md`](docs/cahier_fonctionnel_bi.md), [`docs/validation_bi_v2.md`](docs/validation_bi_v2.md) et [`docs/geographie_stages.md`](docs/geographie_stages.md) pour les limites et décisions métier encore en attente.

### Déploiement public sur Render

Le fichier `render.yaml` déploie le frontend et l’API dans un seul service web. Il charge le classeur `data/raw/stages_cleaned2.xlsx` et le référentiel `data/interim/geographic_reference.csv`, qui sont suivis par Git pour ce déploiement parce qu’ils ont été confirmés fictifs et approuvés pour publication. Tout autre fichier sous `data/` reste ignoré et n’est pas copié dans l’image Docker.

1. Poussez la branche `feature/react-fastapi-migration` sur GitHub.
2. Dans Render, choisissez **New → Blueprint**, reliez le dépôt et sélectionnez cette branche.
3. Vérifiez que le service `supmicrotech-dashboard` est configuré avec `BI_DATA_MODE=real`, puis lancez le déploiement.
4. Après le déploiement, ouvrez [supmicrotech-bi.onrender.com](https://supmicrotech-bi.onrender.com).

Le Dockerfile construit React, puis FastAPI sert l’interface et l’API depuis la même origine. Le mode `real` lit ces deux fichiers sur le serveur ; Streamlit n’est pas utilisé par le service Render. L’offre gratuite Render peut mettre le service en veille après une période d’inactivité, ce qui ralentit la première requête suivante.
