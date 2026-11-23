"""Middleware ASGI que asigna un request id a cada petición y registra una línea por pedido."""

import logging
import re
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")

logger = logging.getLogger(__name__)


def resolve_request_id(incoming: str | None) -> str:
    """Reutiliza el id recibido solo si es seguro (letras, números y guiones, hasta 64);
    si no, genera uno nuevo."""
    if incoming is not None and _VALID_REQUEST_ID.fullmatch(incoming):
        return incoming
    return uuid4().hex


class RequestIdMiddleware:
    """Guarda el id en `request.state.request_id`, lo devuelve en `X-Request-ID` y deja
    en el log método, ruta, estado, duración e id de cada petición."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                incoming = value.decode("latin-1")
                break
        request_id = resolve_request_id(incoming)
        scope.setdefault("state", {})["request_id"] = request_id

        status_code = 500
        started = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            # Si la excepción sigue de largo, la respuesta 500 la arma el manejador genérico.
            duration_ms = (time.perf_counter() - started) * 1000
            logger.info(
                "%s %s %s %.1fms request_id=%s",
                scope.get("method"),
                scope.get("path"),
                status_code,
                duration_ms,
                request_id,
            )
