"""Pruebas de cliente Qdrant, asegurar_coleccion y vector store."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from qdrant_client.models import Distance

from src.api.configuracion import obtener_configuracion
from src.rag.qdrant_store import (
    asegurar_coleccion,
    distancia_desde_settings,
    obtener_qdrant_client,
    obtener_vector_store,
    reiniciar_cliente_qdrant,
)


@pytest.fixture
def qdrant_memoria(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    yield
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()


def test_obtener_qdrant_client_singleton_memoria(qdrant_memoria: None) -> None:
    c1 = obtener_qdrant_client()
    c2 = obtener_qdrant_client()
    assert c1 is c2


def test_asegurar_coleccion_idempotente(qdrant_memoria: None) -> None:
    cliente = obtener_qdrant_client()
    asegurar_coleccion(cliente, "col_test", 8, Distance.COSINE)
    asegurar_coleccion(cliente, "col_test", 8, Distance.COSINE)


def test_asegurar_coleccion_falla_si_dims_distintas(qdrant_memoria: None) -> None:
    cliente = obtener_qdrant_client()
    asegurar_coleccion(cliente, "col_dims", 4, Distance.COSINE)
    with pytest.raises(ValueError, match="size=4"):
        asegurar_coleccion(cliente, "col_dims", 8, Distance.COSINE)


def test_asegurar_coleccion_falla_si_distancia_distinta(qdrant_memoria: None) -> None:
    cliente = obtener_qdrant_client()
    asegurar_coleccion(cliente, "col_dist", 4, Distance.COSINE)
    with pytest.raises(ValueError, match="distance="):
        asegurar_coleccion(cliente, "col_dist", 4, Distance.DOT)


def test_obtener_vector_store_memoria(
    qdrant_memoria: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QDRANT_COLLECTION", "vs_mem")
    monkeypatch.setenv("EMBEDDING_DIMS", "16")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    vs = obtener_vector_store()
    assert vs.collection_name == "vs_mem"


def test_distancia_desde_settings_enum() -> None:
    assert distancia_desde_settings("Cosine") == Distance.COSINE
    assert distancia_desde_settings("Dot") == Distance.DOT


def test_distancia_desde_settings_invalida() -> None:
    with pytest.raises(ValueError, match="no soportada"):
        distancia_desde_settings("Hamming")


def test_settings_distancia_invalida_en_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_DISTANCE", "Hamming")
    obtener_configuracion.cache_clear()
    with pytest.raises(ValidationError):
        obtener_configuracion()
