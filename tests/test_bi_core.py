"""Tests synthétiques du socle BI, sans dépendance au classeur réel."""

from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bi.config import PROJECT_ROOT as CONFIGURED_PROJECT_ROOT  # noqa: E402
from bi.config import STAGES_SOURCE_FILE  # noqa: E402
from bi.analytics import (  # noqa: E402
    count_conventions,
    count_conventions_by_category,
    count_rate,
    count_students,
    field_coverage,
    filter_stages,
    quality_summary,
)
from bi.ingestion import (  # noqa: E402
    DataFileError,
    MissingColumnsError,
    load_stages,
    validate_columns,
)


def make_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n_convention_de_stage": ["C-1", "C-1", "C-2", None],
            "n_etudiant": ["E-1", "E-1", "E-2", None],
            "annee_academique": ["2024/2025", "2024/2025", None, "2023/2024"],
            "type_de_stage": ["PFE", "PFE", None, "SIB"],
            "nature_du_stage": [
                "Stage en entreprise",
                None,
                "Stage en laboratoire",
                None,
            ],
        }
    )


class AnalyticsTests(unittest.TestCase):
    def test_config_paths_are_anchored_to_project(self) -> None:
        self.assertEqual(CONFIGURED_PROJECT_ROOT, PROJECT_ROOT)
        self.assertEqual(
            STAGES_SOURCE_FILE,
            PROJECT_ROOT / "data" / "raw" / "stages_cleaned2.xlsx",
        )

    def test_counts_distinct_conventions_and_students(self) -> None:
        data = make_data()
        self.assertEqual(count_conventions(data), 2)
        self.assertEqual(count_students(data), 2)

    def test_category_counts_include_missing_and_explicit_denominator(self) -> None:
        result = count_conventions_by_category(
            make_data(), "nature_du_stage"
        )

        missing = result.loc[result["category_is_missing"]].iloc[0]
        known = result.loc[~result["category_is_missing"]]
        self.assertEqual(int(missing["convention_count"]), 1)
        self.assertEqual(int(missing["denominator"]), 2)
        self.assertAlmostEqual(float(missing["percentage"]), 50.0)
        self.assertEqual(int(known["convention_count"].sum()), 2)
        self.assertTrue((known["denominator"] == 2).all())

    def test_category_counts_can_exclude_missing_with_known_denominator(self) -> None:
        result = count_conventions_by_category(
            make_data(), "nature_du_stage", include_missing=False
        )
        self.assertEqual(len(result), 2)
        self.assertTrue((result["denominator"] == 2).all())
        self.assertFalse(result["category_is_missing"].any())

    def test_coverage_uses_row_denominator_and_reports_empty_input(self) -> None:
        data = make_data()
        coverage = field_coverage(data, ["nature_du_stage"]).iloc[0]
        self.assertEqual(int(coverage["present_count"]), 2)
        self.assertEqual(int(coverage["missing_count"]), 2)
        self.assertEqual(int(coverage["denominator"]), 4)
        self.assertEqual(float(coverage["completion_percentage"]), 50.0)

        empty = field_coverage(data.iloc[0:0], ["nature_du_stage"]).iloc[0]
        self.assertEqual(int(empty["denominator"]), 0)
        self.assertIsNone(empty["completion_percentage"])

    def test_count_rate_handles_zero_denominator_explicitly(self) -> None:
        result = count_rate(0, 0)
        self.assertEqual(result.count, 0)
        self.assertEqual(result.denominator, 0)
        self.assertIsNone(result.percentage)
        with self.assertRaises(ValueError):
            count_rate(1, 0)

    def test_filters_support_single_combined_missing_and_empty_selection(self) -> None:
        data = make_data()

        year_result = filter_stages(
            data,
            academic_years=["2024/2025"],
            include_missing_year=False,
        )
        self.assertEqual(len(year_result), 2)

        combined = filter_stages(
            data,
            academic_years=["2024/2025"],
            stage_types=["PFE"],
            stage_natures=["Stage en entreprise"],
            include_missing_nature=False,
        )
        self.assertEqual(len(combined), 1)
        self.assertEqual(
            combined["n_convention_de_stage"].iloc[0], "C-1"
        )

        with_missing = filter_stages(
            data,
            stage_types=["PFE"],
            include_missing_type=True,
        )
        without_missing = filter_stages(
            data,
            stage_types=["PFE"],
            include_missing_type=False,
        )
        self.assertEqual(len(with_missing), 3)
        self.assertEqual(len(without_missing), 2)

        empty = filter_stages(data, stage_types=[])
        self.assertTrue(empty.empty)
        self.assertTrue(data.index.equals(pd.RangeIndex(4)))

        missing_only = filter_stages(
            data,
            stage_types=[None],
        )
        self.assertEqual(len(missing_only), 1)
        self.assertTrue(missing_only["type_de_stage"].isna().all())

        empty_with_missing_enabled = filter_stages(
            data,
            stage_types=[],
            include_missing_type=True,
        )
        self.assertTrue(empty_with_missing_enabled.empty)

    def test_no_match_returns_empty_and_none_means_no_restriction(self) -> None:
        data = make_data()
        no_match = filter_stages(
            data,
            stage_types=["UNKNOWN"],
            include_missing_type=False,
        )
        unrestricted = filter_stages(data)
        self.assertTrue(no_match.empty)
        self.assertEqual(len(unrestricted), len(data))

    def test_filters_require_only_columns_used_by_active_filters(self) -> None:
        data = pd.DataFrame({"n_convention_de_stage": ["C-1"]})
        self.assertEqual(len(filter_stages(data)), 1)
        with self.assertRaises(MissingColumnsError):
            filter_stages(data, stage_types=["PFE"])

    def test_quality_summary_is_aggregate_and_marks_unavailable_fields(self) -> None:
        data = make_data()
        summary = quality_summary(
            data,
            tracked_fields=["n_convention_de_stage", "not_in_schema"],
        )
        self.assertEqual(summary["row_count"], 4)
        self.assertEqual(summary["convention_count"], 2)
        self.assertEqual(summary["student_count"], 2)
        self.assertEqual(summary["exact_duplicate_rows"], 0)
        self.assertEqual(summary["unavailable_fields"], ("not_in_schema",))
        self.assertEqual(
            list(summary["field_coverage"]["field"]),
            ["n_convention_de_stage"],
        )

    def test_required_and_optional_columns_are_distinguished(self) -> None:
        optional_missing = validate_columns(
            pd.DataFrame({"required": [1]}),
            required_columns=["required"],
            optional_columns=["optional"],
        )
        self.assertEqual(optional_missing, ("optional",))
        with self.assertRaises(MissingColumnsError) as context:
            validate_columns(
                pd.DataFrame({"optional": [1]}),
                required_columns=["required"],
                optional_columns=["optional"],
            )
        self.assertEqual(context.exception.missing_columns, ("required",))


class IngestionTests(unittest.TestCase):
    def test_missing_source_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "missing.xlsx"
            with self.assertRaisesRegex(DataFileError, "Fichier source absent"):
                load_stages(missing)

    def test_unreadable_source_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            invalid = Path(temporary_directory) / "invalid.xlsx"
            invalid.write_bytes(b"not an excel workbook")
            with self.assertRaisesRegex(
                DataFileError, "Impossible de lire le fichier source"
            ):
                load_stages(invalid)

    def test_excel_is_read_and_schema_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workbook = Path(temporary_directory) / "synthetic.xlsx"
            pd.DataFrame(
                {
                    "n_convention_de_stage": ["C-1"],
                    "optional_field": ["value"],
                }
            ).to_excel(workbook, index=False)

            loaded = load_stages(
                workbook,
                required_columns=["n_convention_de_stage"],
                optional_columns=["optional_field", "not_present"],
            )
            self.assertEqual(len(loaded), 1)
            self.assertEqual(
                validate_columns(
                    loaded,
                    required_columns=["n_convention_de_stage"],
                    optional_columns=["optional_field", "not_present"],
                ),
                ("not_present",),
            )
            with self.assertRaises(MissingColumnsError):
                load_stages(workbook, required_columns=["required_field"])


if __name__ == "__main__":
    unittest.main()
