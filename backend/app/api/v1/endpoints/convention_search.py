"""Routes de recherche multicritère des conventions."""

from fastapi import APIRouter, Depends, HTTPException
import pandas as pd

from backend.app.schemas.convention_search import (
    ConventionSearchOptions,
    ConventionSearchRequest,
    ConventionSearchResponse,
)
from backend.app.services.convention_search import (
    SearchFieldUnavailableError,
    get_convention_search_options,
    search_conventions,
)
from backend.app.services.dashboard import get_dashboard_data

router = APIRouter(tags=["convention-search"])


@router.get(
    "/conventions/search/options",
    response_model=ConventionSearchOptions,
    summary="Options des critères de recherche de conventions",
)
def convention_search_options(
    data: pd.DataFrame = Depends(get_dashboard_data),
) -> ConventionSearchOptions:
    return get_convention_search_options(data)


@router.post(
    "/conventions/search",
    response_model=ConventionSearchResponse,
    summary="Recherche multicritère paginée de conventions",
    description=(
        "Combine les critères renseignés avec une logique ET et ne dépend pas "
        "des filtres globaux du dashboard. Renvoie une liste de champs ciblés, "
        "y compris les noms/prénoms et identifiants étudiants présents dans la "
        "source. Dans ce déploiement, les données ont été autorisées par le "
        "propriétaire ; cette route ne dispose pas d’authentification."
    ),
)
def convention_search(
    request: ConventionSearchRequest,
    data: pd.DataFrame = Depends(get_dashboard_data),
) -> ConventionSearchResponse:
    try:
        return search_conventions(data, request)
    except SearchFieldUnavailableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
