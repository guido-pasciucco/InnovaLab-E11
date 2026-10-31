from uuid import UUID

import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.caba_tramites.models import (
    CabaIncludedResource,
    CabaProcedureDetail,
    CabaProcedureDocument,
    CabaProceduresResponse,
    CabaRequirementItem,
    CabaResponsibleOffice,
    CabaStartButton,
    CabaStepItem,
)

PROCEDURES_PATH = "/node/tramites_obelisco"
PROCEDURE_FIELDS = "title,path,changed,body"

# El contenido de cada trámite está armado con párrafos anidados:
# sección → columna → componente → ítems. Se piden solo los componentes de las tres
# columnas posibles y los ítems de requisitos y pasos.
_COMPONENT_PATHS = [
    f"field_contenido.field_seccion.{column}.field_componente"
    for column in ("field_columna_central", "field_columna_izquierda", "field_columna_derecha")
]
_DETAIL_INCLUDE = ",".join(
    f"{path}{suffix}"
    for path in _COMPONENT_PATHS
    for suffix in ("", ".field_item_requisito_tramite", ".field_item_paso_del_tramite")
)

# Sparse fieldsets: solo los campos que se usan. Un valor vacío descarta todos los
# atributos de párrafos que se incluyen pero no se usan (textos largos, costos, etc.).
DETAIL_PARAMS: dict[str, str] = {
    "include": _DETAIL_INCLUDE,
    "fields[node--tramites_obelisco]": f"{PROCEDURE_FIELDS},field_contenido",
    "fields[paragraph--seccion]": "field_seccion",
    "fields[paragraph--seccion_1_columna]": "field_columna_central",
    "fields[paragraph--seccion_2_columnas]": "field_columna_izquierda,field_columna_derecha",
    "fields[paragraph--componentes]": "field_componente",
    "fields[paragraph--requisito_tramite]": "field_item_requisito_tramite",
    "fields[paragraph--item_requisito_tramite]": "field_texto,field_cuerpo",
    "fields[paragraph--pasos_del_tramite]": "field_item_paso_del_tramite",
    "fields[paragraph--item_titulo_del_paso]": "field_titulo,field_parrafo",
    "fields[paragraph--organismo_responsable]": "field_titulo",
    "fields[paragraph--boton_iniciar_tramite]": "field_link_iniciar_tramite",
    "fields[paragraph--parrafo]": "",
    "fields[paragraph--costo_del_tramite]": "",
    "fields[paragraph--collapse_base]": "",
    "fields[paragraph--descargables]": "",
    "fields[paragraph--sedes]": "",
}


class CabaTramitesError(Exception):
    """La API de trámites de la Ciudad no está disponible o devolvió una respuesta inesperada."""


def normalize_query(query: str) -> str:
    """Quita los espacios sobrantes de la búsqueda antes de enviarla."""
    return " ".join(query.split())


def search_params(query: str, limit: int) -> dict[str, str | int]:
    """Parámetros JSON:API para buscar trámites publicados cuyo título contiene el texto."""
    return {
        "filter[status]": 1,
        "filter[title][operator]": "CONTAINS",
        "filter[title][value]": normalize_query(query),
        "sort": "title",
        "page[limit]": limit,
        "fields[node--tramites_obelisco]": PROCEDURE_FIELDS,
    }


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.caba_tramites_base_url,
        timeout=settings.caba_tramites_timeout_seconds,
    )


async def search_procedures(query: str, limit: int = 10) -> CabaProceduresResponse:
    """Busca trámites publicados por texto en el título (sin distinguir mayúsculas ni acentos)."""
    try:
        async with _client() as client:
            response = await client.get(PROCEDURES_PATH, params=search_params(query, limit))
            response.raise_for_status()
            return CabaProceduresResponse.model_validate_json(response.content)
    except httpx.HTTPError as exc:
        raise CabaTramitesError(f"No se pudo consultar la API de trámites: {exc}") from exc
    except ValidationError as exc:
        raise CabaTramitesError("La API de trámites devolvió una respuesta inesperada.") from exc


async def get_procedure(procedure_id: UUID) -> CabaProcedureDetail | None:
    """Devuelve el detalle de un trámite, o None si no existe o no está publicado."""
    try:
        async with _client() as client:
            response = await client.get(
                f"{PROCEDURES_PATH}/{procedure_id}", params=DETAIL_PARAMS
            )
            # Un id inexistente o no publicado no devuelve 404: redirige a una página HTML.
            if response.is_redirect:
                return None
            response.raise_for_status()
            document = CabaProcedureDocument.model_validate_json(response.content)
            return _to_detail(document)
    except httpx.HTTPError as exc:
        raise CabaTramitesError(f"No se pudo consultar la API de trámites: {exc}") from exc
    except ValidationError as exc:
        raise CabaTramitesError("La API de trámites devolvió una respuesta inesperada.") from exc


def _to_detail(document: CabaProcedureDocument) -> CabaProcedureDetail:
    """Recorre los párrafos incluidos y se queda con requisitos, pasos, organismo y botón."""
    included = {(resource.type, resource.id): resource for resource in document.included}

    def children(parent: CabaIncludedResource, field: str) -> list[CabaIncludedResource]:
        relationship = parent.relationships.get(field)
        if relationship is None or not isinstance(relationship.data, list):
            return []
        return [
            included[(ref.type, ref.id)]
            for ref in relationship.data
            if (ref.type, ref.id) in included
        ]

    def of_type(resource_type: str) -> list[CabaIncludedResource]:
        return [resource for resource in document.included if resource.type == resource_type]

    requirements = [
        CabaRequirementItem.model_validate(item.attributes)
        for container in of_type("paragraph--requisito_tramite")
        for item in children(container, "field_item_requisito_tramite")
    ]
    steps = [
        CabaStepItem.model_validate(item.attributes)
        for container in of_type("paragraph--pasos_del_tramite")
        for item in children(container, "field_item_paso_del_tramite")
    ]
    offices = of_type("paragraph--organismo_responsable")
    buttons = of_type("paragraph--boton_iniciar_tramite")
    return CabaProcedureDetail(
        procedure=document.data,
        requirements=requirements,
        steps=steps,
        responsible_office=(
            CabaResponsibleOffice.model_validate(offices[0].attributes) if offices else None
        ),
        start_button=(
            CabaStartButton.model_validate(buttons[0].attributes) if buttons else None
        ),
    )
