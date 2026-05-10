from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

EXPERIENCE_LEVELS = ["Debutant", "Confirme", "Avance", "Senior", "Non precise"]
DIPLOMA_LEVELS = [
    "Non precise",
    "Aucun diplome requis",
    "Bac",
    "Bac+2",
    "Bac+3",
    "Bac+5",
    "Doctorat",
]
DEFAULT_INCLUDED_CONTRACT_TYPES = ["CDI", "CDD", "Freelance", "Interim", "Non precise"]
EXCLUDED_CONTRACT_TYPES = ["Stage", "Alternance"]

DEFAULT_SKILL_DICTIONARY = {
    "API": ["api", "rest", "graphql"],
    "AWS": ["aws", "amazon web services"],
    "Docker": ["docker"],
    "FastAPI": ["fastapi"],
    "Git": ["git", "github", "gitlab"],
    "Java": ["java"],
    "JavaScript": ["javascript", "typescript", "node.js", "nodejs"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Linux": ["linux"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Python": ["python", "django", "flask"],
    "React": ["react", "next.js", "nextjs"],
    "SQL": ["sql", "sqlite", "mysql"],
}


class NormalizedOfferResult(Protocol):
    title: str
    company: str
    contract_type: str
    description_source: str | None
    remote_text: str | None


class FilterableOfferResult(NormalizedOfferResult, Protocol):
    experience_level: str
    diploma_level: str


@dataclass(frozen=True)
class Enrichment:
    skill_tags: tuple[str, ...]
    experience_level: str
    diploma_level: str


@dataclass(frozen=True)
class ResultFilters:
    contract_types: tuple[str, ...] = tuple(DEFAULT_INCLUDED_CONTRACT_TYPES)
    experience_levels: tuple[str, ...] = ()
    diploma_levels: tuple[str, ...] = ()


def enrich_result(
    result: NormalizedOfferResult,
    *,
    skill_dictionary: dict[str, list[str]] | None = None,
) -> Enrichment:
    corpus = _searchable_text(result)
    dictionary = skill_dictionary or DEFAULT_SKILL_DICTIONARY
    return Enrichment(
        skill_tags=extract_skill_tags(corpus, dictionary),
        experience_level=extract_experience_level(corpus),
        diploma_level=extract_diploma_level(corpus),
    )


def extract_skill_tags(
    text: str, skill_dictionary: dict[str, list[str]]
) -> tuple[str, ...]:
    normalized = _normalize(text)
    tags = [
        label
        for label, aliases in skill_dictionary.items()
        if any(_contains_term(normalized, alias) for alias in aliases)
    ]
    return tuple(sorted(tags, key=str.casefold))


def extract_experience_level(text: str) -> str:
    normalized = _normalize(text)
    years = _extract_year_counts(normalized)
    if years:
        max_years = max(years)
        if max_years >= 5:
            return "Senior"
        if max_years >= 3:
            return "Avance"
        if max_years > 1:
            return "Confirme"
        return "Debutant"

    if any(term in normalized for term in ["senior", "experimente", "confirme"]):
        return "Senior" if "senior" in normalized else "Confirme"
    if any(
        term in normalized for term in ["junior", "debutant", "premiere experience"]
    ):
        return "Debutant"
    return "Non precise"


def extract_diploma_level(text: str) -> str:
    normalized = _normalize(text)
    if any(term in normalized for term in ["doctorat", "phd", "these"]):
        return "Doctorat"
    if any(term in normalized for term in ["bac+5", "bac 5", "master", "ingenieur"]):
        return "Bac+5"
    if any(term in normalized for term in ["bac+3", "bac 3", "licence", "bachelor"]):
        return "Bac+3"
    if any(term in normalized for term in ["bac+2", "bac 2", "bts", "dut", "but"]):
        return "Bac+2"
    if any(term in normalized for term in ["niveau bac", "baccalaureat"]):
        return "Bac"
    if any(
        term in normalized
        for term in [
            "aucun diplome",
            "sans diplome",
            "diplome non requis",
            "pas de diplome requis",
        ]
    ):
        return "Aucun diplome requis"
    return "Non precise"


def apply_result_filters[T: FilterableOfferResult](
    results: list[T], filters: ResultFilters
) -> list[T]:
    return [result for result in results if _matches_filters(result, filters)]


def normalized_filter_values(
    values: list[str] | None, allowed: list[str]
) -> tuple[str, ...]:
    if values is None:
        return ()
    allowed_values = set(allowed)
    return tuple(value for value in values if value in allowed_values)


def build_result_filters(
    *,
    contract_types: list[str] | None = None,
    experience_levels: list[str] | None = None,
    diploma_levels: list[str] | None = None,
) -> ResultFilters:
    normalized_contracts = normalized_filter_values(
        contract_types, DEFAULT_INCLUDED_CONTRACT_TYPES + EXCLUDED_CONTRACT_TYPES
    )
    return ResultFilters(
        contract_types=normalized_contracts or tuple(DEFAULT_INCLUDED_CONTRACT_TYPES),
        experience_levels=normalized_filter_values(
            experience_levels, EXPERIENCE_LEVELS
        ),
        diploma_levels=normalized_filter_values(diploma_levels, DIPLOMA_LEVELS),
    )


def _matches_filters(result: FilterableOfferResult, filters: ResultFilters) -> bool:
    if result.contract_type not in filters.contract_types:
        return False
    if (
        filters.experience_levels
        and result.experience_level not in filters.experience_levels
    ):
        return False
    if filters.diploma_levels and result.diploma_level not in filters.diploma_levels:
        return False
    return True


def _searchable_text(result: NormalizedOfferResult) -> str:
    return " ".join(
        value
        for value in [
            result.title,
            result.company,
            result.contract_type,
            result.description_source,
            result.remote_text,
        ]
        if value
    )


def _contains_term(normalized_text: str, term: str) -> bool:
    normalized_term = _normalize(term)
    return normalized_term in normalized_text


def _normalize(value: str) -> str:
    return value.casefold().replace("é", "e").replace("è", "e").replace("ê", "e")


def _extract_year_counts(normalized_text: str) -> list[int]:
    years = []
    parts = normalized_text.replace("-", " ").replace("+", " ").split()
    for index, part in enumerate(parts[:-1]):
        if not part.isdigit():
            continue
        if parts[index + 1].startswith("an"):
            years.append(int(part))
    return years
