from datetime import UTC, datetime
from uuid import uuid4

from conco.guidance.domain import (
    Activity,
    ActivityProcedures,
    ApplicableProcedure,
    ContextAnswers,
    Procedure,
    apply_context,
)


def _applicable(title: str, **conditions: bool) -> ApplicableProcedure:
    return ApplicableProcedure(
        procedure=Procedure(
            id=uuid4(),
            title=title,
            official_url="https://buenosaires.gob.ar/tramites/x",
            summary="",
            last_updated=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        note=f"Nota de {title}.",
        applies_when=ContextAnswers(**conditions),
    )


CAFETERIA = ActivityProcedures(
    activity=Activity(slug="cafeteria", name="Cafetería"),
    procedures=[
        _applicable("Habilitación", takes_over_existing=False),
        _applicable("Habilitación exprés", under_200_m2=True, takes_over_existing=False),
        _applicable("Transmisión", takes_over_existing=True),
        _applicable("Ingresos Brutos"),
        _applicable("Registro de Empleadores", has_employees=True),
    ],
)


def _titles(answers: ContextAnswers) -> dict[str, str]:
    result = apply_context(CAFETERIA, answers)
    return {p.procedure.title: p.status for p in result.procedures}


def test_without_answers_keeps_everything_and_marks_conditions_as_may_apply() -> None:
    assert _titles(ContextAnswers()) == {
        "Habilitación": "may_apply",
        "Habilitación exprés": "may_apply",
        "Transmisión": "may_apply",
        "Ingresos Brutos": "applies",
        "Registro de Empleadores": "may_apply",
    }


def test_answers_drop_contradicted_procedures_and_confirm_the_rest() -> None:
    answers = ContextAnswers(takes_over_existing=True, has_employees=False)

    assert _titles(answers) == {"Transmisión": "applies", "Ingresos Brutos": "applies"}
    assert apply_context(CAFETERIA, answers).excluded_count == 3


def test_partial_answers_keep_procedures_with_unanswered_conditions() -> None:
    assert _titles(ContextAnswers(takes_over_existing=False)) == {
        "Habilitación": "applies",
        "Habilitación exprés": "may_apply",
        "Ingresos Brutos": "applies",
        "Registro de Empleadores": "may_apply",
    }


def test_asks_only_the_questions_the_activity_uses_in_a_fixed_order() -> None:
    result = apply_context(CAFETERIA, ContextAnswers(has_employees=True))

    assert [(q.id, q.answer) for q in result.questions] == [
        ("has_employees", True),
        ("under_200_m2", None),
        ("takes_over_existing", None),
    ]
    assert result.questions[0].text == "¿Vas a contratar personal?"
