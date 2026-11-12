"""Embeddings de la búsqueda de actividades vía Cloudflare Workers AI."""

import time

import httpx

from conco.config import settings

_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)


class EmbeddingProviderError(Exception):
    """El proveedor de embeddings no está configurado o no respondió; la búsqueda no está disponible."""


class CloudflareTextEmbedder:
    """Adaptador: llama a Cloudflare Workers AI por HTTP (ruta OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        account_id: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.embedding_api_key
        self._account_id = account_id if account_id is not None else settings.cloudflare_account_id
        self._model_name = model_name or settings.cloudflare_embedding_model

    @property
    def model_name(self) -> str:
        return self._model_name

    def warm_up(self) -> None:
        """Preflight barato: detecta falta de configuración antes que la primera consulta real."""
        self.embed(["ping"])

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            raise EmbeddingProviderError("EMBEDDING_API_KEY no configurada: no se puede vectorizar")
        if not self._account_id:
            raise EmbeddingProviderError(
                "CLOUDFLARE_ACCOUNT_ID no configurado: no se puede vectorizar"
            )
        url = f"https://api.cloudflare.com/client/v4/accounts/{self._account_id}/ai/v1/embeddings"
        payload = {"model": self._model_name, "input": list(texts)}
        body = self._post_with_retry(url, payload)
        return self._parse_vectors(body, expected=len(texts))

    def _post_with_retry(self, url: str, payload: dict) -> dict:
        # Un reintento: quien llama suele estar esperando una respuesta.
        attempts = 2
        for attempt in range(attempts):
            try:
                response = httpx.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=_TIMEOUT,
                )
            except httpx.TransportError as exc:
                if attempt + 1 < attempts:
                    time.sleep(0.5)
                    continue
                raise EmbeddingProviderError(
                    f"No se pudo conectar con Cloudflare Workers AI: {exc}"
                ) from exc
            if response.status_code == 429 or response.status_code >= 500:
                if attempt + 1 < attempts:
                    time.sleep(self._retry_delay(response))
                    continue
                raise EmbeddingProviderError(
                    f"Cloudflare Workers AI devolvió {response.status_code}: {response.text[:200]}"
                )
            if response.status_code >= 400:
                raise EmbeddingProviderError(
                    f"Cloudflare Workers AI devolvió {response.status_code}: {response.text[:200]}"
                )
            return response.json()
        raise EmbeddingProviderError("Cloudflare Workers AI no respondió")  # pragma: no cover

    @staticmethod
    def _retry_delay(response: httpx.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        try:
            return min(float(retry_after), 5.0) if retry_after is not None else 0.5
        except ValueError:
            return 0.5

    @staticmethod
    def _parse_vectors(body: object, expected: int) -> list[list[float]]:
        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            raise EmbeddingProviderError("Cloudflare Workers AI devolvió una respuesta sin 'data'")
        vectors: list[list[float] | None]
        if all(isinstance(item, dict) and "index" in item for item in data):
            vectors = [None] * len(data)
            for item in data:
                vectors[int(item["index"])] = item["embedding"]
        else:
            vectors = [item["embedding"] for item in data if isinstance(item, dict)]
        if len(vectors) != expected or any(vector is None for vector in vectors):
            raise EmbeddingProviderError(
                f"Cloudflare Workers AI devolvió {len(vectors)} vectores para {expected} textos"
            )
        return [vector for vector in vectors if vector is not None]


def create_embedder() -> CloudflareTextEmbedder:
    """Punto único de construcción del embedder: Cloudflare Workers AI (ADR-005)."""
    return CloudflareTextEmbedder()
