"""Recherche multicritère paginée dans les champs autorisés du classeur."""

import math
from numbers import Integral, Real

import pandas as pd

from backend.app.schemas.convention_search import (
    ConventionSearchOptions,
    ConventionSearchRequest,
    ConventionSearchResponse,
    ConventionSearchResult,
)
from backend.app.services.dashboard import get_filter_options

SEARCH_FIELDS = {
    "subject_id": "id_sujet_pfe",
    "convention_id": "n_convention_de_stage",
    "student_id": "n_etudiant",
    "first_name": "prenom_de_l_eleve",
    "last_name": "nom_de_l_eleve",
    "company": "entreprise",
    "academic_year": "annee_academique",
    "stage_type": "type_de_stage",
    "stage_nature": "nature_du_stage",
    "city": "ville_lieu_stage",
    "country": "pays_lieu_stage",
}

RESULT_FIELDS = (
    "n_convention_de_stage",
    "id_sujet_pfe",
    "n_etudiant",
    "prenom_de_l_eleve",
    "nom_de_l_eleve",
    "entreprise",
    "annee_academique",
    "type_de_stage",
    "nature_du_stage",
    "ville_lieu_stage",
    "pays_lieu_stage",
)


class SearchFieldUnavailableError(ValueError):
    """La source ne contient pas le champ demandé."""


def get_convention_search_options(data: pd.DataFrame) -> ConventionSearchOptions:
    """Expose les champs présents et les options catégorielles réellement chargées."""
    options = get_filter_options(data)
    available_fields = [
        key for key, column in SEARCH_FIELDS.items() if column in data.columns
    ]
    return ConventionSearchOptions(
        available_fields=available_fields,
        academic_years=options.academic_years,
        stage_types=options.stage_types,
        stage_natures=options.stage_natures,
    )


def _identifier(value: object) -> str | None:
    if pd.isna(value):
        return None
    if isinstance(value, Integral):
        return str(value)
    if isinstance(value, Real) and float(value).is_integer():
        return str(int(value))
    return " ".join(str(value).split())


def _contains(data: pd.DataFrame, column: str, value: str) -> pd.Series:
    if column not in data.columns:
        raise SearchFieldUnavailableError(
            f"Le champ « {column} » n’est pas disponible dans la source."
        )
    return data[column].astype("string").str.contains(
        value.strip(), case=False, regex=False, na=False
    )


def _exact_identifier(
    data: pd.DataFrame, column: str, value: str
) -> pd.Series:
    if column not in data.columns:
        raise SearchFieldUnavailableError(
            f"Le champ « {column} » n’est pas disponible dans la source."
        )
    target = _identifier(value)
    if target is None:
        return pd.Series(False, index=data.index)
    return data[column].map(_identifier).str.casefold().eq(target.casefold())


def _exact_category(
    data: pd.DataFrame,
    column: str,
    value: str | None,
    include_missing: bool,
) -> pd.Series | None:
    if value is None and not include_missing:
        return None
    if column not in data.columns:
        raise SearchFieldUnavailableError(
            f"Le champ « {column} » n’est pas disponible dans la source."
        )
    if include_missing:
        return data[column].isna()
    return data[column].astype("string").str.casefold().eq(value.casefold())


def _result_value(row: pd.Series, column: str) -> str | None:
    if column not in row.index:
        return None
    value = row[column]
    if pd.isna(value):
        return None
    return _identifier(value)


def search_conventions(
    data: pd.DataFrame, request: ConventionSearchRequest
) -> ConventionSearchResponse:
    """Filtre côté serveur avec ET logique, puis renvoie une page de champs ciblés."""
    mask = pd.Series(True, index=data.index)

    if request.subject_id and request.subject_id.strip():
        mask &= _exact_identifier(
            data, SEARCH_FIELDS["subject_id"], request.subject_id
        )
    if request.convention_id and request.convention_id.strip():
        mask &= _exact_identifier(
            data, SEARCH_FIELDS["convention_id"], request.convention_id
        )
    if request.student_id_exact and request.student_id_exact.strip():
        mask &= _exact_identifier(
            data, SEARCH_FIELDS["student_id"], request.student_id_exact
        )
    if request.company_contains and request.company_contains.strip():
        mask &= _contains(data, SEARCH_FIELDS["company"], request.company_contains)
    if request.student_name_contains and request.student_name_contains.strip():
        first_name = SEARCH_FIELDS["first_name"]
        last_name = SEARCH_FIELDS["last_name"]
        for column in (first_name, last_name):
            if column not in data.columns:
                raise SearchFieldUnavailableError(
                    f"Le champ « {column} » n’est pas disponible dans la source."
                )
        full_name = (
            data[first_name].fillna("").astype("string")
            + " "
            + data[last_name].fillna("").astype("string")
        )
        mask &= full_name.str.contains(
            request.student_name_contains.strip(),
            case=False,
            regex=False,
            na=False,
        )

    category_criteria = (
        (
            "academic_year",
            request.academic_year,
            request.academic_year_missing,
        ),
        ("stage_type", request.stage_type, request.stage_type_missing),
        ("stage_nature", request.stage_nature, request.stage_nature_missing),
    )
    for key, value, include_missing in category_criteria:
        criterion = _exact_category(
            data, SEARCH_FIELDS[key], value, include_missing
        )
        if criterion is not None:
            mask &= criterion

    for key, value in (
        ("city", request.city_contains),
        ("country", request.country_contains),
    ):
        if value and value.strip():
            mask &= _contains(data, SEARCH_FIELDS[key], value)

    matches = data.loc[mask, [column for column in RESULT_FIELDS if column in data]]
    total_count = len(matches)
    total_pages = math.ceil(total_count / request.page_size) if total_count else 0
    page = min(request.page, total_pages) if total_pages else 1
    start = (page - 1) * request.page_size
    page_data = matches.iloc[start : start + request.page_size]

    results: list[ConventionSearchResult] = []
    for _, row in page_data.iterrows():
        first = _result_value(row, SEARCH_FIELDS["first_name"])
        last = _result_value(row, SEARCH_FIELDS["last_name"])
        student_name = " ".join(value for value in (first, last) if value) or None
        results.append(
            ConventionSearchResult(
                convention_id=_result_value(row, SEARCH_FIELDS["convention_id"]),
                subject_id=_result_value(row, SEARCH_FIELDS["subject_id"]),
                student_id=_result_value(row, SEARCH_FIELDS["student_id"]),
                student_name=student_name,
                company=_result_value(row, SEARCH_FIELDS["company"]),
                academic_year=_result_value(row, SEARCH_FIELDS["academic_year"]),
                stage_type=_result_value(row, SEARCH_FIELDS["stage_type"]),
                stage_nature=_result_value(row, SEARCH_FIELDS["stage_nature"]),
                city=_result_value(row, SEARCH_FIELDS["city"]),
                country=_result_value(row, SEARCH_FIELDS["country"]),
            )
        )

    return ConventionSearchResponse(
        total_count=total_count,
        page=page,
        page_size=request.page_size,
        total_pages=total_pages,
        results=results,
    )
