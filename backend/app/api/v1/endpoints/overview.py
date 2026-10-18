"""KPI et agrégats de la Vue d'ensemble."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
import pandas as pd

from backend.app.schemas.overview import OverviewResponse
from backend.app.services.dashboard import get_dashboard_data, get_overview

router = APIRouter(tags=["overview"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="KPI et agrégations de la vue d'ensemble",
    description=(
        "Les filtres sont des paramètres répétés : "
        "`?academic_years=2024%2F2025&stage_types=PFE`. "
        "Un paramètre de catégorie omis ne filtre pas cette catégorie. "
        "Pour inclure les valeurs manquantes, ajouter le booléen correspondant "
        "à `true`; avec les valeurs omises cela sélectionne uniquement les "
        "valeurs manquantes. Fournir `include_missing_*=false` sans valeur "
        "catégorielle explicite sélectionne zéro ligne. Une valeur de catégorie "
        "explicitement sélectionnée exclut les manquants par défaut."
    ),
)
def overview(
    academic_years: Annotated[list[str] | None, Query()] = None,
    stage_types: Annotated[list[str] | None, Query()] = None,
    stage_natures: Annotated[list[str] | None, Query()] = None,
    include_missing_year: bool | None = None,
    include_missing_type: bool | None = None,
    include_missing_nature: bool | None = None,
    data: pd.DataFrame = Depends(get_dashboard_data),
) -> OverviewResponse:
    """Calcule les indicateurs sur les données filtrées côté serveur."""
    return get_overview(
        data,
        academic_years=academic_years,
        stage_types=stage_types,
        stage_natures=stage_natures,
        include_missing_year=include_missing_year,
        include_missing_type=include_missing_type,
        include_missing_nature=include_missing_nature,
    )
