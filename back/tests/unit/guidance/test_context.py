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


def test_excluded_lists_the_discarded_procedures_in_catalog_order() -> None:
    answers = ContextAnswers(takes_over_existing=True, has_employees=False)

    result = apply_context(CAFETERIA, answers)

    by_title = {a.procedure.title: a.procedure.id for a in CAFETERIA.procedures}
    assert [(e.id, e.title) for e in result.excluded] == [
        (by_title["Habilitación"], "Habilitación"),
        (by_title["Habilitación exprés"], "Habilitación exprés"),
        (by_title["Registro de Empleadores"], "Registro de Empleadores"),
    ]
    assert result.excluded_count == len(result.excluded)


def test_excluded_says_which_answers_discarded_each_procedure() -> None:
    answers = ContextAnswers(under_200_m2=False, takes_over_existing=True, has_employees=False)

    result = apply_context(CAFETERIA, answers)

    assert {e.title: e.because for e in result.excluded} == {
        "Habilitación": ["takes_over_existing"],
        "Habilitación exprés": ["under_200_m2", "takes_over_existing"],
        "Registro de Empleadores": ["has_employees"],
    }


def test_excluded_is_empty_without_answers() -> None:
    assert apply_context(CAFETERIA, ContextAnswers()).excluded == []


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
