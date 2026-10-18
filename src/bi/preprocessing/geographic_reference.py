"""Création manuelle d'un modèle de référentiel de destinations."""

import argparse
from pathlib import Path
import tempfile

import pandas as pd

from bi.analytics.geography import (
    CITY_COLUMN,
    COUNTRY_COLUMN,
    REFERENCE_COLUMNS,
    destination_id,
)
from bi.config import GEOGRAPHIC_REFERENCE_FILE, STAGES_SOURCE_FILE
from bi.ingestion import MissingColumnsError, load_stages


def build_geographic_reference_template(data: pd.DataFrame) -> pd.DataFrame:
    """Crée un modèle par ville+pays, sans coordonnées ni données personnelles."""
    if CITY_COLUMN not in data.columns or COUNTRY_COLUMN not in data.columns:
        missing = tuple(
            field
            for field in (CITY_COLUMN, COUNTRY_COLUMN)
            if field not in data.columns
        )
        raise MissingColumnsError(missing)

    destinations: dict[str, tuple[str, str, str, str]] = {}
    for source_city, source_country in data[
        [CITY_COLUMN, COUNTRY_COLUMN]
    ].itertuples(index=False, name=None):
        if pd.isna(source_city):
            continue
        city_label = str(source_city)
        country_label = "" if pd.isna(source_country) else str(source_country)
        city = " ".join(city_label.split())
        country = " ".join(country_label.split()) or None
        if not city:
            continue
        identifier = destination_id(city, country)
        if identifier is not None:
            destinations.setdefault(
                identifier, (city_label, country_label, city, country or "")
            )

    rows = [
        {
            "destination_id": identifier,
            "source_city_label": values[0],
            "source_country_label": values[1],
            "city": values[2],
            "country": values[3],
            "latitude": "",
            "longitude": "",
            "status": "pending",
            "coordinate_source": "",
            "verified_at": "",
            "validated": False,
        }
        for identifier, values in sorted(destinations.items())
    ]
    return pd.DataFrame(rows, columns=REFERENCE_COLUMNS)


def write_geographic_reference_template(
    data: pd.DataFrame,
    output_path: str | Path = GEOGRAPHIC_REFERENCE_FILE,
    overwrite: bool = False,
) -> Path:
    """Écrit explicitement un modèle CSV sans écraser un référentiel existant."""
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(
            f"Le référentiel existe déjà : {output.name}. "
            "Utilisez overwrite=True après sauvegarde si son remplacement est voulu."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    template = build_geographic_reference_template(data)
    with tempfile.NamedTemporaryFile(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
    try:
        template.to_csv(temporary, index=False, encoding="utf-8")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prépare un modèle local de destinations sans lancer de géocodage."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=GEOGRAPHIC_REFERENCE_FILE,
        help="Chemin du CSV de référence (défaut : data/interim/geographic_reference.csv).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remplace explicitement un fichier de référence existant.",
    )
    arguments = parser.parse_args()
    source = load_stages(
        STAGES_SOURCE_FILE,
        required_columns=(CITY_COLUMN, COUNTRY_COLUMN),
    )
    output = write_geographic_reference_template(
        source, arguments.output, overwrite=arguments.overwrite
    )
    print(
        f"Modèle créé : {output.name} "
        f"({len(build_geographic_reference_template(source))} destinations)."
    )


if __name__ == "__main__":
    main()
