"""Tests de recherche API sur données exclusivement synthétiques."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.app.main import app
from backend.app.services import dashboard


def make_search_data(count: int = 4) -> pd.DataFrame:
    rows = []
    for index in range(count):
        rows.append(
            {
                "n_convention_de_stage": f"DEMO-{index + 1:04d}",
                "n_etudiant": f"STUDENT-{index // 2 + 1:04d}",
                "nom_de_l_eleve": "Dupont" if index % 2 == 0 else "Martin",
                "prenom_de_l_eleve": f"Étudiant{index + 1}",
                "annee_academique": "2024/2025" if index < 2 else "2023/2024",
                "type_de_stage": "PFE" if index % 2 == 0 else "SIB",
                "nature_du_stage": None if index == 3 else "Entreprise",
                "entreprise": (
                    "Laboratoire Alpha" if index % 2 == 0 else "Société Bêta"
                ),
                "ville_lieu_stage": "Besançon" if index < 2 else "Lyon",
                "pays_lieu_stage": "France",
                "referent_pedagogique_mail": "must-not-be-returned@example.invalid",
                "descriptif_du_stage": "Sensitive free text must not be returned",
            }
        )
    return pd.DataFrame.from_records(rows)


@pytest.fixture
def search_client() -> Iterator[TestClient]:
    data = make_search_data()
    app.dependency_overrides[dashboard.get_dashboard_data] = lambda: data
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_search_options_expose_actual_categories_but_no_pfe_subject_field(
    search_client: TestClient,
) -> None:
    response = search_client.get("/api/v1/conventions/search/options")

    assert response.status_code == 200
    body = response.json()
    assert "convention_id" in body["available_fields"]
    assert "first_name" in body["available_fields"]
    assert "last_name" in body["available_fields"]
    assert "student_id" in body["available_fields"]
    assert "subject_id" not in body["available_fields"]
    assert [option["value"] for option in body["stage_types"]] == ["PFE", "SIB"]
    assert body["stage_natures"][-1]["is_missing"] is True


def test_search_exact_identifiers_partial_company_and_whitespace(
    search_client: TestClient,
) -> None:
    response = search_client.post(
        "/api/v1/conventions/search",
        json={
            "convention_id": " DEMO-0001 ",
            "company_contains": "ALPHA",
            "student_id_exact": " STUDENT-0001 ",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert body["results"][0]["convention_id"] == "DEMO-0001"
    assert body["results"][0]["student_name"] == "Étudiant1 Dupont"


def test_search_combines_criteria_with_and_and_ignores_global_filters(
    search_client: TestClient,
) -> None:
    response = search_client.post(
        "/api/v1/conventions/search?academic_years=2099%2F2100",
        json={
            "company_contains": "alpha",
            "academic_year": "2024/2025",
            "stage_type": "PFE",
            "city_contains": "besanç",
        },
    )

    assert response.status_code == 200
    assert response.json()["total_count"] == 1
    assert response.json()["results"][0]["convention_id"] == "DEMO-0001"


def test_search_can_select_missing_category_values(search_client: TestClient) -> None:
    response = search_client.post(
        "/api/v1/conventions/search",
        json={"stage_nature_missing": True},
    )

    assert response.status_code == 200
    assert response.json()["total_count"] == 1
    assert response.json()["results"][0]["stage_nature"] is None


def test_search_empty_results_are_successful_and_out_of_range_pages_clamp(
    search_client: TestClient,
) -> None:
    no_results = search_client.post(
        "/api/v1/conventions/search",
        json={"company_contains": "not present"},
    )
    assert no_results.status_code == 200
    assert no_results.json()["total_count"] == 0
    assert no_results.json()["results"] == []
    assert no_results.json()["page"] == 1

    out_of_range = search_client.post(
        "/api/v1/conventions/search",
        json={"stage_type": "PFE", "page": 99},
    )
    assert out_of_range.json()["page"] == out_of_range.json()["total_pages"]
    assert len(out_of_range.json()["results"]) == out_of_range.json()["total_count"]


def test_search_rejects_empty_criteria_and_unavailable_subject_identifier(
    search_client: TestClient,
) -> None:
    empty = search_client.post("/api/v1/conventions/search", json={})
    unavailable = search_client.post(
        "/api/v1/conventions/search",
        json={"subject_id": "PFE-123"},
    )

    assert empty.status_code == 422
    assert unavailable.status_code == 422


def test_search_rejects_value_and_missing_flag_for_same_category(
    search_client: TestClient,
) -> None:
    response = search_client.post(
        "/api/v1/conventions/search",
        json={"stage_nature": "Entreprise", "stage_nature_missing": True},
    )

    assert response.status_code == 422


def test_search_paginates_server_side_for_every_supported_page_size() -> None:
    data = make_search_data(127)
    app.dependency_overrides[dashboard.get_dashboard_data] = lambda: data

    with TestClient(app) as client:
        seen: set[str] = set()
        for page_size in (10, 20, 50, 100):
            first = client.post(
                "/api/v1/conventions/search",
                json={"stage_type": "PFE", "page": 1, "page_size": page_size},
            )
            body = first.json()
            assert first.status_code == 200
            assert body["total_count"] == 64
            assert len(body["results"]) == min(page_size, 64)
            assert body["page_size"] == page_size
            second_results = []
            if body["total_pages"] > 1:
                second_page = client.post(
                    "/api/v1/conventions/search",
                    json={"stage_type": "PFE", "page": 2, "page_size": page_size},
                )
                assert second_page.status_code == 200
                second_results = second_page.json()["results"]
            ids = [
                result["convention_id"]
                for result in body["results"] + second_results
            ]
            assert len(ids) == len(set(ids))
            seen.update(ids)
        assert len(seen) == 64
    app.dependency_overrides.clear()


def test_search_returns_only_whitelisted_fields(search_client: TestClient) -> None:
    response = search_client.post(
        "/api/v1/conventions/search",
        json={"convention_id": "DEMO-0001"},
    )

    assert response.status_code == 200
    serialized = response.text
    assert "must-not-be-returned" not in serialized
    assert "Sensitive free text" not in serialized
