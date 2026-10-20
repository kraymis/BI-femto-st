"""Tests géographiques avec des destinations synthétiques uniquement."""

from pathlib import Path
import json
import sys
import tempfile
import unittest

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bi.analytics.geography import (  # noqa: E402
    GeographicReferenceError,
    aggregate_geography,
    destination_id,
    _distance_band,
    haversine_km,
    load_geographic_reference,
    validate_geographic_reference,
)
from bi.analytics.filters import filter_stages  # noqa: E402
from bi.ingestion import MissingColumnsError  # noqa: E402
from bi.preprocessing.geographic_reference import (  # noqa: E402
    build_geographic_reference_template,
    write_geographic_reference_template,
)


REFERENCE_COLUMNS = [
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
]


def reference_row(
    city: str,
    country: str,
    latitude: object = "",
    longitude: object = "",
    status: str = "pending",
    validated: bool = False,
) -> dict[str, object]:
    return {
        "destination_id": destination_id(city, country),
        "source_city_label": city,
        "source_country_label": country,
        "city": city,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "status": status,
        "coordinate_source": "Synthetic test reference" if validated else "",
        "verified_at": "2026-01-01" if validated else "",
        "validated": validated,
    }


def make_reference() -> pd.DataFrame:
    return pd.DataFrame(
        [
            reference_row(
                "Besançon", "France", 47.250944, 5.9942287, "located", True
            ),
            reference_row(
                "Paris", "France", 48.8566, 2.3522, "located", True
            ),
            reference_row(
                "BadCoordinates", "Pays X", 91, 181, "located", True
            ),
            reference_row("PendingTown", "Pays Y"),
            reference_row(
                "AmbiguousTown", "Pays W", status="ambiguous"
            ),
        ],
        columns=REFERENCE_COLUMNS,
    )


def make_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n_convention_de_stage": [
                "SYN-1",
                "SYN-1",
                "SYN-2",
                "SYN-3",
                "SYN-4",
                "SYN-4",
                "SYN-5",
                "SYN-6",
                "SYN-7",
                "SYN-8",
                "SYN-9",
            ],
            "ville_lieu_stage": [
                " Besançon ",
                "Besançon",
                "Paris",
                None,
                "Lyon",
                "Bâle",
                "VilleAbsenteDuRéférentiel",
                "BadCoordinates",
                "PendingTown",
                "AmbiguousTown",
                None,
            ],
            "pays_lieu_stage": [
                "France",
                "France",
                "France",
                "Pays Z",
                "France",
                "Suisse",
                "Pays X",
                "Pays X",
                "Pays Y",
                "Pays W",
                None,
            ],
            "annee_academique": [
                "2024/2025",
                "2024/2025",
                "2023/2024",
                "2023/2024",
                "2024/2025",
                "2024/2025",
                "2023/2024",
                "2023/2024",
                "2024/2025",
                "2024/2025",
                "2023/2024",
            ],
            "type_de_stage": [
                "PFE",
                "PFE",
                "SIB",
                "PFE",
                "PFE",
                "PFE",
                "PFE",
                "PFE",
                "SIB",
                "PFE",
                "SIB",
            ],
            "nature_du_stage": [
                "Entreprise",
                None,
                "Entreprise",
                "Entreprise",
                "Laboratoire",
                None,
                "Entreprise",
                "Entreprise",
                "Laboratoire",
                "Entreprise",
                "Entreprise",
            ],
        }
    )


class HaversineTests(unittest.TestCase):
    def test_same_point_is_zero(self) -> None:
        self.assertEqual(haversine_km(47.25, 5.99, 47.25, 5.99), 0.0)

    def test_known_distance_and_symmetry(self) -> None:
        distance = haversine_km(0, 0, 0, 1)
        self.assertIsNotNone(distance)
        self.assertAlmostEqual(float(distance), 111.195, delta=0.02)
        self.assertAlmostEqual(
            float(haversine_km(0, 1, 0, 0)), float(distance), places=9
        )

    def test_missing_nonnumeric_and_out_of_range_coordinates_are_not_calculated(
        self,
    ) -> None:
        self.assertIsNone(haversine_km(None, 0, 0, 0))
        self.assertIsNone(haversine_km("unknown", 0, 0, 0))
        self.assertIsNone(haversine_km(91, 0, 0, 0))
        self.assertIsNone(haversine_km(0, 181, 0, 0))
        self.assertIsNone(haversine_km(float("inf"), 0, 0, 0))

    def test_distance_band_boundaries_are_explicit(self) -> None:
        self.assertEqual(_distance_band(24.999), "Moins de 25 km")
        self.assertEqual(_distance_band(25), "25 à moins de 100 km")
        self.assertEqual(_distance_band(100), "100 à moins de 300 km")
        self.assertEqual(_distance_band(300), "300 km et plus")
        with self.assertRaises(ValueError):
            _distance_band(float("inf"))


class GeographicReferenceTests(unittest.TestCase):
    def test_valid_reference_loads(self) -> None:
        reference = validate_geographic_reference(make_reference())
        self.assertEqual(
            reference.loc[reference["city"] == "Paris", "resolution_status"].item(),
            "located",
        )

    def test_valid_csv_reference_loads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.csv"
            reference = make_reference()
            reference.loc[
                reference["status"] == "located", "status"
            ] = "resolved"
            reference.to_csv(path, index=False)
            loaded = load_geographic_reference(path)
        self.assertTrue((loaded.loc[
            loaded["resolution_status"] == "located", "status"
        ] == "located").all())
        self.assertEqual(len(loaded), len(make_reference()))

    def test_destination_aggregation_keeps_conventions_with_company_names(
        self,
    ) -> None:
        reference = make_reference()
        reference["companies"] = ""
        reference["stage_ids"] = ""
        paris_index = reference.index[reference["city"] == "Paris"][0]
        reference.at[paris_index, "companies"] = json.dumps(
            ["Entreprise synthétique A", "Entreprise synthétique B"]
        )
        reference.at[paris_index, "stage_ids"] = json.dumps(["CONV-SYN-1"])

        data = make_data()
        data["entreprise"] = [
            "Entreprise synthétique A",
            "Entreprise synthétique A",
            "Entreprise synthétique B",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]

        result = aggregate_geography(data, reference)
        besancon = result.destinations.loc[
            result.destinations["city"] == "Besançon"
        ]
        self.assertEqual(
            besancon["conventions"].item(),
            [
                {
                    "convention_id": "SYN-1",
                    "companies": ["Entreprise synthétique A"],
                }
            ],
        )

        paris = result.destinations.loc[result.destinations["city"] == "Paris"]

        self.assertEqual(
            paris["companies"].item(),
            ["Entreprise synthétique A", "Entreprise synthétique B"],
        )
        self.assertEqual(paris["stage_ids"].item(), ["CONV-SYN-1"])

    def test_invalid_optional_reference_list_is_reported(self) -> None:
        reference = make_reference()
        reference["stage_ids"] = ""
        paris_index = reference.index[reference["city"] == "Paris"][0]
        reference.at[paris_index, "stage_ids"] = "not-json"

        with self.assertRaisesRegex(
            GeographicReferenceError, "stage_ids"
        ):
            aggregate_geography(make_data(), reference)

    def test_missing_file_and_required_columns_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                GeographicReferenceError, "absent"
            ):
                load_geographic_reference(Path(directory) / "missing.csv")

        with self.assertRaises(MissingColumnsError):
            validate_geographic_reference(pd.DataFrame({"city": ["Paris"]}))

    def test_duplicate_destination_is_rejected(self) -> None:
        row = reference_row("Paris", "France")
        with self.assertRaisesRegex(
            GeographicReferenceError, "dupliquées"
        ):
            validate_geographic_reference(
                pd.DataFrame([row, row], columns=REFERENCE_COLUMNS)
            )

    def test_invalid_and_unverified_coordinates_have_distinct_statuses(self) -> None:
        checked = validate_geographic_reference(make_reference())
        invalid = checked.loc[
            checked["city"] == "BadCoordinates", "resolution_status"
        ].item()
        pending = checked.loc[
            checked["city"] == "PendingTown", "resolution_status"
        ].item()
        self.assertEqual(invalid, "invalid_coordinates")
        self.assertEqual(pending, "pending")
        unverified = validate_geographic_reference(
            pd.DataFrame(
                [
                    reference_row(
                        "UnverifiedTown",
                        "Pays Q",
                        48.0,
                        2.0,
                        status="located",
                        validated=False,
                    )
                ],
                columns=REFERENCE_COLUMNS,
            )
        )
        self.assertEqual(
            unverified["resolution_status"].item(), "unvalidated"
        )

    def test_manual_template_is_destination_level_and_contains_no_personal_fields(
        self,
    ) -> None:
        data = make_data().assign(
            n_etudiant=["private"] * len(make_data()),
            courriel=["private@example.test"] * len(make_data()),
        )
        template = build_geographic_reference_template(data)
        self.assertEqual(template["destination_id"].nunique(), len(template))
        self.assertNotIn("n_convention_de_stage", template.columns)
        self.assertNotIn("n_etudiant", template.columns)
        self.assertNotIn("courriel", template.columns)
        self.assertTrue(template["latitude"].eq("").all())
        self.assertTrue(template["longitude"].eq("").all())

    def test_template_writer_refuses_to_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reference.csv"
            write_geographic_reference_template(make_data(), output)
            with self.assertRaises(FileExistsError):
                write_geographic_reference_template(make_data(), output)


class GeographicAggregationTests(unittest.TestCase):
    def test_distinct_conventions_coverage_and_unresolved_reasons(self) -> None:
        result = aggregate_geography(make_data(), make_reference())
        self.assertEqual(result.summary["total_conventions"], 9)
        self.assertEqual(result.summary["located_conventions"], 2)
        self.assertEqual(result.summary["not_located_conventions"], 7)
        self.assertEqual(result.summary["destination_available_conventions"], 6)
        self.assertEqual(result.summary["localized_destinations"], 2)
        self.assertAlmostEqual(result.summary["coverage_percentage"], 200 / 9)
        self.assertEqual(result.summary["country_denominator"], 7)
        self.assertEqual(result.summary["missing_country_conventions"], 1)
        france = result.countries.loc[
            result.countries["country"] == "France"
        ].iloc[0]
        self.assertEqual(int(france["convention_count"]), 2)

        statuses = result.status_counts.set_index("status")["convention_count"]
        self.assertEqual(int(statuses["missing_destination"]), 2)
        self.assertEqual(int(statuses["ambiguous"]), 1)
        self.assertEqual(int(statuses["not_in_reference"]), 1)
        self.assertEqual(int(statuses["invalid_coordinates"]), 1)
        self.assertEqual(int(statuses["pending"]), 1)
        self.assertEqual(int(statuses["ambiguous_reference"]), 1)
        self.assertAlmostEqual(float(result.countries["percentage"].sum()), 100)

    def test_repeated_rows_do_not_double_count_and_output_has_no_ids(self) -> None:
        result = aggregate_geography(make_data(), make_reference())
        besancon = result.destinations.loc[
            result.destinations["city"] == "Besançon"
        ].iloc[0]
        self.assertEqual(int(besancon["convention_count"]), 1)
        self.assertNotIn("n_convention_de_stage", result.destinations.columns)
        self.assertNotIn("n_etudiant", result.destinations.columns)

    def test_distance_bands_have_localized_convention_denominator(self) -> None:
        result = aggregate_geography(make_data(), make_reference())
        bands = result.distance_bands.set_index("distance_band")
        self.assertEqual(int(bands.loc["Moins de 25 km", "convention_count"]), 1)
        self.assertEqual(int(bands.loc["300 km et plus", "convention_count"]), 1)
        self.assertTrue((bands["denominator"] == 2).all())
        self.assertAlmostEqual(float(bands["percentage"].sum()), 100.0)

    def test_empty_input_has_zero_denominator_and_no_fake_zero_distance(self) -> None:
        empty = make_data().iloc[0:0]
        result = aggregate_geography(empty, make_reference())
        self.assertEqual(result.summary["total_conventions"], 0)
        self.assertIsNone(result.summary["coverage_percentage"])
        self.assertTrue(result.destinations.empty)
        self.assertTrue(result.distance_bands["percentage"].isna().all())

    def test_invalid_school_reference_coordinates_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "coordonnées"):
            aggregate_geography(
                make_data(), make_reference(), school_latitude=95
            )

    def test_shared_global_filter_updates_geographic_counts(self) -> None:
        filtered = filter_stages(make_data(), stage_types=("SIB",))
        result = aggregate_geography(filtered, make_reference())
        self.assertEqual(result.summary["total_conventions"], 3)
        self.assertEqual(result.summary["located_conventions"], 1)


if __name__ == "__main__":
    unittest.main()
