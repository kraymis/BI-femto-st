"""Lecture Excel et validation des colonnes sans transformation des valeurs."""

from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException

from bi.config import STAGES_SOURCE_FILE


BASE_REQUIRED_COLUMNS = ("n_convention_de_stage",)


class DataFileError(RuntimeError):
    """Le fichier source est absent ou ne peut pas être lu."""


class MissingColumnsError(ValueError):
    """Une ou plusieurs colonnes obligatoires sont absentes."""

    def __init__(self, missing_columns: Iterable[str]) -> None:
        self.missing_columns = tuple(missing_columns)
        missing = ", ".join(self.missing_columns)
        super().__init__(f"Colonnes obligatoires absentes : {missing}")


def validate_columns(
    data: pd.DataFrame,
    required_columns: Iterable[str],
    optional_columns: Iterable[str] = (),
) -> tuple[str, ...]:
    """Valide les colonnes requises et retourne les colonnes facultatives absentes."""
    required = tuple(dict.fromkeys(required_columns))
    optional = tuple(
        column
        for column in dict.fromkeys(optional_columns)
        if column not in required
    )
    missing_required = tuple(
        column for column in required if column not in data.columns
    )
    if missing_required:
        raise MissingColumnsError(missing_required)
    return tuple(column for column in optional if column not in data.columns)


def load_stages(
    path: str | Path = STAGES_SOURCE_FILE,
    required_columns: Iterable[str] = BASE_REQUIRED_COLUMNS,
    optional_columns: Iterable[str] = (),
) -> pd.DataFrame:
    """Charge le classeur des stages en lecture seule et valide son schéma."""
    source = Path(path)
    if not source.exists() or not source.is_file():
        raise DataFileError(f"Fichier source absent : {source.name}")

    try:
        data = pd.read_excel(
            source,
            engine="openpyxl",
            engine_kwargs={"read_only": True, "data_only": True},
        )
    except (BadZipFile, ImportError, InvalidFileException, OSError, ValueError) as exc:
        raise DataFileError(
            f"Impossible de lire le fichier source : {source.name}"
        ) from exc

    validate_columns(data, required_columns, optional_columns)
    return data
