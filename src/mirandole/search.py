from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mirandole.storage import (
    SearchSession,
    StoredOfferResult,
    create_search_session,
    save_offer_results,
    save_source_failure,
)

RAYONS_DEMANDE_KM = [10, 20, 30, 50, 100]


class DemoSourceUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class OfferResult:
    source_name: str
    source_radius_km: int
    result_identity: str
    title: str
    company: str
    city: str
    published_at: str | None
    contract_type: str
    salary: str | None
    source_url: str
    remote_text: str | None = None


@dataclass(frozen=True)
class SearchTrace:
    session: SearchSession
    result_count: int
    failure_count: int


class DemoSourceConnector:
    source_name = "Source demo"
    supported_radii_km = [20, 50, 100]

    def map_rayon_source(self, rayon_demande_km: int) -> int:
        for supported_radius in self.supported_radii_km:
            if supported_radius >= rayon_demande_km:
                return supported_radius
        return self.supported_radii_km[-1]

    def search(
        self, *, intitule: str, localisation: str, rayon_demande_km: int
    ) -> list[OfferResult]:
        if "echec" in intitule.casefold():
            raise DemoSourceUnavailable(
                "La Source d'offres demo est indisponible pour cette recherche."
            )

        rayon_source_km = self.map_rayon_source(rayon_demande_km)
        title = intitule.strip()
        city = localisation.strip()
        source_slug = _slugify(title)

        return [
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                result_identity=f"{self.source_name}:demo-{source_slug}-1",
                title=f"{title} Python",
                company="Atelier Hexagone",
                city=city,
                published_at="2026-05-09",
                contract_type="CDI",
                salary="45 000 - 55 000 EUR",
                source_url=f"https://example.test/offres/{source_slug}-python",
                remote_text="Teletravail partiel",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                result_identity=f"{self.source_name}:demo-{source_slug}-2",
                title=f"{title} Data",
                company="Cooperative Loire",
                city=city,
                published_at="2026-05-07",
                contract_type="CDD",
                salary=None,
                source_url=f"https://example.test/offres/{source_slug}-data",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                result_identity=f"{self.source_name}:demo-{source_slug}-3",
                title=f"{title} Support applicatif",
                company="Service Numerique Ouest",
                city=city,
                published_at=None,
                contract_type="Interim",
                salary="380 EUR / jour",
                source_url=f"https://example.test/offres/{source_slug}-support",
            ),
        ]


def run_search_trace(
    database_path: Path,
    *,
    intitule: str,
    localisation: str,
    rayon_demande_km: int,
    connector: DemoSourceConnector | None = None,
) -> SearchTrace:
    session = create_search_session(
        database_path,
        intitule=intitule.strip(),
        localisation=localisation.strip(),
        rayon_demande_km=rayon_demande_km,
    )
    source_connector = connector or DemoSourceConnector()

    try:
        results = source_connector.search(
            intitule=session.intitule,
            localisation=session.localisation,
            rayon_demande_km=session.rayon_demande_km,
        )
    except DemoSourceUnavailable as exc:
        save_source_failure(
            database_path,
            session_id=session.id,
            source_name=source_connector.source_name,
            message=str(exc),
        )
        return SearchTrace(session=session, result_count=0, failure_count=1)

    save_offer_results(
        database_path,
        session_id=session.id,
        results=[
            StoredOfferResult(
                id=0,
                session_id=session.id,
                source_name=result.source_name,
                source_radius_km=result.source_radius_km,
                result_identity=result.result_identity,
                title=result.title,
                company=result.company,
                city=result.city,
                published_at=result.published_at,
                contract_type=result.contract_type,
                salary=result.salary,
                source_url=result.source_url,
                remote_text=result.remote_text,
                inactive=False,
            )
            for result in results
        ],
    )
    return SearchTrace(session=session, result_count=len(results), failure_count=0)


def _slugify(value: str) -> str:
    slug = "-".join(value.casefold().split())
    return slug or "recherche"
