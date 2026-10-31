# Dependencias del backend

Qué paquetes de Python usa el backend de CONCO, para qué sirve cada uno y cómo instalarlos. Las dependencias se gestionan con [uv](https://docs.astral.sh/uv/) y se declaran en [`back/pyproject.toml`](../back/pyproject.toml).

## Instalación rápida

1. Instalar uv una sola vez por máquina: `curl -LsSf https://astral.sh/uv/install.sh | sh` (o `brew install uv`).
2. Desde la carpeta `back/`, instalar todo: `uv sync`. Crea `.venv/`, instala las versiones exactas de `uv.lock` e instala el propio proyecto (`conco`) en modo editable.
3. Levantar la API: `uv run uvicorn conco.main:app --reload`.

`uv run` ejecuta el comando dentro de `.venv/` sin necesidad de activarlo.

## Archivos de dependencias

| Archivo | Qué guarda | Quién lo edita | ¿Se sube al repo? |
|---------|------------|----------------|-------------------|
| `pyproject.toml` | Las dependencias que pedimos, con rangos de versión. | Las personas, o `uv add` | Sí |
| `uv.lock` | Las versiones exactas instaladas, incluidas las transitivas. | Solo uv, nunca a mano | Sí |
| `.venv/` | El entorno virtual con los paquetes instalados. | uv | No |

## Dependencias directas

Son las que pedimos explícitamente en `back/pyproject.toml`.

| Paquete | Versión permitida | Para qué sirve |
|---------|-------------------|----------------|
| `fastapi` | `>=0.115,<1.0` | Framework web. Define los endpoints (qué responde la API) y genera la documentación interactiva en `/docs`. |
| `uvicorn[standard]` | `>=0.30,<1.0` | Servidor ASGI. Escucha en un puerto, recibe las peticiones HTTP y se las pasa a FastAPI. |
| `pydantic` | `>=2.8,<3.0` | Validación de datos. Define la forma de lo que entra y sale de la API y rechaza los datos inválidos. |
| `pydantic-settings` | `>=2.16,<3.0` | Lee la configuración desde variables de entorno y el archivo `.env`, validando sus tipos (`src/conco/config.py`). |

**Rangos de versión:** `>=2.8,<3.0` acepta correcciones y mejoras, pero nunca un salto de versión mayor, que suele traer cambios incompatibles.

## Dependencias transitivas

uv también instala las dependencias de nuestras dependencias. No hace falta declararlas: sus versiones exactas quedan fijadas en `uv.lock`.

| Paquete | Lo trae | Para qué sirve |
|---------|---------|----------------|
| `starlette` | fastapi | Base web sobre la que está construido FastAPI. |
| `pydantic-core` | pydantic | Motor de validación compilado de Pydantic. |
| `anyio` | starlette | Soporte para código asíncrono. |
| `h11` | uvicorn | Implementación del protocolo HTTP/1.1. |
| `click` | uvicorn | Interfaz de línea de comandos de `uvicorn`. |
| `opentelemetry-api` | fastapi | API de observabilidad (trazas y métricas). |
| `typing-extensions`, `typing-inspection`, `annotated-types`, `annotated-doc`, `idna` | varios | Utilidades internas de tipado y de manejo de dominios. |

## Extras de `uvicorn[standard]`

Los corchetes `[standard]` piden accesorios opcionales de uvicorn:

| Paquete | Para qué sirve |
|---------|----------------|
| `uvloop` | Bucle de eventos más rápido. |
| `httptools` | Lectura de HTTP más rápida. |
| `watchfiles` | Detecta cambios en los archivos para `--reload`. |
| `websockets` | Soporte para WebSockets. |
| `python-dotenv` | Carga variables desde un archivo `.env`. |
| `pyyaml` | Permite configurar los logs en formato YAML. |

## Reglas del equipo

- **Siempre usar el entorno virtual.** Instalar paquetes globalmente puede generar conflictos entre proyectos, y Ubuntu lo bloquea (`externally-managed-environment`). uv crea y usa `.venv/` automáticamente.
- **`.venv/` no se sube al repositorio.** Está en `back/.gitignore`: es pesado y depende de cada máquina. Se suben `pyproject.toml` y `uv.lock`, y cada persona crea su propio entorno con `uv sync`.
- **Si agregás una dependencia,** usá `uv add <paquete>` (actualiza `pyproject.toml` y `uv.lock`), subí ambos archivos y actualizá este documento.
- **No uses `pip install`** en este proyecto: instalaría paquetes que no quedan registrados en `uv.lock`.
