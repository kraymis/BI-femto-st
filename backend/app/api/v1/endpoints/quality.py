"""Contrôles agrégés de qualité des données."""

import pandas as pd
from fastapi import APIRouter, Depends

from backend.app.api.v1.dependencies import get_filtered_data
from backend.app.schemas.analytics import QualityResponse
from backend.app.services.dashboard import (
    get_dashboard_data,
    get_quality_analysis,
)

router = APIRouter(tags=["quality"])


@router.get(
    "/quality",
    response_model=QualityResponse,
    summary="Qualité des données",
    description=(
        "Retourne des contrôles agrégés sur le fichier complet et la couverture "
        "du périmètre filtré. Aucune donnée individuelle n'est exposée."
    ),
)
def quality_analysis(
    full_data: pd.DataFrame = Depends(get_dashboard_data),
    filtered_data: pd.DataFrame = Depends(get_filtered_data),
) -> QualityResponse:
    """Retourne la qualité globale et la couverture du périmètre filtré."""
    return get_quality_analysis(full_data, filtered_data)
