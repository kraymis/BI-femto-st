"""Tests des agrégations V2 sur des jeux synthétiques uniquement."""

from pathlib import Path
import sys
import unittest

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bi.analytics import (  # noqa: E402
    convention_crosstab,
    crosstab_row_percentages,
    crosstab_with_totals,
    filter_aggregated_categories,
    yearly_field_coverage,
)
from bi.ingestion import MissingColumnsError  # noqa: E402


def make_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n_convention_de_stage": ["C-1", "C-1", "C-2", "C-3", "C-4"],
            "annee_academique": [
                "2024/2025",
                "2024/2025",
                "2024/2025",
                "2023/2024",
                None,
            ],
            "type_de_stage": ["PFE", "PFE", "SIB", "PFE", None],
            "nature_du_stage": [
                "Entreprise",
                "Entreprise",
                "Laboratoire",
                None,
                "Entreprise",
            ],
        }
    )


class CrosstabTests(unittest.TestCase):
    def test_year_by_type_counts_distinct_conventions(self) -> None:
        result = convention_crosstab(
            make_data(), "annee_academique", "type_de_stage"
        )
        self.assertEqual(int(result.loc["2024/2025", "PFE"]), 1)
        self.assertEqual(int(result.loc["2024/2025", "SIB"]), 1)
        self.assertEqual(int(result.loc["2023/2024", "PFE"]), 1)
        self.assertEqual(int(result.loc["2024/2025"].sum()), 2)

    def test_type_by_nature_includes_missing_and_row_percentages_sum_to_100(
        self,
    ) -> None:
        counts = convention_crosstab(
            make_data(), "type_de_stage", "nature_du_stage"
        )
        self.assertEqual(int(counts.loc["PFE"].sum()), 2)
        self.assertEqual(int(counts.loc["SIB"].sum()), 1)
        self.assertIn("Non renseigné", counts.columns)

        percentages = crosstab_row_percentages(counts)
        for _, row in percentages.iterrows():
            self.assertAlmostEqual(float(row.sum()), 100.0)

    def test_missing_label_does_not_collide_with_source_category(self) -> None:
        data = pd.DataFrame(
            {
                "n_convention_de_stage": ["C-1", "C-2"],
                "type_de_stage": ["Non renseigné", None],
                "nature_du_stage": ["A", "A"],
            }
        )
        result = convention_crosstab(
            data, "type_de_stage", "nature_du_stage"
        )
        self.assertEqual(len(result.index), 2)
        self.assertIn("Non renseigné", result.index)
        self.assertIn("Non renseigné (valeur absente)", result.index)

    def test_empty_crosstab_preserves_schema_labels(self) -> None:
        empty = make_data().iloc[0:0]
        result = convention_crosstab(
            empty, "annee_academique", "type_de_stage"
        )
        self.assertTrue(result.empty)
        self.assertEqual(result.index.name, "annee_academique")
        self.assertEqual(result.columns.name, "type_de_stage")
        self.assertTrue(crosstab_row_percentages(result).empty)

    def test_missing_required_column_is_reported(self) -> None:
        data = pd.DataFrame({"n_convention_de_stage": ["C-1"]})
        with self.assertRaises(MissingColumnsError):
            convention_crosstab(data, "missing_row", "missing_column")

    def test_totals_match_distinct_conventions_without_cell_double_count(self) -> None:
        counts = convention_crosstab(
            make_data(), "annee_academique", "type_de_stage"
        )
        totals = crosstab_with_totals(counts)
        self.assertEqual(
            int(totals.loc["Total", "Total conventions"]), 4
        )
        self.assertEqual(int(totals.loc["2024/2025", "Total conventions"]), 2)

    def test_ambiguous_convention_category_assignment_is_rejected(self) -> None:
        data = pd.DataFrame(
            {
                "n_convention_de_stage": ["C-1", "C-1"],
                "annee_academique": ["2024/2025", "2024/2025"],
                "type_de_stage": ["PFE", "SIB"],
            }
        )
        with self.assertRaisesRegex(ValueError, "plusieurs modalités"):
            convention_crosstab(
                data, "annee_academique", "type_de_stage"
            )


class QualityAggregationTests(unittest.TestCase):
    def test_yearly_coverage_includes_unknown_year_and_uses_row_denominators(
        self,
    ) -> None:
        result = yearly_field_coverage(
            make_data(), "annee_academique", ["nature_du_stage"]
        )
        unknown_year = result.loc[
            result["academic_year"] == "Non renseigné"
        ].iloc[0]
        self.assertEqual(int(unknown_year["denominator"]), 1)
        self.assertEqual(int(unknown_year["missing_count"]), 0)
        self.assertEqual(float(unknown_year["completion_percentage"]), 100.0)

        pfe_year = result.loc[
            result["academic_year"] == "2024/2025"
        ].iloc[0]
        self.assertEqual(int(pfe_year["denominator"]), 3)
        self.assertEqual(int(pfe_year["present_count"]), 3)
        self.assertAlmostEqual(
            float(pfe_year["completion_percentage"]), 100.0
        )

    def test_yearly_coverage_handles_empty_and_missing_field(self) -> None:
        empty = make_data().iloc[0:0]
        result = yearly_field_coverage(
            empty, "annee_academique", ["nature_du_stage"]
        )
        self.assertTrue(result.empty)
        with self.assertRaises(MissingColumnsError):
            yearly_field_coverage(empty, "annee_academique", ["absent"])

    def test_category_search_only_filters_aggregate_rows(self) -> None:
        aggregated = pd.DataFrame(
            {
                "label": ["PFE", "SIB", "Stage en entreprise"],
                "convention_count": [2, 1, 3],
            }
        )
        result = filter_aggregated_categories(
            aggregated, ["label"], "stage"
        )
        self.assertEqual(result["label"].tolist(), ["Stage en entreprise"])
        self.assertEqual(len(filter_aggregated_categories(
            aggregated, ["label"], ""
        )), 3)


if __name__ == "__main__":
    unittest.main()
