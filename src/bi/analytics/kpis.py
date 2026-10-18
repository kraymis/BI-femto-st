"""KPI V1 calculés sans dépendance à l’interface."""

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from bi.ingestion import validate_columns


CONVENTION_COLUMN = "n_convention_de_stage"
STUDENT_COLUMN = "n_etudiant"
MISSING_LABEL = "Non renseigné"


@dataclass(frozen=True)
class CountRate:
    """Effectif, dénominateur et taux en pourcentage."""

    count: int
    denominator: int
    percentage: float | None


def count_rate(count: int, denominator: int) -> CountRate:
    """Construit un taux explicite ; un dénominateur nul donne un taux absent."""
    if count < 0:
        raise ValueError("L’effectif ne peut pas être négatif.")
    if denominator < 0:
        raise ValueError("Le dénominateur ne peut pas être négatif.")
    if count > denominator:
        raise ValueError("L’effectif ne peut pas dépasser le dénominateur.")
    percentage = count * 100 / denominator if denominator else None
    return CountRate(count, denominator, percentage)


def count_conventions(data: pd.DataFrame) -> int:
    """Compte les conventions distinctes, sans les assimiler à des stages."""
    validate_columns(data, (CONVENTION_COLUMN,))
    return int(data[CONVENTION_COLUMN].nunique(dropna=True))


def count_students(data: pd.DataFrame) -> int:
    """Compte les identifiants étudiants distincts sans les exposer."""
    validate_columns(data, (STUDENT_COLUMN,))
    return int(data[STUDENT_COLUMN].nunique(dropna=True))


def count_conventions_by_category(
    data: pd.DataFrame,
    category_column: str,
    include_missing: bool = True,
    missing_label: str = MISSING_LABEL,
) -> pd.DataFrame:
    """Compte les conventions distinctes par catégorie avec dénominateur explicite.

    Si les valeurs inconnues sont incluses, le dénominateur couvre toutes les
    conventions. Sinon, il couvre uniquement celles ayant une catégorie connue.
    """
    validate_columns(data, (CONVENTION_COLUMN, category_column))
    category_values = data[category_column]
    if include_missing:
        denominator = count_conventions(data)
        selected = data
    else:
        selected = data.loc[category_values.notna()]
        denominator = count_conventions(selected)

    rows: list[dict[str, object]] = []
    for value, group in selected.groupby(
        category_column, dropna=include_missing is False, sort=False
    ):
        is_missing = bool(pd.isna(value))
        if is_missing and not include_missing:
            continue
        category = missing_label if is_missing else value
        convention_count = int(group[CONVENTION_COLUMN].nunique(dropna=True))
        rows.append(
            {
                "category": category,
                "category_is_missing": is_missing,
                "convention_count": convention_count,
                "denominator": denominator,
                "percentage": count_rate(
                    convention_count, denominator
                ).percentage,
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "category",
            "category_is_missing",
            "convention_count",
            "denominator",
            "percentage",
        ],
    )
