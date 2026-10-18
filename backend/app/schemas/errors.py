"""Réponses d'erreur publiques et non sensibles."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
