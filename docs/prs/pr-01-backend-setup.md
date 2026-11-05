# PR 01/09 — Setup del backend (feature/01-backend-setup → main)

**GitHub:** PR #62 — [chained 01/09] refactor(back): set up uv project with src/conco layout

**En una frase:** se dejó el backend listo para trabajar: el código reorganizado en una sola carpeta con el nombre del proyecto, todas sus dependencias declaradas con versiones exactas iguales para todos, y su configuración editable sin tocar el programa.

## Qué se hizo

1. Agrupó todo el código del backend en una única carpeta con el nombre del proyecto (`conco`), para que sea fácil saber dónde vive cada cosa.
2. Reemplazó la lista de dependencias escrita a mano por una declarada dentro del proyecto: qué se usa y en qué versión se le permite actualizarse a cada una.
3. Fijó además las versiones exactas que se instalan en un archivo que viaja con el proyecto: quien lo descargue, en cualquier momento y lugar, recibe siempre las mismas versiones y todo funciona igual para todos.
4. Sacó la configuración del código: los sitios que tienen permiso para conectarse a la API se escriben en un archivo aparte (`/.env`), sin tener que modificar el programa ni reiniciar el proyecto entero.
5. Eliminó dos archivos empezados que nada del sistema ya usaba, y Actualizó la guía de dependencias (`docs/DEPENDENCIAS.md`) para reflejar esta nueva forma de trabajar.

## Secciones de código importantes

**La lista completa de dependencias** — `back/pyproject.toml`:

```toml
[project]
name = "conco"
version = "0.1.0"
description = "CONCO API: general guidance on commercial procedures for entrepreneurs."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115,<1.0",
    "uvicorn[standard]>=0.30,<1.0",
    "pydantic>=2.8,<3.0",
    "pydantic-settings>=2.16,<3.0",
]

[build-system]
requires = ["uv_build>=0.13.1,<0.14"]
build-backend = "uv_build"
```

Acá queda declarado qué necesita el backend para funcionar y hasta qué versión se le permite actualizarse a cada pieza.

**Las versiones exactas que se instalan** — `back/uv.lock` (líneas 1-8 y 197-199):

```toml
version = 1
revision = 5
requires-python = ">=3.12"

[[package]]
name = "annotated-doc"
version = "0.0.5"
source = { registry = "https://pypi.org/simple" }
...
[[package]]
name = "pydantic"
version = "2.14.2"
```

Por cada pieza queda guardada la versión exacta que se instaló: el proyecto se descarga y funciona igual en cualquier computadora.

**La configuración del backend** — `back/src/conco/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la API, leída de variables de entorno y del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
```

Los sitios con permiso de conexión tienen valores por defecto, y se pueden cambiar editando el archivo `.env` sin tocar el código.

**El backend usando esa configuración** — `back/src/conco/main.py` (líneas 4 y 12-15):

```python
from conco.config import settings
...
# Los orígenes permitidos se configuran con CORS_ORIGINS en el archivo .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
```

La API toma los sitios con permiso del archivo configurado en vez de tenerlos escritos a mano dentro del código, como ocurría antes.

**La lista anterior, que este PR elimina** — `back/requirements` (en la rama `main`):

```text
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
pydantic>=2.8,<3.0
```

La lista anterior: anotaba solo una parte de las piezas que se usan y, sobre todo, no garantizaba versiones exactas iguales para todos.

## Por qué importa en la cadena

De `main` recibió la base con la primer definición de qué era el backend y qué iba a hacer. Deja resuelto cómo se monta el proyecto, cómo se instalan sus dependencias y cómo se configura su acceso, para que los siguientes PRs agreguen funciones nuevas sin reorganizar nada: la cadena sigue en la rama `feature/02-georef-integration`, donde entra el primer proveedor de información, el servicio de direcciones del Estado.
