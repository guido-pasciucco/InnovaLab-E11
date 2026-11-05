# PR 07/09 — Oficinas cercanas (feature/07-epok-integration → feature/06-boletin-oficial-integration)

**GitHub:** PR #68 — [chained 07/09] feat(back): integrate USIG EPOK nearby commune offices

**En una frase:** Conectó la libreta de lugares del Gobierno de la Ciudad para que CONCO diga qué sedes comunales tenés a tu alrededor, con dirección, teléfono y la página oficial de la comuna.

## Qué se hace

1. Le agregó a CONCO una pregunta nueva: ¿dónde puedo ir en persona cerca de donde estoy? El Gobierno de la Ciudad mantiene su propia libreta de lugares —las sedes y subsedes comunales— y este PR la enchufó desde el lado de CONCO.
2. La consulta se hace en dos tandas: primero se pide la lista de lugares que están alrededor de un punto (dentro de un radio fijo, de 3 kilómetros por defecto) y recién después se mira la ficha de cada uno de los primeros que salieron.
3. Las fichas de los lugares elegidos se piden todas juntas, en un mismo lote, para que nadie espere a que le atiendan de a una.
4. La lista se ordena de lo más cerca a lo más lejos y se corta en la cantidad pedida (entre 1 y 5; si nadie eligió cantidad, son 3). Dato curioso que quedó escrito: la libreta del Gobierno no ordena por cercanía y trae la distancia escrita "a mano", así que CONCO la ordena y la lee con lupa.
5. Si una sede no tiene dirección, se la deja afuera: sin dirección no hay lugar para ir. Y de la ficha sale también el enlace oficial de la comuna, que venía escondido como una tarjetita pegada adentro de otra tarjeta.
6. Todo quedó respaldado por pruebas: las que juegan con copias que no necesitan internet, y las que llamaron a la libreta real del Gobierno antes de abrir el PR. Además hay un atajo para curiosear: un comando que uno invoca a mano y muestra la respuesta cruda del Gobierno, sin pasos intermedios.

## Secciones de código importantes

**Pedir la lista del radio y dejarla ya ordenada** — `back/src/conco/integrations/epok/client.py`:

```python
async def find_nearby(
    longitude: float, latitude: float, categories: Sequence[str], radius_meters: int
) -> list[EpokPlace]:
    """Busca lugares de las categorías dadas dentro de un radio alrededor de un punto (WGS84)."""
    params: dict[str, str | int | float] = {
        "x": longitude,
        "y": latitude,
        "categorias": ",".join(categories),
        "radio": radius_meters,
    }
    body = await _get(NEARBY_PATH, params)
    try:
        result = EpokNearbyPlaces.model_validate_json(body)
    except ValidationError as exc:
        raise EpokError("EPOK devolvió una respuesta inesperada.") from exc
    return sorted(result.places, key=lambda place: place.distance_meters)
```

El Gobierno entrega la lista sin orden y con las distancias escritas al pasar; este pedacito la pide con el punto y el radio, y la devuelve ya ordenada de lo más cerca a lo más lejos. Si la respuesta viene rara, avisa que algo no está bien.

**La ficha de un lugar: lo mínimo y necesario** — `back/src/conco/integrations/epok/models.py`:

```python
class EpokPlace(BaseModel):
    """Un lugar de `reverseGeocoderLugares`, solo con los campos que usa CONCO.

    EPOK informa la distancia en metros como texto (`"962.53"`); Pydantic la convierte a número.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(alias="nombre")
    distance_meters: float = Field(alias="distancia")
```

De cada lugar solo quedan tres datos: su número de legajo, su nombre y su distancia. Como la distancia llega escrita "a mano" (por ejemplo, entre comillas), acá se traduce a número de una vez y para siempre.

**Pedir todas las fichas juntas** — `back/src/conco/geolocation/infrastructure.py`:

```python
        try:
            places = await find_nearby_places(
                longitude=longitude,
                latitude=latitude,
                categories=[COMMUNE_OFFICES_CATEGORY],
                radius_meters=settings.epok_radius_meters,
            )
            closest = places[:limit]
            contents = await asyncio.gather(*(get_object(place.id) for place in closest))
        except EpokError as exc:
            raise NearbyOfficeError(str(exc)) from exc
```

Se corta la lista en las primeras (según lo que pidió la persona) y después se piden las fichas de todas a la vez, al mismo tiempo: nadie espera una fila eterna. Si cualquier parte se cae, sube el mismo aviso de "no está disponible".

**Sacar la página oficial de una tarjeta pegada** — `back/src/conco/geolocation/infrastructure.py`:

```python
def extract_link(html: str | None) -> str | None:
    """Extrae el enlace de un dato que EPOK publica como HTML (`<a href="...">Página web</a>`).

    Devuelve None si no hay un enlace web: así no se expone HTML ni enlaces de otro tipo.
    """
    if not html:
        return None
    parser = _FirstLinkParser()
    parser.feed(html)
    parser.close()
    return parser.link
```

La página oficial de la comuna no viene limpia: viene escondida dentro de una tarjetita pegada en la ficha. Acá se le saca la primera dirección web de verdad, y si no hay tarjeta, no se expone contenido vacío.

**La puerta que la persona usa** — `back/src/conco/geolocation/api.py`:

```python
@router.get("/nearby-offices", response_model=NearbyOfficesResponse)
async def get_nearby_offices(
    finder: Annotated[NearbyOfficeFinder, Depends(get_nearby_office_finder)],
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
    limit: Annotated[
        int,
        Query(ge=1, le=5, description="Cantidad máxima de oficinas."),
    ] = 3,
) -> NearbyOfficesResponse:
    """Lista las sedes y subsedes comunales más cercanas a un punto de la Ciudad de Buenos Aires.

    Si no hay ninguna en el radio de búsqueda, devuelve una lista vacía.
    """
    try:
        offices = await finder.find_nearby(latitude=latitude, longitude=longitude, limit=limit)
    except NearbyOfficeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=OFFICES_UNAVAILABLE_DETAIL
        ) from exc
    return NearbyOfficesResponse(offices=offices, source=finder.source)
```

Esta es la ventanilla del mostrador: la persona llega con un punto y la cantidad, y se va con la lista de sedes cerca, cada una citando la fuente oficial. Si la libreta del Gobierno no está disponible, la ventana avisa con franqueza en lugar de colgar a alguien. Un dato fino: si en ese radio no hay ninguna sede, la respuesta es una lista vacía, no un susto.

## Por qué importa en la cadena

Con este PR suma la parte de a dónde ir en persona, habilitando la puerta física más cercana.