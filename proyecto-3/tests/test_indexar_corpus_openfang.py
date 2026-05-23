"""Pruebas de ingesta corpus -> memoria OpenFang (sin red)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingesta.cliente_memoria import ClienteMemoriaOpenFang, embedding_a_bytes
from src.ingesta.fragmentar import fragmentar
from src.ingesta.fuentes import OpcionesFuentes, planificar_todas_las_fuentes
from src.ingesta.idempotencia import calcular_content_hash, memory_id_desde_source_id
from src.ingesta.markdown import leer_markdown
from src.ingesta.modelos import ChunkPlanificado
from src.ingesta.pdf_taam import extraer_texto_pdf
from src.ingesta.pipeline import OpcionesIngesta, ejecutar_ingesta


def test_fragmentar_solape() -> None:
    texto = "a" * 2500
    partes = fragmentar(texto, tam=1000, solape=150)
    assert len(partes) == 3
    assert len(partes[0]) == 1000
    assert partes[1].startswith("a" * 150)


def test_leer_markdown_front_matter(tmp_path: Path) -> None:
    ruta = tmp_path / "doc.md"
    ruta.write_text(
        "---\ntitle: Cuidados\n---\n\nTexto del cuerpo.\n",
        encoding="utf-8",
    )
    meta, cuerpo = leer_markdown(ruta)
    assert meta.get("title") == "Cuidados"
    assert "Texto del cuerpo" in cuerpo


def test_planificar_sin_fuentes(tmp_path: Path) -> None:
    chunks, n_md, n_pdf, _ = planificar_todas_las_fuentes(
        tmp_path,
        OpcionesFuentes(),
    )
    assert chunks == []
    assert n_md == 0
    assert n_pdf == 0


def test_sin_fuentes_exit_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAO_WORKSPACE_ROOT", str(tmp_path))
    from src.configuracion import obtener_configuracion

    obtener_configuracion.cache_clear()
    stats = ejecutar_ingesta(
        obtener_configuracion(),
        OpcionesIngesta(dry_run=True),
    )
    assert "sin_fuentes" in stats.advertencias


def test_pdf_sin_texto_warning_no_abort(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    ruta = tmp_path / "vacio.pdf"
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    with ruta.open("wb") as archivo:
        escritor.write(archivo)

    assert extraer_texto_pdf(ruta) is None

    raiz = tmp_path / "ws"
    (raiz / "data" / "taam").mkdir(parents=True)
    destino = raiz / "data" / "taam" / "vacio.pdf"
    destino.write_bytes(ruta.read_bytes())

    chunks, _, n_pdf, omitidos = planificar_todas_las_fuentes(
        raiz,
        OpcionesFuentes(incluir_markdown=False, incluir_pdf=True),
    )
    assert n_pdf == 1
    assert chunks == []
    assert omitidos >= 1


def _crear_db_memories(ruta_db: Path) -> None:
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta_db)
    conn.execute(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'episodic',
            confidence REAL NOT NULL DEFAULT 1.0,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            accessed_at TEXT NOT NULL,
            access_count INTEGER NOT NULL DEFAULT 0,
            deleted INTEGER NOT NULL DEFAULT 0,
            embedding BLOB DEFAULT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def test_idempotencia_cliente_sqlite(tmp_path: Path) -> None:
    db = tmp_path / "openfang.db"
    _crear_db_memories(db)
    agent_id = "00000000-0000-0000-0000-000000000099"
    chunk = ChunkPlanificado(
        source_id="markdown:test.md:0",
        content_hash=calcular_content_hash("hola mundo"),
        memory_id=memory_id_desde_source_id("markdown:test.md:0"),
        texto="hola mundo",
        tipo_fuente="markdown",
        ruta_relativa="data/markdown/test.md",
        titulo="Test",
        chunk_index=0,
    )
    vector = [0.1] * 8
    cliente = ClienteMemoriaOpenFang(db, agent_id)

    s1 = cliente.escribir_chunks([chunk], [vector])
    assert s1.chunks_insertados == 1
    assert s1.chunks_omitidos == 0

    s2 = cliente.escribir_chunks([chunk], [vector])
    assert s2.chunks_insertados == 0
    assert s2.chunks_omitidos == 1

    chunk2 = ChunkPlanificado(
        source_id=chunk.source_id,
        content_hash=calcular_content_hash("texto nuevo"),
        memory_id=chunk.memory_id,
        texto="texto nuevo",
        tipo_fuente=chunk.tipo_fuente,
        ruta_relativa=chunk.ruta_relativa,
        titulo=chunk.titulo,
        chunk_index=chunk.chunk_index,
    )
    s3 = cliente.escribir_chunks([chunk2], [vector])
    assert s3.chunks_actualizados == 1


def test_dry_run_no_escribe_db(tmp_path: Path) -> None:
    raiz = tmp_path / "ws"
    md = raiz / "data" / "markdown"
    md.mkdir(parents=True)
    (md / "uno.md").write_text("---\ntitle: Uno\n---\n\nContenido de prueba largo.\n" * 50, encoding="utf-8")

    db = tmp_path / "db" / "openfang.db"
    _crear_db_memories(db)

    class CfgFake:
        def raiz_workspace(self) -> Path:
            return raiz

        def ruta_db_openfang(self) -> Path:
            return db

        def resolver_agent_id_openfang(self) -> str:
            return "agent-fake"

        openfang_api_url = "http://127.0.0.1:9"

        def exigir_openai_api_key(self) -> str:
            raise AssertionError("no debe llamar OpenAI en dry-run")

    stats = ejecutar_ingesta(CfgFake(), OpcionesIngesta(dry_run=True, limite=1))
    assert stats.chunks_planificados > 0
    assert stats.chunks_insertados == 0
    conn = sqlite3.connect(db)
    count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    conn.close()
    assert count == 0


def test_embedding_a_bytes_roundtrip() -> None:
    vector = [1.0, -2.5, 0.0]
    blob = embedding_a_bytes(vector)
    assert len(blob) == len(vector) * 4


@patch("src.ingesta.pipeline.publicar_resumen_ingesta", return_value=True)
@patch("src.ingesta.pipeline.crear_embedder_openai")
def test_ejecutar_ingesta_mock_sin_red(
    mock_embedder_factory: MagicMock,
    _mock_kv: MagicMock,
    tmp_path: Path,
) -> None:
    raiz = tmp_path / "ws"
    md = raiz / "data" / "markdown"
    md.mkdir(parents=True)
    (md / "a.md").write_text("---\ntitle: A\n---\n\n" + ("parrafo " * 200), encoding="utf-8")

    db = tmp_path / "openfang.db"
    _crear_db_memories(db)

    mock_embedder_factory.return_value = lambda textos: [[0.0] * 4 for _ in textos]

    class CfgFake:
        def raiz_workspace(self) -> Path:
            return raiz

        def ruta_db_openfang(self) -> Path:
            return db

        def resolver_agent_id_openfang(self) -> str:
            return "agent-1"

        openfang_api_url = "http://127.0.0.1:9"
        openai_embedding_model = "text-embedding-3-small"

        def exigir_openai_api_key(self) -> str:
            return "sk-test"

    with patch("src.ingesta.pipeline.daemon_openfang_activo", return_value=False):
        stats = ejecutar_ingesta(CfgFake(), OpcionesIngesta(limite=1))
    assert stats.chunks_insertados >= 1
