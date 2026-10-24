"""Assemblage des routes de l'API V1."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    companies_geography,
    convention_search,
    filters,
    health,
    overview,
    quality,
    stages,
    temporal,
)

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(filters.router)
router.include_router(overview.router)
router.include_router(temporal.router)
router.include_router(stages.router)
router.include_router(companies_geography.router)
router.include_router(convention_search.router)
router.include_router(quality.router)
