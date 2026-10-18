"""Application FastAPI de la migration BI."""

from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from backend.app.api.v1.router import router as v1_router  # noqa: E402
from backend.app.schemas.errors import ErrorResponse  # noqa: E402
from bi.ingestion import DataFileError, MissingColumnsError  # noqa: E402

app = FastAPI(
    title="API BI des stages",
    description=(
        "API de lecture agrégée pour la migration progressive du dashboard BI. "
        "Les enregistrements sources et identifiants individuels ne sont jamais "
        "retournés."
    ),
    version="1.0.0",
)
app.include_router(v1_router)


@app.exception_handler(DataFileError)
async def data_file_error_handler(
    request: Request, exc: DataFileError
) -> JSONResponse:
    """Signale une source indisponible sans révéler de chemin local."""
    response = ErrorResponse(
        code="source_unavailable",
        message="Le fichier source est absent ou illisible.",
    )
    return JSONResponse(status_code=503, content=response.model_dump())


@app.exception_handler(MissingColumnsError)
async def missing_columns_error_handler(
    request: Request, exc: MissingColumnsError
) -> JSONResponse:
    """Signale un schéma invalide sans retourner de contenu source."""
    response = ErrorResponse(
        code="invalid_source_schema",
        message="Le fichier source ne contient pas toutes les colonnes requises.",
    )
    return JSONResponse(status_code=503, content=response.model_dump())
