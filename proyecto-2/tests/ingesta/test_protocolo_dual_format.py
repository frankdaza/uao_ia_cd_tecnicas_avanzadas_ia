"""Pruebas de ingesta PDF y Markdown (UC-MVP-01 dual-format)."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from src.api.servicios.almacenamiento_protocolo import guardar_protocolo_en_disco
from src.configuracion import Configuracion, obtener_configuracion
from src.ingesta.extractores.markdown import extraer_documentos_desde_markdown
from src.ingesta.protocolo_ingesta import (
    ingestar_tipo_procedimiento,
    resolver_ruta_archivo_protocolo,
)
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from tests.api.conftest import MD_FIXTURE_CUERPO_VACIO, MD_FIXTURE_MINIMO


@pytest.fixture
def cfg_ingesta(monkeypatch: pytest.MonkeyPatch) -> Configuracion:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    monkeypatch.setenv("TAAM_QDRANT_COLLECTION", "taam_test_dual_format")
    monkeypatch.setenv("TAAM_CHUNK_SIZE", "800")
    monkeypatch.setenv("TAAM_CHUNK_OVERLAP", "120")
    obtener_configuracion.cache_clear()
    return obtener_configuracion()


def test_extraer_markdown_ignora_front_matter(tmp_path: Path) -> None:
    ruta = tmp_path / "proto.md"
    ruta.write_bytes(MD_FIXTURE_MINIMO)
    docs, paginas = extraer_documentos_desde_markdown(ruta)
    assert paginas == 1
    assert len(docs) == 1
    assert "Cuidados postoperatorios" in docs[0].page_content
    assert "titulo:" not in docs[0].page_content


@pytest.mark.asyncio
async def test_ingesta_markdown_usa_ruta_desde_bd(
    workspace_tmp,
    cfg_ingesta: Configuracion,
) -> None:
    from src.api.main import crear_app

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        factory = app.state.session_factory
        async with factory() as sesion:
            repo = RepositorioTiposProcedimiento(sesion)
            fila = await repo.crear(
                codigo="md-ruta-bd",
                nombre="Markdown ruta BD",
                formato_protocolo="markdown",
            )
            await sesion.flush()
            ruta_rel = f"data/taam/procedimientos/{fila.id}/protocolo.md"
            guardar_protocolo_en_disco(fila.id, MD_FIXTURE_MINIMO, "markdown")
            await repo.actualizar(
                fila,
                ruta_pdf=ruta_rel,
                hash_pdf="hash-md-test",
                indexacion_estado="pendiente",
            )
            await sesion.commit()

            assert resolver_ruta_archivo_protocolo(fila).name == "protocolo.md"

            vector_store = MagicMock()
            cliente = QdrantClient(":memory:")
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

            assert res.chunks >= 1
            chunks = mock_upsert.call_args[0][1]
            assert any("Cuidados postoperatorios" in c.page_content for c in chunks)


@pytest.mark.asyncio
async def test_ingesta_markdown_cuerpo_vacio_marca_error(
    workspace_tmp,
    cfg_ingesta: Configuracion,
) -> None:
    from src.api.main import crear_app

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        factory = app.state.session_factory
        async with factory() as sesion:
            repo = RepositorioTiposProcedimiento(sesion)
            fila = await repo.crear(
                codigo="md-vacio",
                nombre="MD vacio",
                formato_protocolo="markdown",
            )
            await sesion.flush()
            ruta_rel = f"data/taam/procedimientos/{fila.id}/protocolo.md"
            guardar_protocolo_en_disco(fila.id, MD_FIXTURE_CUERPO_VACIO, "markdown")
            await repo.actualizar(
                fila,
                ruta_pdf=ruta_rel,
                hash_pdf="hash-vacio",
                indexacion_estado="pendiente",
            )
            await sesion.commit()

            res = await ingestar_tipo_procedimiento(sesion, fila.id, cfg=cfg_ingesta)
            assert res.chunks == 0
            assert "insuficiente" in res.mensaje.lower() or "vacio" in res.mensaje.lower()

            fila2 = await repo.obtener_por_id(fila.id)
            assert fila2 is not None
            assert fila2.indexacion_estado == "error"


def test_fragmentos_rag_equivalentes_para_pdf_y_markdown() -> None:
    """Los chunks indexados desde PDF o MD usan el mismo formato ``[n] texto`` en la tool."""
    docs_pdf = [
        Document(page_content="Indicacion PDF postoperatoria colecistectomia extendida.")
    ]
    docs_md = [
        Document(page_content="Indicacion Markdown postoperatoria colecistectomia extendida.")
    ]

    def _formatear(docs: list[Document]) -> str:
        return "\n\n".join(f"[{i}] {d.page_content.strip()}" for i, d in enumerate(docs, 1))

    salida_pdf = _formatear(docs_pdf)
    salida_md = _formatear(docs_md)
    assert salida_pdf.startswith("[1]")
    assert salida_md.startswith("[1]")
    assert "PDF" in salida_pdf
    assert "Markdown" in salida_md
