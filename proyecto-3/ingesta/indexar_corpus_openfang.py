#!/usr/bin/env python3
"""
Ingesta del corpus del workspace hacia la memoria semantica de OpenFang.

Escribe en ``{OPENFANG_HOME}/data/openfang.db`` (tabla ``memories``) con scope
``semantic`` y embeddings OpenAI. Structured KV opcional via REST.

Uso:
    uv run python ingesta/indexar_corpus_openfang.py --dry-run --limite 5
    uv run python ingesta/indexar_corpus_openfang.py --solo-markdown
    uv run python ingesta/indexar_corpus_openfang.py --permitir-db-en-vivo
"""

from __future__ import annotations

import argparse
import logging

from src.configuracion import obtener_configuracion
from src.ingesta.pipeline import OpcionesIngesta, ejecutar_ingesta

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingesta corpus Markdown y PDF TAAM hacia memoria OpenFang.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista fuentes y cuenta chunks sin escribir en SQLite ni llamar OpenAI.",
    )
    parser.add_argument(
        "--solo-markdown",
        action="store_true",
        help="Solo archivos bajo data/markdown/.",
    )
    parser.add_argument(
        "--solo-taam-pdf",
        action="store_true",
        help="Solo PDFs bajo data/taam/.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        metavar="N",
        help="Maximo de archivos por tipo (markdown o pdf).",
    )
    parser.add_argument(
        "--permitir-db-en-vivo",
        action="store_true",
        help="Permite escribir en SQLite aunque el daemon OpenFang este activo.",
    )
    parser.add_argument(
        "--tam-chunk",
        type=int,
        default=1000,
        help="Tamano de fragmento en caracteres (default: 1000).",
    )
    parser.add_argument(
        "--solape",
        type=int,
        default=150,
        help="Solape entre fragmentos (default: 150).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.solo_markdown and args.solo_taam_pdf:
        logger.error("Use solo uno de --solo-markdown o --solo-taam-pdf")
        raise SystemExit(2)

    cfg = obtener_configuracion()
    nivel = cfg.log_level.upper()
    if nivel in logging._nameToLevel:
        logging.getLogger().setLevel(logging._nameToLevel[nivel])

    opciones = OpcionesIngesta(
        dry_run=args.dry_run,
        solo_markdown=args.solo_markdown,
        solo_taam_pdf=args.solo_taam_pdf,
        limite=args.limite,
        permitir_db_en_vivo=args.permitir_db_en_vivo,
        tam_chunk=args.tam_chunk,
        solape=args.solape,
    )

    stats = ejecutar_ingesta(cfg, opciones)

    print("Ingesta OpenFang")
    print(f"  Workspace:     {cfg.raiz_workspace()}")
    print(f"  Markdown:      {stats.archivos_markdown} archivos")
    print(f"  TAAM PDF:      {stats.archivos_pdf} archivos")
    print(f"  Omitidos:      {stats.archivos_omitidos} archivos")
    print(f"  Chunks:        {stats.chunks_planificados} planificados")
    if not args.dry_run:
        print(f"  Insertados:    {stats.chunks_insertados}")
        print(f"  Actualizados:  {stats.chunks_actualizados}")
        print(f"  Omitidos hash: {stats.chunks_omitidos}")
    print(f"  DB:            {cfg.ruta_db_openfang()}")
    if args.dry_run:
        print("  Modo:          dry-run (sin escritura)")

    if "sin_fuentes" in stats.advertencias:
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
