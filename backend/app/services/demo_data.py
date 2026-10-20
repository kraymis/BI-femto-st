"""Données fictives destinées uniquement à la démonstration publique."""

import pandas as pd

from bi.analytics.geography import REFERENCE_COLUMNS, destination_id


_RECORDS = (
    {
        "n_convention_de_stage": "DEMO-001",
        "n_etudiant": "ETUDIANT-FICTIF-01",
        "annee_academique": "2023/2024",
        "type_de_stage": "PFE",
        "nature_du_stage": "Recherche",
        "entreprise": "Organisation fictive Alpha",
        "entreprise_lieu_stage": "Organisation fictive Alpha",
        "date_debut": "2024-02-01",
        "date_fin": "2024-07-31",
        "pays_lieu_stage": "France",
        "ville_lieu_stage": "Besançon",
        "cp_lieu_stage": "25000",
        "ville": "Besançon",
        "code_postal": "25000",
        "date_soutenance": "2024-09-10",
    },
    {
        "n_convention_de_stage": "DEMO-002",
        "n_etudiant": "ETUDIANT-FICTIF-02",
        "annee_academique": "2023/2024",
        "type_de_stage": "PFE",
        "nature_du_stage": "Entreprise",
        "entreprise": "Société fictive Bêta",
        "entreprise_lieu_stage": "Société fictive Bêta",
        "date_debut": "2024-01-15",
        "date_fin": "2024-06-30",
        "pays_lieu_stage": "France",
        "ville_lieu_stage": "Lyon",
        "cp_lieu_stage": "69000",
        "ville": "Lyon",
        "code_postal": "69000",
        "date_soutenance": "2024-07-08",
    },
    {
        "n_convention_de_stage": "DEMO-003",
        "n_etudiant": "ETUDIANT-FICTIF-03",
        "annee_academique": "2024/2025",
        "type_de_stage": "PFE",
        "nature_du_stage": "Recherche",
        "entreprise": "Institut fictif Gamma",
        "entreprise_lieu_stage": "Institut fictif Gamma",
        "date_debut": "2025-02-03",
        "date_fin": "2025-07-25",
        "pays_lieu_stage": "France",
        "ville_lieu_stage": "Besançon",
        "cp_lieu_stage": "25000",
        "ville": "Besançon",
        "code_postal": "25000",
        "date_soutenance": None,
    },
    {
        "n_convention_de_stage": "DEMO-004",
        "n_etudiant": "ETUDIANT-FICTIF-04",
        "annee_academique": "2024/2025",
        "type_de_stage": "Assistant ingénieur",
        "nature_du_stage": "Entreprise",
        "entreprise": "Organisation fictive Delta",
        "entreprise_lieu_stage": "Organisation fictive Delta",
        "date_debut": "2025-04-01",
        "date_fin": "2025-07-31",
        "pays_lieu_stage": "Suisse",
        "ville_lieu_stage": "Lausanne",
        "cp_lieu_stage": None,
        "ville": "Lausanne",
        "code_postal": None,
        "date_soutenance": None,
    },
    {
        "n_convention_de_stage": "DEMO-005",
        "n_etudiant": "ETUDIANT-FICTIF-05",
        "annee_academique": "2024/2025",
        "type_de_stage": "PFE",
        "nature_du_stage": "Recherche",
        "entreprise": "Organisation fictive Alpha",
        "entreprise_lieu_stage": "Organisation fictive Alpha",
        "date_debut": "2025-02-10",
        "date_fin": "2025-07-31",
        "pays_lieu_stage": "France",
        "ville_lieu_stage": "Besançon",
        "cp_lieu_stage": "25000",
        "ville": "Besançon",
        "code_postal": "25000",
        "date_soutenance": "2025-09-12",
    },
    {
        "n_convention_de_stage": "DEMO-006",
        "n_etudiant": "ETUDIANT-FICTIF-06",
        "annee_academique": "2025/2026",
        "type_de_stage": "Stage court",
        "nature_du_stage": None,
        "entreprise": "Laboratoire fictif Epsilon",
        "entreprise_lieu_stage": "Laboratoire fictif Epsilon",
        "date_debut": "2026-04-01",
        "date_fin": "2026-06-30",
        "pays_lieu_stage": "France",
        "ville_lieu_stage": "Lyon",
        "cp_lieu_stage": "69000",
        "ville": "Lyon",
        "code_postal": "69000",
        "date_soutenance": None,
    },
    {
        "n_convention_de_stage": "DEMO-007",
        "n_etudiant": "ETUDIANT-FICTIF-07",
        "annee_academique": None,
        "type_de_stage": "PFE",
        "nature_du_stage": "Entreprise",
        "entreprise": None,
        "entreprise_lieu_stage": None,
        "date_debut": "2025-02-01",
        "date_fin": "2025-07-31",
        "pays_lieu_stage": "Canada",
        "ville_lieu_stage": "Montréal",
        "cp_lieu_stage": None,
        "ville": "Montréal",
        "code_postal": None,
        "date_soutenance": None,
    },
)

_DESTINATIONS = (
    ("Besançon", "France", 47.2378, 6.0241),
    ("Lyon", "France", 45.7640, 4.8357),
    ("Lausanne", "Suisse", 46.5197, 6.6323),
    ("Montréal", "Canada", 45.5019, -73.5674),
)


def get_demo_dashboard_data() -> pd.DataFrame:
    """Retourne un jeu déterministe sans données issues des fichiers locaux."""
    return pd.DataFrame.from_records(_RECORDS)


def get_demo_geographic_reference() -> pd.DataFrame:
    """Retourne des coordonnées illustratives pour les destinations de démo."""
    return pd.DataFrame.from_records(
        [
            {
                "destination_id": destination_id(city, country),
                "source_city_label": city,
                "source_country_label": country,
                "city": city,
                "country": country,
                "latitude": latitude,
                "longitude": longitude,
                "status": "located",
                "coordinate_source": "Coordonnées illustratives — données fictives",
                "verified_at": "demo",
                "validated": True,
            }
            for city, country, latitude, longitude in _DESTINATIONS
        ],
        columns=REFERENCE_COLUMNS,
    )
