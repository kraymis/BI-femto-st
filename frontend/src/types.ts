export type FilterKey = 'academic_years' | 'stage_types' | 'stage_natures'

export type MissingFilterKey =
  | 'include_missing_year'
  | 'include_missing_type'
  | 'include_missing_nature'

export interface FilterOption {
  value: string | null
  label: string
  is_missing: boolean
}

export interface FilterOptions {
  academic_years: FilterOption[]
  stage_types: FilterOption[]
  stage_natures: FilterOption[]
}

export interface OverviewKpis {
  row_count: number
  convention_count: number
  student_count: number
  academic_year_count: number
  stage_type_count: number
}

export interface CategoryAggregate {
  category: string
  category_is_missing: boolean
  convention_count: number
  denominator: number
  percentage: number | null
}

export interface OverviewResponse {
  kpis: OverviewKpis
  filters: {
    academic_years: (string | null)[] | null
    stage_types: (string | null)[] | null
    stage_natures: (string | null)[] | null
  }
  yearly_conventions: CategoryAggregate[]
  conventions_by_type: CategoryAggregate[]
  conventions_by_nature: CategoryAggregate[]
  notices: string[]
}

export interface CategoryLabel {
  category: string
  category_is_missing: boolean
}

export interface CrossTabCell {
  row_category: string
  row_is_missing: boolean
  column_category: string
  column_is_missing: boolean
  convention_count: number
  row_total: number
  percentage: number | null
}

export interface CrossTabTotal {
  category: string
  category_is_missing: boolean
  convention_count: number
}

export interface CrossTabResponse {
  row_categories: CategoryLabel[]
  column_categories: CategoryLabel[]
  cells: CrossTabCell[]
  row_totals: CrossTabTotal[]
  column_totals: CrossTabTotal[]
  grand_total: number
  unavailable: boolean
}

export interface TemporalAnalysisResponse {
  yearly_conventions: CategoryAggregate[]
  year_by_type: CrossTabResponse
  notices: string[]
}

export interface StageAnalysisResponse {
  conventions_by_type: CategoryAggregate[]
  conventions_by_nature: CategoryAggregate[]
  type_by_nature: CrossTabResponse
}

export interface FieldCoverage {
  field: string
  label: string
  present_count: number
  missing_count: number
  denominator: number
  completion_percentage: number | null
}

export interface GeographySummary {
  total_conventions: number
  destination_available_conventions: number
  located_conventions: number
  not_located_conventions: number
  coverage_percentage: number | null
  localized_destinations: number
  ambiguous_conventions: number
  ambiguous_country_conventions: number
  missing_country_conventions: number
  country_denominator: number
}

export interface GeographyStatus {
  status: string
  label: string
  convention_count: number
  denominator: number
  percentage: number | null
}

export interface GeographyDestination {
  city: string
  country: string | null
  convention_count: number
  latitude: number
  longitude: number
  distance_km: number
  distance_band: string
  companies: string[]
  conventions: {
    convention_id: string
    companies: string[]
  }[]
}

export interface CompanyGeographyResponse {
  exploration_coverage: FieldCoverage[]
  companies_available: boolean
  companies: CategoryAggregate[]
  country_available: boolean
  country_present_count: number | null
  row_count: number
  geography_available: boolean
  geography_message: string | null
  geography_threshold: number | null
  geography_summary: GeographySummary | null
  geography_status_counts: GeographyStatus[]
  destinations: GeographyDestination[]
  countries: CategoryAggregate[]
  distance_bands: CategoryAggregate[]
}

export interface MissingField {
  field: string
  label: string
}

export interface YearlyCoverage extends FieldCoverage {
  academic_year: string
}

export interface QualityAlert {
  code: string
  message: string
}

export interface QualityResponse {
  full_row_count: number
  full_convention_count: number
  filtered_convention_count: number
  exact_duplicate_rows: number
  repeated_convention_rows: number | null
  missing_fields: MissingField[]
  full_coverage: FieldCoverage[]
  filtered_coverage: FieldCoverage[]
  yearly_coverage: YearlyCoverage[]
  yearly_fields: string[]
  alerts: QualityAlert[]
}

export type DashboardPage =
  | 'overview'
  | 'temporal'
  | 'stages'
  | 'companies-geography'
  | 'quality'

export type SelectedFilters = Record<FilterKey, string[]>
