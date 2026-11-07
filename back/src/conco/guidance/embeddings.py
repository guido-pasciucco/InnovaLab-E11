from functools import cache

from fastembed import TextEmbedding

from conco.config import settings


@cache
def _load_model(model_name: str) -> TextEmbedding:
    """Carga el modelo una sola vez por proceso: la primera vez lo descarga (~220 MB)."""
    return TextEmbedding(model_name=model_name)


class FastEmbedTextEmbedder:
    """Adaptador: corre el modelo de embeddings dentro del mismo proceso de la API (ONNX)."""

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embedding_model

    @property
    def model_name(self) -> str:
        return self._model_name

    def warm_up(self) -> None:
        """Carga el modelo antes de la primera búsqueda, para que no tarde la primera respuesta."""
        _load_model(self._model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = _load_model(self._model_name)
        return [vector.tolist() for vector in model.embed(texts)]
