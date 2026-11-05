# PR 06/09 — Integración del Boletín Oficial (feature/06-boletin-oficial-integration → feature/05-usig-integration)

**GitHub:** PR #67 — [chained 06/09] feat(back): integrate CABA Boletín Oficial regulation lookup

**En una frase:** Preguntás "ley 6101, año 2018" y la app te muestra la norma de verdad: su resumen, quién la dictó, cuándo salió en el Boletín y el enlace al documento oficial.

## Qué se hace

1. Al mostrador de orientación le sumó una ventanilla nueva: buscar una norma por tipo (ley o decreto), número y año.
2. Cada respuesta trae el resumen de la norma, el organismo que la dictó, la fecha de publicación, el número de la edición del Boletín donde apareció y el enlace para descargar el documento.
3. No elige por vos: si hay más de una norma con el mismo tipo, número y año (pasa, porque la Ciudad numera los decretos del Ejecutivo y de la Legislatura por separado), las muestra todas.
4. Domestica las rarezas del archivo: el año te lo contesta con dos dígitos (18 en vez de 2018), los enlaces llegan en formato viejo y se entregan renovados, y "sin resultados" contesta con el número cero, no con una lista vacía.
5. Si la norma no existe, contesta "no se encontró"; si el archivo no funciona, sale el amable "probal de nuevo más tarde". Toda respuesta cita la fuente oficial.
6. El papel de la app queda claro: muestra la referencia, no te asesora — no interpreta si la norma se aplica a tu caso concreto.

## Secciones de código importantes

**La ficha de norma** — `back/src/conco/guidance/domain.py`:

```python
class RegulationType(StrEnum):
    """Tipos de norma que se pueden consultar por número y año."""

    LEY = "ley"
    DECRETO = "decreto"


class Regulation(BaseModel):
    """Norma oficial publicada (ley o decreto) que respalda un trámite o requisito.

    Se cita como referencia de la fuente, no como una determinación legal (RN-04).
    """

    model_config = ConfigDict(frozen=True)

    type: RegulationType
    number: int
    year: int
    summary: str
    issuing_body: str | None
    publication_date: date
    bulletin_number: int
    document_url: str | None
```

La ficha de la norma: de qué tipo es (ley o decreto), número, año, resumen, firma, edición en que se publicó y enlace al documento. Lo que no está: la interpretación.

**El pedido escrito donde nadie lo espera** — `back/src/conco/integrations/boletin_oficial/client.py`:

```python
def results_path(norm_type: BoletinOficialNormType, number: int, year: int) -> str:
    """Arma la ruta de búsqueda: los filtros van dentro de la ruta, no en la query string.

    Se envían siempre tipo, número y año (con cuatro dígitos): sin tipo se mezclan tipos de
    norma y sin año se mezclan años.
    """
    return f"{RESULTS_PATH}/tipoNorma={NORM_TYPE_IDS[norm_type]}&nNorma={number}&anio={year}"
```

Este archivo pide las cosas de una forma particular: los datos del pedido van escritos dentro de la propia dirección, no aparte en la lista de detalle. Se aprendió el capricho y se sigue al pie de la letra, porque si falta un dato, mezcla todo.

**Releerlo todo con lupa, aunque el archivo diga "yo ya filtré"** — `back/src/conco/integrations/boletin_oficial/client.py`:

```python
def _matching(
    norms: list[BoletinOficialNorm], norm_type: BoletinOficialNormType, number: int, year: int
) -> list[BoletinOficialNorm]:
    """Se queda con las normas del tipo, número y año pedidos, sin repetir ninguna.

    La API ya filtra, pero se vuelve a comprobar por si ignora algún filtro.
    """
    seen: set[int] = set()
    matching: list[BoletinOficialNorm] = []
    for norm in norms:
        if (
            norm.type_name == norm_type.value
            and norm.number == number
            and norm.short_year in (year, year % 100)
            and norm.id not in seen
        ):
            seen.add(norm.id)
            matching.append(norm)
    return matching
```

Ni con el paquete sellado: aunque el archivo ya dice que filtra, la app revisa uno por uno que cada norma sea de verdad la pedida y no aparezca repetida.

**El año completo, devuelto como si nada** — `back/src/conco/guidance/infrastructure.py`:

```python
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
        ...
        document_url=norm.documents[0].url,
    )
```

El archivo contesta el año como "18" cuando le pediste 2018; en la traducción siempre sale completo. Si hay varias ediciones o documentos, se toma la primera.

**La ventanilla nueva, con modales** — `back/src/conco/guidance/api.py`:

```python
@router.get(
    "/regulations/{regulation_type}/{number}/{year}",
    response_model=RegulationLookupResponse,
)
async def find_regulation(
    registry: Annotated[RegulationRegistry, Depends(get_regulation_registry)],
    regulation_type: Annotated[RegulationType, Path(description="Tipo de norma.")],
    number: Annotated[int, Path(ge=1, description="Número de la norma, por ejemplo: 6101.")],
    year: Annotated[
        int, Path(ge=1900, le=2100, description="Año de la norma con cuatro dígitos.")
    ],
) -> RegulationLookupResponse:
    """Busca una ley o un decreto de la Ciudad de Buenos Aires en el Boletín Oficial.

    La norma se muestra como referencia de la fuente oficial: CONCO no interpreta su
    alcance ni determina si se aplica a un caso concreto (RN-04). Puede haber más de una
    norma con el mismo tipo, número y año (por ejemplo, decretos del Poder Ejecutivo y de la
    Legislatura).
    """
    try:
        regulations = await registry.find(regulation_type, number, year)
    except RegulationLookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=REGULATIONS_UNAVAILABLE_DETAIL
        ) from exc
    if not regulations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la norma solicitada en el Boletín Oficial.",
        )
    return RegulationLookupResponse(regulations=regulations, source=registry.source)
```

La ventanilla: tipo, número y año, cada dato en su lugar. Si no hay nada, "no se encontró"; si el archivo cae, "probá más tarde"; y si hay varias normas, contesta todas, no solo la primera.

## Por qué importa en la cadena

Con este PR el trío queda completo: ubicar, orientar y justificar con la fuente. La cadena está lista para la próxima pieza.