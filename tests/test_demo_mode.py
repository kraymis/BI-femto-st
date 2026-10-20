from fastapi.testclient import TestClient

from backend.app.main import app


def test_demo_mode_uses_only_synthetic_dashboard_and_geography(monkeypatch) -> None:
    monkeypatch.setenv("BI_DATA_MODE", "demo")
    client = TestClient(app)

    options = client.get("/api/v1/filters/options")
    overview = client.get("/api/v1/overview")
    geography = client.get("/api/v1/companies-geography")

    assert options.status_code == 200
    assert overview.status_code == 200
    assert overview.json()["kpis"]["convention_count"] == 7
    assert geography.status_code == 200
    destinations = geography.json()["destinations"]
    assert {destination["city"] for destination in destinations} == {
        "Besançon",
        "Lyon",
        "Lausanne",
        "Montréal",
    }
    assert all(
        convention["convention_id"].startswith("DEMO-")
        for destination in destinations
        for convention in destination["conventions"]
    )
    assert "ETUDIANT-FICTIF" not in str(
        (options.json(), overview.json(), geography.json())
    )
