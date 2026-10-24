import { useEffect, useMemo, useState } from 'react'
import type {
  ChangeEvent,
  FormEvent,
} from 'react'
import { DataTable } from './components/DataTable'
import { PaginationControls } from './components/PaginationControls'
import {
  getConventionSearchOptions,
  searchConventions,
} from './services/dashboardApi'
import type {
  ConventionSearchCriteria,
  ConventionSearchOptions,
  ConventionSearchResponse,
} from './types'

interface SearchFormValues {
  subject_id: string
  convention_id: string
  company_contains: string
  student_name_contains: string
  student_id_exact: string
  academic_year: string
  stage_type: string
  stage_nature: string
  city_contains: string
  country_contains: string
}

const EMPTY_FORM: SearchFormValues = {
  subject_id: '',
  convention_id: '',
  company_contains: '',
  student_name_contains: '',
  student_id_exact: '',
  academic_year: '',
  stage_type: '',
  stage_nature: '',
  city_contains: '',
  country_contains: '',
}

const MISSING_OPTION = '__missing__'
const VALUE_PREFIX = 'value:'

function toCriteria(form: SearchFormValues): ConventionSearchCriteria {
  const criteria: ConventionSearchCriteria = {}
  for (const field of [
    'subject_id',
    'convention_id',
    'company_contains',
    'student_name_contains',
    'student_id_exact',
    'city_contains',
    'country_contains',
  ] as const) {
    const value = form[field].trim()
    if (value) criteria[field] = value
  }
  for (const [formKey, requestKey, missingKey] of [
    ['academic_year', 'academic_year', 'academic_year_missing'],
    ['stage_type', 'stage_type', 'stage_type_missing'],
    ['stage_nature', 'stage_nature', 'stage_nature_missing'],
  ] as const) {
    const selected = form[formKey]
    if (selected === MISSING_OPTION) {
      criteria[missingKey] = true
    } else if (selected.startsWith(VALUE_PREFIX)) {
      criteria[requestKey] = selected.slice(VALUE_PREFIX.length)
    }
  }
  return criteria
}

function hasCriteria(criteria: ConventionSearchCriteria) {
  return Object.values(criteria).some((value) => value !== undefined && value !== false)
}

function criterionSelectOptions(
  options: ConventionSearchOptions['academic_years'],
  emptyLabel: string,
) {
  return (
    <>
      <option value="">{emptyLabel}</option>
      {options.map((option, index) => (
        <option
          key={`${option.is_missing ? 'missing' : option.value}-${index}`}
          value={option.is_missing ? MISSING_OPTION : `${VALUE_PREFIX}${option.value ?? ''}`}
        >
          {option.label}
        </option>
      ))}
    </>
  )
}

function SearchField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}) {
  return (
    <label className="convention-search-field">
      <span>{label}</span>
      <input
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}

export function ConventionSearch() {
  const [options, setOptions] = useState<ConventionSearchOptions | null>(null)
  const [optionsError, setOptionsError] = useState<string | null>(null)
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [form, setForm] = useState<SearchFormValues>(EMPTY_FORM)
  const [submittedCriteria, setSubmittedCriteria] =
    useState<ConventionSearchCriteria | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [response, setResponse] = useState<ConventionSearchResponse | null>(null)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getConventionSearchOptions(controller.signal)
      .then((result) => {
        setOptions(result)
        setOptionsError(null)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setOptionsError(
          error instanceof Error
            ? error.message
            : 'Impossible de charger les champs de recherche.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingOptions(false)
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!submittedCriteria) return
    const controller = new AbortController()
    searchConventions(submittedCriteria, page, pageSize, controller.signal)
      .then((result) => {
        setResponse(result)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setResponse(null)
        setSearchError(
          error instanceof Error ? error.message : 'La recherche a échoué.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsSearching(false)
      })
    return () => controller.abort()
  }, [submittedCriteria, page, pageSize])

  const available = useMemo(
    () => new Set(options?.available_fields ?? []),
    [options],
  )
  const visibleColumns = useMemo(
    () => {
      const columns: [keyof ConventionSearchResponse['results'][number], string][] = []
      if (available.has('convention_id')) {
        columns.push(['convention_id', 'Numéro de convention'])
      }
      if (available.has('subject_id')) columns.push(['subject_id', 'Sujet PFE'])
      if (available.has('first_name') && available.has('last_name')) {
        columns.push(['student_name', 'Étudiant'])
      }
      if (available.has('student_id')) {
        columns.push(['student_id', 'Identifiant étudiant'])
      }
      if (available.has('company')) columns.push(['company', 'Entreprise d’accueil'])
      if (available.has('academic_year')) {
        columns.push(['academic_year', 'Année académique'])
      }
      if (available.has('stage_type')) columns.push(['stage_type', 'Type de stage'])
      if (available.has('stage_nature')) {
        columns.push(['stage_nature', 'Nature du stage'])
      }
      if (available.has('city')) columns.push(['city', 'Ville'])
      if (available.has('country')) columns.push(['country', 'Pays'])
      return columns
    },
    [available],
  )

  function updateField(
    field: keyof SearchFormValues,
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setFormError(null)
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const criteria = toCriteria(form)
    if (!hasCriteria(criteria)) {
      setFormError('Renseignez au moins un critère avant de lancer la recherche.')
      return
    }
    setPage(1)
    setResponse(null)
    setSearchError(null)
    setFormError(null)
    setIsSearching(true)
    setSubmittedCriteria(criteria)
  }

  function resetSearch() {
    setForm(EMPTY_FORM)
    setSubmittedCriteria(null)
    setPage(1)
    setPageSize(10)
    setResponse(null)
    setSearchError(null)
    setFormError(null)
    setIsSearching(false)
  }

  function changePage(nextPage: number) {
    setIsSearching(true)
    setSearchError(null)
    setPage(nextPage)
  }

  function changePageSize(size: number) {
    setIsSearching(true)
    setSearchError(null)
    setPageSize(size)
    setPage(1)
  }

  return (
    <section className="convention-search-panel" aria-labelledby="convention-search-title">
      <div className="convention-search-heading">
        <div>
          <p className="eyebrow">RECHERCHE STRUCTURÉE</p>
          <h2 id="convention-search-title">Recherche de conventions</h2>
          <p>Combinez des critères ; les filtres globaux des graphiques ne s’appliquent pas ici.</p>
        </div>
      </div>
      {optionsError ? (
        <div className="inline-error" role="alert">{optionsError}</div>
      ) : isLoadingOptions || !options ? (
        <div className="filters-loading" aria-live="polite">Chargement des champs disponibles…</div>
      ) : (
        <>
          <form onSubmit={submitSearch}>
            <div className="convention-search-grid">
              {available.has('subject_id') && (
                <SearchField
                  label="Identifiant du sujet PFE"
                  value={form.subject_id}
                  onChange={(value) => setForm((current) => ({ ...current, subject_id: value }))}
                />
              )}
              {available.has('convention_id') && (
                <SearchField
                  label="Numéro de convention"
                  value={form.convention_id}
                  onChange={(value) => setForm((current) => ({ ...current, convention_id: value }))}
                />
              )}
              {available.has('company') && (
                <SearchField
                  label="Entreprise d’accueil"
                  value={form.company_contains}
                  placeholder="Nom ou partie du nom"
                  onChange={(value) => setForm((current) => ({ ...current, company_contains: value }))}
                />
              )}
            </div>
            {(
              (available.has('first_name') && available.has('last_name')) ||
              available.has('student_id') ||
              options.academic_years.length > 0 ||
              options.stage_types.length > 0 ||
              options.stage_natures.length > 0 ||
              available.has('city') ||
              available.has('country')
            ) && (
              <details className="search-advanced">
                <summary>Critères avancés</summary>
                <div className="convention-search-grid advanced-search-grid">
                  {available.has('first_name') && available.has('last_name') && (
                    <SearchField
                      label="Nom ou prénom de l’étudiant"
                      value={form.student_name_contains}
                      onChange={(value) => setForm((current) => ({ ...current, student_name_contains: value }))}
                    />
                  )}
                  {available.has('student_id') && (
                    <SearchField
                      label="Identifiant étudiant (exact)"
                      value={form.student_id_exact}
                      onChange={(value) => setForm((current) => ({ ...current, student_id_exact: value }))}
                    />
                  )}
                  {options.academic_years.length > 0 && (
                    <label className="convention-search-field">
                      <span>Année académique</span>
                      <select value={form.academic_year} onChange={(event) => updateField('academic_year', event)}>
                        {criterionSelectOptions(options.academic_years, 'Toutes les années')}
                      </select>
                    </label>
                  )}
                  {options.stage_types.length > 0 && (
                    <label className="convention-search-field">
                      <span>Type de stage</span>
                      <select value={form.stage_type} onChange={(event) => updateField('stage_type', event)}>
                        {criterionSelectOptions(options.stage_types, 'Tous les types')}
                      </select>
                    </label>
                  )}
                  {options.stage_natures.length > 0 && (
                    <label className="convention-search-field">
                      <span>Nature du stage</span>
                      <select value={form.stage_nature} onChange={(event) => updateField('stage_nature', event)}>
                        {criterionSelectOptions(options.stage_natures, 'Toutes les natures')}
                      </select>
                    </label>
                  )}
                  {available.has('city') && (
                    <SearchField
                      label="Ville du lieu de stage"
                      value={form.city_contains}
                      onChange={(value) => setForm((current) => ({ ...current, city_contains: value }))}
                    />
                  )}
                  {available.has('country') && (
                    <SearchField
                      label="Pays du lieu de stage"
                      value={form.country_contains}
                      onChange={(value) => setForm((current) => ({ ...current, country_contains: value }))}
                    />
                  )}
                </div>
              </details>
            )}
            {formError && <div className="inline-warning" role="alert">{formError}</div>}
            <div className="convention-search-actions">
              <button className="primary-button" type="submit" disabled={isSearching}>
                Rechercher
              </button>
              <button className="secondary-button" type="button" onClick={resetSearch}>
                Réinitialiser
              </button>
              <span className="search-independence-note">
                La recherche est indépendante des filtres globaux.
              </span>
            </div>
          </form>
          {searchError && <div className="error-banner" role="alert">{searchError}</div>}
          {isSearching ? (
            <div className="search-loading" aria-live="polite">
              <span className="spinner" /> Recherche des conventions…
            </div>
          ) : response ? (
            <div className="convention-search-results">
              <div className="section-heading search-results-heading">
                <div>
                  <h3>Résultats de recherche</h3>
                  <p>{response.total_count} convention(s) correspondante(s)</p>
                </div>
              </div>
              {response.total_count === 0 ? (
                <div className="table-empty" role="status">
                  Aucune convention ne correspond aux critères renseignés.
                </div>
              ) : (
                <>
                  <DataTable
                    headers={visibleColumns.map(([, label]) => label)}
                    rows={response.results.map((result) =>
                      visibleColumns.map(([key]) => {
                        const value = result[key as keyof typeof result]
                        return typeof value === 'string' && value.trim()
                          ? value
                          : 'Non renseigné'
                      }),
                    )}
                  />
                  <PaginationControls
                    page={response.page}
                    pageSize={response.page_size}
                    totalCount={response.total_count}
                    totalPages={response.total_pages}
                    itemLabel="conventions"
                    onPageChange={changePage}
                    onPageSizeChange={changePageSize}
                  />
                </>
              )}
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}
