"""Agrégats d'exploration des entreprises et des lieux."""

import pandas as pd
from fastapi import APIRouter, Depends

from backend.app.api.v1.dependencies import get_filtered_data
from backend.app.schemas.analytics import CompanyGeographyResponse
from backend.app.services.dashboard import get_company_geography

router = APIRouter(tags=["companies-geography"])


@router.get(
    "/companies-geography",
    response_model=CompanyGeographyResponse,
    summary="Entreprises et géographie",
    description=(
        "Retourne des couvertures et agrégats. Les détails géographiques sont "
        "limités au seuil configuré dans src/bi/config.py. Pour chaque "
        "destination publiée, la réponse expose les numéros de convention "
        "associés et les libellés entreprise disponibles. Aucun identifiant "
        "étudiant ou ligne source complète n'est exposé. Cette route ne possède "
        "pas d'authentification et doit rester sur un réseau de confiance."
    ),
)
def companies_geography(
    data: pd.DataFrame = Depends(get_filtered_data),
) -> CompanyGeographyResponse:
    """Retourne des couvertures, classements et destinations agrégés."""
    return get_company_geography(data)
