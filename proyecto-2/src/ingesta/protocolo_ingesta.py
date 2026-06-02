"""
Ingesta de protocolos PDF o Markdown: extraccion, chunking LangChain y upsert en Qdrant TAAM.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion, obtener_configuracion
from src.ingesta.extractores.markdown import extraer_documentos_desde_markdown
from src.ingesta.extractores.pdf import extraer_documentos_desde_pdf
from src.ingesta.reintentos import ejecutar_con_reintentos
from src.persistencia.modelos import TipoProcedimiento
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.rag.vector_store import crear_vector_store, obtener_cliente_qdrant
from src.rutas_workspace import resolver_ruta_workspace

logger = logging.getLogger(__name__)

_MIN_CARACTERES_TEXTO = 40

_Extractor = Callable[[Path], tuple[list[Document], int]]


@dataclass(frozen=True)
class ResultadoIngesta:
    """Resumen de una corrida de ingesta sobre un procedimiento."""

    tipo_id: uuid.UUID
    noop: bool
    paginas: int
    chunks: int
    version: int
    mensaje: str


def _splitter_desde_config(cfg: Configuracion) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=cfg.taam_chunk_size,
        chunk_overlap=cfg.taam_chunk_overlap,
    )


def obtener_extractor(formato_protocolo: str) -> _Extractor:
    """Devuelve la funcion de extraccion segun ``formato_protocolo`` en BD."""
    if formato_protocolo == "pdf":
        return extraer_documentos_desde_pdf
    if formato_protocolo == "markdown":
        return extraer_documentos_desde_markdown
    raise ValueError(f"formato_protocolo no soportado: {formato_protocolo}")


def resolver_ruta_archivo_protocolo(fila: TipoProcedimiento) -> Path:
    """Resuelve la ruta en disco desde ``fila.ruta_pdf`` (cualquier extension)."""
    if not fila.ruta_pdf:
        raise ValueError("Sin ruta de protocolo en BD.")
    return resolver_ruta_workspace(fila.ruta_pdf)


def dividir_en_chunks(
    documentos: list[Document],
    cfg: Configuracion,
) -> list[Document]:
    """Aplica ``RecursiveCharacterTextSplitter`` y asigna ``chunk_index``."""
    if not documentos:
        return []
    trozos = _splitter_desde_config(cfg).split_documents(documentos)
    for indice, doc in enumerate(trozos):
        meta = dict(doc.metadata)
        meta["chunk_index"] = indice
        doc.metadata = meta
    return trozos


def _id_estable_chunk(
    tipo_id: uuid.UUID,
    version: int,
    chunk_index: int,
    contenido: str,
) -> str:
    """UUID determinista para upsert idempotente por chunk."""
    base = f"{tipo_id}:{version}:{chunk_index}:{hashlib.sha256(contenido.encode()).hexdigest()}"
    digest = hashlib.sha256(base.encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


def _enriquecer_metadatos_chunks(
    chunks: list[Document],
    *,
    tipo_id: uuid.UUID,
    version: int,
    hash_pdf: str,
) -> list[Document]:
    tipo_str = str(tipo_id)
    for doc in chunks:
        doc.metadata = {
            **doc.metadata,
            "tipo_procedimiento_id": tipo_str,
            "version": version,
            "hash_pdf": hash_pdf,
        }
        doc.id = _id_estable_chunk(
            tipo_id,
            version,
            int(doc.metadata.get("chunk_index", 0)),
            doc.page_content,
        )
    return chunks


def eliminar_vectores_procedimiento(
    cliente: QdrantClient,
    coleccion: str,
    tipo_id: uuid.UUID,
) -> None:
    """Borra todos los puntos del procedimiento antes de re-ingestar."""
    if not cliente.collection_exists(coleccion):
        return
    filtro = Filter(
        must=[
            FieldCondition(
                key="metadata.tipo_procedimiento_id",
                match=MatchValue(value=str(tipo_id)),
            )
        ]
    )
    cliente.delete(collection_name=coleccion, points_selector=filtro)


def _total_caracteres(documentos: list[Document]) -> int:
    return sum(len(d.page_content) for d in documentos)


def _version_efectiva(fila: TipoProcedimiento) -> int:
    if fila.qdrant_collection_version is not None:
        return fila.qdrant_collection_version
    return 1


def debe_omitir_ingesta(fila: TipoProcedimiento, *, forzar: bool = False) -> bool:
    """No-op si ya esta indexado con el mismo hash."""
    if forzar:
        return False
    return (
        fila.indexacion_estado == "ok"
        and bool(fila.hash_pdf)
        and fila.ruta_pdf is not None
    )


def ingestar_chunks_en_qdrant(
    vector_store: QdrantVectorStore,
    chunks: list[Document],
    *,
    cfg: Configuracion,
    tipo_id: uuid.UUID,
) -> None:
    """Upsert con reintentos (embed + escritura en Qdrant)."""
    if not chunks:
        return
    etiqueta = str(tipo_id)

    def _upsert() -> None:
        vector_store.add_documents(chunks, ids=[doc.id for doc in chunks if doc.id])

    ejecutar_con_reintentos(
        _upsert,
        intentos=cfg.ingesta_reintentos,
        espera_max_seg=cfg.ingesta_backoff_max_seg,
        log=logger,
        operacion="add_documents",
        etiqueta=etiqueta,
    )


async def ingestar_tipo_procedimiento(
    sesion: AsyncSession,
    tipo_id: uuid.UUID,
    *,
    cfg: Configuracion | None = None,
    forzar: bool = False,
    vector_store: QdrantVectorStore | None = None,
    cliente_qdrant: QdrantClient | None = None,
) -> ResultadoIngesta:
    """
    Pipeline completo para un ``tipo_procedimiento_id``.

    Actualiza ``indexacion_estado`` y ``qdrant_collection_version`` en la misma sesion.
    """
    conf = cfg or obtener_configuracion()
    repo = RepositorioTiposProcedimiento(sesion)
    fila = await repo.obtener_por_id(tipo_id)
    if fila is None:
        raise ValueError(f"Procedimiento {tipo_id} no encontrado.")

    if not fila.ruta_pdf or not fila.hash_pdf:
        await repo.actualizar(fila, indexacion_estado="error")
        await sesion.commit()
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=False,
            paginas=0,
            chunks=0,
            version=_version_efectiva(fila),
            mensaje="Falta ruta de protocolo o hash; no se puede indexar.",
        )

    if debe_omitir_ingesta(fila, forzar=forzar) and not forzar:
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=True,
            paginas=0,
            chunks=0,
            version=_version_efectiva(fila),
            mensaje=(
                "Ingesta omitida: indexacion_estado=ok y mismo protocolo ya indexado "
                "(use --forzar para re-indexar)."
            ),
        )

    try:
        ruta = resolver_ruta_archivo_protocolo(fila)
    except ValueError:
        await repo.actualizar(fila, indexacion_estado="error")
        await sesion.commit()
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=False,
            paginas=0,
            chunks=0,
            version=_version_efectiva(fila),
            mensaje="Falta ruta de protocolo en BD.",
        )

    if not ruta.is_file():
        await repo.actualizar(fila, indexacion_estado="error")
        await sesion.commit()
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=False,
            paginas=0,
            chunks=0,
            version=_version_efectiva(fila),
            mensaje=f"Archivo de protocolo no encontrado en disco: {ruta}",
        )

    version = _version_efectiva(fila)
    formato = fila.formato_protocolo or "pdf"
    try:
        extractor = obtener_extractor(formato)
        documentos, paginas = extractor(ruta)
        if _total_caracteres(documentos) < _MIN_CARACTERES_TEXTO:
            detalle = (
                "Texto extraido insuficiente (PDF escaneado sin OCR o vacio). "
                "Revise el protocolo."
                if formato == "pdf"
                else "Cuerpo Markdown insuficiente tras el front matter. Revise el protocolo."
            )
            await repo.actualizar(fila, indexacion_estado="error")
            await sesion.commit()
            return ResultadoIngesta(
                tipo_id=tipo_id,
                noop=False,
                paginas=paginas,
                chunks=0,
                version=version,
                mensaje=detalle,
            )

        chunks = dividir_en_chunks(documentos, conf)
        chunks = _enriquecer_metadatos_chunks(
            chunks,
            tipo_id=tipo_id,
            version=version,
            hash_pdf=fila.hash_pdf,
        )

        cli = cliente_qdrant or obtener_cliente_qdrant(conf.qdrant_url)
        eliminar_vectores_procedimiento(cli, conf.taam_qdrant_collection, tipo_id)

        vs = vector_store or crear_vector_store(conf, cliente=cli)
        ingestar_chunks_en_qdrant(vs, chunks, cfg=conf, tipo_id=tipo_id)

        kwargs_ok: dict = {"indexacion_estado": "ok"}
        if fila.qdrant_collection_version is None:
            kwargs_ok["qdrant_collection_version"] = version
        await repo.actualizar(fila, **kwargs_ok)
        await sesion.commit()

        logger.info(
            "Ingesta TAAM ok tipo_id=%s formato=%s paginas=%s chunks=%s version=%s",
            tipo_id,
            formato,
            paginas,
            len(chunks),
            version,
        )
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=False,
            paginas=paginas,
            chunks=len(chunks),
            version=version,
            mensaje="Indexacion completada.",
        )
    except Exception as exc:
        logger.exception("Ingesta TAAM fallo para tipo_id=%s", tipo_id)
        await repo.actualizar(fila, indexacion_estado="error")
        await sesion.commit()
        return ResultadoIngesta(
            tipo_id=tipo_id,
            noop=False,
            paginas=0,
            chunks=0,
            version=version,
            mensaje=f"Error de ingesta: {exc}",
        )


async def ingestar_pendientes(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    cfg: Configuracion | None = None,
    limite: int = 50,
    forzar: bool = False,
) -> list[ResultadoIngesta]:
    """Procesa filas con ``indexacion_estado=pendiente`` (hasta ``limite``)."""
    conf = cfg or obtener_configuracion()
    resultados: list[ResultadoIngesta] = []
    async with session_factory() as sesion:
        repo = RepositorioTiposProcedimiento(sesion)
        filas = await repo.listar_por_indexacion("pendiente", limite=limite)
        for fila in filas:
            res = await ingestar_tipo_procedimiento(
                sesion,
                fila.id,
                cfg=conf,
                forzar=forzar,
            )
            resultados.append(res)
    return resultados


async def ejecutar_ingesta_en_sesion_nueva(
    session_factory: async_sessionmaker[AsyncSession],
    tipo_id: uuid.UUID,
    *,
    cfg: Configuracion | None = None,
    forzar: bool = False,
) -> ResultadoIngesta:
    """Util para BackgroundTasks: abre sesion, ingesta y cierra."""
    async with session_factory() as sesion:
        return await ingestar_tipo_procedimiento(
            sesion,
            tipo_id,
            cfg=cfg,
            forzar=forzar,
        )
