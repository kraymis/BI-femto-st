"""Préparation de tableaux agrégés pour les pages BI."""

from collections.abc import Iterable

import pandas as pd

from bi.analytics.kpis import CONVENTION_COLUMN
from bi.ingestion import validate_columns


MISSING_LABEL = "Non renseigné"


def _display_categories(
    values: pd.Series, missing_label: str = MISSING_LABEL
) -> pd.Series:
    """Produit des libellés d’affichage distincts sans toucher aux valeurs source."""
    used_labels: set[str] = set()
    labels_by_value: dict[object, str] = {}
    unique_values = values.drop_duplicates().tolist()
    source_labels = {
        str(value) for value in unique_values if not pd.isna(value)
    }
    missing_display = missing_label
    while missing_display in source_labels:
        missing_display = f"{missing_display} (valeur absente)"

    for value in unique_values:
        is_missing = bool(pd.isna(value))
        base_label = missing_display if is_missing else str(value)
        label = base_label
        suffix = 2
        while label in used_labels:
            label = f"{base_label} (modalité {suffix})"
            suffix += 1
        used_labels.add(label)
        if not is_missing:
            labels_by_value[value] = label

    output = [
        missing_display if pd.isna(value) else labels_by_value[value]
        for value in values
    ]
    return pd.Series(output, index=values.index, dtype="string")


def convention_crosstab(
    data: pd.DataFrame,
    row_column: str,
    column_column: str,
    missing_label: str = MISSING_LABEL,
) -> pd.DataFrame:
    """Compte les conventions distinctes dans un tableau croisé.

    Les conventions répétées dans une même cellule ne sont comptées qu’une fois.
    Les valeurs absentes sont représentées par un libellé d’affichage distinct
    de toute modalité source portant le même texte.
    """
    validate_columns(data, (CONVENTION_COLUMN, row_column, column_column))
    if data.empty:
        result = pd.DataFrame()
        result.index.name = row_column
        result.columns.name = column_column
        return result

    working = pd.DataFrame(
        {
            "__row": _display_categories(data[row_column], missing_label),
            "__column": _display_categories(data[column_column], missing_label),
            "__convention": data[CONVENTION_COLUMN],
        },
        index=data.index,
    )
    assignments = working.dropna(subset=["__convention"]).drop_duplicates()
    ambiguous_rows = assignments.groupby("__convention", sort=False).agg(
        row_categories=("__row", "nunique"),
        column_categories=("__column", "nunique"),
    )
    if (
        (ambiguous_rows["row_categories"] > 1)
        | (ambiguous_rows["column_categories"] > 1)
    ).any():
        raise ValueError(
            "Une convention correspond à plusieurs modalités dans le tableau croisé."
        )

    result = working.pivot_table(
        index="__row",
        columns="__column",
        values="__convention",
        aggfunc="nunique",
        fill_value=0,
        observed=True,
        sort=False,
    )
    result.index.name = row_column
    result.columns.name = column_column
    return result.astype("int64")


def crosstab_row_percentages(counts: pd.DataFrame) -> pd.DataFrame:
    """Convertit un tableau d’effectifs en pourcentages par ligne.

    Le dénominateur est la somme des cellules de la ligne ; une ligne de
    dénominateur nul reste entièrement manquante plutôt que d’être convertie
    en zéros ou en pourcentages artificiels.
    """
    denominators = counts.sum(axis=1).replace(0, pd.NA)
    return counts.div(denominators, axis=0).mul(100)


def crosstab_with_totals(counts: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les totaux marginaux à un tableau d’effectifs non ambigu."""
    if counts.empty:
        return counts.copy()

    total_column = "Total conventions"
    while total_column in counts.columns:
        total_column = f"{total_column} (total)"
    total_row = "Total"
    while total_row in counts.index:
        total_row = f"{total_row} (total)"

    result = counts.copy()
    result[total_column] = result.sum(axis=1)
    totals = result.sum(axis=0)
    result.loc[total_row] = totals
    return result


def filter_aggregated_categories(
    data: pd.DataFrame,
    columns: Iterable[str],
    query: str,
) -> pd.DataFrame:
    """Recherche textuelle parmi les lignes d’un tableau déjà agrégé."""
    selected_columns = tuple(dict.fromkeys(columns))
    validate_columns(data, selected_columns)
    if not query:
        return data.copy()

    query = query.casefold()
    mask = pd.Series(False, index=data.index, dtype=bool)
    for column in selected_columns:
        mask |= data[column].astype("string").str.casefold().str.contains(
            query, regex=False, na=False
        )
    return data.loc[mask].copy()


def yearly_field_coverage(
    data: pd.DataFrame,
    year_column: str,
    fields: Iterable[str],
    missing_label: str = MISSING_LABEL,
) -> pd.DataFrame:
    """Retourne les taux de complétude des champs, par année et par ligne."""
    selected_fields = tuple(dict.fromkeys(fields))
    validate_columns(data, (year_column, *selected_fields))
    years = _display_categories(data[year_column], missing_label)
    grouped_data = data.copy()
    grouped_data["__academic_year"] = years

    rows: list[dict[str, object]] = []
    for year, group in grouped_data.groupby(
        "__academic_year", sort=False, observed=True
    ):
        for field in selected_fields:
            denominator = len(group)
            present = int(group[field].notna().sum())
            missing = denominator - present
            percentage = present * 100 / denominator if denominator else None
            rows.append(
                {
                    "academic_year": year,
                    "field": field,
                    "present_count": present,
                    "missing_count": missing,
                    "denominator": denominator,
                    "completion_percentage": percentage,
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "academic_year",
            "field",
            "present_count",
            "missing_count",
            "denominator",
            "completion_percentage",
        ],
    )
