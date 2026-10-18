"""Assemblage des routes de l'API V1."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import filters, health, overview

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(filters.router)
router.include_router(overview.router)
