#!/usr/bin/env python3
"""Cuenta fragmentos semanticos en openfang.db (ingesta RAG)."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def _resolver_db() -> Path:
    home = os.environ.get("OPENFANG_HOME")
    if home:
        base = Path(home)
        if not base.is_absolute():
            base = Path(__file__).resolve().parents[1] / base
    else:
        base = Path(__file__).resolve().parents[1] / "openfang" / "data"
    return base / "data" / "openfang.db"


def contar_semanticas(ruta_db: Path) -> int:
    if not ruta_db.is_file():
        return 0
    conexion = sqlite3.connect(ruta_db)
    try:
        cursor = conexion.execute(
            "SELECT COUNT(*) FROM memories WHERE scope = ?",
            ("semantic",),
        )
        fila = cursor.fetchone()
        return int(fila[0]) if fila else 0
    finally:
        conexion.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=None, help="Ruta a openfang.db")
    parser.add_argument(
        "--exigir-ingesta",
        action="store_true",
        help="Exit 1 si no hay memorias semanticas",
    )
    args = parser.parse_args()
    ruta = args.db or _resolver_db()
    total = contar_semanticas(ruta)
    print(f"memorias_semanticas={total} db={ruta}")
    if args.exigir_ingesta and total == 0:
        print(
            "error: sin ingesta; ejecuta ingesta/indexar_corpus_openfang.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
