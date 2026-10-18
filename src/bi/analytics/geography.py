"""Aggregations géographiques indépendantes de Streamlit."""

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from bi.config import SCHOOL_LATITUDE, SCHOOL_LONGITUDE
from bi.ingestion import validate_columns


CONVENTION_COLUMN = "n_convention_de_stage"
CITY_COLUMN = "ville_lieu_stage"
COUNTRY_COLUMN = "pays_lieu_stage"
REFERENCE_COLUMNS = (
    "destination_id",
    "source_city_label",
    "source_country_label",
    "city",
    "country",
    "latitude",
    "longitude",
    "status",
    "coordinate_source",
    "verified_at",
    "validated",
)
EARTH_RADIUS_KM = 6371.0088
DISTANCE_BANDS = (
    ("Moins de 25 km", 0.0, 25.0),
    ("25 à moins de 100 km", 25.0, 100.0),
    ("100 à moins de 300 km", 100.0, 300.0),
    ("300 km et plus", 300.0, math.inf),
)
REFERENCE_STATUSES = {"pending", "not_found", "ambiguous", "located"}
STATUS_LABELS = {
    "missing_destination": "Destination absente de la source",
    "ambiguous": "Convention associée à plusieurs destinations",
    "not_in_reference": "Destination absente du référentiel",
    "pending": "Coordonnées à préparer",
    "not_found": "Destination non localisée",
    "ambiguous_reference": "Destination ambiguë dans le référentiel",
    "invalid_coordinates": "Coordonnées invalides",
    "unvalidated": "Coordonnées non validées",
    "located": "Destination localisée",
}


class GeographicReferenceError(ValueError):
    """Le référentiel géographique est absent ou invalide."""


@dataclass(frozen=True)
class GeographyResult:
    """Résultats agrégés ; aucune clé de convention n'est exposée."""

    summary: dict[str, int | float | None]
    status_counts: pd.DataFrame
    destinations: pd.DataFrame
    countries: pd.DataFrame
    distance_bands: pd.DataFrame


def _normalized_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = " ".join(str(value).split())
    return normalized or None


def destination_id(city: object, country: object) -> str | None:
    """Construit une clé reproductible ville+pays sans fusionner les homonymes."""
    normalized_city = _normalized_text(city)
    if normalized_city is None:
        return None
    normalized_country = _normalized_text(country) or ""
    key = f"{normalized_city}\0{normalized_country}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def _is_valid_coordinate_pair(latitude: object, longitude: object) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError, OverflowError):
        return False
    return (
        math.isfinite(lat)
        and math.isfinite(lon)
        and -90 <= lat <= 90
        and -180 <= lon <= 180
    )


def _reference_values(value: object, label: str) -> list[str]:
    if value is None or pd.isna(value) or not str(value).strip():
        return []
    try:
        labels = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise GeographicReferenceError(
            f"La liste « {label} » du référentiel est invalide."
        ) from exc
    if not isinstance(labels, list) or any(
        not isinstance(label, str) or not label.strip() for label in labels
    ):
        raise GeographicReferenceError(
            f"La liste « {label} » du référentiel est invalide."
        )
    return list(dict.fromkeys(label.strip() for label in labels))


def haversine_km(
    latitude_a: object,
    longitude_a: object,
    latitude_b: object,
    longitude_b: object,
) -> float | None:
    """Distance à vol d'oiseau en kilomètres ; valeurs invalides non calculables."""
    values = (latitude_a, longitude_a, latitude_b, longitude_b)
    if any(pd.isna(value) for value in values):
        return None
    if not _is_valid_coordinate_pair(latitude_a, longitude_a):
        return None
    if not _is_valid_coordinate_pair(latitude_b, longitude_b):
        return None

    lat_a, lon_a, lat_b, lon_b = map(float, values)
    lat_a, lon_a, lat_b, lon_b = map(
        math.radians, (lat_a, lon_a, lat_b, lon_b)
    )
    delta_lat = lat_b - lat_a
    delta_lon = lon_b - lon_a
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a)
        * math.cos(lat_b)
        * math.sin(delta_lon / 2) ** 2
    )
    central_angle = 2 * math.asin(math.sqrt(min(1.0, haversine)))
    return EARTH_RADIUS_KM * central_angle


def validate_geographic_reference(reference: pd.DataFrame) -> pd.DataFrame:
    """Valide le schéma, l'unicité et les coordonnées du référentiel local."""
    validate_columns(reference, REFERENCE_COLUMNS)
    result = reference.loc[:, REFERENCE_COLUMNS].copy()
    for optional_column in ("companies", "stage_ids"):
        if optional_column in reference.columns:
            result[optional_column] = reference[optional_column]
    result["city"] = result["city"].map(_normalized_text)
    result["country"] = result["country"].map(_normalized_text)
    if result["city"].isna().any():
        raise GeographicReferenceError(
            "Le référentiel contient une destination sans ville exploitable."
        )

    expected_ids = [
        destination_id(city, country) for city, country in zip(
            result["city"], result["country"]
        )
    ]
    supplied_ids = result["destination_id"].astype("string").tolist()
    if supplied_ids != expected_ids:
        raise GeographicReferenceError(
            "Une clé de destination ne correspond pas à la ville et au pays."
        )
    if result["destination_id"].duplicated().any():
        raise GeographicReferenceError(
            "Le référentiel contient des destinations dupliquées."
        )

    statuses = result["status"].astype("string").str.strip().str.lower()
    statuses = statuses.replace({"resolved": "located"})
    if statuses.isna().any() or not statuses.isin(REFERENCE_STATUSES).all():
        raise GeographicReferenceError(
            "Le référentiel contient un statut de géocodage non reconnu."
        )
    result["status"] = statuses

    raw_latitude = result["latitude"]
    raw_longitude = result["longitude"]
    latitude = pd.to_numeric(raw_latitude, errors="coerce")
    longitude = pd.to_numeric(raw_longitude, errors="coerce")
    latitude_present = raw_latitude.notna() & raw_latitude.astype(
        "string"
    ).str.strip().ne("")
    longitude_present = raw_longitude.notna() & raw_longitude.astype(
        "string"
    ).str.strip().ne("")
    coordinate_text_present = latitude_present | longitude_present
    coordinate_pair_valid = pd.Series(
        [
            _is_valid_coordinate_pair(lat, lon)
            for lat, lon in zip(latitude, longitude)
        ],
        index=result.index,
        dtype=bool,
    )
    coordinate_pair_valid &= latitude.notna() & longitude.notna()

    validated = (
        result["validated"]
        .astype("string")
        .str.strip()
        .str.lower()
        .isin(("true", "1", "yes", "oui"))
    )
    metadata_present = (
        result["coordinate_source"].notna()
        & result["coordinate_source"].astype("string").str.strip().ne("")
        & result["verified_at"].notna()
        & result["verified_at"].astype("string").str.strip().ne("")
    )

    resolution_status: list[str] = []
    for position, status in enumerate(result["status"].tolist()):
        has_coordinates = bool(coordinate_text_present.iloc[position])
        valid_pair = bool(coordinate_pair_valid.iloc[position])
        if status == "ambiguous":
            resolution_status.append("ambiguous_reference")
        elif has_coordinates and not valid_pair:
            resolution_status.append("invalid_coordinates")
        elif status == "located" and (
            not valid_pair
            or not bool(validated.iloc[position])
            or not bool(metadata_present.iloc[position])
        ):
            resolution_status.append("unvalidated")
        elif status == "located":
            resolution_status.append("located")
        else:
            resolution_status.append(status)

    result["latitude"] = latitude.where(coordinate_pair_valid)
    result["longitude"] = longitude.where(coordinate_pair_valid)
    result["resolution_status"] = resolution_status
    return result


def load_geographic_reference(
    path: str | Path,
) -> pd.DataFrame:
    """Charge et valide un référentiel CSV local, sans appel réseau."""
    source = Path(path)
    if not source.is_file():
        raise GeographicReferenceError(
            f"Référentiel géographique absent : {source.name}"
        )
    try:
        reference = pd.read_csv(source)
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as exc:
        raise GeographicReferenceError(
            f"Impossible de lire le référentiel géographique : {source.name}"
        ) from exc
    return validate_geographic_reference(reference)


def _distance_band(distance: float) -> str:
    for label, lower, upper in DISTANCE_BANDS:
        if lower <= distance < upper:
            return label
    raise ValueError("La distance doit être positive ou nulle et finie.")


def aggregate_geography(
    data: pd.DataFrame,
    reference: pd.DataFrame,
    school_latitude: float = SCHOOL_LATITUDE,
    school_longitude: float = SCHOOL_LONGITUDE,
) -> GeographyResult:
    """Associe les conventions à des destinations puis retourne des agrégats."""
    validate_columns(data, (CONVENTION_COLUMN, CITY_COLUMN, COUNTRY_COLUMN))
    if not _is_valid_coordinate_pair(school_latitude, school_longitude):
        raise ValueError("Les coordonnées de référence de l'école sont invalides.")
    checked_reference = validate_geographic_reference(reference)
    reference_by_id = checked_reference.set_index("destination_id")
    source = data.loc[:, [CONVENTION_COLUMN, CITY_COLUMN, COUNTRY_COLUMN]]

    convention_destinations: dict[object, set[str]] = {}
    convention_country_values: dict[object, set[str]] = {}
    source_labels: dict[str, tuple[str, str | None]] = {}
    for convention, city, country in source.itertuples(index=False, name=None):
        if pd.isna(convention):
            continue
        normalized_city = _normalized_text(city)
        normalized_country = _normalized_text(country)
        if normalized_country is not None:
            convention_country_values.setdefault(convention, set()).add(
                normalized_country
            )
        if normalized_city is None:
            continue
        identifier = destination_id(normalized_city, normalized_country)
        if identifier is None:
            continue
        convention_destinations.setdefault(convention, set()).add(identifier)
        source_labels.setdefault(
            identifier, (normalized_city, normalized_country)
        )

    total_conventions = int(source[CONVENTION_COLUMN].nunique(dropna=True))
    status_by_convention: dict[object, str] = {}
    located_by_destination: dict[str, set[object]] = {}
    for convention in source[CONVENTION_COLUMN].dropna().drop_duplicates():
        destination_ids = convention_destinations.get(convention, set())
        if len(destination_ids) > 1:
            status_by_convention[convention] = "ambiguous"
        elif not destination_ids:
            status_by_convention[convention] = "missing_destination"
        else:
            identifier = next(iter(destination_ids))
            if identifier not in reference_by_id.index:
                status_by_convention[convention] = "not_in_reference"
            else:
                resolution = str(
                    reference_by_id.at[identifier, "resolution_status"]
                )
                status_by_convention[convention] = resolution
                if resolution == "located":
                    located_by_destination.setdefault(identifier, set()).add(
                        convention
                    )

    status_counts = {
        status: sum(value == status for value in status_by_convention.values())
        for status in STATUS_LABELS
    }
    status_frame = pd.DataFrame(
        [
            {
                "status": status,
                "label": label,
                "convention_count": status_counts[status],
                "denominator": total_conventions,
                "percentage": (
                    status_counts[status] * 100 / total_conventions
                    if total_conventions
                    else None
                ),
            }
            for status, label in STATUS_LABELS.items()
        ]
    )

    destination_rows: list[dict[str, Any]] = []
    for identifier, conventions in located_by_destination.items():
        reference_row = reference_by_id.loc[identifier]
        distance = haversine_km(
            reference_row["latitude"],
            reference_row["longitude"],
            school_latitude,
            school_longitude,
        )
        if distance is None or not math.isfinite(distance):
            continue
        city, country = source_labels[identifier]
        destination_rows.append(
            {
                "destination_id": identifier,
                "city": city,
                "country": country,
                "convention_count": len(conventions),
                "latitude": float(reference_row["latitude"]),
                "longitude": float(reference_row["longitude"]),
                "distance_km": distance,
                "distance_band": _distance_band(distance),
                "companies": (
                    _reference_values(reference_row["companies"], "companies")
                    if "companies" in reference_by_id.columns
                    else []
                ),
                "stage_ids": (
                    _reference_values(reference_row["stage_ids"], "stage_ids")
                    if "stage_ids" in reference_by_id.columns
                    else []
                ),
            }
        )
    destinations = pd.DataFrame(
        destination_rows,
        columns=(
            "destination_id",
            "city",
            "country",
            "convention_count",
            "latitude",
            "longitude",
            "distance_km",
            "distance_band",
            "companies",
            "stage_ids",
        ),
    )

    country_counts: dict[str, set[object]] = {}
    ambiguous_country_conventions = 0
    missing_country_conventions = 0
    for convention in source[CONVENTION_COLUMN].dropna().drop_duplicates():
        countries = convention_country_values.get(convention, set())
        if len(countries) > 1:
            ambiguous_country_conventions += 1
            continue
        if not countries:
            missing_country_conventions += 1
            continue
        country = next(iter(countries))
        country_counts.setdefault(country, set()).add(convention)
    country_denominator = sum(len(conventions) for conventions in country_counts.values())
    country_rows = [
        {
            "country": country,
            "category_is_missing": False,
            "convention_count": len(conventions),
            "denominator": country_denominator,
            "percentage": (
                len(conventions) * 100 / country_denominator
                if country_denominator
                else None
            ),
        }
        for country, conventions in country_counts.items()
    ]
    countries_frame = pd.DataFrame(
        country_rows,
        columns=(
            "country",
            "category_is_missing",
            "convention_count",
            "denominator",
            "percentage",
        ),
    )

    localizable_count = len(
        {
            convention
            for conventions in located_by_destination.values()
            for convention in conventions
        }
    )
    distance_rows: list[dict[str, object]] = []
    for label, _, _ in DISTANCE_BANDS:
        count = (
            int(
                destinations.loc[
                    destinations["distance_band"] == label, "convention_count"
                ].sum()
            )
            if not destinations.empty
            else 0
        )
        distance_rows.append(
            {
                "distance_band": label,
                "convention_count": count,
                "denominator": localizable_count,
                "percentage": (
                    count * 100 / localizable_count
                    if localizable_count
                    else None
                ),
            }
        )

    usable_destination_count = sum(
        len(ids) == 1 for ids in convention_destinations.values()
    )
    coverage_percentage = (
        localizable_count * 100 / total_conventions
        if total_conventions
        else None
    )
    summary: dict[str, int | float | None] = {
        "total_conventions": total_conventions,
        "destination_available_conventions": usable_destination_count,
        "located_conventions": localizable_count,
        "not_located_conventions": total_conventions - localizable_count,
        "coverage_percentage": coverage_percentage,
        "localized_destinations": len(located_by_destination),
        "ambiguous_conventions": status_counts["ambiguous"],
        "ambiguous_country_conventions": ambiguous_country_conventions,
        "missing_country_conventions": missing_country_conventions,
        "country_denominator": country_denominator,
    }
    return GeographyResult(
        summary=summary,
        status_counts=status_frame,
        destinations=destinations,
        countries=countries_frame,
        distance_bands=pd.DataFrame(distance_rows),
    )
