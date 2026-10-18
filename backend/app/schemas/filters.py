"""Schémas des options de filtres."""

from pydantic import BaseModel


class FilterOption(BaseModel):
    value: str | None
    label: str
    is_missing: bool


class FilterOptionsResponse(BaseModel):
    academic_years: list[FilterOption]
    stage_types: list[FilterOption]
    stage_natures: list[FilterOption]
