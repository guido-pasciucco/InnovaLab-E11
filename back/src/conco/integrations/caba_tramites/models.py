from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CabaText(BaseModel):
    """Texto con formato de Drupal; `format` indica si `value` es texto plano o HTML."""

    value: str
    format: str


class CabaPath(BaseModel):
    """Ruta pública del trámite dentro de buenosaires.gob.ar."""

    alias: str


class CabaProcedureAttributes(BaseModel):
    """Atributos de un trámite pedidos con `fields[node--tramites_obelisco]`."""

    title: str
    path: CabaPath
    changed: datetime
    body: CabaText


class CabaProcedure(BaseModel):
    """Un recurso `node--tramites_obelisco` del JSON:API."""

    id: UUID
    attributes: CabaProcedureAttributes


class CabaProceduresResponse(BaseModel):
    """Respuesta de la búsqueda de trámites (colección JSON:API)."""

    model_config = ConfigDict(populate_by_name=True)

    procedures: list[CabaProcedure] = Field(alias="data")


class CabaResourceIdentifier(BaseModel):
    """Referencia JSON:API a otro recurso (tipo + id)."""

    type: str
    id: str


class CabaRelationship(BaseModel):
    """Relación JSON:API: una referencia, una lista de referencias o null."""

    data: list[CabaResourceIdentifier] | CabaResourceIdentifier | None = None


class CabaIncludedResource(BaseModel):
    """Párrafo incluido con `include`; sus atributos dependen del tipo de párrafo."""

    type: str
    id: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    relationships: dict[str, CabaRelationship] = Field(default_factory=dict)


class CabaProcedureDocument(BaseModel):
    """Respuesta del detalle de un trámite: el trámite y sus párrafos incluidos."""

    data: CabaProcedure
    included: list[CabaIncludedResource] = Field(default_factory=list)


class CabaRequirementItem(BaseModel):
    """Párrafo `item_requisito_tramite`: un título opcional y uno o más textos HTML."""

    model_config = ConfigDict(populate_by_name=True)

    heading: str | None = Field(default=None, alias="field_texto")
    bodies: list[CabaText] = Field(alias="field_cuerpo")


class CabaStepItem(BaseModel):
    """Párrafo `item_titulo_del_paso`: título del paso y, si la tiene, su explicación en HTML."""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="field_titulo")
    text: CabaText | None = Field(default=None, alias="field_parrafo")


class CabaResponsibleOffice(BaseModel):
    """Párrafo `organismo_responsable`: nombre del organismo a cargo del trámite."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="field_titulo")


class CabaLink(BaseModel):
    """Enlace de Drupal."""

    uri: str


class CabaStartButton(BaseModel):
    """Párrafo `boton_iniciar_tramite`: enlace oficial para iniciar el trámite."""

    model_config = ConfigDict(populate_by_name=True)

    link: CabaLink = Field(alias="field_link_iniciar_tramite")


class CabaProcedureDetail(BaseModel):
    """Detalle de un trámite ya resuelto: los párrafos útiles, en el orden de la página."""

    procedure: CabaProcedure
    requirements: list[CabaRequirementItem]
    steps: list[CabaStepItem]
    responsible_office: CabaResponsibleOffice | None
    start_button: CabaStartButton | None
