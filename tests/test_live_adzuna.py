import os

import pytest

from mirandole.search import AdzunaConnector


@pytest.mark.live_adzuna
def test_live_adzuna_smoke(pytestconfig: pytest.Config) -> None:
    if "live_adzuna" not in pytestconfig.option.markexpr:
        pytest.skip("live_adzuna mark must be explicitly selected")

    app_id = os.getenv("MIRANDOLE_ADZUNA_APP_ID")
    app_key = os.getenv("MIRANDOLE_ADZUNA_APP_KEY")
    if not app_id or not app_key:
        pytest.skip("MIRANDOLE_ADZUNA_APP_ID and MIRANDOLE_ADZUNA_APP_KEY required")

    connector = AdzunaConnector(
        app_id=app_id,
        app_key=app_key,
        results_per_page=5,
        max_results=5,
    )

    results = connector.search(
        intitule="Administrateur systeme",
        localisation="Paris",
        rayon_demande_km=10,
    )

    assert len(results) <= 5
    assert all(result.source_name == "Adzuna" for result in results)
