"""Tests del embedder de Cloudflare Workers AI (HTTP, sin red real)."""

import httpx
import pytest
import respx

from conco.config import settings
from conco.guidance.embeddings import (
    CloudflareTextEmbedder,
    EmbeddingProviderError,
    create_embedder,
)

ACCOUNT_ID = "cuenta-de-prueba"
API_KEY = "token-de-prueba"
URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1/embeddings"


def make_embedder() -> CloudflareTextEmbedder:
    return CloudflareTextEmbedder(api_key=API_KEY, account_id=ACCOUNT_ID)


def embedding_response(vectors: list[list[float]]) -> dict:
    return {
        "data": [{"index": index, "embedding": vector} for index, vector in enumerate(vectors)],
        "model": "@cf/baai/bge-m3",
        "usage": {"prompt_tokens": 3, "total_tokens": 3},
    }


@respx.mock
def test_embed_devuelve_vectores_en_orden_de_entrada() -> None:
    shuffled = {
        "data": [
            {"index": 1, "embedding": [0.2, 0.2]},
            {"index": 0, "embedding": [0.1, 0.1]},
        ],
        "model": "@cf/baai/bge-m3",
        "usage": {"prompt_tokens": 2, "total_tokens": 2},
    }
    respx.post(URL).respond(200, json=shuffled)

    vectors = make_embedder().embed(["verduleria", "kiosco"])

    assert vectors == [[0.1, 0.1], [0.2, 0.2]]


@respx.mock
def test_embed_envia_modelo_textos_y_autorizacion() -> None:
    route = respx.post(URL).respond(200, json=embedding_response([[0.1, 0.2]]))

    make_embedder().embed(["verduleria"])

    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    import json

    body = json.loads(request.content)
    assert body == {"model": "@cf/baai/bge-m3", "input": ["verduleria"]}


def test_embed_sin_api_key_falla_rapido_y_claro() -> None:
    with pytest.raises(EmbeddingProviderError, match="EMBEDDING_API_KEY"):
        CloudflareTextEmbedder(api_key="", account_id=ACCOUNT_ID).embed(["hola"])


def test_embed_sin_account_id_falla_rapido_y_claro() -> None:
    with pytest.raises(EmbeddingProviderError, match="CLOUDFLARE_ACCOUNT_ID"):
        CloudflareTextEmbedder(api_key=API_KEY, account_id="").embed(["hola"])


@respx.mock
def test_embed_reintenta_una_vez_ante_429() -> None:
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(429, json={"errors": [{"message": "rate limited"}]}),
            httpx.Response(200, json=embedding_response([[0.3, 0.4]])),
        ]
    )

    vectors = make_embedder().embed(["verduleria"])

    assert vectors == [[0.3, 0.4]]
    assert route.call_count == 2


@respx.mock
def test_embed_sin_reintentos_ante_4xx_que_no_es_429() -> None:
    route = respx.post(URL).respond(400, json={"errors": [{"message": "bad request"}]})

    with pytest.raises(EmbeddingProviderError, match="400"):
        make_embedder().embed(["verduleria"])

    assert route.call_count == 1


@respx.mock
def test_embed_lanza_si_el_endpoint_sigue_fallando() -> None:
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(500, text="boom"),
            httpx.Response(500, text="boom"),
        ]
    )

    with pytest.raises(EmbeddingProviderError, match="500"):
        make_embedder().embed(["verduleria"])


def test_create_embedder_elige_cloudflare_por_defecto() -> None:
    assert isinstance(create_embedder(), CloudflareTextEmbedder)


def test_create_embedder_respeta_fastembed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "embedding_provider", "fastembed")

    from conco.guidance.embeddings import FastEmbedTextEmbedder

    assert isinstance(create_embedder(), FastEmbedTextEmbedder)


def test_create_embedder_rechaza_proveedores_desconocidos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "embedding_provider", "bogus")

    with pytest.raises(EmbeddingProviderError, match="bogus"):
        create_embedder()
