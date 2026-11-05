# PR 04/09 — Integración de trámites (feature/04-caba-tramites-integration → feature/03-geolocation-endpoint)

**GitHub:** PR #65 — [chained 04/09] feat(back): integrate CABA official procedures (trámites) API

**En una frase:** Puso a la app un mostrador de trámites: se pregunta por un trámite oficial de la Ciudad y se responde con requisitos, pasos, organismo y enlace oficial.

## Qué se hace

1. Sumó una sección de orientación con una ventana de búsqueda: se escribe el nombre de un trámite y aparecen las coincidencias del catálogo publicado del Gobierno de la Ciudad.
2. Cada trámite se puede pedir en detalle: los requisitos (la lista de compras), los pasos en orden (la receta), el organismo a cargo y el enlace oficial para iniciar.
3. Toda respuesta viene con el sello de la fuente: nombre, página web y permiso de uso, para que nadie pregunte de dónde sacaron esto.
4. Pide bien y a medida: solo trámites ya publicados, ordenados por título y con tope de resultados, para no cargar con todo el archivo de arriba a abajo.
5. Descubrió que un trámite inexistente no contesta "no existe" directo, sino que manda a otra página; ahora la app reconoce esa jugada y avisa la verdad: no está.
6. Si el sitio de la Ciudad no responde o contesta cualquier cosa, la app no se cuelga: sale con un mensaje amable de "probal de nuevo más tarde". Y para verificar todo sin conectar, guardó copias de respuestas reales del sitio.

## Secciones de código importantes

**La ficha en blanco que todo proveedor llena igual** — `back/src/conco/guidance/domain.py`:

```python
class ProcedureCatalog(Protocol):
    """Puerto: cualquier catálogo oficial capaz de buscar trámites y mostrar su detalle."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def search(self, query: str, limit: int) -> list[Procedure]:
        """Devuelve los trámites que coinciden; lanza ProcedureSearchError si falla."""
        ...
```

Es la ficha en blanco del mostrador: cualquier proveedor de trámites tiene que llenarla con los mismos campos y la misma forma.

**El traductor del mostrador, con el sello de la fuente** — `back/src/conco/guidance/infrastructure.py`:

```python
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
```

Este es el traductor: recibe la respuesta del catálogo de la Ciudad y la acomoda en la ficha del proyecto. El sello con la fuente sale de acá.

**La ventana, con modales** — `back/src/conco/guidance/api.py`:

```python
@router.get("/procedures", response_model=ProcedureSearchResponse)
async def search_procedures(
    catalog: Annotated[ProcedureCatalog, Depends(get_procedure_catalog)],
    query: Annotated[
        str,
        Query(
            min_length=3,
            max_length=100,
            pattern=r"\S",
            description="Texto a buscar en el nombre del trámite, por ejemplo: habilitación.",
        ),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=20, description="Quantity máxima de resultados."),
    ] = 10,
) -> ProcedureSearchResponse:
    """Busca trámites oficiales de la Ciudad de Buenos Aires por su nombre."""
    try:
        procedures = await catalog.search(query, limit=limit)
    except ProcedureSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=UNAVAILABLE_DETAIL
        ) from exc
    return ProcedureSearchResponse(procedures=procedures, source=catalog.source)
```

La ventana no acepta preguntas de media palabra (mínimo tres letras) ni pedidos desmedidos (máximo veinte resultados). Si la fuente no está, contesta amable "probal de nuevo más tarde"; y en la respuesta va siempre el sello de la fuente.

**El pedido armado a la medida del proyecto** — `back/src/conco/integrations/caba_tramites/client.py`:

```python
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
```

Solo trámites publicados, ordenados por título y con tope por pedido.

**Si te manda a otra página, es que no está** — `back/src/conco/integrations/caba_tramites/client.py`:

```python
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
```

El catálogo de la Ciudad redirige a otra página cuando un trámite no existe en vez de avisar "no está". El cliente detecta eso y contesta la verdad: no está.

## Por qué importa en la cadena

Con este PR la cadena arranca a orientar, y deja un molde para copiar (proveedor con ficha única y sello de fuente) que usan los dos que le siguen.