import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Circle,
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'
import { latLngBounds } from 'leaflet'
import {
  getCompaniesGeography,
  getQuality,
  getStages,
  getTemporal,
} from '../services/dashboardApi'
import type {
  CategoryAggregate,
  CategoryLabel,
  CompanyGeographyResponse,
  CrossTabResponse,
  DashboardPage,
  FieldCoverage,
  GeographyDestination,
  QualityResponse,
  StageAnalysisResponse,
  TemporalAnalysisResponse,
} from '../types'
import CategoryChart from '../CategoryChart'
import { DataTable } from '../components/DataTable'
import { PaginationControls } from '../components/PaginationControls'

const PAGE_TITLES: Record<Exclude<DashboardPage, 'overview'>, string> = {
  temporal: 'Analyse temporelle',
  stages: 'Analyse des stages',
  'companies-geography': 'Entreprises et géographie',
  quality: 'Qualité des données',
}

const PALETTE = [
  '#315f84',
  '#5d85a5',
  '#6b947d',
  '#b28754',
  '#8c739d',
  '#6c9d9b',
  '#b16f69',
  '#8293a4',
]

const formatCount = (value: number) => new Intl.NumberFormat('fr-FR').format(value)

function formatPercentage(value: number | null) {
  if (value === null) return 'Non calculable'
  return `${new Intl.NumberFormat('fr-FR', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(value)} %`
}

function useApiResource<T>(
  query: string,
  load: (query: string, signal: AbortSignal) => Promise<T>,
) {
  const [resource, setResource] = useState<{
    query: string
    data: T | null
    error: string | null
    loading: boolean
  }>({ query: '', data: null, error: null, loading: true })

  useEffect(() => {
    const controller = new AbortController()
    load(query, controller.signal)
      .then((data) => setResource({ query, data, error: null, loading: false }))
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === 'AbortError') return
        setResource({
          query,
          data: null,
          error: reason instanceof Error
            ? reason.message
            : 'Impossible de charger les données de cette page.',
          loading: false,
        })
      })
    return () => controller.abort()
  }, [load, query])

  const isCurrentQuery = resource.query === query
  return {
    data: isCurrentQuery ? resource.data : null,
    error: isCurrentQuery ? resource.error : null,
    loading: !isCurrentQuery || resource.loading,
  }
}

function PageStatus<T>({
  resource,
  children,
}: {
  resource: { data: T | null; error: string | null; loading: boolean }
  children: (data: T) => ReactNode
}) {
  if (resource.error) {
    return <div className="error-banner" role="alert">{resource.error}</div>
  }
  if (resource.loading || !resource.data) {
    return (
      <div className="loading-card" aria-live="polite">
        <span className="spinner spinner-large" />
        <strong>Chargement des indicateurs…</strong>
        <span>Les calculs sont réalisés par l’API BI.</span>
      </div>
    )
  }
  return <>{children(resource.data)}</>
}

function EmptySelectionState() {
  return (
    <div className="empty-state" role="status">
      <span className="empty-icon" aria-hidden="true">⌕</span>
      <h2>Aucun résultat pour cette sélection</h2>
      <p>
        Aucune convention ne correspond aux filtres sélectionnés. Modifiez la
        sélection ou réinitialisez les filtres globaux.
      </p>
    </div>
  )
}

function Metric({
  label,
  value,
  description,
}: {
  label: string
  value: string | number
  description?: string
}) {
  return (
    <article className="metric-card">
      <div className="metric-heading">
        <span className="metric-label">{label}</span>
      </div>
      <strong className="metric-value">
        {typeof value === 'number' ? formatCount(value) : value}
      </strong>
      {description && <p className="metric-description">{description}</p>}
    </article>
  )
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="chart-card analysis-panel">
      <div className="chart-title-row">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  )
}

function CrossTabTable({
  data,
  measure,
}: {
  data: CrossTabResponse
  measure: 'counts' | 'percentages'
}) {
  if (data.unavailable) {
    return (
      <div className="inline-warning" role="status">
        Tableau croisé indisponible : une convention est associée à plusieurs
        modalités pour cette dimension.
      </div>
    )
  }
  const getCell = (row: CategoryLabel, column: CategoryLabel) =>
    data.cells.find(
      (cell) =>
        cell.row_category === row.category &&
        cell.row_is_missing === row.category_is_missing &&
        cell.column_category === column.category &&
        cell.column_is_missing === column.category_is_missing,
    )
  const rows = data.row_categories.map((row) => {
    const cells = data.column_categories.map((column) => {
      const cell = getCell(row, column)
      if (!cell) return '—'
      return measure === 'counts'
        ? formatCount(cell.convention_count)
        : formatPercentage(cell.percentage)
    })
    const total = data.row_totals.find(
      (item) =>
        item.category === row.category &&
        item.category_is_missing === row.category_is_missing,
    )
    cells.push(
      measure === 'counts'
        ? formatCount(total?.convention_count ?? 0)
        : total?.convention_count
          ? '100,0 %'
          : 'Non calculable',
    )
    return [
      row.category,
      ...cells,
    ]
  })
  if (measure === 'counts' && data.row_categories.length) {
    rows.push([
      'Total',
      ...data.column_totals.map((total) => formatCount(total.convention_count)),
      formatCount(data.grand_total),
    ])
  }
  return (
    <DataTable
      headers={[
        'Catégorie',
        ...data.column_categories.map((category) => category.category),
        measure === 'counts' ? 'Total conventions' : 'Total de ligne',
      ]}
      rows={rows}
    />
  )
}

function MeasureSwitch({
  value,
  onChange,
}: {
  value: 'counts' | 'percentages'
  onChange: (value: 'counts' | 'percentages') => void
}) {
  return (
    <div className="measure-switch" role="group" aria-label="Mesure des tableaux">
      <button
        type="button"
        aria-pressed={value === 'counts'}
        onClick={() => onChange('counts')}
      >
        Effectifs
      </button>
      <button
        type="button"
        aria-pressed={value === 'percentages'}
        onClick={() => onChange('percentages')}
      >
        Pourcentages par ligne
      </button>
    </div>
  )
}

function CompositionChart({
  data,
  measure,
  title,
}: {
  data: CrossTabResponse
  measure: 'counts' | 'percentages'
  title: string
}) {
  const chartData = data.row_categories.map((row) => {
    const entry: Record<string, string | number | null> = {
      category: row.category,
    }
    for (const column of data.column_categories) {
      const cell = data.cells.find(
        (candidate) =>
          candidate.row_category === row.category &&
          candidate.row_is_missing === row.category_is_missing &&
          candidate.column_category === column.category &&
          candidate.column_is_missing === column.category_is_missing,
      )
      entry[column.category] = measure === 'counts'
        ? cell?.convention_count ?? 0
        : cell?.percentage ?? null
    }
    return entry
  })
  if (data.unavailable) {
    return <div className="table-empty">Composition indisponible pour ce périmètre.</div>
  }
  if (chartData.length === 0) {
    return <div className="table-empty">Aucune donnée à afficher.</div>
  }
  return (
    <div className="chart-canvas analysis-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 12, right: 18, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="#e9edf2" strokeDasharray="3 4" vertical={false} />
          <XAxis dataKey="category" tick={{ fill: '#637487', fontSize: 11 }} />
          <YAxis
            allowDecimals={measure === 'percentages'}
            domain={measure === 'percentages' ? [0, 100] : undefined}
            tick={{ fill: '#728096', fontSize: 11 }}
          />
          <Tooltip formatter={(value) => measure === 'percentages'
            ? formatPercentage(typeof value === 'number' ? value : null)
            : formatCount(Number(value ?? 0))}
          />
          <Legend />
          {data.column_categories.map((column, index) => (
            <Bar
              key={`${column.category}-${column.category_is_missing}`}
              dataKey={column.category}
              name={column.category}
              stackId="composition"
              fill={PALETTE[index % PALETTE.length]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <p className="chart-caption">{title}</p>
    </div>
  )
}

function TemporalPage({ query }: { query: string }) {
  const load = useMemo(() => getTemporal, [])
  const resource = useApiResource<TemporalAnalysisResponse>(query, load)
  const [measure, setMeasure] = useState<'counts' | 'percentages'>('counts')
  return (
    <PageStatus resource={resource}>
      {(data) => data.yearly_conventions.length === 0 ? <EmptySelectionState /> : (
        <div className="analysis-page">
          <p className="page-subtitle">
            Répartition descriptive des conventions au fil des années académiques.
          </p>
          <MeasureSwitch value={measure} onChange={setMeasure} />
          <section className="charts-grid">
            <CategoryChart
              title="Conventions par année"
              data={data.yearly_conventions}
              color="#245A81"
              wide
            />
            <Panel
              title="Composition annuelle par type"
              subtitle={measure === 'counts'
                ? 'Conventions distinctes'
                : 'Pourcentage parmi les catégories observées de chaque année'}
            >
              <CompositionChart
                data={data.year_by_type}
                measure={measure}
                title="Les volumes ne constituent pas une comparaison de périodes complètes."
              />
            </Panel>
            <Panel title="Tableau croisé — année × type">
              <CrossTabTable data={data.year_by_type} measure={measure} />
            </Panel>
            <Panel title="Composition relative au sein de chaque année">
              <CrossTabTable data={data.year_by_type} measure="percentages" />
            </Panel>
          </section>
          {data.notices.map((notice) => (
            <div className="notice-banner" key={notice}>{notice}</div>
          ))}
        </div>
      )}
    </PageStatus>
  )
}

function StagePage({ query }: { query: string }) {
  const load = useMemo(() => getStages, [])
  const resource = useApiResource<StageAnalysisResponse>(query, load)
  const [measure, setMeasure] = useState<'counts' | 'percentages'>('counts')
  const [topN, setTopN] = useState(10)
  const [search, setSearch] = useState('')
  return (
    <PageStatus resource={resource}>
      {(data) => {
        const queryText = search.trim().toLocaleLowerCase('fr')
        const matches = (row: CategoryAggregate) =>
          !queryText || row.category.toLocaleLowerCase('fr').includes(queryText)
        const types = data.conventions_by_type.filter(matches)
        const natures = data.conventions_by_nature.filter(matches)
        if (types.length === 0 && natures.length === 0) {
          return <EmptySelectionState />
        }
        const summaryRows = [
          ...types.map((row) => ({ family: 'Type', row })),
          ...natures.map((row) => ({ family: 'Nature', row })),
        ]
        return (
          <div className="analysis-page">
            <p className="page-subtitle">
              Composition par type et nature ; les effectifs comptent des conventions distinctes.
            </p>
            <div className="analysis-controls">
              <MeasureSwitch value={measure} onChange={setMeasure} />
              <label className="control-field">
                Catégories affichées
                <select value={topN} onChange={(event) => setTopN(Number(event.target.value))}>
                  {[5, 10, 20, 50].map((value) => <option key={value}>{value}</option>)}
                </select>
              </label>
              <label className="control-field search-field">
                Rechercher une catégorie
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Saisir un libellé"
                />
              </label>
            </div>
            <section className="charts-grid">
              <CategoryChart title="Types de stage" data={types.slice(0, topN)} color="#3B78A1" horizontal />
              <CategoryChart title="Natures de stage" data={natures.slice(0, topN)} color="#50886C" horizontal />
              <Panel title="Tableau croisé — type × nature">
                <CrossTabTable data={data.type_by_nature} measure={measure} />
              </Panel>
              <Panel title="Récapitulatif des catégories">
                <DataTable
                  headers={['Famille', 'Catégorie', 'Conventions distinctes', 'Dénominateur', 'Part du total']}
                  rows={summaryRows.map(({ family, row }) => [
                    family,
                    row.category,
                    formatCount(row.convention_count),
                    formatCount(row.denominator),
                    formatPercentage(row.percentage),
                  ])}
                  emptyMessage="Aucune catégorie ne correspond à la recherche."
                />
                {!queryText && (
                  <p className="chart-caption">
                    Le sélecteur Top N limite uniquement les graphiques ; le tableau conserve toutes les catégories.
                  </p>
                )}
              </Panel>
            </section>
          </div>
        )
      }}
    </PageStatus>
  )
}

function CoverageTable({ rows }: { rows: FieldCoverage[] }) {
  return (
    <DataTable
      headers={['Champ', 'Valeurs renseignées', 'Valeurs manquantes', 'Couverture']}
      rows={rows.map((row) => [
        row.label,
        `${formatCount(row.present_count)} / ${formatCount(row.denominator)}`,
        formatCount(row.missing_count),
        formatPercentage(row.completion_percentage),
      ])}
    />
  )
}

function DestinationMap({
  destinations,
  radiusKm,
  radiusEnabled,
}: {
  destinations: GeographyDestination[]
  radiusKm: number
  radiusEnabled: boolean
}) {
  const bounds = useMemo(() => {
    const points: [number, number][] = [
      [47.250944, 5.9942287],
      ...destinations.map(
        (item): [number, number] => [item.latitude, item.longitude],
      ),
    ]
    const schoolLatitude = 47.250944
    const schoolLongitude = 5.9942287
    if (radiusEnabled) {
      const latitudeDelta = radiusKm / 111.32
      const longitudeDelta =
        radiusKm / (111.32 * Math.cos((schoolLatitude * Math.PI) / 180))
      points.push(
        [schoolLatitude - latitudeDelta, schoolLongitude - longitudeDelta],
        [schoolLatitude + latitudeDelta, schoolLongitude + longitudeDelta],
      )
    }
    return latLngBounds(points)
  }, [destinations, radiusKm, radiusEnabled])
  return (
    <div className="map-container">
      <MapContainer
        center={[47.250944, 5.9942287]}
        zoom={5}
        scrollWheelZoom
        className="destination-map"
      >
        <BoundsUpdater bounds={bounds} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {radiusEnabled && (
          <Circle
            center={[47.250944, 5.9942287]}
            radius={radiusKm * 1000}
            pathOptions={{
              color: '#2f6f9f',
              weight: 2,
              fillColor: '#75a9cb',
              fillOpacity: 0.12,
            }}
          />
        )}
        {destinations.map((destination) => (
          <CircleMarker
            key={`${destination.city}:${destination.country ?? ''}`}
            center={[destination.latitude, destination.longitude]}
            radius={7}
            pathOptions={{ color: '#fff', weight: 2, fillColor: '#246b9e', fillOpacity: 0.92 }}
          >
            <Popup>
              <strong>{destination.city}, {destination.country ?? 'Pays non renseigné'}</strong>
              <br />
              Conventions distinctes : {formatCount(destination.convention_count)}
              <br />
              <strong>Conventions associées :</strong>
              <ul className="map-convention-list">
                {destination.conventions.map((convention) => (
                  <li key={convention.convention_id}>
                    <strong>{convention.convention_id}</strong>
                    {convention.companies.length > 0 && (
                      <span> — Entreprise : {convention.companies.join(', ')}</span>
                    )}
                  </li>
                ))}
              </ul>
              <br />
              Distance estimée à vol d’oiseau :{' '}
              {new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(destination.distance_km)} km
            </Popup>
          </CircleMarker>
        ))}
        <CircleMarker
          center={[47.250944, 5.9942287]}
          radius={9}
          pathOptions={{ color: '#fff', weight: 2, fillColor: '#b22222', fillOpacity: 1 }}
        >
          <Popup>SUPMICROTECH-ENSMM — établissement de référence</Popup>
        </CircleMarker>
      </MapContainer>
    </div>
  )
}

function BoundsUpdater({ bounds }: { bounds: ReturnType<typeof latLngBounds> }) {
  const map = useMap()
  useEffect(() => {
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [20, 20] })
  }, [bounds, map])
  return null
}

function CompaniesGeographyPage({ query }: { query: string }) {
  const load = useMemo(() => getCompaniesGeography, [])
  const resource = useApiResource<CompanyGeographyResponse>(query, load)
  const [companyTopN, setCompanyTopN] = useState(10)
  const [companySearch, setCompanySearch] = useState('')
  const [destinationTopN, setDestinationTopN] = useState(10)
  const [radiusKm, setRadiusKm] = useState(100)
  const [radiusInputValue, setRadiusInputValue] = useState('100')
  const [radiusEnabled, setRadiusEnabled] = useState(true)
  const [conventionPagination, setConventionPagination] = useState({
    query,
    radiusKm: 100,
    radiusEnabled: true,
    page: 1,
  })
  const [conventionsPerPage, setConventionsPerPage] = useState(10)
  const conventionPage =
    conventionPagination.query === query &&
    conventionPagination.radiusKm === radiusKm &&
    conventionPagination.radiusEnabled === radiusEnabled
      ? conventionPagination.page
      : 1
  const setConventionPage = (page: number) => {
    setConventionPagination({ query, radiusKm, radiusEnabled, page })
  }
  const destinations = useMemo(
    () =>
      [...(resource.data?.destinations ?? [])].sort(
        (a, b) => b.convention_count - a.convention_count,
      ),
    [resource.data],
  )
  const nearbyDestinations = useMemo(
    () =>
      radiusEnabled
        ? destinations.filter((destination) => destination.distance_km <= radiusKm)
        : destinations,
    [destinations, radiusKm, radiusEnabled],
  )
  const nearbyConventions = useMemo(() => {
    const conventions = new Map<
      string,
      { destination: GeographyDestination; companies: Set<string> }
    >()
    for (const destination of nearbyDestinations) {
      for (const convention of destination.conventions) {
        const detail = conventions.get(convention.convention_id) ?? {
          destination,
          companies: new Set<string>(),
        }
        for (const company of convention.companies) {
          detail.companies.add(company)
        }
        conventions.set(convention.convention_id, detail)
      }
    }
    return [...conventions.entries()].sort(([left], [right]) =>
      left.localeCompare(right, 'fr', { numeric: true }),
    )
  }, [nearbyDestinations])
  const totalConventionPages = Math.ceil(
    nearbyConventions.length / conventionsPerPage,
  )
  const displayedConventionPage = Math.min(
    conventionPage,
    totalConventionPages || 1,
  )
  const visibleConventions = nearbyConventions.slice(
    (displayedConventionPage - 1) * conventionsPerPage,
    displayedConventionPage * conventionsPerPage,
  )
  const updateRadius = (nextRadius: number) => {
    setRadiusKm(nextRadius)
    setRadiusInputValue(String(nextRadius))
    setConventionPagination({
      query,
      radiusKm: nextRadius,
      radiusEnabled,
      page: 1,
    })
  }
  const updateRadiusEnabled = (enabled: boolean) => {
    setRadiusEnabled(enabled)
    setConventionPagination({ query, radiusKm, radiusEnabled: enabled, page: 1 })
  }
  const updateRadiusInput = (value: string) => {
    setRadiusInputValue(value)
    if (value.trim() === '') return
    const nextRadius = Number(value)
    if (Number.isInteger(nextRadius) && nextRadius >= 25 && nextRadius <= 1000) {
      updateRadius(nextRadius)
    }
  }

  return (
    <PageStatus resource={resource}>
      {(data) => {
        if (data.row_count === 0) return <EmptySelectionState />
        const companies = data.companies.filter((row) =>
          row.category.toLocaleLowerCase('fr').includes(companySearch.trim().toLocaleLowerCase('fr')),
        )
        const nearbyCompanies = new Set(
          nearbyConventions.flatMap(([, detail]) => [
            ...detail.companies,
          ]),
        )
        return (
          <div className="analysis-page">
            <p className="page-subtitle">
              Exploration descriptive des libellés d’entreprise et des lieux renseignés.
            </p>
            <div className="notice-banner">
              Ces résultats sont exploratoires : la définition de l’entreprise d’accueil reste à valider.
              Le seuil géographique configuré est de {data.geography_threshold ?? 'aucune'} convention(s) par destination ;
              sa validation institutionnelle reste nécessaire avant diffusion. Aucun export n’est disponible.
            </div>
            <section className="analysis-grid">
              <Panel title="Couverture des champs d’entreprise et de localisation">
                <CoverageTable rows={data.exploration_coverage} />
              </Panel>
              <Panel
                title="Libellés d’entreprise — exploration"
                subtitle="Les libellés ne sont pas des entités juridiques validées et ne sont pas fusionnés."
              >
                {data.companies_available ? (
                  <>
                    <div className="inline-controls">
                      <input
                        type="search"
                        aria-label="Rechercher un libellé d’entreprise"
                        placeholder="Rechercher une entreprise"
                        value={companySearch}
                        onChange={(event) => setCompanySearch(event.target.value)}
                      />
                      <select
                        aria-label="Nombre d’entreprises à afficher"
                        value={companyTopN}
                        onChange={(event) => setCompanyTopN(Number(event.target.value))}
                      >
                        {[5, 10, 20].map((value) => <option key={value}>{value}</option>)}
                      </select>
                    </div>
                    <CategoryChart
                      title="Conventions par libellé d’entreprise"
                      data={companies.slice(0, companyTopN)}
                      color="#557C9E"
                      horizontal
                    />
                    <p className="chart-caption">
                      Les conventions sans libellé restent dans le périmètre global, mais ne figurent pas au classement.
                    </p>
                  </>
                ) : (
                  <div className="table-empty">Le champ entreprise n’est pas disponible.</div>
                )}
              </Panel>
              <Panel title="Destinations par pays">
                {data.country_available ? (
                  <>
                    <Metric
                      label="Pays du lieu renseigné"
                      value={`${formatCount(data.country_present_count ?? 0)} / ${formatCount(data.row_count)} lignes`}
                      description="Indicateur de couverture au niveau ligne, pas un nombre de conventions."
                    />
                    <DataTable
                      headers={['Pays', 'Conventions distinctes', 'Dénominateur', 'Part (%)']}
                      rows={data.countries.map((row) => [
                        row.category,
                        formatCount(row.convention_count),
                        formatCount(row.denominator),
                        formatPercentage(row.percentage),
                      ])}
                      emptyMessage={data.geography_threshold === null
                        ? 'La répartition détaillée par pays est désactivée sans seuil de confidentialité.'
                        : 'Aucun groupe par pays ne satisfait le seuil configuré.'}
                    />
                  </>
                ) : (
                  <div className="table-empty">Le champ du pays du lieu est absent.</div>
                )}
              </Panel>
            </section>
            <Panel title="Couverture géographique et distances">
              <p className="chart-caption">
                Destination calculée uniquement avec les champs ville et pays du lieu de stage.
                La distance est estimée à vol d’oiseau depuis SUPMICROTECH-ENSMM.
              </p>
              {!data.geography_available ? (
                <div className="inline-warning" role="status">
                  {data.geography_message ?? 'L’analyse géographique est indisponible.'}
                </div>
              ) : data.geography_summary ? (
                <>
                  <div className="metrics-grid geo-metrics">
                    <Metric label="Conventions distinctes du périmètre" value={data.geography_summary.total_conventions} />
                    <Metric
                      label="Coordonnées valides"
                      value={`${formatCount(data.geography_summary.located_conventions)} / ${formatCount(data.geography_summary.total_conventions)}`}
                    />
                    <Metric label="Couverture géographique" value={formatPercentage(data.geography_summary.coverage_percentage)} />
                    <Metric
                      label="Conventions avec ville de stage renseignée"
                      value={data.geography_summary.destination_available_conventions}
                      description="Une ville est renseignée dans la source ; des coordonnées valides sont nécessaires pour apparaître sur la carte."
                    />
                    <Metric label="Conventions non localisées" value={data.geography_summary.not_located_conventions} />
                    <Metric label="Destinations localisées" value={data.geography_summary.localized_destinations} />
                    <Metric label="Conventions sans pays" value={data.geography_summary.missing_country_conventions} />
                    <Metric
                      label="Pays renseigné et non ambigu"
                      value={`${formatCount(data.geography_summary.country_denominator)} / ${formatCount(data.geography_summary.total_conventions)}`}
                    />
                  </div>
                  <DataTable
                    headers={['État géographique', 'Conventions', 'Dénominateur', 'Part']}
                    rows={data.geography_status_counts.map((row) => [
                      row.label,
                      formatCount(row.convention_count),
                      formatCount(row.denominator),
                      formatPercentage(row.percentage),
                    ])}
                  />
                  {data.geography_summary.total_conventions > 0 &&
                    data.geography_summary.located_conventions <= data.geography_summary.total_conventions / 2 && (
                      <div className="inline-warning">
                        La majorité des conventions ne peut pas être localisée ; les résultats ne sont pas représentatifs de l’ensemble.
                      </div>
                    )}
                  {!!data.geography_summary.ambiguous_conventions && (
                    <div className="inline-warning">
                      {formatCount(data.geography_summary.ambiguous_conventions)} convention(s) associée(s) à plusieurs destinations sont exclues des distances.
                    </div>
                  )}
                  {!!data.geography_summary.ambiguous_country_conventions && (
                    <div className="inline-warning">
                      {formatCount(data.geography_summary.ambiguous_country_conventions)} convention(s) associée(s) à plusieurs pays sont exclues de la répartition par pays.
                    </div>
                  )}
                  {data.geography_message && (
                    <div className="inline-warning">{data.geography_message}</div>
                  )}
                  {data.destinations.length === 0 ? (
                    <div className="table-empty">
                      Aucune destination ne satisfait le seuil de confidentialité configuré.
                    </div>
                  ) : (
                    <>
                      <h3 className="analysis-subheading">Destinations localisées</h3>
                      <div className="radius-control">
                        <label className="radius-enable">
                          <input
                            type="checkbox"
                            checked={radiusEnabled}
                            onChange={(event) => updateRadiusEnabled(event.target.checked)}
                          />
                          <span>Activer le filtre par rayon</span>
                          <small>
                            {radiusEnabled
                              ? 'Seules les destinations dans le rayon sont affichées.'
                              : 'Désactivé : toutes les destinations localisées qui respectent le seuil sont affichées.'}
                          </small>
                        </label>
                        <div className="radius-control-heading">
                          <div>
                            <label htmlFor="geography-radius">
                              Rayon autour de SUPMICROTECH-ENSMM
                            </label>
                            <p>Distance estimée à vol d’oiseau</p>
                          </div>
                          <label className="radius-number-field">
                            <span>Rayon</span>
                            <div>
                              <input
                                id="geography-radius"
                                type="number"
                                min="25"
                                max="1000"
                                step="1"
                                value={radiusInputValue}
                                disabled={!radiusEnabled}
                                aria-label="Rayon en kilomètres"
                                aria-invalid={
                                  radiusInputValue.trim() !== '' &&
                                  (!Number.isInteger(Number(radiusInputValue)) ||
                                    Number(radiusInputValue) < 25 ||
                                    Number(radiusInputValue) > 1000)
                                }
                                onBlur={() => {
                                  const parsedRadius = Number(radiusInputValue)
                                  if (
                                    !Number.isInteger(parsedRadius) ||
                                    parsedRadius < 25 ||
                                    parsedRadius > 1000
                                  ) {
                                    setRadiusInputValue(String(radiusKm))
                                  }
                                }}
                                onChange={(event) => {
                                  updateRadiusInput(event.target.value)
                                }}
                              />
                              <span>km</span>
                            </div>
                          </label>
                        </div>
                        <div className="radius-slider">
                          <input
                            id="geography-radius-slider"
                            type="range"
                            min="25"
                            max="1000"
                            step="1"
                            value={radiusKm}
                            disabled={!radiusEnabled}
                            aria-valuetext={`${radiusKm} kilomètres`}
                            onChange={(event) => updateRadius(Number(event.target.value))}
                          />
                          <div className="radius-slider-scale" aria-hidden="true">
                            <span>25 km</span>
                            <span>1 000 km</span>
                          </div>
                        </div>
                        <div className="radius-presets" aria-label="Rayons rapides">
                          <span>Repères rapides</span>
                          {[50, 100, 250, 500].map((preset) => (
                            <button
                              type="button"
                              key={preset}
                              className={radiusKm === preset ? 'active' : ''}
                              aria-pressed={radiusKm === preset}
                              disabled={!radiusEnabled}
                              onClick={() => updateRadius(preset)}
                            >
                              {preset} km
                            </button>
                          ))}
                        </div>
                      </div>
                      <p className="chart-caption">
                        {radiusEnabled
                          ? `Le cercle et les résultats utilisent la distance estimée à vol d’oiseau. Les destinations localisées dans un rayon de ${radiusKm} km et respectant le seuil sont affichées.`
                          : 'Le filtre par rayon est désactivé : toutes les destinations localisées respectant le seuil configuré sont affichées.'}
                      </p>
                      <DestinationMap
                        destinations={nearbyDestinations}
                        radiusKm={radiusKm}
                        radiusEnabled={radiusEnabled}
                      />
                      <div className="metrics-grid geo-metrics radius-metrics">
                        <Metric
                          label={radiusEnabled ? 'Destinations dans le rayon' : 'Destinations localisées'}
                          value={nearbyDestinations.length}
                        />
                        <Metric
                          label={radiusEnabled ? 'Conventions dans le rayon' : 'Conventions localisées'}
                          value={nearbyConventions.length}
                        />
                        <Metric label="Entreprises renseignées" value={nearbyCompanies.size} />
                      </div>
                      <h3 className="analysis-subheading">
                        {radiusEnabled
                          ? 'Conventions et entreprises dans le rayon'
                          : 'Conventions et entreprises des destinations localisées'}
                      </h3>
                      <DataTable
                        headers={['Ville', 'Pays', 'Convention', 'Entreprise(s)']}
                        rows={visibleConventions.map(
                          ([conventionId, detail]) => [
                            detail.destination.city,
                            detail.destination.country ?? 'Non renseigné',
                            conventionId,
                            [...detail.companies].join(', ') || 'Non renseignée',
                          ],
                        )}
                        emptyMessage={radiusEnabled
                          ? `Aucune destination localisée dans un rayon de ${radiusKm} km.`
                          : 'Aucune convention associée aux destinations localisées.'}
                      />
                      {nearbyConventions.length > 0 && (
                        <PaginationControls
                          page={displayedConventionPage}
                          pageSize={conventionsPerPage}
                          totalCount={nearbyConventions.length}
                          totalPages={totalConventionPages}
                          itemLabel="conventions"
                          onPageChange={setConventionPage}
                          onPageSizeChange={(size) => {
                            setConventionsPerPage(size)
                            setConventionPage(1)
                          }}
                        />
                      )}
                      <p className="chart-caption">
                        Les données affichées concernent les conventions associées à des destinations dont les coordonnées sont localisées et respectent le seuil de {data.geography_threshold} convention(s). Aucun identifiant étudiant n’est exposé.
                      </p>
                      <div className="inline-controls">
                        <label>
                          Destinations affichées
                          <select value={destinationTopN} onChange={(event) => setDestinationTopN(Number(event.target.value))}>
                            {[5, 10, 20].map((value) => <option key={value}>{value}</option>)}
                          </select>
                        </label>
                      </div>
                      <DataTable
                        headers={['Ville', 'Pays', 'Conventions distinctes', 'Distance estimée à vol d’oiseau']}
                        rows={destinations.slice(0, destinationTopN).map((item) => [
                          item.city,
                          item.country ?? 'Non renseigné',
                          formatCount(item.convention_count),
                          `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(item.distance_km)} km`,
                        ])}
                      />
                      <h3 className="analysis-subheading">Distances par classe</h3>
                      <DataTable
                        headers={['Classe de distance', 'Conventions distinctes', 'Dénominateur', 'Part parmi les conventions localisées']}
                        rows={data.distance_bands.map((item) => [
                          item.category,
                          formatCount(item.convention_count),
                          formatCount(item.denominator),
                          formatPercentage(item.percentage),
                        ])}
                      />
                    </>
                  )}
                </>
              ) : null}
            </Panel>
          </div>
        )
      }}
    </PageStatus>
  )
}

function CompletionChart({
  title,
  data,
}: {
  title: string
  data: { label: string; value: number }[]
}) {
  if (!data.length) return <div className="table-empty">Aucune couverture calculable.</div>
  const sorted = [...data].sort((a, b) => a.value - b.value)
  return (
    <Panel title={title}>
      <div className="chart-canvas quality-chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sorted} layout="vertical" margin={{ top: 10, right: 24, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="#e9edf2" strokeDasharray="3 4" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} tick={{ fontSize: 10 }} />
            <YAxis type="category" dataKey="label" width={160} tick={{ fontSize: 10 }} />
            <Tooltip formatter={(value) => formatPercentage(Number(value))} />
            <Bar dataKey="value" name="Valeurs renseignées" fill="#557C9E" radius={[0, 5, 5, 0]}>
              {sorted.map((row) => <Cell key={row.label} fill="#557C9E" />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  )
}

function QualityPage({ query }: { query: string }) {
  const load = useMemo(() => getQuality, [])
  const resource = useApiResource<QualityResponse>(query, load)
  const [selectedFields, setSelectedFields] = useState<string[] | null>(null)

  return (
    <PageStatus resource={resource}>
      {(data) => {
        const activeFields = selectedFields ?? data.yearly_fields
        const yearlyRows = data.yearly_coverage.filter((row) =>
          activeFields.includes(row.field),
        )
        const lineData = [...new Set(yearlyRows.map((row) => row.academic_year))]
          .map((year) => {
            const point: Record<string, string | number | null> = { year }
            for (const field of activeFields) {
              point[field] = yearlyRows.find(
                (row) => row.academic_year === year && row.field === field,
              )?.completion_percentage ?? null
            }
            return point
          })
        return (
          <div className="analysis-page">
            <p className="page-subtitle">
              Contrôles agrégés uniquement ; aucune correction n’est appliquée au classeur.
            </p>
            <section className="metrics-grid quality-metrics">
              <Metric label="Lignes — fichier complet" value={data.full_row_count} />
              <Metric label="Conventions — fichier complet" value={data.full_convention_count} />
              <Metric label="Conventions — périmètre filtré" value={data.filtered_convention_count} />
            </section>
            <p className="chart-caption">
              Les deux premiers indicateurs concernent le fichier complet ; le troisième suit les filtres globaux.
            </p>
            {data.missing_fields.length > 0 && (
              <div className="inline-warning">
                Champs facultatifs absents ; contrôles indisponibles : {data.missing_fields.map((item) => item.label).join(', ')}.
              </div>
            )}
            <section className="charts-grid">
              <Panel title="Couverture — fichier complet">
                <CoverageTable rows={data.full_coverage} />
              </Panel>
              <CompletionChart
                title="Couverture des champs — fichier complet"
                data={data.full_coverage.flatMap((row) =>
                  row.completion_percentage === null
                    ? []
                    : [{ label: row.label, value: row.completion_percentage }],
                )}
              />
              <Panel title="Couverture — périmètre filtré">
                {data.filtered_coverage.length === 0 && data.full_row_count > 0 ? (
                  <div className="inline-warning">
                    Aucune ligne ne correspond aux filtres ; la couverture filtrée n’est pas calculable.
                  </div>
                ) : (
                  <CoverageTable rows={data.filtered_coverage} />
                )}
              </Panel>
              <Panel title="Couverture par année académique">
                <label className="control-field yearly-field-select">
                  Champs à comparer
                  <select
                    multiple
                    value={activeFields}
                    onChange={(event) => setSelectedFields(
                      Array.from(event.currentTarget.selectedOptions, (option) => option.value),
                    )}
                  >
                    {data.yearly_coverage
                      .filter((row, index, all) => all.findIndex((item) => item.field === row.field) === index)
                      .map((row) => <option key={row.field} value={row.field}>{row.label}</option>)}
                  </select>
                </label>
                {!activeFields.length ? (
                  <div className="table-empty">Sélectionnez au moins un champ pour afficher la comparaison.</div>
                ) : (
                  <div className="chart-canvas yearly-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={lineData} margin={{ top: 12, right: 18, bottom: 12, left: 4 }}>
                        <CartesianGrid stroke="#e9edf2" strokeDasharray="3 4" />
                        <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                        <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} tick={{ fontSize: 10 }} />
                        <Tooltip formatter={(value) => formatPercentage(typeof value === 'number' ? value : null)} />
                        <Legend />
                        {activeFields.map((field, index) => (
                          <Line
                            key={field}
                            type="monotone"
                            dataKey={field}
                            name={data.yearly_coverage.find((row) => row.field === field)?.label ?? field}
                            stroke={PALETTE[index % PALETTE.length]}
                            strokeWidth={2}
                            dot
                            connectNulls={false}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
                <DataTable
                  headers={['Année académique', 'Champ', 'Valeurs renseignées', 'Valeurs manquantes', 'Couverture']}
                  rows={yearlyRows.map((row) => [
                    row.academic_year,
                    row.label,
                    `${formatCount(row.present_count)} / ${formatCount(row.denominator)}`,
                    formatCount(row.missing_count),
                    formatPercentage(row.completion_percentage),
                  ])}
                />
              </Panel>
            </section>
            <Panel title="Alertes de qualité">
              {data.alerts.length ? (
                <ul className="quality-alerts">
                  {data.alerts.map((alert) => <li key={alert.code}>{alert.message}</li>)}
                </ul>
              ) : (
                <div className="table-empty">Aucune alerte selon les contrôles définis.</div>
              )}
            </Panel>
          </div>
        )
      }}
    </PageStatus>
  )
}

export default function AnalyticsPage({
  page,
  query,
}: {
  page: Exclude<DashboardPage, 'overview'>
  query: string
}) {
  return (
    <>
      <section className="page-heading analysis-heading">
        <div>
          <p className="eyebrow">TABLEAU DE BORD · CONVENTIONS DE STAGE</p>
          <h1>{PAGE_TITLES[page]}</h1>
        </div>
      </section>
      {page === 'temporal' && <TemporalPage query={query} />}
      {page === 'stages' && <StagePage query={query} />}
      {page === 'companies-geography' && <CompaniesGeographyPage query={query} />}
      {page === 'quality' && <QualityPage query={query} />}
    </>
  )
}
