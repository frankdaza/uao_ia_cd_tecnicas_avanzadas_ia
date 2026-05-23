#!/usr/bin/env python3
"""
Extrae transcripciones desde el espejo JSONL y SQLite de OpenFang hacia Parquet.

Uso:
    cd proyecto-3
    uv run python analisis_tsne/src/extraer_jsonl.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.configuracion import obtener_configuracion  # noqa: E402
from src.openfang.extraccion_tsne import (  # noqa: E402
    COLUMNAS_PARQUET,
    construir_dataframe_completo,
    escribir_parquet,
)

_SALIDA_DEFAULT = ROOT / "analisis_tsne" / "output" / "sesiones.parquet"


def _configurar_logging(nivel: str) -> None:
    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exporta turnos de chat OpenFang a sesiones.parquet (t-SNE)"
    )
    parser.add_argument(
        "--openfang-home",
        type=Path,
        default=None,
        help="Directorio OPENFANG_HOME (por defecto desde .env)",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=_SALIDA_DEFAULT,
        help="Ruta del archivo parquet de salida",
    )
    parser.add_argument(
        "--incluir-audit",
        action="store_true",
        help="Incluir audit/hand_*.jsonl en la extraccion",
    )
    parser.add_argument(
        "--solo-jsonl",
        action="store_true",
        help="No consultar SQLite (openfang.db)",
    )
    args = parser.parse_args()

    cfg = obtener_configuracion()
    _configurar_logging(cfg.log_level)
    logger = logging.getLogger(__name__)

    raiz = args.openfang_home if args.openfang_home else cfg.openfang_home_absoluto()
    if not raiz.is_dir():
        print(f"openfang_home_inexistente: {raiz}", file=sys.stderr)
        return 2

    ruta_db = cfg.ruta_db_openfang()
    df, fts5_ausente = construir_dataframe_completo(
        raiz,
        ruta_db,
        incluir_audit=args.incluir_audit,
        solo_jsonl=args.solo_jsonl,
    )

    if fts5_ausente:
        logger.warning("fts5_ausente: sin datos SQLite utiles; usando solo JSONL")

    if df.empty:
        print("sin_datos: no hay turnos conversacionales bajo OPENFANG_HOME", file=sys.stderr)
        return 1

    escribir_parquet(df, args.salida)
    sesiones = df["session_id"].nunique() if "session_id" in df.columns else 0
    logger.info(
        "Parquet escrito: %s (%d filas, %d sesiones, columnas=%s)",
        args.salida,
        len(df),
        sesiones,
        list(COLUMNAS_PARQUET),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
