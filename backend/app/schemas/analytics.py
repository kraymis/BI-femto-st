"""Schémas des agrégats consommés par les pages BI migrées."""

from pydantic import BaseModel

from backend.app.schemas.overview import CategoryAggregate


class CategoryLabel(BaseModel):
    category: str
    category_is_missing: bool


class CrossTabCell(BaseModel):
    row_category: str
    row_is_missing: bool
    column_category: str
    column_is_missing: bool
    convention_count: int
    row_total: int
    percentage: float | None


class CrossTabTotal(BaseModel):
    category: str
    category_is_missing: bool
    convention_count: int


class CrossTabResponse(BaseModel):
    row_categories: list[CategoryLabel]
    column_categories: list[CategoryLabel]
    cells: list[CrossTabCell]
    row_totals: list[CrossTabTotal]
    column_totals: list[CrossTabTotal]
    grand_total: int
    unavailable: bool


class TemporalAnalysisResponse(BaseModel):
    yearly_conventions: list[CategoryAggregate]
    year_by_type: CrossTabResponse
    notices: list[str]


class StageAnalysisResponse(BaseModel):
    conventions_by_type: list[CategoryAggregate]
    conventions_by_nature: list[CategoryAggregate]
    type_by_nature: CrossTabResponse


class FieldCoverage(BaseModel):
    field: str
    label: str
    present_count: int
    missing_count: int
    denominator: int
    completion_percentage: float | None


class GeographySummary(BaseModel):
    total_conventions: int
    destination_available_conventions: int
    located_conventions: int
    not_located_conventions: int
    coverage_percentage: float | None
    localized_destinations: int
    ambiguous_conventions: int
    ambiguous_country_conventions: int
    missing_country_conventions: int
    country_denominator: int


class GeographyStatus(BaseModel):
    status: str
    label: str
    convention_count: int
    denominator: int
    percentage: float | None


class ConventionGeographyDetail(BaseModel):
    convention_id: str
    companies: list[str]


class GeographyDestination(BaseModel):
    city: str
    country: str | None
    convention_count: int
    latitude: float
    longitude: float
    distance_km: float
    distance_band: str
    companies: list[str]
    conventions: list[ConventionGeographyDetail]


class CompanyGeographyResponse(BaseModel):
    exploration_coverage: list[FieldCoverage]
    companies_available: bool
    companies: list[CategoryAggregate]
    country_available: bool
    country_present_count: int | None
    row_count: int
    geography_available: bool
    geography_message: str | None
    geography_threshold: int | None
    geography_summary: GeographySummary | None
    geography_status_counts: list[GeographyStatus]
    destinations: list[GeographyDestination]
    countries: list[CategoryAggregate]
    distance_bands: list[CategoryAggregate]


class MissingField(BaseModel):
    field: str
    label: str


class YearlyCoverage(BaseModel):
    academic_year: str
    field: str
    label: str
    present_count: int
    missing_count: int
    denominator: int
    completion_percentage: float | None


class QualityAlert(BaseModel):
    code: str
    message: str


class QualityResponse(BaseModel):
    full_row_count: int
    full_convention_count: int
    filtered_convention_count: int
    exact_duplicate_rows: int
    repeated_convention_rows: int | None
    missing_fields: list[MissingField]
    full_coverage: list[FieldCoverage]
    filtered_coverage: list[FieldCoverage]
    yearly_coverage: list[YearlyCoverage]
    yearly_fields: list[str]
    alerts: list[QualityAlert]
