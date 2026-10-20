"""Tests synthétiques de l'API V1, sans lecture du classeur réel."""

from collections.abc import Iterator
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.main import app
from backend.app.services import dashboard
from bi.analytics.geography import REFERENCE_COLUMNS, destination_id
from bi.ingestion import DataFileError, MissingColumnsError


def make_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "n_convention_de_stage": [
                "PRIVATE-CONVENTION-1",
                "PRIVATE-CONVENTION-1",
                "PRIVATE-CONVENTION-2",
                "PRIVATE-CONVENTION-3",
            ],
            "n_etudiant": [
                "PRIVATE-STUDENT-1",
                "PRIVATE-STUDENT-1",
                "PRIVATE-STUDENT-2",
                "PRIVATE-STUDENT-3",
            ],
            "annee_academique": [
                "2024/2025",
                "2024/2025",
                "2023/2024",
                None,
            ],
            "type_de_stage": ["PFE", "PFE", "SIB", None],
            "nature_du_stage": [
                "Entreprise",
                None,
                "Laboratoire",
                "Non renseigné",
            ],
            "entreprise": ["ACME", "ACME", "Laboratoire B", None],
            "entreprise_lieu_stage": ["ACME", "ACME", "Laboratoire B", None],
            "date_debut": [None, None, None, None],
            "date_fin": [None, None, None, None],
            "pays_lieu_stage": ["FRANCE", "FRANCE", "FRANCE", None],
            "ville_lieu_stage": ["BESANÇON", "BESANÇON", "LYON", None],
            "cp_lieu_stage": [None, None, None, None],
            "ville": [None, None, None, None],
            "code_postal": [None, None, None, None],
            "date_soutenance": [None, None, None, None],
        }
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    data = make_data()
    app.dependency_overrides[dashboard.get_dashboard_data] = lambda: data
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_does_not_load_source_or_expose_local_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_loaded() -> pd.DataFrame:
        raise AssertionError("health ne doit pas charger le classeur")

    monkeypatch.setattr(dashboard, "load_stages", fail_if_loaded)
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_filter_options_include_missing_as_explicit_option(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/filters/options")

    assert response.status_code == 200
    options = response.json()
    assert options["academic_years"][-1] == {
        "value": None,
        "label": "Non renseigné",
        "is_missing": True,
    }
    assert options["stage_types"][-1]["is_missing"] is True
    assert options["stage_natures"][-1]["label"] == (
        "Non renseigné (valeur absente)"
    )
    assert any(
        option["value"] == "Non renseigné" and not option["is_missing"]
        for option in options["stage_natures"]
    )


def test_overview_reuses_distinct_convention_and_student_counts(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"] == {
        "row_count": 4,
        "convention_count": 3,
        "student_count": 3,
        "academic_year_count": 2,
        "stage_type_count": 2,
    }
    assert body["yearly_conventions"][0]["category"] == "2023/2024"
    missing_year = body["yearly_conventions"][-1]
    assert missing_year["category_is_missing"] is True
    assert missing_year["denominator"] == 3
    assert all(
        row["denominator"] == 3
        for row in body["conventions_by_nature"]
    )
    assert sum(
        row["convention_count"] for row in body["conventions_by_nature"]
    ) == 4
    serialized = response.text
    assert "PRIVATE-STUDENT" not in serialized
    assert "PRIVATE-CONVENTION" not in serialized


def test_overview_applies_combined_filters_consistently(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/overview",
        params=[
            ("academic_years", "2024/2025"),
            ("stage_types", "PFE"),
            ("stage_natures", "Entreprise"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"] == {
        "row_count": 1,
        "convention_count": 1,
        "student_count": 1,
        "academic_year_count": 1,
        "stage_type_count": 1,
    }
    assert body["conventions_by_type"][0]["denominator"] == 1
    assert body["conventions_by_nature"][0]["percentage"] == 100.0


def test_overview_can_select_only_missing_values(client: TestClient) -> None:
    response = client.get(
        "/api/v1/overview",
        params={"include_missing_year": "true"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["row_count"] == 1
    assert body["yearly_conventions"] == [
        {
            "category": "Non renseigné",
            "category_is_missing": True,
            "convention_count": 1,
            "denominator": 1,
            "percentage": 100.0,
        }
    ]


def test_overview_unknown_filter_returns_current_empty_result(
    client: TestClient,
) -> None:
    first = client.get(
        "/api/v1/overview", params={"stage_types": "NO-SUCH-CATEGORY"}
    )
    second = client.get(
        "/api/v1/overview",
        params={"academic_years": "NO-SUCH-YEAR", "stage_types": "PFE"},
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["kpis"]["row_count"] == 0
    assert first.json()["kpis"]["convention_count"] == 0
    assert first.json()["yearly_conventions"] == []
    assert second.json()["kpis"]["row_count"] == 0
    assert second.json()["conventions_by_type"] == []


def test_empty_selection_can_be_expressed_without_reusing_old_results(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/overview", params={"include_missing_type": "false"}
    )

    assert response.status_code == 200
    assert response.json()["kpis"]["row_count"] == 0
    assert response.json()["conventions_by_nature"] == []


def test_temporal_endpoint_returns_existing_cross_tab_aggregates(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/temporal")

    assert response.status_code == 200
    body = response.json()
    assert body["yearly_conventions"][0]["category"] == "2023/2024"
    cross_tab = body["year_by_type"]
    assert cross_tab["unavailable"] is False
    assert cross_tab["grand_total"] == 3
    pfe_cell = next(
        cell
        for cell in cross_tab["cells"]
        if cell["row_category"] == "2024/2025"
        and cell["column_category"] == "PFE"
    )
    assert pfe_cell["convention_count"] == 1
    assert pfe_cell["percentage"] == 100.0
    assert response.text.count("PRIVATE-CONVENTION") == 0


def test_temporal_endpoint_returns_empty_results_for_empty_filter(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/temporal",
        params={"academic_years": "NO-SUCH-YEAR"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["yearly_conventions"] == []
    assert body["year_by_type"]["cells"] == []
    assert body["year_by_type"]["grand_total"] == 0


def test_stage_endpoint_applies_multiple_filters_and_preserves_missing(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/stages",
        params=[
            ("academic_years", "2024/2025"),
            ("stage_types", "PFE"),
            ("include_missing_nature", "true"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conventions_by_type"][0]["convention_count"] == 1
    missing_nature = next(
        row
        for row in body["conventions_by_nature"]
        if row["category_is_missing"]
    )
    assert missing_nature["convention_count"] == 1
    assert body["type_by_nature"]["unavailable"] is False
    assert body["type_by_nature"]["grand_total"] == 1


def test_companies_geography_endpoint_exposes_map_convention_details(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reference_path = tmp_path / "geographic_reference.csv"
    city = "BESANÇON"
    country = "FRANCE"
    reference = pd.DataFrame(
        [
            {
                "destination_id": destination_id(city, country),
                "source_city_label": city,
                "source_country_label": country,
                "city": city,
                "country": country,
                "latitude": 47.2378,
                "longitude": 6.0241,
                "status": "located",
                "coordinate_source": "synthetic test",
                "verified_at": "2026-01-01",
                "validated": True,
                "stage_ids": json.dumps(["LEGACY-REFERENCE-ID"]),
                "companies": json.dumps(["ACME"]),
            }
        ],
        columns=[*REFERENCE_COLUMNS, "stage_ids", "companies"],
    )
    reference.to_csv(reference_path, index=False)
    monkeypatch.setattr(dashboard, "GEOGRAPHIC_REFERENCE_FILE", reference_path)
    data = make_data()
    app.dependency_overrides[dashboard.get_dashboard_data] = lambda: data
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/companies-geography")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["companies_available"] is True
    assert body["companies"][0]["category"] == "ACME"
    assert body["geography_available"] is True
    assert any(
        destination["city"] == city
        and destination["convention_count"] == 1
        and destination["conventions"] == [
            {
                "convention_id": "PRIVATE-CONVENTION-1",
                "companies": ["ACME"],
            }
        ]
        for destination in body["destinations"]
    )
    assert "PRIVATE-CONVENTION-1" in response.text
    assert "PRIVATE-STUDENT" not in response.text
    assert "LEGACY-REFERENCE-ID" not in response.text
    assert "destination_id" not in response.text

    monkeypatch.setattr(dashboard, "GEOGRAPHIC_MIN_CONVENTIONS_PER_DESTINATION", 5)
    app.dependency_overrides[dashboard.get_dashboard_data] = lambda: data
    try:
        with TestClient(app) as client:
            suppressed = client.get("/api/v1/companies-geography")
    finally:
        app.dependency_overrides.clear()
    assert suppressed.status_code == 200
    suppressed_body = suppressed.json()
    assert suppressed_body["geography_summary"]["located_conventions"] == 1
    assert suppressed_body["destinations"] == []
    assert suppressed_body["countries"] == []
    assert suppressed_body["distance_bands"] == []


def test_quality_endpoint_separates_full_and_filtered_coverage(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/quality",
        params={"stage_types": "PFE"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_row_count"] == 4
    assert body["full_convention_count"] == 3
    assert body["filtered_convention_count"] == 1
    country_coverage = next(
        field
        for field in body["filtered_coverage"]
        if field["field"] == "pays_lieu_stage"
    )
    assert country_coverage["present_count"] == 2
    assert country_coverage["denominator"] == 2
    assert body["yearly_coverage"]
    assert "PRIVATE-STUDENT" not in response.text
    assert "PRIVATE-CONVENTION" not in response.text


def test_source_load_errors_are_reported_without_paths_or_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_source(*args: object, **kwargs: object) -> pd.DataFrame:
        raise DataFileError("private local path")

    monkeypatch.setattr(dashboard, "load_stages", missing_source)
    with TestClient(app) as client:
        response = client.get("/api/v1/overview")

    assert response.status_code == 503
    assert response.json() == {
        "code": "source_unavailable",
        "message": "Le fichier source est absent ou illisible.",
    }
    assert "private local path" not in response.text


def test_missing_source_columns_return_explicit_schema_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_schema(*args: object, **kwargs: object) -> pd.DataFrame:
        raise MissingColumnsError(("private_column_name",))

    monkeypatch.setattr(dashboard, "load_stages", invalid_schema)
    with TestClient(app) as client:
        response = client.get("/api/v1/filters/options")

    assert response.status_code == 503
    assert response.json()["code"] == "invalid_source_schema"
    assert "private_column_name" not in response.text
