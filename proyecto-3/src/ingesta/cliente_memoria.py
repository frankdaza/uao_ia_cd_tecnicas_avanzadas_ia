"""Escritura idempotente en tabla ``memories`` de OpenFang (SQLite)."""

from __future__ import annotations

import json
import logging
import sqlite3
import struct
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from src.ingesta.modelos import ChunkPlanificado, EstadisticasIngesta

logger = logging.getLogger(__name__)

_SCOPE_SEMANTIC = "semantic"
_SOURCE_DOCUMENT = '"Document"'


def embedding_a_bytes(vector: Sequence[float]) -> bytes:
    """Serializa embedding como f32 little-endian (formato OpenFang)."""
    return struct.pack(f"<{len(vector)}f", *vector)


def _ahora_rfc3339() -> str:
    return datetime.now(UTC).isoformat()


def _metadata_json(chunk: ChunkPlanificado) -> str:
    return json.dumps(
        {
            "source_id": chunk.source_id,
            "content_hash": chunk.content_hash,
            "tipo_fuente": chunk.tipo_fuente,
            "ruta_relativa": chunk.ruta_relativa,
            "titulo": chunk.titulo,
            "chunk_index": chunk.chunk_index,
        },
        ensure_ascii=False,
    )


class ClienteMemoriaOpenFang:
    """Cliente SQLite para memoria semantica del agente."""

    def __init__(
        self,
        ruta_db: Path,
        agent_id: str,
        *,
        timeout_seg: float = 30.0,
    ) -> None:
        self._ruta_db = ruta_db
        self._agent_id = agent_id
        self._timeout = timeout_seg

    def conectar(self) -> sqlite3.Connection:
        self._ruta_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._ruta_db), timeout=self._timeout)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _hash_existente(self, conn: sqlite3.Connection, memory_id: str) -> str | None:
        fila = conn.execute(
            "SELECT json_extract(metadata, '$.content_hash') FROM memories "
            "WHERE id = ? AND deleted = 0",
            (memory_id,),
        ).fetchone()
        if fila is None or fila[0] is None:
            return None
        return str(fila[0])

    def escribir_chunks(
        self,
        chunks: Sequence[ChunkPlanificado],
        embeddings: Sequence[Sequence[float]],
        *,
        dry_run: bool = False,
    ) -> EstadisticasIngesta:
        """Inserta o actualiza chunks; omite si el hash no cambio."""
        stats = EstadisticasIngesta(chunks_planificados=len(chunks))
        if dry_run:
            return stats
        if len(embeddings) != len(chunks):
            raise ValueError("embeddings y chunks deben tener la misma longitud")

        conn = self.conectar()
        try:
            ahora = _ahora_rfc3339()
            for chunk, vector in zip(chunks, embeddings, strict=True):
                prev_hash = self._hash_existente(conn, chunk.memory_id)
                meta = _metadata_json(chunk)
                blob = embedding_a_bytes(vector)

                if prev_hash == chunk.content_hash:
                    stats.chunks_omitidos += 1
                    continue

                if prev_hash is None:
                    conn.execute(
                        """
                        INSERT INTO memories (
                            id, agent_id, content, source, scope, confidence,
                            metadata, created_at, accessed_at, access_count, deleted, embedding
                        ) VALUES (?, ?, ?, ?, ?, 1.0, ?, ?, ?, 0, 0, ?)
                        """,
                        (
                            chunk.memory_id,
                            self._agent_id,
                            chunk.texto,
                            _SOURCE_DOCUMENT,
                            _SCOPE_SEMANTIC,
                            meta,
                            ahora,
                            ahora,
                            blob,
                        ),
                    )
                    stats.chunks_insertados += 1
                else:
                    conn.execute(
                        """
                        UPDATE memories SET
                            content = ?, source = ?, scope = ?, metadata = ?,
                            accessed_at = ?, embedding = ?, deleted = 0
                        WHERE id = ?
                        """,
                        (
                            chunk.texto,
                            _SOURCE_DOCUMENT,
                            _SCOPE_SEMANTIC,
                            meta,
                            ahora,
                            blob,
                            chunk.memory_id,
                        ),
                    )
                    stats.chunks_actualizados += 1
            conn.commit()
        finally:
            conn.close()
        return stats


Embedder = Callable[[list[str]], list[list[float]]]


def crear_embedder_openai(api_key: str, modelo: str) -> Embedder:
    """Fabrica de embedder con API OpenAI."""

    def _embed(textos: list[str]) -> list[list[float]]:
        from openai import OpenAI

        cliente = OpenAI(api_key=api_key)
        respuesta = cliente.embeddings.create(input=textos, model=modelo)
        ordenados = sorted(respuesta.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordenados]

    return _embed


def embedder_en_lotes(
    embedder: Embedder,
    textos: list[str],
    *,
    tam_lote: int = 32,
) -> list[list[float]]:
    """Genera embeddings por lotes."""
    salida: list[list[float]] = []
    for inicio in range(0, len(textos), tam_lote):
        lote = textos[inicio : inicio + tam_lote]
        salida.extend(embedder(lote))
    return salida
