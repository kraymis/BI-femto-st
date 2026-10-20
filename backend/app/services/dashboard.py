"""Chargement des données et orchestration des fonctions analytiques BI."""

import re
import os
from typing import Iterable

import pandas as pd

from bi.analytics.aggregations import (
    convention_crosstab,
    crosstab_row_percentages,
    yearly_field_coverage,
)
from bi.analytics.geography import (
    GeographicReferenceError,
    aggregate_geography,
    load_geographic_reference,
)
from bi.analytics.kpis import (
    count_conventions_by_category,
)
from bi.analytics.quality import field_coverage, quality_summary
from bi.analytics.aggregations import MISSING_LABEL as AGGREGATION_MISSING_LABEL
from bi.analytics.filters import filter_stages
from bi.analytics.kpis import count_conventions, count_students
from bi.config import (
    GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION,
    GEOGRAPHIC_REFERENCE_FILE,
    STAGES_SOURCE_FILE,
)
from bi.ingestion import load_stages

from backend.app.schemas.filters import FilterOption, FilterOptionsResponse
from backend.app.schemas.analytics import (
    CategoryAggregate,
    CategoryLabel,
    CompanyGeographyResponse,
    ConventionGeographyDetail,
    CrossTabCell,
    CrossTabResponse,
    CrossTabTotal,
    FieldCoverage,
    GeographyDestination,
    GeographySummary,
    GeographyStatus,
    QualityAlert,
    QualityResponse,
    StageAnalysisResponse,
    TemporalAnalysisResponse,
)
from backend.app.schemas.overview import (
    CategoryAggregate as OverviewCategoryAggregate,
    OverviewFilters,
    OverviewKpis,
    OverviewResponse,
)
from backend.app.services.demo_data import (
    get_demo_dashboard_data,
    get_demo_geographic_reference,
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
OPTIONAL_DASHBOARD_COLUMNS = (
    "entreprise",
    "entreprise_lieu_stage",
    "date_debut",
    "date_fin",
    "pays_lieu_stage",
    "ville_lieu_stage",
    "cp_lieu_stage",
    "ville",
    "code_postal",
    "date_soutenance",
)
QUALITY_FIELDS = (
    "annee_academique",
    "type_de_stage",
    "nature_du_stage",
    "entreprise",
    "entreprise_lieu_stage",
    "date_debut",
    "date_fin",
    "pays_lieu_stage",
    "ville_lieu_stage",
    "cp_lieu_stage",
    "ville",
    "code_postal",
    "date_soutenance",
)
QUALITY_DEFAULT_YEARLY_FIELDS = (
    "nature_du_stage",
    "entreprise",
    "pays_lieu_stage",
    "date_debut",
)
EXPLORATION_FIELDS = (
    "entreprise",
    "entreprise_lieu_stage",
    "pays_lieu_stage",
    "ville_lieu_stage",
    "cp_lieu_stage",
    "ville",
    "code_postal",
)
FIELD_LABELS = {
    "annee_academique": "Année académique",
    "n_convention_de_stage": "Numéro de convention",
    "n_etudiant": "Identifiant étudiant",
    "type_de_stage": "Type de stage",
    "nature_du_stage": "Nature du stage",
    "entreprise": "Organisme — entreprise",
    "entreprise_lieu_stage": "Entreprise du lieu de stage",
    "date_debut": "Date de début",
    "date_fin": "Date de fin",
    "pays_lieu_stage": "Pays du lieu de stage",
    "ville_lieu_stage": "Ville du lieu de stage",
    "cp_lieu_stage": "Code postal du lieu de stage",
    "ville": "Ville — champ général",
    "code_postal": "Code postal — champ général",
    "date_soutenance": "Date de soutenance",
}


def get_dashboard_data() -> pd.DataFrame:
    """Charge les colonnes nécessaires au dashboard sans supposer les facultatives."""
    data_mode = os.getenv("BI_DATA_MODE", "real").strip().lower()
    if data_mode == "demo":
        return get_demo_dashboard_data()
    if data_mode != "real":
        raise RuntimeError("BI_DATA_MODE doit valoir « real » ou « demo ».")
    return load_stages(
        STAGES_SOURCE_FILE,
        required_columns=OVERVIEW_REQUIRED_COLUMNS,
        optional_columns=OPTIONAL_DASHBOARD_COLUMNS,
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
) -> list[OverviewCategoryAggregate]:
    counts = count_conventions_by_category(data, column)
    source_values = data[column].dropna().drop_duplicates().tolist()
    missing_label = _missing_label(str(value) for value in source_values)
    rows = [
        OverviewCategoryAggregate(
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


def get_filtered_dashboard_data(
    *,
    academic_years: list[str] | None = None,
    stage_types: list[str] | None = None,
    stage_natures: list[str] | None = None,
    include_missing_year: bool | None = None,
    include_missing_type: bool | None = None,
    include_missing_nature: bool | None = None,
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Applique le même contrat de filtres à toutes les pages du dashboard."""
    return _filter_data(
        data,
        {
            "academic_years": academic_years,
            "stage_types": stage_types,
            "stage_natures": stage_natures,
        },
        {
            "academic_years": include_missing_year,
            "stage_types": include_missing_type,
            "stage_natures": include_missing_nature,
        },
    )


def _category_label(value: object, is_missing: bool) -> CategoryLabel:
    return CategoryLabel(category=str(value), category_is_missing=is_missing)


def _cross_tab(data: pd.DataFrame, row_column: str, column_column: str) -> CrossTabResponse:
    try:
        counts = convention_crosstab(data, row_column, column_column)
    except ValueError as exc:
        if "plusieurs modalités" not in str(exc):
            raise
        return CrossTabResponse(
            row_categories=[],
            column_categories=[],
            cells=[],
            row_totals=[],
            column_totals=[],
            grand_total=0,
            unavailable=True,
        )

    percentages = crosstab_row_percentages(counts)
    row_missing_label = _missing_label(
        str(value) for value in data[row_column].dropna().drop_duplicates()
    )
    column_missing_label = _missing_label(
        str(value) for value in data[column_column].dropna().drop_duplicates()
    )
    row_categories = [
        _category_label(label, str(label) == row_missing_label)
        for label in counts.index.tolist()
    ]
    column_categories = [
        _category_label(label, str(label) == column_missing_label)
        for label in counts.columns.tolist()
    ]
    cells: list[CrossTabCell] = []
    row_totals: list[CrossTabTotal] = []
    column_totals: list[CrossTabTotal] = []
    for row_position, row_label in enumerate(counts.index):
        row_total = int(counts.loc[row_label].sum())
        row_totals.append(
            CrossTabTotal(
                category=str(row_label),
                category_is_missing=row_categories[row_position].category_is_missing,
                convention_count=row_total,
            )
        )
        for column_position, column_label in enumerate(counts.columns):
            percentage = percentages.loc[row_label, column_label]
            cells.append(
                CrossTabCell(
                    row_category=str(row_label),
                    row_is_missing=row_categories[row_position].category_is_missing,
                    column_category=str(column_label),
                    column_is_missing=column_categories[
                        column_position
                    ].category_is_missing,
                    convention_count=int(counts.loc[row_label, column_label]),
                    row_total=row_total,
                    percentage=(
                        float(percentage) if not pd.isna(percentage) else None
                    ),
                )
            )
    for column_position, column_label in enumerate(counts.columns):
        column_totals.append(
            CrossTabTotal(
                category=str(column_label),
                category_is_missing=column_categories[
                    column_position
                ].category_is_missing,
                convention_count=int(counts[column_label].sum()),
            )
        )
    return CrossTabResponse(
        row_categories=row_categories,
        column_categories=column_categories,
        cells=cells,
        row_totals=row_totals,
        column_totals=column_totals,
        grand_total=int(counts.to_numpy().sum()),
        unavailable=False,
    )


def get_temporal_analysis(data: pd.DataFrame) -> TemporalAnalysisResponse:
    """Retourne les agrégats temporels existants et le croisement année × type."""
    year_by_type = _cross_tab(data, "annee_academique", "type_de_stage")
    if not year_by_type.unavailable:
        year_by_type.row_categories.sort(
            key=lambda row: _academic_sort_key(row.category)
        )
        year_by_type.row_totals.sort(
            key=lambda row: _academic_sort_key(row.category)
        )
        year_by_type.cells.sort(
            key=lambda cell: _academic_sort_key(cell.row_category)
        )
    return TemporalAnalysisResponse(
        yearly_conventions=_category_aggregates(
            data, "annee_academique", sort_by_year=True
        ),
        year_by_type=year_by_type,
        notices=[LATEST_YEAR_NOTICE],
    )


def get_stage_analysis(data: pd.DataFrame) -> StageAnalysisResponse:
    """Retourne répartitions type/nature et le croisement métier."""
    return StageAnalysisResponse(
        conventions_by_type=_category_aggregates(data, "type_de_stage"),
        conventions_by_nature=_category_aggregates(data, "nature_du_stage"),
        type_by_nature=_cross_tab(data, "type_de_stage", "nature_du_stage"),
    )


def _field_coverages(data: pd.DataFrame, columns: list[str]) -> list[FieldCoverage]:
    if not columns:
        return []
    rows = field_coverage(data, columns)
    return [
        FieldCoverage(
            field=str(row.field),
            label=FIELD_LABELS.get(str(row.field), str(row.field)),
            present_count=int(row.present_count),
            missing_count=int(row.missing_count),
            denominator=int(row.denominator),
            completion_percentage=(
                float(row.completion_percentage)
                if not pd.isna(row.completion_percentage)
                else None
            ),
        )
        for row in rows.itertuples(index=False)
    ]


def get_company_geography(data: pd.DataFrame) -> CompanyGeographyResponse:
    """Retourne l’exploration entreprise et les agrégats géographiques publiables."""
    available_exploration_fields = [
        field for field in EXPLORATION_FIELDS if field in data.columns
    ]
    company_available = "entreprise" in data.columns
    companies: list[OverviewCategoryAggregate] = []
    if company_available:
        companies = [
            row
            for row in _category_aggregates(data, "entreprise")
            if not row.category_is_missing
        ]
    country_available = "pays_lieu_stage" in data.columns
    country_present_count = (
        int(data["pays_lieu_stage"].notna().sum()) if country_available else None
    )
    summary = None
    status_counts: list[GeographyStatus] = []
    destinations: list[GeographyDestination] = []
    countries: list[OverviewCategoryAggregate] = []
    distance_bands: list[CategoryAggregate] = []
    geography_message = None
    required_geo = {
        "n_convention_de_stage",
        "ville_lieu_stage",
        "pays_lieu_stage",
    }
    if not required_geo.issubset(data.columns):
        geography_message = (
            "Les champs requis pour l’analyse géographique ne sont pas disponibles."
        )
    else:
        try:
            data_mode = os.getenv("BI_DATA_MODE", "real").strip().lower()
            if data_mode == "demo":
                reference = get_demo_geographic_reference()
            elif data_mode == "real":
                reference = load_geographic_reference(GEOGRAPHIC_REFERENCE_FILE)
            else:
                raise RuntimeError(
                    "BI_DATA_MODE doit valoir « real » ou « demo »."
                )
            result = aggregate_geography(data, reference)
            summary = GeographySummary(**result.summary)
            status_counts = [
                GeographyStatus(
                    status=str(row.status),
                    label=str(row.label),
                    convention_count=int(row.convention_count),
                    denominator=int(row.denominator),
                    percentage=(
                        float(row.percentage) if not pd.isna(row.percentage) else None
                    ),
                )
                for row in result.status_counts.itertuples(index=False)
            ]
            threshold = GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION
            if threshold is None:
                geography_message = (
                    "Les détails géographiques sont masqués : aucun seuil de "
                    "confidentialité n’est configuré."
                )
            elif threshold < 1:
                geography_message = (
                    "Le seuil de confidentialité doit être supérieur ou égal à 1."
                )
            else:
                destinations = [
                    GeographyDestination(
                        city=str(row.city),
                        country=None if pd.isna(row.country) else str(row.country),
                        convention_count=int(row.convention_count),
                        latitude=float(row.latitude),
                        longitude=float(row.longitude),
                        distance_km=float(row.distance_km),
                        distance_band=str(row.distance_band),
                        companies=list(row.companies),
                        conventions=[
                            ConventionGeographyDetail(
                                convention_id=convention["convention_id"],
                                companies=list(convention["companies"]),
                            )
                            for convention in row.conventions
                        ],
                    )
                    for row in result.destinations.itertuples(index=False)
                    if int(row.convention_count) >= threshold
                ]
                countries = [
                    OverviewCategoryAggregate(
                        category=str(row.country),
                        category_is_missing=False,
                        convention_count=int(row.convention_count),
                        denominator=int(row.denominator),
                        percentage=(
                            float(row.percentage)
                            if not pd.isna(row.percentage)
                            else None
                        ),
                    )
                    for row in result.countries.itertuples(index=False)
                    if int(row.convention_count) >= threshold
                ]
                distance_bands = [
                    CategoryAggregate(
                        category=str(row.distance_band),
                        category_is_missing=False,
                        convention_count=int(row.convention_count),
                        denominator=int(row.denominator),
                        percentage=(
                            float(row.percentage)
                            if not pd.isna(row.percentage)
                            else None
                        ),
                    )
                    for row in result.distance_bands.itertuples(index=False)
                    if int(row.convention_count) >= threshold
                ]
        except (GeographicReferenceError, ValueError):
            geography_message = (
                "Le référentiel ou les données géographiques ne permettent pas "
                "de calculer cette analyse."
            )

    return CompanyGeographyResponse(
        exploration_coverage=_field_coverages(data, available_exploration_fields),
        companies_available=company_available,
        companies=companies,
        country_available=country_available,
        country_present_count=country_present_count,
        row_count=len(data),
        geography_available=summary is not None,
        geography_message=geography_message,
        geography_threshold=GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION,
        geography_summary=summary,
        geography_status_counts=status_counts,
        destinations=destinations,
        countries=countries,
        distance_bands=distance_bands,
    )


def get_quality_analysis(
    full_data: pd.DataFrame,
    filtered_data: pd.DataFrame,
) -> QualityResponse:
    """Reproduit les couvertures et alertes Streamlit sans lignes individuelles."""
    summary = quality_summary(full_data, QUALITY_FIELDS)
    available_fields = [
        field for field in QUALITY_FIELDS if field in full_data.columns
    ]
    filtered_fields = [
        field for field in QUALITY_FIELDS if field in filtered_data.columns
    ]
    yearly_fields = [
        field
        for field in QUALITY_DEFAULT_YEARLY_FIELDS
        if field in available_fields
    ]
    if "annee_academique" in full_data.columns and available_fields:
        yearly = yearly_field_coverage(full_data, "annee_academique", available_fields)
        yearly = yearly.sort_values(
            "academic_year",
            key=lambda values: values.map(_academic_sort_key),
            kind="stable",
        )
        yearly_rows = [
            {
                "academic_year": str(row.academic_year),
                "field": str(row.field),
                "label": FIELD_LABELS.get(str(row.field), str(row.field)),
                "present_count": int(row.present_count),
                "missing_count": int(row.missing_count),
                "denominator": int(row.denominator),
                "completion_percentage": (
                    float(row.completion_percentage)
                    if not pd.isna(row.completion_percentage)
                    else None
                ),
            }
            for row in yearly.itertuples(index=False)
            if not pd.isna(row.completion_percentage)
        ]
    else:
        yearly_rows = []

    alerts: list[QualityAlert] = []
    if "annee_academique" in full_data.columns:
        if full_data["annee_academique"].isna().any():
            alerts.append(
                QualityAlert(
                    code="missing_academic_year",
                    message="Des lignes n’ont pas d’année académique renseignée.",
                )
            )
        valid_years = [
            value
            for value in full_data["annee_academique"].dropna().unique()
            if isinstance(value, str)
        ]
        if valid_years:
            latest_year = max(valid_years, key=_academic_sort_key)
            alerts.append(
                QualityAlert(
                    code="latest_year_may_be_incomplete",
                    message=(
                        f"L’année la plus récente observée ({latest_year}) peut être "
                        "incomplète ; aucune comparaison annuelle officielle n’est proposée."
                    ),
                )
            )
    if "nature_du_stage" in full_data.columns:
        missing_natures = int(full_data["nature_du_stage"].isna().sum())
        if missing_natures:
            alerts.append(
                QualityAlert(
                    code="missing_stage_nature",
                    message=(
                        "La nature du stage est absente sur "
                        f"{missing_natures:,} ligne(s) du fichier complet."
                    ).replace(",", " "),
                )
            )
    if "pays_lieu_stage" not in full_data.columns:
        alerts.append(
            QualityAlert(
                code="missing_country_field",
                message=(
                    "Le champ du pays du lieu de stage est absent ; "
                    "l’analyse géographique est indisponible."
                ),
            )
        )
    elif full_data["pays_lieu_stage"].isna().any():
        alerts.append(
            QualityAlert(
                code="missing_country_values",
                message=(
                    "Le pays du lieu de stage est manquant sur une partie des lignes ; "
                    "les destinations affichées ne représentent que les valeurs renseignées."
                ),
            )
        )

    return QualityResponse(
        full_row_count=int(summary["row_count"]),
        full_convention_count=int(summary["convention_count"] or 0),
        filtered_convention_count=count_conventions(filtered_data),
        exact_duplicate_rows=int(summary["exact_duplicate_rows"]),
        repeated_convention_rows=summary["repeated_convention_rows"],
        missing_fields=[
            {"field": field, "label": FIELD_LABELS.get(field, field)}
            for field in summary["unavailable_fields"]
        ],
        full_coverage=_field_coverages(full_data, available_fields),
        filtered_coverage=_field_coverages(filtered_data, filtered_fields),
        yearly_coverage=yearly_rows,
        yearly_fields=yearly_fields,
        alerts=alerts,
    )
