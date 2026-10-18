"""Tests synthétiques de l'API V1, sans lecture du classeur réel."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.main import app
from backend.app.services import dashboard
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
