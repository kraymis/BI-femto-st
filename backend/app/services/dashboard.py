"""Chargement des données et orchestration des fonctions analytiques BI."""

import re
from typing import Iterable

import pandas as pd

from bi.analytics.aggregations import MISSING_LABEL as AGGREGATION_MISSING_LABEL
from bi.analytics.filters import filter_stages
from bi.analytics.kpis import (
    count_conventions,
    count_conventions_by_category,
    count_students,
)
from bi.config import STAGES_SOURCE_FILE
from bi.ingestion import load_stages

from backend.app.schemas.filters import FilterOption, FilterOptionsResponse
from backend.app.schemas.overview import (
    CategoryAggregate,
    OverviewFilters,
    OverviewKpis,
    OverviewResponse,
)

OVERVIEW_REQUIRED_COLUMNS = (
    "n_convention_de_stage",
    "n_etudiant",
    "annee_academique",
    "type_de_stage",
    "nature_du_stage",
)
CATEGORY_COLUMNS = {
    "academic_years": "annee_academique",
    "stage_types": "type_de_stage",
    "stage_natures": "nature_du_stage",
}
LATEST_YEAR_NOTICE = (
    "La dernière année académique observée peut être incomplète. "
    "Aucune comparaison de périodes ni mesure de durée n’est publiée."
)


def get_dashboard_data() -> pd.DataFrame:
    """Charge le classeur approuvé avec les colonnes nécessaires aux pages V1."""
    return load_stages(
        STAGES_SOURCE_FILE,
        required_columns=OVERVIEW_REQUIRED_COLUMNS,
    )


def _missing_label(values: Iterable[object]) -> str:
    labels = set(values)
    label = AGGREGATION_MISSING_LABEL
    while label in labels:
        label = f"{label} (valeur absente)"
    return label


def _filter_options(data: pd.DataFrame, column: str) -> list[FilterOption]:
    values = data[column].dropna().drop_duplicates().tolist()
    options = [
        FilterOption(value=str(value), label=str(value), is_missing=False)
        for value in values
    ]
    if data[column].isna().any():
        options.append(
            FilterOption(
                value=None,
                label=_missing_label(str(value) for value in values),
                is_missing=True,
            )
        )
    return options


def get_filter_options(data: pd.DataFrame) -> FilterOptionsResponse:
    """Construit les options en conservant l'ordre des valeurs du classeur."""
    return FilterOptionsResponse(
        academic_years=_filter_options(data, "annee_academique"),
        stage_types=_filter_options(data, "type_de_stage"),
        stage_natures=_filter_options(data, "nature_du_stage"),
    )


def _selected_values(
    values: list[str] | None,
    include_missing: bool | None,
) -> list[str | None] | None:
    if values is None and include_missing is None:
        return None
    selected: list[str | None] = list(values or [])
    if include_missing:
        selected.append(None)
    return selected


def _filter_data(
    data: pd.DataFrame,
    selected: dict[str, list[str] | None],
    include_missing: dict[str, bool | None],
) -> pd.DataFrame:
    filters = {
        key: _selected_values(selected[key], include_missing[key])
        for key in CATEGORY_COLUMNS
    }
    return filter_stages(
        data,
        academic_years=filters["academic_years"],
        stage_types=filters["stage_types"],
        stage_natures=filters["stage_natures"],
        include_missing_year=False,
        include_missing_type=False,
        include_missing_nature=False,
    )


def _academic_sort_key(label: str) -> tuple[int, int, str]:
    match = re.fullmatch(r"(\d{4})/(\d{4})", label)
    if match:
        return int(match.group(1)), int(match.group(2)), label
    return (10**9, 10**9, label)


def _category_aggregates(
    data: pd.DataFrame,
    column: str,
    *,
    sort_by_year: bool = False,
) -> list[CategoryAggregate]:
    counts = count_conventions_by_category(data, column)
    source_values = data[column].dropna().drop_duplicates().tolist()
    missing_label = _missing_label(str(value) for value in source_values)
    rows = [
        CategoryAggregate(
            category=(
                missing_label
                if bool(row.category_is_missing)
                else str(row.category)
            ),
            category_is_missing=bool(row.category_is_missing),
            convention_count=int(row.convention_count),
            denominator=int(row.denominator),
            percentage=(
                float(row.percentage)
                if not pd.isna(row.percentage)
                else None
            ),
        )
        for row in counts.itertuples(index=False)
    ]
    if sort_by_year:
        rows.sort(key=lambda row: _academic_sort_key(row.category))
    else:
        rows.sort(key=lambda row: -row.convention_count)
    return rows


def get_overview(
    data: pd.DataFrame,
    *,
    academic_years: list[str] | None = None,
    stage_types: list[str] | None = None,
    stage_natures: list[str] | None = None,
    include_missing_year: bool | None = None,
    include_missing_type: bool | None = None,
    include_missing_nature: bool | None = None,
) -> OverviewResponse:
    """Calcule la Vue d'ensemble après filtres partagés, sans données brutes."""
    selected = {
        "academic_years": academic_years,
        "stage_types": stage_types,
        "stage_natures": stage_natures,
    }
    include_missing = {
        "academic_years": include_missing_year,
        "stage_types": include_missing_type,
        "stage_natures": include_missing_nature,
    }
    filtered = _filter_data(data, selected, include_missing)

    return OverviewResponse(
        kpis=OverviewKpis(
            row_count=len(filtered),
            convention_count=count_conventions(filtered),
            student_count=count_students(filtered),
            academic_year_count=int(
                filtered["annee_academique"].nunique(dropna=True)
            ),
            stage_type_count=int(
                filtered["type_de_stage"].nunique(dropna=True)
            ),
        ),
        filters=OverviewFilters(
            academic_years=_selected_values(academic_years, include_missing_year),
            stage_types=_selected_values(stage_types, include_missing_type),
            stage_natures=_selected_values(
                stage_natures, include_missing_nature
            ),
        ),
        yearly_conventions=_category_aggregates(
            filtered, "annee_academique", sort_by_year=True
        ),
        conventions_by_type=_category_aggregates(filtered, "type_de_stage"),
        conventions_by_nature=_category_aggregates(
            filtered, "nature_du_stage"
        ),
        notices=[LATEST_YEAR_NOTICE],
    )
