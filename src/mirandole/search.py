from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mirandole.enrichment import enrich_result
from mirandole.storage import (
    SearchSession,
    StoredOfferResult,
    create_search_session,
    find_previous_session_for_same_recherche,
    list_result_identities_for_session,
    save_inactive_offer_results_for_missing_identities,
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
    title: str
    company: str
    city: str
    published_at: str | None
    contract_type: str
    salary: str | None
    description_source: str | None
    source_url: str
    source_identifier: str | None = None
    remote_text: str | None = None

    @property
    def result_identity(self) -> str:
        return build_result_identity(
            source_name=self.source_name,
            source_url=self.source_url,
            source_identifier=self.source_identifier,
        )


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
                title=f"{title} Python",
                company="Atelier Hexagone",
                city=city,
                published_at="2026-05-09",
                contract_type="CDI",
                salary="45 000 - 55 000 EUR",
                description_source=(
                    "Developpement Python et FastAPI. Experience 3 ans souhaitee. "
                    "Bac+5 apprecie."
                ),
                source_url=f"https://example.test/offres/{source_slug}-python",
                source_identifier=f"demo-{source_slug}-1",
                remote_text="Teletravail partiel",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Data",
                company="Cooperative Loire",
                city=city,
                published_at="2026-05-07",
                contract_type="CDD",
                salary=None,
                description_source=(
                    "Analyse SQL et tableaux de bord PostgreSQL. Profil confirme "
                    "avec Bac+3."
                ),
                source_url=f"https://example.test/offres/{source_slug}-data",
                source_identifier=f"demo-{source_slug}-2",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Support applicatif",
                company="Service Numerique Ouest",
                city=city,
                published_at=None,
                contract_type="Interim",
                salary="380 EUR / jour",
                description_source=(
                    "Support Linux, Docker et Git. Aucun diplome requis, premiere "
                    "experience acceptee."
                ),
                source_url=f"https://example.test/offres/{source_slug}-support",
                source_identifier=f"demo-{source_slug}-3",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Stage web",
                company="Atelier Hexagone",
                city=city,
                published_at="2026-05-08",
                contract_type="Stage",
                salary=None,
                description_source="Stage JavaScript React pour etudiant Bac+2.",
                source_url=f"https://example.test/offres/{source_slug}-stage-web",
                source_identifier=f"demo-{source_slug}-4",
            ),
            OfferResult(
                source_name=self.source_name,
                source_radius_km=rayon_source_km,
                title=f"{title} Alternance cloud",
                company="Cooperative Loire",
                city=city,
                published_at="2026-05-06",
                contract_type="Alternance",
                salary=None,
                description_source="Alternance AWS Kubernetes niveau Bac.",
                source_url=f"https://example.test/offres/{source_slug}-alternance-cloud",
                source_identifier=f"demo-{source_slug}-5",
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

    previous_session = find_previous_session_for_same_recherche(
        database_path,
        session_id=session.id,
        intitule=session.intitule,
        localisation=session.localisation,
        rayon_demande_km=session.rayon_demande_km,
    )
    previous_result_identities = (
        list_result_identities_for_session(database_path, previous_session.id)
        if previous_session is not None
        else set()
    )
    active_result_identities = {result.result_identity for result in results}
    enriched_results = [
        _stored_result_from_offer_result(
            result,
            session_id=session.id,
            is_new=previous_session is not None
            and result.result_identity not in previous_result_identities,
        )
        for result in results
    ]
    save_offer_results(
        database_path,
        session_id=session.id,
        results=enriched_results,
    )
    save_inactive_offer_results_for_missing_identities(
        database_path,
        session_id=session.id,
        recherche=session,
        successful_source_names={source_connector.source_name},
        active_result_identities=active_result_identities,
    )
    return SearchTrace(session=session, result_count=len(results), failure_count=0)


def _stored_result_from_offer_result(
    result: OfferResult, *, session_id: int, is_new: bool
) -> StoredOfferResult:
    enrichment = enrich_result(result)
    return StoredOfferResult(
        id=0,
        session_id=session_id,
        source_name=result.source_name,
        source_radius_km=result.source_radius_km,
        result_identity=result.result_identity,
        title=result.title,
        company=result.company,
        city=result.city,
        published_at=result.published_at,
        contract_type=result.contract_type,
        salary=result.salary,
        description_source=result.description_source,
        skill_tags=enrichment.skill_tags,
        experience_level=enrichment.experience_level,
        diploma_level=enrichment.diploma_level,
        source_url=result.source_url,
        remote_text=result.remote_text,
        is_new=is_new,
        inactive=False,
    )


def build_result_identity(
    *, source_name: str, source_url: str, source_identifier: str | None = None
) -> str:
    identity_value = source_identifier or _canonicalize_source_url(source_url)
    return f"{source_name}:{identity_value}"


def _canonicalize_source_url(source_url: str) -> str:
    return source_url.strip().split("#", maxsplit=1)[0].rstrip("/")


def _slugify(value: str) -> str:
    slug = "-".join(value.casefold().split())
    return slug or "recherche"
