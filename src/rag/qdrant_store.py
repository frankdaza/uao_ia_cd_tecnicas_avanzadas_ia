"""Cliente Qdrant reusable y QdrantVectorStore para LlamaIndex."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams

from src.api.configuracion import Configuracion, obtener_configuracion

if TYPE_CHECKING:
    from llama_index.vector_stores.qdrant import QdrantVectorStore

logger = logging.getLogger(__name__)

_lock_cliente = threading.Lock()
_cliente_qdrant: QdrantClient | None = None
_log_cliente_emitido = False


def distancia_desde_settings(valor: str) -> Distance:
    """Convierte el literal de settings (p. ej. ``Cosine``) al enum de Qdrant."""
    clave = valor.strip()
    por_nombre = {d.value: d for d in Distance}
    if clave in por_nombre:
        return por_nombre[clave]
    raise ValueError(
        f"Distancia Qdrant no soportada: {valor!r}. "
        f"Valores permitidos: {sorted(por_nombre)!r}"
    )


def reiniciar_cliente_qdrant() -> None:
    """
    Cierra el cliente singleton y lo deja en ``None`` (principalmente para tests).

    No es seguro llamar con peticiones concurrentes al cliente anterior.
    """
    global _cliente_qdrant, _log_cliente_emitido
    with _lock_cliente:
        if _cliente_qdrant is not None:
            try:
                _cliente_qdrant.close()
            except Exception:
                logger.debug("Cierre de cliente Qdrant ignorado", exc_info=True)
            _cliente_qdrant = None
        _log_cliente_emitido = False


def obtener_qdrant_client(
    configuracion: Configuracion | None = None,
) -> QdrantClient:
    """
    Retorna un ``QdrantClient`` singleton por proceso (thread-safe).

    Si ``qdrant_url`` es ``:memory:`` (ignorando mayusculas), usa
    ``QdrantClient(location=\":memory:\")`` para pruebas locales.
    """
    global _cliente_qdrant, _log_cliente_emitido
    if _cliente_qdrant is not None:
        return _cliente_qdrant

    with _lock_cliente:
        if _cliente_qdrant is not None:
            return _cliente_qdrant

        cfg = configuracion or obtener_configuracion()
        url = cfg.qdrant_url.strip()
        if url.lower() == ":memory:":
            cliente = QdrantClient(location=":memory:")
        else:
            api_key = cfg.qdrant_api_key
            if api_key is not None and not str(api_key).strip():
                api_key = None
            cliente = QdrantClient(url=url, api_key=api_key)

        _cliente_qdrant = cliente

        if not _log_cliente_emitido:
            modo = "memoria" if url.lower() == ":memory:" else "remoto"
            logger.info(
                "Qdrant: modo=%s coleccion_config=%s distancia=%s",
                modo,
                cfg.qdrant_collection,
                cfg.qdrant_distance,
            )
            _log_cliente_emitido = True

        return _cliente_qdrant


def _vector_params_desde_coleccion(info: object) -> VectorParams | None:
    """Extrae ``VectorParams`` principal de la respuesta ``get_collection``."""
    params = getattr(info.config, "params", None)
    if params is None:
        return None
    vectors = getattr(params, "vectors", None)
    if vectors is None:
        return None
    if isinstance(vectors, dict):
        if not vectors:
            return None
        primero = next(iter(vectors.values()))
        return primero if isinstance(primero, VectorParams) else None
    if isinstance(vectors, VectorParams):
        return vectors
    return None


def asegurar_coleccion(
    cliente: QdrantClient,
    nombre: str,
    dims: int,
    distancia: Distance,
) -> None:
    """
    Crea la coleccion si no existe; si existe, valida dimensiones y distancia.

    Raises:
        ValueError: si la coleccion existe pero ``size`` o ``distance`` no coinciden.
    """
    if not cliente.collection_exists(nombre):
        cliente.create_collection(
            collection_name=nombre,
            vectors_config=VectorParams(size=dims, distance=distancia),
        )
        asegurar_indices_payload_filtrables(cliente, nombre)
        return

    info = cliente.get_collection(nombre)
    existente = _vector_params_desde_coleccion(info)
    if existente is None:
        raise ValueError(
            f"No se pudo leer la configuracion de vectores de la coleccion {nombre!r}"
        )
    if int(existente.size) != int(dims):
        raise ValueError(
            f"La coleccion {nombre!r} existe con size={existente.size}, "
            f"se esperaba embedding_dims={dims}. Ajusta EMBEDDING_DIMS o usa otra coleccion."
        )
    if existente.distance != distancia:
        raise ValueError(
            f"La coleccion {nombre!r} existe con distance={existente.distance!s}, "
            f"se esperaba {distancia!s}. Ajusta QDRANT_DISTANCE."
        )

    asegurar_indices_payload_filtrables(cliente, nombre)


def asegurar_indices_payload_filtrables(cliente: QdrantClient, nombre: str) -> None:
    """
    Crea indices de payload para filtros RAG (``tipo_pagina``, ``especialidad``, ...).

    En cliente ``:memory:`` Qdrant emite advertencia y el indice no tiene efecto; en
    servidor HTTP los errores por campo ya indexado se ignoran de forma segura.
    """
    keyword = models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD)
    campos = ("tipo_pagina", "especialidad", "sedes", "seccion")
    for campo in campos:
        try:
            cliente.create_payload_index(
                collection_name=nombre,
                field_name=campo,
                field_schema=keyword,
            )
        except Exception as exc:  # noqa: BLE001
            texto = str(exc).lower()
            if "already exists" in texto or "duplicate" in texto:
                logger.debug(
                    "Qdrant: indice payload %r en %r ya existia (%s)",
                    campo,
                    nombre,
                    exc,
                )
                continue
            logger.warning(
                "Qdrant: no se pudo crear indice payload %r en %r (%s). "
                "En modo local :memory: es esperable; en servidor revisa permisos y version.",
                campo,
                nombre,
                exc,
            )


def obtener_vector_store(
    configuracion: Configuracion | None = None,
) -> QdrantVectorStore:
    """
    Construye un ``QdrantVectorStore`` de LlamaIndex con coleccion asegurada.

    La coleccion se crea o valida con ``embedding_dims`` y ``qdrant_distance`` de settings.
    """
    from llama_index.vector_stores.qdrant import QdrantVectorStore

    cfg = configuracion or obtener_configuracion()
    cliente = obtener_qdrant_client(cfg)
    distancia = distancia_desde_settings(cfg.qdrant_distance)
    asegurar_coleccion(cliente, cfg.qdrant_collection, cfg.embedding_dims, distancia)
    return QdrantVectorStore(
        collection_name=cfg.qdrant_collection,
        client=cliente,
        text_key="texto",
    )
