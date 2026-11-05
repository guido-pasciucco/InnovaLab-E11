# PR 03/09 — Endpoint de direcciones (feature/03-geolocation-endpoint → feature/02-georef-integration)

**GitHub:** PR #64 — [chained 03/09] feat(back): expose GET /geolocation/addresses endpoint

**En una frase:** Expuso el buscador de direcciones a través de un endpoint público GET /geolocation/addresses, con validación de entrada, modelo propio de respuesta y mensaje amable cuando el proveedor falla.

## Qué se hace

1. Abrió el endpoint GET /geolocation/addresses para que cualquiera pueda consultar direcciones.
2. Escribió reglas de consulta: la dirección debe tener al menos 3 letras, no solo espacios, y la cantidad de resultados está entre 1 y 10.
3. Definió un modelo propio de dirección (Address) para responder sin depender del formato de Georef.
4. Creó un traductor que convierte la respuesta de Georef al modelo del proyecto y traduce su error a uno propio.
5. Si el proveedor falla, el cliente recibe un mensaje humano y un código 502.
6. Probó el endpoint con un doble del proveedor y una prueba real, y lo conectó al router principal.

## Secciones de código importantes

**Modelo del dominio** — `back/src/conco/geolocation/domain.py`:

```python
class Address(BaseModel):
    """Dirección normalizada, sin depender de qué servicio externo la encontró."""

    model_config = ConfigDict(frozen=True)

    full_address: str
    street: str | None
    number: int | None
    department: str | None
    locality: str | None
    province: str | None
    coordinates: Coordinates | None


class AddressSearchError(Exception):
    """El servicio de direcciones no está disponible o respondió algo inesperado."""


class AddressFinder(Protocol):
    """Puerto: cualquier servicio capaz de buscar direcciones a partir de un texto."""

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        """Devuelve las direcciones que coinciden; lanza AddressSearchError si falla."""
        ...
```

Tres cosas: el modelo propio sobre el que se escribe cada respuesta, el aviso de error propio y el contrato que le pide a cualquier proveedor.

**Traductor** — `back/src/conco/geolocation/infrastructure.py`:

```python
class GeorefAddressFinder:
    """Adaptador: busca direcciones en Georef y las traduce al modelo del dominio."""

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        try:
            response = await search_addresses(
                address, province=province, max_results=limit
            )
        except GeorefError as exc:
            raise AddressSearchError(str(exc)) from exc
        return [_to_domain(georef_address) for georef_address in response.addresses]
```

Va al cliente de Georef, pide la búsqueda y copia los datos al modelo propio; si la consulta falla, devuelve el aviso.

**Endpoint** — `back/src/conco/geolocation/api.py` (líneas 23-25 y 47-56):

```python
@router.get("/addresses", response_model=AddressSearchResponse)
async def search_addresses(
    finder: Annotated[AddressFinder, Depends(get_address_finder)],
...
) -> AddressSearchResponse:
    """Convierte una dirección escrita libremente en direcciones normalizadas con coordenadas aproximadas."""
    try:
        addresses = await finder.search(address, province=province, limit=limit)
    except AddressSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio de direcciones no está disponible. Intentá de nuevo más tarde.",
        ) from exc
    return AddressSearchResponse(addresses=addresses)
```

La puerta recibe la pregunta, la pasa al traductor y entrega la lista; si falla, devuelve el mensaje de "intentá de nuevo más tarde".

**Reglas de consulta** — `back/src/conco/geolocation/api.py` (líneas 26-34 y 43-46):

```python
    address: Annotated[
        str,
        Query(
            min_length=3,
            max_length=200,
            pattern=r"\S",
            description="Dirección escrita libremente, por ejemplo: Corrientes 2500.",
        ),
    ],
...
    limit: Annotated[
        int,
        Query(ge=1, le=10, description="Cantidad máxima de resultados."),
    ] = 5,
```

Piso y techo de la consulta: la dirección puede escribirse suelta pero necesita cuerpo (desde 3 letras, sin ser solo espacios) y la tanda de respuestas no pasa de diez.

**Conexión al router** — `back/src/conco/main.py` (líneas 5 y 22):

```python
from conco.geolocation.api import router as geolocation_router
...
app.include_router(geolocation_router)
```

Dos líneas para registrar el endpoint en la app.

## Por qué importa en la cadena

Con este PR deja el buscador de direcciones expuesto al público con validación, reglas y traducción. La vidriera está abierta para más proveedores detrás de la misma ficha.