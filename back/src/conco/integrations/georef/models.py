from pydantic import BaseModel, ConfigDict, Field


class GeorefNamedEntity(BaseModel):
    """Entidad de Georef con id y nombre (departamento, provincia, localidad, municipio)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    name: str | None = Field(default=None, alias="nombre")


class GeorefStreet(GeorefNamedEntity):
    """Calle de Georef; en las calles de cruce todos los campos pueden venir en null."""

    category: str | None = Field(default=None, alias="categoria")


class GeorefHeight(BaseModel):
    """Altura (número) de la dirección; viene en null si no se indicó número."""

    model_config = ConfigDict(populate_by_name=True)

    unit: str | None = Field(default=None, alias="unidad")
    value: int | None = Field(default=None, alias="valor")


class GeorefCoordinates(BaseModel):
    """Coordenadas aproximadas de la dirección."""

    lat: float
    lon: float


class GeorefAddress(BaseModel):
    """Una dirección normalizada devuelta por Georef."""

    model_config = ConfigDict(populate_by_name=True)

    nomenclature: str = Field(alias="nomenclatura")
    street: GeorefStreet = Field(alias="calle")
    height: GeorefHeight = Field(alias="altura")
    cross_street_1: GeorefStreet = Field(alias="calle_cruce_1")
    cross_street_2: GeorefStreet = Field(alias="calle_cruce_2")
    department: GeorefNamedEntity = Field(alias="departamento")
    census_locality: GeorefNamedEntity = Field(alias="localidad_censal")
    province: GeorefNamedEntity = Field(alias="provincia")
    floor: str | None = Field(default=None, alias="piso")
    location: GeorefCoordinates | None = Field(default=None, alias="ubicacion")


class GeorefAddressesResponse(BaseModel):
    """Respuesta del endpoint /direcciones de Georef."""

    model_config = ConfigDict(populate_by_name=True)

    count: int = Field(alias="cantidad")
    total: int
    start: int = Field(alias="inicio")
    addresses: list[GeorefAddress] = Field(alias="direcciones")


class GeorefLocation(BaseModel):
    """Entidades de Georef que contienen un punto.

    Fuera de la Argentina (por ejemplo, en el mar) las entidades vienen con id y nombre en null.
    """

    model_config = ConfigDict(populate_by_name=True)

    lat: float
    lon: float
    province: GeorefNamedEntity = Field(alias="provincia")
    department: GeorefNamedEntity = Field(alias="departamento")
    municipality: GeorefNamedEntity = Field(alias="municipio")


class GeorefLocationResponse(BaseModel):
    """Respuesta del endpoint /ubicacion de Georef."""

    model_config = ConfigDict(populate_by_name=True)

    location: GeorefLocation = Field(alias="ubicacion")
