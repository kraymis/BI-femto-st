import type {
  CompanyGeographyResponse,
  ConventionSearchCriteria,
  ConventionSearchOptions,
  ConventionSearchResponse,
  FilterOptions,
  OverviewResponse,
  QualityResponse,
  SelectedFilters,
  StageAnalysisResponse,
  TemporalAnalysisResponse,
} from '../types'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? '' : 'http://localhost:8000')
).replace(/\/$/, '')

export interface ApiError {
  code?: string
  message?: string
}

export async function fetchJson<T>(
  url: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(url, { signal })
  if (!response.ok) {
    let message = `Le service a répondu avec le code ${response.status}.`
    try {
      const error = (await response.json()) as ApiError
      if (error.message) message = error.message
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new Error(message)
  }
  return (await response.json()) as T
}

export async function getFilterOptions(signal?: AbortSignal) {
  return fetchJson<FilterOptions>(
    `${API_BASE_URL}/api/v1/filters/options`,
    signal,
  )
}

export function createFilterQuery(
  options: FilterOptions,
  selected: SelectedFilters,
): string {
  const params = new URLSearchParams()
  const filters = [
    {
      key: 'academic_years',
      missingKey: 'include_missing_year',
      options: options.academic_years,
    },
    {
      key: 'stage_types',
      missingKey: 'include_missing_type',
      options: options.stage_types,
    },
    {
      key: 'stage_natures',
      missingKey: 'include_missing_nature',
      options: options.stage_natures,
    },
  ] as const

  for (const filter of filters) {
    for (const option of filter.options) {
      const optionKey = option.is_missing ? 'missing:' : `value:${option.value ?? ''}`
      if (
        selected[filter.key].includes(optionKey) &&
        option.value !== null
      ) {
        params.append(filter.key, option.value)
      }
    }
    params.set(
      filter.missingKey,
      String(
        filter.options.some((option) => {
          const optionKey = option.is_missing
            ? 'missing:'
            : `value:${option.value ?? ''}`
          return option.is_missing && selected[filter.key].includes(optionKey)
        }),
      ),
    )
  }
  return params.toString()
}

export function getOverview(query: string, signal?: AbortSignal) {
  return fetchJson<OverviewResponse>(
    `${API_BASE_URL}/api/v1/overview?${query}`,
    signal,
  )
}

export function getTemporal(query: string, signal?: AbortSignal) {
  return fetchJson<TemporalAnalysisResponse>(
    `${API_BASE_URL}/api/v1/temporal?${query}`,
    signal,
  )
}

export function getStages(query: string, signal?: AbortSignal) {
  return fetchJson<StageAnalysisResponse>(
    `${API_BASE_URL}/api/v1/stages?${query}`,
    signal,
  )
}

export function getCompaniesGeography(query: string, signal?: AbortSignal) {
  return fetchJson<CompanyGeographyResponse>(
    `${API_BASE_URL}/api/v1/companies-geography?${query}`,
    signal,
  )
}

export function getConventionSearchOptions(signal?: AbortSignal) {
  return fetchJson<ConventionSearchOptions>(
    `${API_BASE_URL}/api/v1/conventions/search/options`,
    signal,
  )
}

export function searchConventions(
  criteria: ConventionSearchCriteria,
  page: number,
  pageSize: number,
  signal?: AbortSignal,
) {
  return fetch(`${API_BASE_URL}/api/v1/conventions/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...criteria, page, page_size: pageSize }),
    signal,
  }).then(async (response) => {
    if (!response.ok) {
      let message = `Le service a répondu avec le code ${response.status}.`
      try {
        const error = (await response.json()) as ApiError & { detail?: string }
        if (error.message) message = error.message
        else if (error.detail) message = error.detail
      } catch {
        // Keep the status-based message when the response is not JSON.
      }
      throw new Error(message)
    }
    return (await response.json()) as ConventionSearchResponse
  }).catch((error: unknown) => {
    if (error instanceof TypeError) {
      throw new Error(
        'Impossible de joindre l’API de recherche. Vérifiez que le backend est démarré et que son URL/CORS autorise le frontend.',
      )
    }
    throw error
  })
}

export function getQuality(query: string, signal?: AbortSignal) {
  return fetchJson<QualityResponse>(
    `${API_BASE_URL}/api/v1/quality?${query}`,
    signal,
  )
}
