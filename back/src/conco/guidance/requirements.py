"""Consolidates the official requirement rows published for an activity's procedures."""

import hashlib
import unicodedata
from collections.abc import Sequence
from uuid import UUID

from conco.guidance.domain import Requirement, RequirementOrigin
from conco.guidance.infrastructure import html_to_text

# (procedure_id, procedure_title, official_url, heading, text)
RequirementRow = tuple[UUID, str, str, str | None, str]


def normalize_requirement_text(text: str) -> str:
    """Dedup key: visible text, lowercase, no accents, whitespace collapsed."""
    plain = html_to_text(text)
    decomposed = unicodedata.normalize("NFKD", plain)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.lower().split())


def build_requirements(rows: Sequence[RequirementRow]) -> list[Requirement]:
    """One requirement per non-empty body row, merged by normalized text in first-seen order.

    Rows are expected in ``(activity position, requirement position)`` order; the text and
    heading of the first row of each group are kept and later rows only add an origin.
    """
    order: list[str] = []
    first: dict[str, tuple[str, str | None]] = {}
    origins: dict[str, list[RequirementOrigin]] = {}
    for procedure_id, procedure_title, official_url, heading, text in rows:
        if not text or not text.strip():
            continue
        key = normalize_requirement_text(text)
        if not key:
            continue
        if key not in origins:
            order.append(key)
            first[key] = (text, heading)
            origins[key] = []
        origins[key].append(
            RequirementOrigin(
                procedure_id=procedure_id,
                procedure_title=procedure_title,
                official_url=official_url,
            )
        )
    return [
        Requirement(
            id="req-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12],
            text=first[key][0],
            heading=first[key][1],
            origins=origins[key],
        )
        for key in order
    ]
