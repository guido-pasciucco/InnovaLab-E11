# PR 05/09 — Contexto de ubicación (feature/05-usig-integration → feature/04-caba-tramites-integration)

**GitHub:** PR #66 — [chained 05/09] feat(back): integrate USIG datos útiles for CABA address context

**En una frase:** Una vez encontrada una dirección o un punto del mapa, la app ahora explica el lugar: a qué barrio y comuna pertenece y sus códigos postales.

## Qué se hace

1. Amplió la parte de ubicación: además de encontrar direcciones, ahora explica el lugar — barrio, comuna y los dos códigos postales (el corto y el detallado, el que lleva letra).
2. Hay dos maneras de preguntar: por calle y altura, o por coordenadas. Por coordenadas el servicio no informa códigos postales, y así queda contado.
3. Aprendió la mancha grande del servicio de la Ciudad: contesta siempre "todo bien", aunque la calle no exista. Ahora se lee de punta a punta lo que respondió y se decide con eso, no con la cara de la portada.
4. Si el lugar no está dentro de la Ciudad, contesta que no se encontró; si el servicio entero está caído, avisa con un amable "intentá de nuevo más tarde".
5. La respuesta siempre nombra la fuente con su licencia, igual que venía haciendo el mostrador de trámites del PR anterior.
6. Lo que no corresponde, afuera: el servicio también ofrece datos de catastro y zonificación; la app no informa nada de eso, así que ninguno de esos datos entra.

## Secciones de código importantes

**La ficha del lugar** — `back/src/conco/geolocation/domain.py`:

```python
class AddressContext(BaseModel):
    """Barrio, comuna y códigos postales de una ubicación de CABA.

    No incluye datos de catastro ni de zonificación: CONCO no los informa (RN-04).
    Los códigos postales pueden faltar, por ejemplo cuando se consulta por coordenadas.
    """

    model_config = ConfigDict(frozen=True)

    neighborhood: str
    commune: str
    postal_code: str | None
    argentine_postal_code: str | None
```

La ficha del lugar: barrio, comuna y los dos códigos. La nota al pie es la clave: nada de catastro ni zonificación, y si algo falta (por ejemplo al preguntar por coordenadas), se nota en la respuesta y no se disfraza.

**Dos maneras de preguntar** — `back/src/conco/integrations/usig/client.py`:

```python
async def get_datos_utiles_by_address(street: str, number: int) -> UsigDatosUtiles | None:
    """Devuelve comuna, barrio y códigos postales de una dirección de CABA.

    Devuelve None si USIG no encuentra la dirección o si está fuera de la Ciudad.
    """
    return await _get_datos_utiles({"calle": normalize_street(street), "altura": number})


async def get_datos_utiles_by_coordinates(
    longitude: float, latitude: float
) -> UsigDatosUtiles | None:
    """Devuelve comuna y barrio de un punto (WGS84). Por coordenadas no hay códigos postales.

    Devuelve None si el punto está fuera de la Ciudad.
    """
    return await _get_datos_utiles({"x": longitude, "y": latitude})
```

Los dos caminos: por calle y altura (con códigos postales) o por punto en el mapa (sin ellos). Si el lugar no está, contesta que no está.

**El espejo que lee la respuesta real** — `back/src/conco/integrations/usig/client.py`:

```python
def _parse(body: bytes) -> UsigDatosUtiles | None:
    """Interpreta el cuerpo sin mirar el Content-Type: USIG declara JSON como text/javascript.

    Todos los casos llegan con estado 200: un texto `ERROR: ...` si no encuentra la dirección,
    la página de ayuda en HTML si faltan parámetros, y JSON con comuna y barrio vacíos si el
    lugar está fuera de la Ciudad.
    """
    if body.lstrip().startswith(NOT_FOUND_PREFIX):
        return None
    try:
        result = UsigDatosUtiles.model_validate_json(body)
    except ValidationError as exc:
        raise UsigError("USIG devolvió una respuesta inesperada.") from exc
    if not result.commune.strip() or not result.neighborhood.strip():
        return None
    return result
```

USIG siempre responde 200; hay que leer el cuerpo para saber si realmente encontró algo.

**El mostrador nuevo dentro de la misma casa** — `back/src/conco/geolocation/api.py`:

```python
@router.get("/address-context", response_model=AddressContextResponse)
async def get_address_context(
    provider: Annotated[AddressContextProvider, Depends(get_address_context_provider)],
    street: Annotated[
        str,
        Query(
            min_length=2,
            max_length=100,
            pattern=r"\S",
            description="Nombre de la calle, por ejemplo: Corrientes.",
        ),
    ],
    number: Annotated[
        int,
        Query(ge=1, le=99999, description="Altura de la calle, por ejemplo: 2500."),
    ],
) -> AddressContextResponse:
    """Informa barrio, comuna y códigos postales de una dirección de la Ciudad de Buenos Aires."""
    try:
        context = await provider.by_address(street, number)
    except AddressContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=CONTEXT_UNAVAILABLE_DETAIL
        ) from exc
    return _context_response(context, provider)
```

La pregunta con regla: calle de al menos dos letras y altura razonable. Si la fuente cae, "intentá de nuevo más tarde"; si el lugar no está, "no se encontró" — y siempre con el sello de la fuente.

**Lo que falta, sin disfraz** — `back/src/conco/geolocation/infrastructure.py`:

```python
def _to_context(result: UsigDatosUtiles) -> AddressContext:
    """Copia barrio, comuna y códigos postales; un código vacío se informa como None."""
    return AddressContext(
        neighborhood=result.neighborhood.strip(),
        commune=result.commune.strip(),
        postal_code=(result.postal_code or "").strip() or None,
        argentine_postal_code=(result.argentine_postal_code or "").strip() or None,
    )
```

Pequeño y honesto: si un código postal llega vacío, no se inventa ni se manda un par de espacios; queda un claro "no hay".

## Por qué importa en la cadena

Con este PR la app no solo ubica: entiende el lugar (barrio y comuna), y la cadena queda lista para las normas que respaldan los trámites.