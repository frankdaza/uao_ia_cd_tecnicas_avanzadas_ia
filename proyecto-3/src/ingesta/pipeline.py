"""Orquestacion de planificacion e ingesta."""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from src.configuracion import Configuracion
from src.ingesta.cliente_memoria import (
    ClienteMemoriaOpenFang,
    crear_embedder_openai,
    embedder_en_lotes,
)
from src.ingesta.fuentes import OpcionesFuentes, planificar_todas_las_fuentes
from src.ingesta.kv_catalogo import publicar_resumen_ingesta
from src.ingesta.modelos import EstadisticasIngesta

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpcionesIngesta:
    dry_run: bool = False
    solo_markdown: bool = False
    solo_taam_pdf: bool = False
    limite: int | None = None
    permitir_db_en_vivo: bool = False
    tam_chunk: int = 1000
    solape: int = 150


def daemon_openfang_activo(api_base: str) -> bool:
    """``True`` si ``GET /api/health`` responde."""
    url = f"{api_base.rstrip('/')}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=2) as respuesta:
            return respuesta.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def ejecutar_ingesta(cfg: Configuracion, opciones: OpcionesIngesta) -> EstadisticasIngesta:
    """Planifica fuentes y escribe en SQLite (o solo imprime en dry-run)."""
    raiz = cfg.raiz_workspace()
    incluir_md = not opciones.solo_taam_pdf
    incluir_pdf = not opciones.solo_markdown
    if opciones.solo_markdown:
        incluir_pdf = False
    if opciones.solo_taam_pdf:
        incluir_md = False

    chunks, n_md, n_pdf, omitidos = planificar_todas_las_fuentes(
        raiz,
        OpcionesFuentes(
            incluir_markdown=incluir_md,
            incluir_pdf=incluir_pdf,
            limite_archivos=opciones.limite,
        ),
        tam_chunk=opciones.tam_chunk,
        solape=opciones.solape,
    )

    stats = EstadisticasIngesta(
        archivos_markdown=n_md,
        archivos_pdf=n_pdf,
        archivos_omitidos=omitidos,
        chunks_planificados=len(chunks),
    )

    if n_md == 0 and n_pdf == 0:
        logger.error("sin_fuentes: no hay archivos .md ni .pdf en el workspace")
        stats.advertencias.append("sin_fuentes")
        return stats

    ruta_db = cfg.ruta_db_openfang()
    agent_id = cfg.resolver_agent_id_openfang()

    if opciones.dry_run:
        logger.info(
            "dry-run: markdown=%s pdf=%s chunks=%s db=%s agent=%s",
            n_md,
            n_pdf,
            len(chunks),
            ruta_db,
            agent_id,
        )
        return stats

    if daemon_openfang_activo(cfg.openfang_api_url) and not opciones.permitir_db_en_vivo:
        logger.warning(
            "OpenFang daemon activo en %s; use --permitir-db-en-vivo o detenga openfang stop",
            cfg.openfang_api_url,
        )
        stats.advertencias.append("daemon_activo")

    api_key = cfg.exigir_openai_api_key()
    embedder = crear_embedder_openai(api_key, cfg.openai_embedding_model)
    textos = [c.texto for c in chunks]
    embeddings = embedder_en_lotes(embedder, textos) if textos else []

    cliente = ClienteMemoriaOpenFang(ruta_db, agent_id)
    escritura = cliente.escribir_chunks(chunks, embeddings, dry_run=False)
    stats.chunks_insertados = escritura.chunks_insertados
    stats.chunks_actualizados = escritura.chunks_actualizados
    stats.chunks_omitidos = escritura.chunks_omitidos

    publicar_resumen_ingesta(
        cfg.openfang_api_url,
        agent_id,
        {
            "archivos_markdown": n_md,
            "archivos_pdf": n_pdf,
            "chunks_planificados": len(chunks),
            "chunks_insertados": stats.chunks_insertados,
            "chunks_actualizados": stats.chunks_actualizados,
            "chunks_omitidos": stats.chunks_omitidos,
        },
    )
    return stats
