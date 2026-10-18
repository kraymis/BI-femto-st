"""Filtres de données partagés, sans normalisation des valeurs métier."""

from collections.abc import Iterable

import pandas as pd

from bi.ingestion import validate_columns


def _apply_category_filter(
    data: pd.DataFrame,
    column: str,
    selected_values: Iterable[object] | None,
    include_missing: bool,
) -> pd.Series:
    if selected_values is None:
        return pd.Series(True, index=data.index, dtype=bool)

    values = tuple(selected_values)
    if not values:
        return pd.Series(False, index=data.index, dtype=bool)

    selected_missing = any(pd.isna(value) for value in values)
    non_missing_values = tuple(value for value in values if not pd.isna(value))
    mask = data[column].isin(non_missing_values)
    if include_missing or selected_missing:
        mask = mask | data[column].isna()
    return mask


def filter_stages(
    data: pd.DataFrame,
    academic_years: Iterable[object] | None = None,
    stage_types: Iterable[object] | None = None,
    stage_natures: Iterable[object] | None = None,
    include_missing_year: bool = True,
    include_missing_type: bool = True,
    include_missing_nature: bool = True,
) -> pd.DataFrame:
    """Filtre par année, type et nature ; une sélection vide retourne zéro ligne.

    ``None`` signifie « aucune restriction ». Une collection vide est une
    sélection explicite sans valeur et retourne donc un résultat vide.
    L’inclusion des valeurs absentes est configurable pour chaque filtre.
    """
    filters = (
        ("annee_academique", academic_years, include_missing_year),
        ("type_de_stage", stage_types, include_missing_type),
        ("nature_du_stage", stage_natures, include_missing_nature),
    )
    active_filters = tuple(
        (column, values, include_missing)
        for column, values, include_missing in filters
        if values is not None
    )
    validate_columns(data, (column for column, _, _ in active_filters))

    mask = pd.Series(True, index=data.index, dtype=bool)
    for column, values, include_missing in active_filters:
        mask &= _apply_category_filter(data, column, values, include_missing)
    return data.loc[mask].copy()
