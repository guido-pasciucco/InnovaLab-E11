from html.parser import HTMLParser
from uuid import UUID

from conco.config import settings
from conco.guidance.domain import (
    Procedure,
    ProcedureDetail,
    ProcedureSearchError,
    Regulation,
    RegulationLookupError,
    RegulationType,
    Source,
)
from conco.integrations.boletin_oficial.client import (
    BoletinOficialError,
    BoletinOficialNormType,
    find_norms,
)
from conco.integrations.boletin_oficial.models import BoletinOficialNorm
from conco.integrations.caba_tramites.client import (
    CabaTramitesError,
    get_procedure,
    search_procedures,
)
from conco.integrations.caba_tramites.models import (
    CabaProcedure,
    CabaProcedureDetail,
    CabaRequirementItem,
    CabaStepItem,
    CabaText,
)

# Etiquetas que separan bloques de texto: al quitarlas se reemplazan por un espacio.
_BLOCK_TAGS = frozenset(
    {"br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "td", "tr", "ul"}
)
_IGNORED_TAGS = frozenset({"script", "style"})


class _TextExtractor(HTMLParser):
    """Junta el texto visible de un fragmento HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORED_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Convierte un fragmento HTML en texto plano de una sola línea."""
    extractor = _TextExtractor()
    extractor.feed(html)
    extractor.close()
    return " ".join("".join(extractor.parts).split())


class CabaProcedureCatalog:
    """Adaptador: busca trámites en la API de la Ciudad y los traduce al modelo del dominio."""

    @property
    def source(self) -> Source:
        return Source(
            name="Trámites del Gobierno de la Ciudad de Buenos Aires",
            url=f"{settings.caba_tramites_site_url}/gobierno/tramites",
            license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
        )

    async def search(self, query: str, limit: int) -> list[Procedure]:
        try:
            response = await search_procedures(query, limit=limit)
        except CabaTramitesError as exc:
            raise ProcedureSearchError(str(exc)) from exc
        return [_to_procedure(procedure) for procedure in response.procedures]

    async def get(self, procedure_id: UUID) -> ProcedureDetail | None:
        try:
            detail = await get_procedure(procedure_id)
        except CabaTramitesError as exc:
            raise ProcedureSearchError(str(exc)) from exc
        return _to_detail(detail) if detail is not None else None


def _text(text: CabaText) -> str:
    """Devuelve el texto plano, quitando el HTML solo cuando el formato no es texto plano."""
    if text.format == "plain_text":
        return " ".join(text.value.split())
    return html_to_text(text.value)


def _to_procedure(procedure: CabaProcedure) -> Procedure:
    """Copia los datos del resumen y arma el enlace a la página oficial del trámite."""
    attributes = procedure.attributes
    return Procedure(
        id=procedure.id,
        title=attributes.title.strip(),
        official_url=f"{settings.caba_tramites_site_url}{attributes.path.alias}",
        summary=_text(attributes.body),
        last_updated=attributes.changed,
    )


def _requirements(item: CabaRequirementItem) -> list[str]:
    """Un requisito por cada texto del ítem; si el ítem tiene título, se antepone."""
    heading = (item.heading or "").strip()
    texts = [text for text in (_text(body) for body in item.bodies) if text]
    return [f"{heading}: {text}" if heading else text for text in texts]


def _step(step: CabaStepItem) -> str:
    """Título del paso seguido de su explicación, si la tiene."""
    title = step.title.strip()
    explanation = _text(step.text) if step.text is not None else ""
    return f"{title}: {explanation}" if explanation else title


def _to_detail(detail: CabaProcedureDetail) -> ProcedureDetail:
    summary = _to_procedure(detail.procedure)
    return ProcedureDetail(
        **summary.model_dump(),
        requirements=[
            requirement
            for item in detail.requirements
            for requirement in _requirements(item)
        ],
        steps=[_step(step) for step in detail.steps],
        responsible_office=(
            detail.responsible_office.name.strip() if detail.responsible_office else None
        ),
        start_url=detail.start_button.link.uri if detail.start_button else None,
    )


_NORM_TYPES: dict[RegulationType, BoletinOficialNormType] = {
    RegulationType.LEY: BoletinOficialNormType.LEY,
    RegulationType.DECRETO: BoletinOficialNormType.DECRETO,
}


class BoletinOficialRegulationRegistry:
    """Adaptador: busca normas en el Boletín Oficial de la Ciudad y las traduce al dominio."""

    @property
    def source(self) -> Source:
        return Source(
            name="Boletín Oficial de la Ciudad de Buenos Aires",
            url=settings.boletin_oficial_site_url,
            license=(
                "Sin licencia explícita: normas oficiales de publicación obligatoria y "
                "acceso público"
            ),
        )

    async def find(
        self, regulation_type: RegulationType, number: int, year: int
    ) -> list[Regulation]:
        try:
            norms = await find_norms(_NORM_TYPES[regulation_type], number, year)
        except BoletinOficialError as exc:
            raise RegulationLookupError(str(exc)) from exc
        return [_to_regulation(norm, regulation_type, year) for norm in norms]


def _to_regulation(
    norm: BoletinOficialNorm, regulation_type: RegulationType, year: int
) -> Regulation:
    """Usa la primera edición y el primer documento publicados.

    El año es el pedido, con cuatro dígitos: la API lo devuelve con dos (2018 → 18).
    """
    bulletin = norm.bulletins[0]
    return Regulation(
        type=regulation_type,
        number=norm.number,
        year=year,
        summary=" ".join(norm.summary.split()),
        issuing_body=norm.issuing_body.strip() if norm.issuing_body else None,
        publication_date=bulletin.publication_date,
        bulletin_number=bulletin.bulletin_number,
        document_url=norm.documents[0].url,
    )
