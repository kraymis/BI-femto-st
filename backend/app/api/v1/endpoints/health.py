"""Contrôle de disponibilité de l'application."""

from fastapi import APIRouter

from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Confirme que le processus API répond sans lire les données."""
    return HealthResponse(status="ok")
