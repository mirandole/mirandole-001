from dataclasses import dataclass

from mirandole.enrichment import (
    ResultFilters,
    apply_result_filters,
    build_result_filters,
    enrich_result,
)


@dataclass(frozen=True)
class ResultatOffre:
    title: str
    company: str
    contract_type: str
    description_source: str | None
    remote_text: str | None = None
    experience_level: str = "Non precise"
    diploma_level: str = "Non precise"


def test_tags_de_competence_are_extracted_from_configurable_dictionary() -> None:
    result = ResultatOffre(
        title="Developpeur backend",
        company="Atelier Hexagone",
        contract_type="CDI",
        description_source="Construction API avec Python et PostgreSQL.",
    )

    enrichment = enrich_result(
        result,
        skill_dictionary={
            "Backend": ["api"],
            "Langage Python": ["python"],
            "Base de donnees": ["postgresql"],
        },
    )

    assert enrichment.skill_tags == ("Backend", "Base de donnees", "Langage Python")


def test_niveau_experience_demande_is_extracted() -> None:
    result = ResultatOffre(
        title="Ingenieur plateforme",
        company="Service Numerique Ouest",
        contract_type="CDI",
        description_source="Experience 5 ans minimum en production.",
    )

    enrichment = enrich_result(result)

    assert enrichment.experience_level == "Senior"


def test_niveau_diplome_demande_is_extracted() -> None:
    result = ResultatOffre(
        title="Analyste data",
        company="Cooperative Loire",
        contract_type="CDD",
        description_source="Formation Bac+3 ou licence informatique.",
    )

    enrichment = enrich_result(result)

    assert enrichment.diploma_level == "Bac+3"


def test_default_contract_filters_exclude_stage_and_alternance() -> None:
    results = [
        ResultatOffre("Dev", "A", "CDI", None),
        ResultatOffre("Stage web", "A", "Stage", None),
        ResultatOffre("Cloud", "A", "Alternance", None),
        ResultatOffre("Support", "A", "Interim", None),
        ResultatOffre("Source sans contrat", "A", "Non precise", None),
    ]

    filtered = apply_result_filters(results, build_result_filters())

    assert [result.contract_type for result in filtered] == [
        "CDI",
        "Interim",
        "Non precise",
    ]


def test_post_aggregation_filters_match_contract_experience_and_diploma() -> None:
    results = [
        ResultatOffre(
            "Dev Python",
            "A",
            "CDI",
            None,
            experience_level="Avance",
            diploma_level="Bac+5",
        ),
        ResultatOffre(
            "Support Linux",
            "B",
            "Interim",
            None,
            experience_level="Debutant",
            diploma_level="Aucun diplome requis",
        ),
    ]

    filtered = apply_result_filters(
        results,
        ResultFilters(
            contract_types=("CDI", "Interim"),
            experience_levels=("Debutant",),
            diploma_levels=("Aucun diplome requis",),
        ),
    )

    assert [result.title for result in filtered] == ["Support Linux"]
