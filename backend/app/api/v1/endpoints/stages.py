"""Agrégats de l'analyse des stages."""

import pandas as pd
from fastapi import APIRouter, Depends

from backend.app.api.v1.dependencies import get_filtered_data
from backend.app.schemas.analytics import StageAnalysisResponse
from backend.app.services.dashboard import get_stage_analysis

router = APIRouter(tags=["stages"])


@router.get(
    "/stages",
    response_model=StageAnalysisResponse,
    summary="Analyse des stages",
    description=(
        "Retourne les distributions existantes par type et nature ainsi que le "
        "tableau croisé type × nature, sous les mêmes filtres globaux."
    ),
)
def stage_analysis(
    data: pd.DataFrame = Depends(get_filtered_data),
) -> StageAnalysisResponse:
    """Retourne les distributions et le croisement type × nature."""
    return get_stage_analysis(data)
