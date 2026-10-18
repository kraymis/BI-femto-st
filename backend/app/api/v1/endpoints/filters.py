"""Options réellement disponibles pour les filtres globaux."""

from fastapi import APIRouter, Depends
import pandas as pd

from backend.app.schemas.filters import FilterOptionsResponse
from backend.app.services.dashboard import get_dashboard_data, get_filter_options

router = APIRouter(tags=["filters"])


@router.get("/filters/options", response_model=FilterOptionsResponse)
def filter_options(
    data: pd.DataFrame = Depends(get_dashboard_data),
) -> FilterOptionsResponse:
    """Retourne les modalités présentes, en distinguant les valeurs absentes."""
    return get_filter_options(data)
