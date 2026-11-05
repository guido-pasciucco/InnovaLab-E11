# PR 08/09 — ¿Estás en la Ciudad? (feature/08-georef-caba-check → feature/07-epok-integration)

**GitHub:** PR #69 — [chained 08/09] feat(back): add CABA location check with Georef reverse geocoding

**En una frase:** Agregó a CONCO la pregunta «este punto, ¿es de la Ciudad?», apoyada en el servicio nacional de Georef, que ahora también acepta un punto del mapa y lo lee al revés.

## Qué se hace

1. Aprovechó que la rama 02 ya tenía la conexión con la libreta nacional de lugares de la Argentina, y le abrió una segunda puerta: además de buscar por dirección escrita, ese mismo servicio ahora también recibe un punto del mapa y dice a qué provincia pertenece.
2. La respuesta es clara: sí si el punto es de la Ciudad, no si es de otra provincia o está fuera del país. Estar fuera no es un error: es información.
3. Para decidir si el punto es de la Ciudad, mira el ID de provincia (02) y no el nombre escrito, porque el número no cambia.
4. Antes de preguntar afuera, revisa en casa que los dos números del punto estén dentro de su escala posible, porque si alguien viene con un dato imposible, el servicio falla antes de recibir el problema.
5. Lo que ya existía (buscar por dirección escrita) y lo nuevo (leer un punto al revés) comparten ahora la misma receta interna; las pruebas viejas quedaron igual.
6. También quedó respaldado por pruebas nuevas (con copias sin internet) y por el atajo que la rama 02 dejó para mirar puntos.

## Secciones de código importantes

**Leer un punto al revés** — `back/src/conco/integrations/georef/client.py`:

```python
async def locate(latitude: float, longitude: float) -> GeorefLocationResponse:
    """Consulta el endpoint /ubicacion de Georef (geocodificación inversa de un punto).

    Fuera de la Argentina Georef responde 200 con provincia, departamento y municipio en null.
    """
    params = {"lat": latitude, "lon": longitude}
    return await _get("/ubicacion", params, GeorefLocationResponse)
```

Este es el «leeme esto al revés»: le pasa el punto al servicio de la Nación y recibe de vuelta a qué provincia pertenece.

**Lo que trae el sobre** — `back/src/conco/integrations/georef/models.py`:

```python
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
```

Es el modelo del sobre que devuelve el servicio: punto, provincia, departamento y municipio.

**Chequeo: por número de documento, no por nombre** — `back/src/conco/geolocation/infrastructure.py`:

```python
CABA_PROVINCE_ID = "02"
"""Id de la Ciudad Autónoma de Buenos Aires en Georef (código INDEC de provincia)."""


class GeorefLocationChecker:
    """Adaptador: ubica un punto con el endpoint /ubicacion de Georef y verifica si es CABA.

    La verificación usa el id de provincia, no el nombre, para no depender de cómo se escribe.
    """
    ...

    async def check(self, latitude: float, longitude: float) -> LocationCheck:
        try:
            response = await locate(latitude=latitude, longitude=longitude)
        except GeorefError as exc:
            raise LocationCheckError(str(exc)) from exc
        location = response.location
        return LocationCheck(
            in_caba=location.province.id == CABA_PROVINCE_ID,
            province=location.province.name,
            department=location.department.name,
        )
```

Aquí se decide el sí y el no: se pregunta si el ID de provincia del punto es el «02» de la Ciudad.

**El formato de salida** — `back/src/conco/geolocation/domain.py`:

```python
class LocationCheck(BaseModel):
    """Resultado de verificar si un punto está dentro de la Ciudad de Buenos Aires (RN-02).

    `province` y `department` se informan como los publica la fuente; fuera de la Argentina
    (por ejemplo, en el mar) vienen en None.
    """

    model_config = ConfigDict(frozen=True)

    in_caba: bool
    province: str | None
    department: str | None
```

Es el papelito de salida: sí o no, más el nombre de la provincia y del sector tal como los escribe la fuente oficial, o vacíos si el punto navegó hacia el mar.

**La ventana donde la persona pregunta** — `back/src/conco/geolocation/api.py`:

```python
@router.get("/location-check", response_model=LocationCheckResponse)
async def check_location(
    checker: Annotated[LocationChecker, Depends(get_location_checker)],
    latitude: Annotated[
        float,
        Query(ge=-90, le=90, description="Latitud en grados (WGS84), por ejemplo: -34.6047137."),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=-180, le=180, description="Longitud en grados (WGS84), por ejemplo: -58.4021372."
        ),
    ],
) -> LocationCheckResponse:
    """Indica si un punto está dentro de la Ciudad de Buenos Aires (RN-02).

    Un punto de otra provincia o fuera de la Argentina no es un error: responde 200 con
    `in_caba: false` (fuera de la Argentina, provincia y departamento vienen en null).
    """
    try:
        check = await checker.check(latitude=latitude, longitude=longitude)
    except LocationCheckError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=LOCATION_UNAVAILABLE_DETAIL
        ) from exc
    return LocationCheckResponse(location=check, source=checker.source)
```

La ventanilla del mostrador: la persona marca un punto y CONCO responde si es de la Ciudad. Los límites del punto se chequean en la puerta misma: si alguien viene con un dato imposible, la ventanilla lo rechaza y no envía el problema al servicio nacional. Si el servicio falla, avisa amablemente.

## Por qué importa en la cadena

Con este PR agrega la consulta geográfica de si un punto es de la Ciudad, regla que atraviesa todo el proyecto.