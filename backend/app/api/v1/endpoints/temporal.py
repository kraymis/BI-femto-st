"""Agrégats de l'analyse temporelle."""

import pandas as pd
from fastapi import APIRouter, Depends

from backend.app.api.v1.dependencies import get_filtered_data
from backend.app.schemas.analytics import TemporalAnalysisResponse
from backend.app.services.dashboard import get_temporal_analysis

router = APIRouter(tags=["temporal"])


@router.get(
    "/temporal",
    response_model=TemporalAnalysisResponse,
    summary="Analyse temporelle",
    description=(
        "Retourne les conventions distinctes par année et le tableau croisé "
        "année × type. Les filtres globaux de la Vue d’ensemble sont réutilisés."
    ),
)
def temporal_analysis(
    data: pd.DataFrame = Depends(get_filtered_data),
) -> TemporalAnalysisResponse:
    """Retourne la série annuelle et le croisement année × type."""
    return get_temporal_analysis(data)
