# Frontend BI — Dashboard React

Frontend React + TypeScript construit avec Vite. Cette première étape de
migration reproduit les cinq pages Streamlit et consomme uniquement les
réponses agrégées de l’API FastAPI : Vue d’ensemble, Analyse temporelle,
Analyse des stages, Entreprises et géographie, et Qualité des données. Streamlit
reste disponible comme référence fonctionnelle pendant la validation.

## Prérequis

- Node.js `^20.19.0` ou `>=22.12.0`.
- npm, fourni avec Node.js.

## Démarrage en développement

Depuis la racine du dépôt, dans un terminal, démarrez l’API :

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Dans un second terminal :

```powershell
Set-Location frontend
npm install
npm run dev
```

Ouvrez `http://localhost:5173`. L’API utilise par défaut
`http://localhost:8000`. Pour configurer une autre URL, copiez `.env.example`
vers `.env.local` et modifiez `VITE_API_BASE_URL`. Seules les origines Vite
locales `http://localhost:5173` et `http://127.0.0.1:5173` sont autorisées en
CORS.

## Build

```powershell
npm run build
```

Les pages utilisent `GET /api/v1/overview`, `/temporal`, `/stages`,
`/companies-geography` et `/quality`. Les options partagées viennent de
`GET /api/v1/filters/options`. Les calculs sont exécutés dans `src/bi/` et le
frontend ne demande ni ne reçoit de lignes brutes ou d’identifiants étudiants.
Les popups de la carte présentent le nombre de conventions par destination,
les numéros de convention associés et, lorsqu’il est renseigné, le libellé
`entreprise` de chaque convention. La carte utilise les coordonnées publiables
renvoyées par le backend et OpenStreetMap pour son fond cartographique ; les
détails sous le seuil configuré restent masqués. L’API n’ayant pas
d’authentification, elle doit rester sur un réseau de confiance.

## Vérifications

Depuis `frontend/` :

```powershell
npm test
npm run lint
npm run build
```
