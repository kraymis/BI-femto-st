"""Schémas Pydantic de la Vue d'ensemble."""

from pydantic import BaseModel


class OverviewKpis(BaseModel):
    row_count: int
    convention_count: int
    student_count: int
    academic_year_count: int
    stage_type_count: int


class CategoryAggregate(BaseModel):
    category: str
    category_is_missing: bool
    convention_count: int
    denominator: int
    percentage: float | None


class OverviewFilters(BaseModel):
    academic_years: list[str | None] | None
    stage_types: list[str | None] | None
    stage_natures: list[str | None] | None


class OverviewResponse(BaseModel):
    kpis: OverviewKpis
    filters: OverviewFilters
    yearly_conventions: list[CategoryAggregate]
    conventions_by_type: list[CategoryAggregate]
    conventions_by_nature: list[CategoryAggregate]
    notices: list[str]
