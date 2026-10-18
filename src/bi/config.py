"""Configuration centrale des chemins du projet."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
STAGES_SOURCE_FILE = RAW_DATA_DIR / "stages_cleaned2.xlsx"
GEOGRAPHIC_REFERENCE_FILE = INTERIM_DATA_DIR / "geographic_reference.csv"

SCHOOL_NAME = "SUPMICROTECH-ENSMM"
SCHOOL_ADDRESS = "26, rue de l'Épitaphe, CS 51813, 25030 Besançon Cedex, France"
SCHOOL_LATITUDE = 47.250944
SCHOOL_LONGITUDE = 5.9942287
SCHOOL_COORDINATES_SOURCE = "https://www.supmicrotech.fr/fr/contact"
SCHOOL_COORDINATES_VERIFIED_ON = "2026-10-17"

# Destinations below the user-approved minimum are omitted from detailed views.
GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION: int | None = 1
