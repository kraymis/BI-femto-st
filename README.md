# Système d’information intelligent — BI des stages

Cette partie du projet de fin d’études « Système d’information intelligent pour le pilotage et l’exploration des données d’une école d’ingénieurs » fournit un tableau de bord de Business Intelligence consacré aux conventions de stage.

## Objectifs de la partie BI

La V2 comprend cinq pages : Vue d’ensemble, Analyse temporelle, Analyse des stages, Entreprises et géographie, et Qualité des données. Elle présente des indicateurs agrégés et ne publie ni KPI de durée non validé ni comparaison de périodes. Elle n’affiche aucune ligne individuelle et ne modifie pas le classeur source. Les exports restent désactivés tant que la politique de confidentialité des petits effectifs n’est pas validée.

## Prérequis

- Python 3.10 ou ultérieur.
- `pip`, fourni avec les installations Python usuelles.

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

- `data/` : emplacements des données brutes, intermédiaires et préparées. Le classeur local `data/raw/stages_cleaned2.xlsx` peut contenir des informations personnelles ; il ne doit pas être diffusé.
- `notebooks/` : futurs travaux exploratoires et expérimentations.
- `src/bi/` : package Python de la partie BI, organisé par responsabilité.
- `dashboards/` : interface Streamlit.
- `tests/` : tests synthétiques des fonctions analytiques et d’ingestion.
- `docs/` : documentation technique et décisions d’architecture.

Le détail des modules figure dans [`docs/architecture.md`](docs/architecture.md). Les chemins applicatifs sont définis dans `src/bi/config.py` relativement à l’emplacement du module.

## Lancement

Après activation de l’environnement virtuel et installation des dépendances :

```powershell
python -m streamlit run dashboards/app.py
```

### API FastAPI (migration progressive)

L’API et Streamlit sont deux processus indépendants. Depuis la racine du projet,
l’API démarre avec :

```powershell
python -m uvicorn backend.app.main:app --reload
```

La documentation interactive est disponible sur `http://127.0.0.1:8000/docs`.
Les options de filtres sont exposées par `GET /api/v1/filters/options`, et les
KPI de la vue d’ensemble par `GET /api/v1/overview`. Les filtres catégoriels
utilisent des paramètres répétés, par exemple
`/api/v1/overview?academic_years=2024%2F2025&stage_types=PFE`. Les paramètres
`include_missing_year`, `include_missing_type` et `include_missing_nature`
permettent d’inclure explicitement les valeurs absentes ; si un seul de ces
paramètres est fourni à `true` sans valeur de catégorie, seules les lignes
manquantes de ce champ sont sélectionnées. Un paramètre catégoriel omis avec
son booléen omis est sans restriction ; fournir le booléen à `false` sans
valeur sélectionnée produit un résultat vide. L’API ne retourne ni ligne source
ni identifiant individuel.

Pour lancer les tests :

```powershell
python -m unittest discover -s tests -v
python -m pytest tests/test_api_v1.py -v
```

Consultez [`docs/audit_bi.md`](docs/audit_bi.md), [`docs/cahier_fonctionnel_bi.md`](docs/cahier_fonctionnel_bi.md), [`docs/validation_bi_v2.md`](docs/validation_bi_v2.md) et [`docs/geographie_stages.md`](docs/geographie_stages.md) pour les limites, les validations et les décisions métier encore en attente.
