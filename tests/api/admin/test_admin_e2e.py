"""Integracion admin (PATCH) con streaming del agente (MOCK_LLM, httpx AsyncClient)."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.configuracion import obtener_configuracion
from src.api.dependencias import obtener_bundle_runtime_agente, obtener_sesion_db
from src.api.factoria_grafo_agente import construir_grafo_agente_mock_llm
from src.api.main import crear_app
from src.persistencia.modelos import ConfigAdminM2, Usuario
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain
from src.rag.runtime.qdrant_store import reiniciar_cliente_qdrant
from tests.conftest import pool_memoria_falso


def _parsear_eventos_sse(cuerpo: bytes) -> list[tuple[str, dict[str, Any]]]:
    salida: list[tuple[str, dict[str, Any]]] = []
    buffer = cuerpo.decode("utf-8", errors="replace")
    evento_actual: str | None = None
    for linea in buffer.splitlines():
        if linea.startswith("event:"):
            evento_actual = linea.split(":", 1)[1].strip()
        elif linea.startswith("data:") and evento_actual:
            raw = linea[5:].strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            salida.append((evento_actual, payload))
            evento_actual = None
    return salida


@dataclass
class EstadoSesionCompartida:
    """Estado mutable compartido entre peticiones HTTP falsas (sin PostgreSQL)."""

    config: ConfigAdminM2 | None = None
    usuario: Usuario | None = None


class SesionFalsaCompartida:
    """Sesion minima compatible con ``ServicioAgenteM2Config`` y ``RepositorioUsuarios.get``."""

    def __init__(self, estado: EstadoSesionCompartida) -> None:
        self._e = estado

    async def get(self, model: type, ident: object) -> object | None:
        if model is ConfigAdminM2 and ident == 1:
            return self._e.config
        if (
            model is Usuario
            and self._e.usuario is not None
            and ident == self._e.usuario.id
        ):
            return self._e.usuario
        return None

    async def execute(self, _stmt: object) -> object:
        res = MagicMock()
        res.scalars.return_value.first.return_value = self._e.config
        return res

    def add(self, obj: object) -> None:
        if isinstance(obj, ConfigAdminM2):
            self._e.config = obj

    async def flush(self) -> None:
        if self._e.config is not None:
            self._e.config.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        return

    async def rollback(self) -> None:
        return


@pytest.fixture(autouse=True)
def limpiar_cache_config() -> None:
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


@pytest.mark.asyncio
async def test_patch_rag_mmr_lambda_reflejado_en_bundle_del_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tras PATCH de ``rag_mmr_lambda``, el bundle del siguiente stream expone el mismo valor."""
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-t83")
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("QDRANT_COLLECTION", "corpus_t83_bundle")
    monkeypatch.setenv("RAG_RERANKER_HABILITADO", "0")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()

    class _EmbFijo:
        def get_query_embedding(self, texto: str) -> list[float]:
            return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    monkeypatch.setattr(
        "src.rag.runtime.embeddings.obtener_embeddings", lambda _c=None: _EmbFijo()
    )

    from qdrant_client.models import Distance, PointStruct, VectorParams

    from src.rag.runtime.qdrant_store import obtener_qdrant_client

    cfg = obtener_configuracion()
    cli = obtener_qdrant_client(cfg)
    nombre = cfg.qdrant_collection
    cli.create_collection(
        nombre, vectors_config=VectorParams(size=8, distance=Distance.COSINE)
    )
    cli.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="f0000001-0001-4001-8001-000000000001",
                vector=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                payload={
                    "archivo": "t83.md",
                    "titulo": "T83",
                    "source_url": "",
                    "chunk_index": 0,
                    "texto": "contenido de prueba task 83",
                },
            )
        ],
    )

    estado = EstadoSesionCompartida()
    uid = uuid.UUID("f0000003-0003-4003-8003-000000000003")
    estado.usuario = Usuario(
        id=uid, documento_identidad="doc-t83", nombre="Usuario T83"
    )

    async def _sesion_falsa() -> AsyncIterator[SesionFalsaCompartida]:
        yield SesionFalsaCompartida(estado)

    bundles: list = []

    async def _bundle_registrado(
        sesion: AsyncSession = Depends(obtener_sesion_db),
    ) -> Any:
        from src.api.servicios.agente_m2_config import ServicioAgenteM2Config

        svc = ServicioAgenteM2Config(sesion)
        b = await svc.construir_bundle_tiempo_ejecucion()
        bundles.append(b)
        return b

    app = crear_app()
    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    app.dependency_overrides[obtener_bundle_runtime_agente] = _bundle_registrado
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.psycopg_pool = pool_memoria_falso()
            app.state.grafo_agente = construir_grafo_agente_mock_llm(cfg)
            headers_admin = {
                "X-Admin-Key": "clave-admin-t83",
                "Content-Type": "application/json",
            }
            r_patch = await client.patch(
                "/api/admin/config",
                headers=headers_admin,
                json={"version": 0, "rag_mmr_lambda": 0.3},
            )
            assert r_patch.status_code == 200
            assert abs(float(r_patch.json()["rag_mmr_lambda"]) - 0.3) < 1e-9

            sid = sesion_id_memoria_langchain(uid)
            async with client.stream(
                "POST",
                "/api/agente/stream",
                headers={"X-Session-Id": sid},
                json={
                    "session_id": sid,
                    "pregunta": "e2e7001 consulta de prueba task 83",
                    "primer_turno": True,
                },
            ) as resp:
                assert resp.status_code == 200
                cuerpo = await resp.aread()
    finally:
        app.dependency_overrides.clear()

    assert len(bundles) >= 1
    assert abs(bundles[0].rag_mmr_lambda - 0.3) < 1e-9
    eventos = _parsear_eventos_sse(cuerpo)
    assert not any(
        e == "error" and isinstance(p, dict) and p.get("codigo") == "agente_error"
        for e, p in eventos
    )


@pytest.mark.asyncio
async def test_segundo_patch_con_version_obsoleta_devuelve_409(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-t83-409")
    estado = EstadoSesionCompartida()
    estado.config = ConfigAdminM2(
        id=1,
        version=2,
        updated_at=datetime.now(UTC),
    )

    async def _sesion_falsa() -> AsyncIterator[SesionFalsaCompartida]:
        yield SesionFalsaCompartida(estado)

    app = crear_app()
    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        h = {"X-Admin-Key": "clave-admin-t83-409", "Content-Type": "application/json"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r_conflict = await client.patch(
                "/api/admin/config",
                headers=h,
                json={"version": 1, "rag_mmr_lambda": 0.11},
            )
    finally:
        app.dependency_overrides.clear()

    assert r_conflict.status_code == 409


@pytest.mark.asyncio
async def test_stream_reranker_falla_emite_fuentes_sin_codigo_agente_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si el cross-encoder falla, el pipeline degrada y el SSE no termina en ``agente_error``."""
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-t83-rnk")
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    monkeypatch.setenv("QDRANT_URL", ":memory:")
    monkeypatch.setenv("EMBEDDING_DIMS", "8")
    monkeypatch.setenv("QDRANT_COLLECTION", "corpus_t83_rnk")
    monkeypatch.setenv("RAG_RERANKER_HABILITADO", "0")
    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    from src.rag.runtime.reranker_cross_encoder import RerankerCrossEncoder

    RerankerCrossEncoder.reiniciar_singletons_prueba()

    class _EmbFijo:
        def get_query_embedding(self, texto: str) -> list[float]:
            return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    monkeypatch.setattr(
        "src.rag.runtime.embeddings.obtener_embeddings", lambda _c=None: _EmbFijo()
    )

    def _cross_encoder_falso() -> type:
        class _CE:
            def __init__(self, modelo: str = "") -> None:
                _ = modelo

            def predict(self, *args: object, **kwargs: object) -> list[float]:
                raise RuntimeError("modelo reranker no disponible en prueba")

        return _CE

    monkeypatch.setattr(
        "src.rag.runtime.reranker_cross_encoder._importar_cross_encoder",
        _cross_encoder_falso,
    )

    from qdrant_client.models import Distance, PointStruct, VectorParams

    from src.rag.runtime.qdrant_store import obtener_qdrant_client

    cfg = obtener_configuracion()
    cli = obtener_qdrant_client(cfg)
    nombre = cfg.qdrant_collection
    cli.create_collection(
        nombre, vectors_config=VectorParams(size=8, distance=Distance.COSINE)
    )
    cli.upsert(
        collection_name=nombre,
        points=[
            PointStruct(
                id="f0000002-0002-4002-8002-000000000002",
                vector=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                payload={
                    "archivo": "rnk.md",
                    "titulo": "Rnk",
                    "source_url": "",
                    "chunk_index": 0,
                    "texto": "texto rerank prueba",
                },
            )
        ],
    )

    estado = EstadoSesionCompartida()
    uid = uuid.UUID("f0000004-0004-4004-8004-000000000004")
    estado.usuario = Usuario(
        id=uid, documento_identidad="doc-t83-rnk", nombre="Usuario Rnk"
    )

    async def _sesion_falsa() -> AsyncIterator[SesionFalsaCompartida]:
        yield SesionFalsaCompartida(estado)

    app = crear_app()
    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        headers_admin = {
            "X-Admin-Key": "clave-admin-t83-rnk",
            "Content-Type": "application/json",
        }
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            app.state.psycopg_pool = pool_memoria_falso()
            app.state.grafo_agente = construir_grafo_agente_mock_llm(cfg)
            await client.patch(
                "/api/admin/config",
                headers=headers_admin,
                json={
                    "version": 0,
                    "rag_reranker_habilitado": True,
                    "rag_mmr_habilitado": True,
                    "rag_mmr_lambda": 0.5,
                    "rag_reranker_modelo": "modelo-invalido-xyz",
                },
            )

            sid = sesion_id_memoria_langchain(uid)
            async with client.stream(
                "POST",
                "/api/agente/stream",
                headers={"X-Session-Id": sid},
                json={
                    "session_id": sid,
                    "pregunta": "e2e7001 pregunta rerank degradado",
                    "primer_turno": True,
                },
            ) as resp:
                assert resp.status_code == 200
                cuerpo = await resp.aread()
    finally:
        app.dependency_overrides.clear()

    eventos = _parsear_eventos_sse(cuerpo)
    errores_agente = [
        p
        for e, p in eventos
        if e == "error" and isinstance(p, dict) and p.get("codigo") == "agente_error"
    ]
    assert errores_agente == []
    assert any(e == "fuentes" for e, _ in eventos)
    assert any(e == "final" for e, _ in eventos)
