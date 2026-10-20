"""Dépendances HTTP partagées par les pages de l'API V1."""

from typing import Annotated

from fastapi import Depends, Query
import pandas as pd

from backend.app.services.dashboard import (
    get_dashboard_data,
    get_filtered_dashboard_data,
)


def get_filtered_data(
    academic_years: Annotated[list[str] | None, Query()] = None,
    stage_types: Annotated[list[str] | None, Query()] = None,
    stage_natures: Annotated[list[str] | None, Query()] = None,
    include_missing_year: bool | None = None,
    include_missing_type: bool | None = None,
    include_missing_nature: bool | None = None,
    data: pd.DataFrame = Depends(get_dashboard_data),
) -> pd.DataFrame:
    """Applique les mêmes filtres globaux, y compris la sélection des valeurs absentes."""
    return get_filtered_dashboard_data(
        academic_years=academic_years,
        stage_types=stage_types,
        stage_natures=stage_natures,
        include_missing_year=include_missing_year,
        include_missing_type=include_missing_type,
        include_missing_nature=include_missing_nature,
        data=data,
    )
