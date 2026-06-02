"""Pruebas de ingesta PDF → Qdrant (LangChain + RecursiveCharacterTextSplitter)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.configuracion import Configuracion, obtener_configuracion
from src.ingesta.protocolo_ingesta import (
    ResultadoIngesta,
    debe_omitir_ingesta,
    dividir_en_chunks,
    eliminar_vectores_procedimiento,
    extraer_documentos_desde_pdf,
    ingestar_tipo_procedimiento,
)
from src.persistencia.modelos import TipoProcedimiento
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from tests.api.conftest import PDF_FIXTURE_MINIMO


@pytest.fixture
def cfg_ingesta(monkeypatch: pytest.MonkeyPatch) -> Configuracion:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    monkeypatch.setenv("TAAM_QDRANT_COLLECTION", "taam_test_protocolos")
    monkeypatch.setenv("TAAM_CHUNK_SIZE", "800")
    monkeypatch.setenv("TAAM_CHUNK_OVERLAP", "120")
    obtener_configuracion.cache_clear()
    return obtener_configuracion()


def test_recursive_splitter_genera_chunk_index(cfg_ingesta: Configuracion) -> None:
    docs = [
        Document(page_content="A" * 400, metadata={"pagina": 1, "nombre_archivo": "protocolo.pdf"}),
        Document(page_content="B" * 500, metadata={"pagina": 2, "nombre_archivo": "protocolo.pdf"}),
    ]
    chunks = dividir_en_chunks(docs, cfg_ingesta)
    assert len(chunks) >= 2
    assert all("chunk_index" in c.metadata for c in chunks)
    assert chunks[0].metadata["chunk_index"] == 0


def test_debe_omitir_ingesta_cuando_ok() -> None:
    fila = TipoProcedimiento(
        codigo="x",
        nombre="y",
        formato_protocolo="pdf",
        indexacion_estado="ok",
        hash_pdf="abc",
        ruta_pdf="data/taam/procedimientos/x/protocolo.pdf",
    )
    assert debe_omitir_ingesta(fila) is True
    assert debe_omitir_ingesta(fila, forzar=True) is False


def test_eliminar_vectores_procedimiento_filtra_por_tipo_id(cfg_ingesta: Configuracion) -> None:
    cliente = QdrantClient(":memory:")
    coleccion = "test_delete_taam"
    cliente.create_collection(
        collection_name=coleccion,
        vectors_config=VectorParams(size=8, distance=Distance.COSINE),
    )
    otro_id = str(uuid.uuid4())
    tipo_id = uuid.uuid4()
    cliente.upsert(
        collection_name=coleccion,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.1] * 8,
                payload={
                    "metadata": {
                        "tipo_procedimiento_id": str(tipo_id),
                        "version": 1,
                    }
                },
            ),
            PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.2] * 8,
                payload={
                    "metadata": {
                        "tipo_procedimiento_id": otro_id,
                        "version": 1,
                    }
                },
            ),
        ],
    )
    eliminar_vectores_procedimiento(cliente, coleccion, tipo_id)
    restantes, _ = cliente.scroll(collection_name=coleccion, limit=10)
    assert len(restantes) == 1
    assert restantes[0].payload["metadata"]["tipo_procedimiento_id"] == otro_id


@pytest.mark.asyncio
async def test_ingestar_noop_si_ya_ok(
    workspace_tmp,
    cfg_ingesta: Configuracion,
) -> None:
    from src.api.main import crear_app
    from src.persistencia.motor import crear_motor_async, crear_session_factory

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        factory = app.state.session_factory
        async with factory() as sesion:
            repo = RepositorioTiposProcedimiento(sesion)
            fila = await repo.crear(
                codigo="noop-1",
                nombre="Procedimiento noop",
                ruta_pdf="data/taam/x/protocolo.pdf",
                hash_pdf="deadbeef",
                indexacion_estado="ok",
                qdrant_collection_version=1,
            )
            await sesion.commit()
            res = await ingestar_tipo_procedimiento(sesion, fila.id, cfg=cfg_ingesta)
    assert res.noop is True
    assert res.chunks == 0


@pytest.mark.asyncio
async def test_ingestar_pdf_con_mock_qdrant(
    workspace_tmp,
    cfg_ingesta: Configuracion,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.api.main import crear_app
    from src.api.servicios.almacenamiento_pdf import guardar_pdf_en_disco

    texto_largo = (
        "Protocolo postoperatorio de colecistectomia. " * 30
    )
    docs_fake = [
        Document(
            page_content=texto_largo,
            metadata={"pagina": 1, "nombre_archivo": "protocolo.pdf"},
        )
    ]

    monkeypatch.setattr(
        "src.ingesta.protocolo_ingesta.extraer_documentos_desde_pdf",
        lambda _ruta: (docs_fake, 1),
    )

    cliente = QdrantClient(":memory:")
    vector_store = MagicMock()
    vector_store.add_documents = MagicMock()

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        factory = app.state.session_factory
        async with factory() as sesion:
            repo = RepositorioTiposProcedimiento(sesion)
            fila = await repo.crear(
                codigo="ing-1",
                nombre="Ingesta prueba",
                formato_protocolo="pdf",
            )
            await sesion.flush()
            guardar_pdf_en_disco(fila.id, PDF_FIXTURE_MINIMO)
            await repo.actualizar(
                fila,
                ruta_pdf=f"data/taam/procedimientos/{fila.id}/protocolo.pdf",
                hash_pdf="hash123",
                indexacion_estado="pendiente",
                formato_protocolo="pdf",
            )
            await sesion.commit()

            with patch(
                "src.ingesta.protocolo_ingesta.crear_vector_store",
                return_value=vector_store,
            ):
                with patch(
                    "src.ingesta.protocolo_ingesta.obtener_cliente_qdrant",
                    return_value=cliente,
                ):
                    with patch(
                        "src.ingesta.protocolo_ingesta.ingestar_chunks_en_qdrant",
                    ) as mock_upsert:
                        res = await ingestar_tipo_procedimiento(
                            sesion,
                            fila.id,
                            cfg=cfg_ingesta,
                            cliente_qdrant=cliente,
                        )
                mock_upsert.assert_called_once()

            assert res.noop is False
            assert res.chunks >= 1
            assert res.paginas == 1

            async with factory() as sesion2:
                fila2 = await RepositorioTiposProcedimiento(sesion2).obtener_por_id(fila.id)
            assert fila2 is not None
            assert fila2.indexacion_estado == "ok"
            assert fila2.qdrant_collection_version == 1
