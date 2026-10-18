"""Calculs analytiques indépendants de l’interface."""

from bi.analytics.filters import filter_stages
from bi.analytics.geography import (
    GeographyResult,
    GeographicReferenceError,
    aggregate_geography,
    destination_id,
    haversine_km,
    load_geographic_reference,
    validate_geographic_reference,
)
from bi.analytics.aggregations import (
    convention_crosstab,
    crosstab_row_percentages,
    crosstab_with_totals,
    filter_aggregated_categories,
    yearly_field_coverage,
)
from bi.analytics.kpis import (
    CountRate,
    count_conventions,
    count_conventions_by_category,
    count_students,
    count_rate,
)
from bi.analytics.quality import field_coverage, quality_summary

__all__ = [
    "CountRate",
    "GeographyResult",
    "GeographicReferenceError",
    "aggregate_geography",
    "convention_crosstab",
    "count_conventions",
    "count_conventions_by_category",
    "count_rate",
    "count_students",
    "destination_id",
    "field_coverage",
    "filter_aggregated_categories",
    "filter_stages",
    "haversine_km",
    "load_geographic_reference",
    "crosstab_row_percentages",
    "crosstab_with_totals",
    "quality_summary",
    "yearly_field_coverage",
    "validate_geographic_reference",
]
