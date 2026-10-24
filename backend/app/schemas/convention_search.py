"""Contrats de recherche structurée des conventions."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.filters import FilterOption


class ConventionSearchOptions(BaseModel):
    available_fields: list[str]
    academic_years: list[FilterOption]
    stage_types: list[FilterOption]
    stage_natures: list[FilterOption]


class ConventionSearchRequest(BaseModel):
    subject_id: str | None = None
    convention_id: str | None = None
    company_contains: str | None = None
    student_name_contains: str | None = None
    student_id_exact: str | None = None
    academic_year: str | None = None
    academic_year_missing: bool = False
    stage_type: str | None = None
    stage_type_missing: bool = False
    stage_nature: str | None = None
    stage_nature_missing: bool = False
    city_contains: str | None = None
    country_contains: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: Literal[10, 20, 50, 100] = 10

    @model_validator(mode="after")
    def require_at_least_one_criterion(self) -> "ConventionSearchRequest":
        criteria = (
            self.subject_id,
            self.convention_id,
            self.company_contains,
            self.student_name_contains,
            self.student_id_exact,
            self.academic_year,
            self.stage_type,
            self.stage_nature,
            self.city_contains,
            self.country_contains,
        )
        if not any(value and value.strip() for value in criteria) and not any(
            (
                self.academic_year_missing,
                self.stage_type_missing,
                self.stage_nature_missing,
            )
        ):
            raise ValueError("Renseignez au moins un critère de recherche.")
        if any(
            value is not None and missing
            for value, missing in (
                (self.academic_year, self.academic_year_missing),
                (self.stage_type, self.stage_type_missing),
                (self.stage_nature, self.stage_nature_missing),
            )
        ):
            raise ValueError(
                "Choisissez une modalité ou les valeurs non renseignées, pas les deux."
            )
        return self


class ConventionSearchResult(BaseModel):
    convention_id: str | None
    subject_id: str | None
    student_id: str | None
    student_name: str | None
    company: str | None
    academic_year: str | None
    stage_type: str | None
    stage_nature: str | None
    city: str | None
    country: str | None


class ConventionSearchResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    total_pages: int
    results: list[ConventionSearchResult]
