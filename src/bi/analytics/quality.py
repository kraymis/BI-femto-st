"""Mesures agrégées de complétude et contrôles de qualité V1."""

from collections.abc import Iterable
from typing import Any

import pandas as pd

from bi.analytics.kpis import (
    CONVENTION_COLUMN,
    STUDENT_COLUMN,
    count_conventions,
    count_rate,
    count_students,
)
from bi.ingestion import validate_columns


DEFAULT_QUALITY_FIELDS = (
    "annee_academique",
    CONVENTION_COLUMN,
    STUDENT_COLUMN,
    "type_de_stage",
    "nature_du_stage",
    "entreprise",
    "date_debut",
    "date_fin",
    "pays_lieu_stage",
    "date_soutenance",
)


def field_coverage(
    data: pd.DataFrame, columns: Iterable[str]
) -> pd.DataFrame:
    """Retourne les valeurs présentes, manquantes et taux par ligne."""
    selected_columns = tuple(dict.fromkeys(columns))
    validate_columns(data, selected_columns)
    denominator = len(data)

    rows: list[dict[str, object]] = []
    for column in selected_columns:
        present = int(data[column].notna().sum())
        rate = count_rate(present, denominator)
        rows.append(
            {
                "field": column,
                "present_count": present,
                "missing_count": denominator - present,
                "denominator": denominator,
                "completion_percentage": rate.percentage,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "field",
            "present_count",
            "missing_count",
            "denominator",
            "completion_percentage",
        ],
    )


def quality_summary(
    data: pd.DataFrame,
    tracked_fields: Iterable[str] = DEFAULT_QUALITY_FIELDS,
) -> dict[str, Any]:
    """Retourne uniquement des contrôles agrégés et les champs indisponibles."""
    fields = tuple(dict.fromkeys(tracked_fields))
    available_fields = tuple(
        field for field in fields if field in data.columns
    )
    missing_fields = tuple(
        field for field in fields if field not in data.columns
    )
    counts = field_coverage(data, available_fields)
    has_conventions = CONVENTION_COLUMN in data.columns
    has_students = STUDENT_COLUMN in data.columns

    summary: dict[str, Any] = {
        "row_count": len(data),
        "exact_duplicate_rows": int(data.duplicated(keep=False).sum()),
        "convention_count": (
            count_conventions(data) if has_conventions else None
        ),
        "student_count": count_students(data) if has_students else None,
        "repeated_convention_rows": (
            int(
                data[CONVENTION_COLUMN].dropna().duplicated().sum()
            )
            if has_conventions
            else None
        ),
        "field_coverage": counts,
        "unavailable_fields": missing_fields,
    }
    return summary
