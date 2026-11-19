import hashlib
from datetime import UTC, datetime
from uuid import UUID

from conco.guidance.domain import (
    Activity,
    ActivityProcedures,
    ApplicableProcedure,
    ContextAnswers,
    Procedure,
    REQUIREMENTS_NOTE,
    RequirementOrigin,
    apply_context,
)
from conco.guidance.requirements import (
    build_requirements,
    normalize_requirement_text,
)

HABILITACION_ID = UUID("338718b4-a2a0-44af-baa4-083f5d834b12")
EMPLEADORES_ID = UUID("1fb7a579-8fc2-4216-b113-684cc272f7f1")
HABILITACION_URL = "https://buenosaires.gob.ar/tramites/habilitacion"
EMPLEADORES_URL = "https://buenosaires.gob.ar/tramites/empleadores"


def test_duplicate_requirements_merge_origins_preserving_order_and_heading() -> None:
    rows = [
        (HABILITACION_ID, "Habilitación", HABILITACION_URL, "Documentación", "  DNI <b>del</b> Titular  "),
        (HABILITACION_ID, "Habilitación", HABILITACION_URL, None, "   "),
        (EMPLEADORES_ID, "Empleadores", EMPLEADORES_URL, None, "dni del titular"),
        (EMPLEADORES_ID, "Empleadores", EMPLEADORES_URL, "Otro", "Acreditar domicilio"),
    ]

    result = build_requirements(rows)

    assert len(result) == 2
    first, second = result
    assert first.text == "  DNI <b>del</b> Titular  "
    assert first.heading == "Documentación"
    assert first.origins == [
        RequirementOrigin(
            procedure_id=HABILITACION_ID,
            procedure_title="Habilitación",
            official_url=HABILITACION_URL,
        ),
        RequirementOrigin(
            procedure_id=EMPLEADORES_ID,
            procedure_title="Empleadores",
            official_url=EMPLEADORES_URL,
        ),
    ]
    assert second.text == "Acreditar domicilio"
    assert second.heading == "Otro"
    assert [origin.procedure_id for origin in second.origins] == [EMPLEADORES_ID]


def test_requirement_id_is_stable_sha256_prefix_of_normalized_text() -> None:
    key = normalize_requirement_text("DNI del Titular")
    expected = "req-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]

    [first] = build_requirements(
        [(HABILITACION_ID, "Habilitación", HABILITACION_URL, None, "  DNI del  Titular ")]
    )
    [second] = build_requirements(
        [(EMPLEADORES_ID, "Empleadores", EMPLEADORES_URL, None, "dni DEL titular")]
    )

    assert first.id == expected
    assert second.id == first.id


def test_apply_context_carries_requirements_and_note() -> None:
    requirements = build_requirements(
        [(HABILITACION_ID, "Habilitación", HABILITACION_URL, None, "DNI del titular")]
    )
    activity = ActivityProcedures(
        activity=Activity(slug="peluqueria", name="Peluquería"),
        procedures=[
            ApplicableProcedure(
                procedure=Procedure(
                    id=HABILITACION_ID,
                    title="Habilitación",
                    official_url=HABILITACION_URL,
                    summary="",
                    last_updated=datetime(2026, 1, 1, tzinfo=UTC),
                ),
                note="Nota.",
                applies_when=ContextAnswers(has_employees=True),
            )
        ],
        requirements=requirements,
    )

    result = apply_context(activity, ContextAnswers(has_employees=False))

    assert result.procedures == []
    assert result.requirements == requirements
    assert result.requirements_note == REQUIREMENTS_NOTE
