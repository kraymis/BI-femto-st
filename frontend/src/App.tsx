import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  createFilterQuery,
  getFilterOptions,
  getOverview,
} from './services/dashboardApi'
import type {
  DashboardPage,
  FilterKey,
  FilterOption,
  FilterOptions,
  MissingFilterKey,
  OverviewResponse,
  SelectedFilters,
} from './types'

const CategoryChart = lazy(() => import('./CategoryChart'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPages'))

const FILTERS: {
  key: FilterKey
  missingKey: MissingFilterKey
  label: string
  optionsKey: FilterKey
}[] = [
  {
    key: 'academic_years',
    missingKey: 'include_missing_year',
    label: 'Année académique',
    optionsKey: 'academic_years',
  },
  {
    key: 'stage_types',
    missingKey: 'include_missing_type',
    label: 'Type de stage',
    optionsKey: 'stage_types',
  },
  {
    key: 'stage_natures',
    missingKey: 'include_missing_nature',
    label: 'Nature du stage',
    optionsKey: 'stage_natures',
  },
]

const CHART_COLORS = {
  year: '#315f84',
  type: '#5d85a5',
  nature: '#6b947d',
}

const NAV_ITEMS: {
  page: DashboardPage
  label: string
  icon: string
}[] = [
  { page: 'overview', label: 'Vue d’ensemble', icon: '▦' },
  { page: 'temporal', label: 'Analyse temporelle', icon: '◷' },
  { page: 'stages', label: 'Analyse des stages', icon: '◫' },
  { page: 'companies-geography', label: 'Entreprises & géographie', icon: '⌖' },
  { page: 'quality', label: 'Qualité des données', icon: '✓' },
]

function optionKey(option: FilterOption): string {
  return option.is_missing ? 'missing:' : `value:${option.value ?? ''}`
}

function formatCount(value: number): string {
  return new Intl.NumberFormat('fr-FR').format(value)
}

function FilterPicker({
  label,
  options,
  selected,
  onChange,
}: {
  label: string
  options: FilterOption[]
  selected: string[]
  onChange: (next: string[]) => void
}) {
  const allSelected = selected.length === options.length

  function toggle(key: string) {
    onChange(
      selected.includes(key)
        ? selected.filter((value) => value !== key)
        : [...selected, key],
    )
  }

  return (
    <details className="filter-picker">
      <summary>
        <span>{label}</span>
        <span className="filter-count">
          {selected.length === options.length
            ? 'Toutes'
            : `${selected.length} sélectionnée${selected.length > 1 ? 's' : ''}`}
        </span>
        <span className="chevron" aria-hidden="true" />
      </summary>
      <div className="filter-menu">
        <div className="filter-menu-actions">
          <button
            type="button"
            onClick={() =>
              onChange(allSelected ? [] : options.map(optionKey))
            }
          >
            {allSelected ? 'Tout désélectionner' : 'Tout sélectionner'}
          </button>
          <span>{selected.length} / {options.length}</span>
        </div>
        <div className="filter-options">
          {options.map((option) => {
            const key = optionKey(option)
            return (
              <label className="filter-option" key={key}>
                <input
                  type="checkbox"
                  checked={selected.includes(key)}
                  onChange={() => toggle(key)}
                />
                <span>{option.label}</span>
              </label>
            )
          })}
          {options.length === 0 && (
            <p className="filter-empty">Aucune option disponible.</p>
          )}
        </div>
      </div>
    </details>
  )
}

function MetricCard({
  label,
  value,
  description,
  icon,
}: {
  label: string
  value: number
  description: string
  icon: string
}) {
  return (
    <article className="metric-card">
      <div className="metric-heading">
        <span className="metric-icon" aria-hidden="true">{icon}</span>
        <span className="metric-label">{label}</span>
      </div>
      <strong className="metric-value">{formatCount(value)}</strong>
      <p className="metric-description">{description}</p>
    </article>
  )
}

function App() {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  const [selected, setSelected] = useState<SelectedFilters | null>(
    null,
  )
  const [activePage, setActivePage] = useState<DashboardPage>('overview')
  const [overview, setOverview] = useState<OverviewResponse | null>(null)
  const [optionsError, setOptionsError] = useState<string | null>(null)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [isLoadingOverview, setIsLoadingOverview] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    getFilterOptions(controller.signal)
      .then((options) => {
        setFilterOptions(options)
        setIsLoadingOverview(true)
        setSelected(
          Object.fromEntries(
            FILTERS.map(({ key, optionsKey }) => [
              key,
              options[optionsKey].map(optionKey),
            ]),
          ) as SelectedFilters,
        )
        setOptionsError(null)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setOptionsError(
          error instanceof Error
            ? error.message
            : 'Impossible de charger les options des filtres.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingOptions(false)
      })
    return () => controller.abort()
  }, [])

  const queryString = useMemo(() => {
    if (!filterOptions || !selected) return null
    return createFilterQuery(filterOptions, selected)
  }, [filterOptions, selected])

  useEffect(() => {
    if (queryString === null || activePage !== 'overview') return
    const controller = new AbortController()
    getOverview(queryString, controller.signal)
      .then((result) => {
        setOverview(result)
        setOverviewError(null)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setOverview(null)
        setOverviewError(
          error instanceof Error
            ? error.message
            : 'Impossible de charger les indicateurs.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingOverview(false)
      })
    return () => controller.abort()
  }, [activePage, queryString])

  function updateFilter(key: FilterKey, values: string[]) {
    setIsLoadingOverview(true)
    setOverview(null)
    setOverviewError(null)
    setSelected((current) => (current ? { ...current, [key]: values } : current))
  }

  function resetFilters() {
    if (!filterOptions) return
    const next = Object.fromEntries(
      FILTERS.map(({ key, optionsKey }) => [
        key,
        filterOptions[optionsKey].map(optionKey),
      ]),
    ) as SelectedFilters
    if (
      selected &&
      FILTERS.every(({ key }) => {
        const currentValues = selected[key]
        const nextValues = next[key]
        return (
          currentValues.length === nextValues.length &&
          currentValues.every((value, index) => value === nextValues[index])
        )
      })
    ) {
      return
    }
    setIsLoadingOverview(true)
    setOverview(null)
    setOverviewError(null)
    setSelected(
      next,
    )
  }

  const hasRows = (overview?.kpis.row_count ?? 0) > 0
  const currentPageTitle =
    NAV_ITEMS.find((item) => item.page === activePage)?.label ?? 'Vue d’ensemble'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Accueil BI des stages">
          <img
            className="brand-logo"
            src="/femto-st-logo.jpg"
            alt="Logo SUPMICROTECH-ENSMM"
          />
          <span className="brand-copy">
            <strong>SUPMICROTECH</strong>
            <small>Pilotage des stages</small>
          </span>
        </a>

        <div className="nav-section-label">ESPACE DE PILOTAGE</div>
        <nav aria-label="Navigation principale">
          {NAV_ITEMS.map((item) => (
            <button
              className={`nav-link${activePage === item.page ? ' active' : ''}`}
              type="button"
              key={item.page}
              aria-current={activePage === item.page ? 'page' : undefined}
              onClick={() => {
                if (item.page === 'overview' && activePage !== 'overview') {
                  setIsLoadingOverview(true)
                }
                setActivePage(item.page)
              }}
            >
              <span className="nav-symbol" aria-hidden="true">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          <div>
            <strong>Source en lecture seule</strong>
            <small>Aucune modification du classeur</small>
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            Pilotage des stages <span>/</span> <strong>{currentPageTitle}</strong>
          </div>
          <div className="topbar-meta">
            <span className="api-indicator">
              <span className="status-dot" /> API BI
            </span>
            <span className="topbar-divider" />
            <span>SUPMICROTECH</span>
          </div>
        </header>

        {activePage === 'overview' && (
          <section className="page-heading">
            <div>
              <p className="eyebrow">TABLEAU DE BORD · CONVENTIONS DE STAGE</p>
              <h1>Vue d’ensemble</h1>
              <p className="page-subtitle">
                Les indicateurs clés pour suivre l’activité des stages et son évolution.
              </p>
            </div>
            <div className="live-badge">
              <span className="status-dot" /> Données actualisées à la demande
            </div>
          </section>
        )}

        <section className="filters-panel" aria-label="Filtres globaux">
          <div className="filters-header">
            <div>
              <h2>Filtres globaux</h2>
              <p>Le même périmètre est appliqué à tous les indicateurs.</p>
            </div>
            <button
              className="reset-button"
              type="button"
              onClick={resetFilters}
              disabled={!filterOptions || !selected}
            >
              <span aria-hidden="true">↻</span> Réinitialiser
            </button>
          </div>
          {optionsError ? (
            <div className="inline-error" role="alert">
              <strong>Filtres indisponibles.</strong> {optionsError}
            </div>
          ) : isLoadingOptions || !filterOptions || !selected ? (
            <div className="filters-loading" aria-live="polite">
              Chargement des options de filtres…
            </div>
          ) : (
            <div className="filter-grid">
              {FILTERS.map(({ key, label, optionsKey }) => (
                <FilterPicker
                  key={key}
                  label={label}
                  options={filterOptions[optionsKey]}
                  selected={selected[key]}
                  onChange={(values) => updateFilter(key, values)}
                />
              ))}
            </div>
          )}
        </section>

        {activePage === 'overview' ? (
          <>
        <div className="section-heading">
          <div>
            <h2>Indicateurs clés</h2>
            <p>
              {overview
                ? `${formatCount(overview.kpis.row_count)} lignes dans le périmètre sélectionné`
                : 'Périmètre sélectionné'}
            </p>
          </div>
          {isLoadingOverview && (
            <span className="refreshing"><span className="spinner" /> Actualisation…</span>
          )}
        </div>

        {overviewError && (
          <div className="error-banner" role="alert">
            <span className="alert-icon">!</span>
            <div>
              <strong>Impossible de charger la vue d’ensemble</strong>
              <p>{overviewError}</p>
            </div>
          </div>
        )}

        {!overviewError && (isLoadingOverview && !overview ? (
          <div className="loading-card" aria-live="polite">
            <span className="spinner spinner-large" />
            <strong>Chargement des indicateurs…</strong>
            <span>Les calculs sont réalisés par l’API BI.</span>
          </div>
        ) : overview && hasRows ? (
          <>
            <section className="metrics-grid" aria-label="Indicateurs clés">
              <MetricCard
                label="Conventions distinctes"
                value={overview.kpis.convention_count}
                description="Décompte distinct des numéros de convention. Ce n’est pas un nombre de stages validé."
                icon="▤"
              />
              <MetricCard
                label="Étudiants distincts"
                value={overview.kpis.student_count}
                description="Nombre d’identifiants distincts, sans exposer les identifiants."
                icon="♙"
              />
              <MetricCard
                label="Années académiques renseignées"
                value={overview.kpis.academic_year_count}
                description="Modalités d’année présentes dans le périmètre."
                icon="▦"
              />
              <MetricCard
                label="Types de stage renseignés"
                value={overview.kpis.stage_type_count}
                description="Catégories distinctes ; les valeurs manquantes ne sont pas un type."
                icon="◈"
              />
            </section>

            <div className="scope-note">
              <span className="scope-icon" aria-hidden="true">i</span>
              <span>
                Les conventions sont comptées distinctement. Un numéro de convention
                n’est pas assimilé à un stage sans validation métier.
              </span>
            </div>

            {overview.notices.map((notice) => (
              <div className="notice-banner" key={notice}>
                <span className="notice-icon" aria-hidden="true">!</span>
                <span>{notice}</span>
              </div>
            ))}

            {isLoadingOverview && <div className="updating-overlay" aria-hidden="true" />}

            <section className="charts-grid" aria-label="Graphiques de synthèse">
              <Suspense
                fallback={
                  <div className="chart-loading">Chargement des graphiques…</div>
                }
              >
                <CategoryChart
                  title="Évolution des conventions"
                  data={overview.yearly_conventions}
                  color={CHART_COLORS.year}
                  wide
                />
                <CategoryChart
                  title="Répartition par type"
                  data={overview.conventions_by_type}
                  color={CHART_COLORS.type}
                  horizontal
                />
                <CategoryChart
                  title="Répartition par nature"
                  data={overview.conventions_by_nature}
                  color={CHART_COLORS.nature}
                  horizontal
                />
              </Suspense>
            </section>
            <p className="data-note">
              Les valeurs manquantes sont affichées comme « Non renseigné ». Les
              catégories ne sont ni fusionnées ni harmonisées.
            </p>
          </>
        ) : overview ? (
          <div className="empty-state" role="status">
            <span className="empty-icon" aria-hidden="true">⌕</span>
            <h2>Aucun résultat pour cette sélection</h2>
            <p>
              Aucune convention ne correspond aux filtres sélectionnés. Modifiez la
              sélection ou réinitialisez les filtres.
            </p>
            <button type="button" className="primary-button" onClick={resetFilters}>
              Réinitialiser les filtres
            </button>
          </div>
        ) : null)}
          </>
        ) : queryString && (
          <Suspense
            fallback={
              <div className="loading-card" aria-live="polite">
                <span className="spinner spinner-large" />
                <strong>Chargement de la page…</strong>
              </div>
            }
          >
            <AnalyticsPage
              page={activePage}
              query={queryString}
            />
          </Suspense>
        )}

        <footer className="page-footer">
          <span>BI · Pilotage des stages</span>
          <span>
            Source chargée côté serveur · Identifiants étudiants non affichés ·
            Détail des conventions localisées dans les popups
          </span>
        </footer>
      </main>
    </div>
  )
}

export default App
