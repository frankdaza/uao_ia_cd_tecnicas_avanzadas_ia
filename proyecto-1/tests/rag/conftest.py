"""Fixtures compartidos RAG (embeddings y reranker falsos, golden minimo)."""

from __future__ import annotations

import hashlib
from typing import Any

import pytest
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import ConfigDict, Field


class FakeEmbeddingsDeterministas(BaseEmbedding):
    """
    Embeddings reproducibles por hash del texto (deterministas en CI).

    El vector se normaliza a norma ~1 para compatibilidad con similitud coseno.
    """

    model_config = ConfigDict(extra="ignore")

    dimension: int = Field(
        default=8, ge=2, le=8192, description="Dimension del vector denso."
    )

    def _vector_desde_texto(self, texto: str) -> list[float]:
        h = hashlib.sha256(texto.encode("utf-8")).digest()
        valores = [float(h[i % len(h)]) / 255.0 + 1e-6 for i in range(self.dimension)]
        # Normaliza (evita vector nulo)
        s = sum(v * v for v in valores) ** 0.5
        if s < 1e-9:
            return [1.0] + [0.0] * (self.dimension - 1)
        return [v / s for v in valores]

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._vector_desde_texto(f"q:{query}")

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._vector_desde_texto(f"t:{text}")

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)


class FakeRerankerDeterminista:
    """Reranker de prueba: score proporcional al indice (estable por orden de entrada)."""

    def puntuar(
        self,
        consulta: str,
        textos: list[str],
        **_kwargs: object,
    ) -> list[float]:
        _ = consulta
        return [float(i) for i in range(len(textos))]


class FakeRerankerPromueveIndice:
    """Asigna score maximo al candidato en ``indice_preferido`` (0-based)."""

    def __init__(self, indice_preferido: int) -> None:
        self._indice = int(indice_preferido)

    def puntuar(
        self,
        consulta: str,
        textos: list[str],
        **_kwargs: object,
    ) -> list[float]:
        _ = consulta
        n = len(textos)
        if n <= 0:
            return []
        out = [1.0] * n
        if 0 <= self._indice < n:
            out[self._indice] = 100.0
        return out


class FakeVectorStoreDocumentado:
    """
    Placeholder TASK-83: el recuperador productivo usa ``QdrantVectorStore``.

    Los tests de integracion del pipeline usan Qdrant en memoria (``location=\":memory:\"``)
    con fixtures locales; esta clase queda como ancla semantica para futuros mocks mas ligeros.
    """

    pass


@pytest.fixture
def fake_embeddings_deterministas() -> FakeEmbeddingsDeterministas:
    return FakeEmbeddingsDeterministas(dimension=8)


@pytest.fixture
def fake_reranker_determinista() -> FakeRerankerDeterminista:
    return FakeRerankerDeterminista()


@pytest.fixture
def golden_minimo() -> list[dict[str, Any]]:
    """Muestras cortas alineadas a tokens MOCK_LLM / consultas RAG de humo."""
    return [
        {"id": "g1", "consulta": "e2e7001 politicas institucionales"},
        {"id": "g2", "consulta": "e2e7002 horario PBX"},
        {"id": "g3", "consulta": "mision vision institucional"},
    ]
