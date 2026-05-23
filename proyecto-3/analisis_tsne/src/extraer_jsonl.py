#!/usr/bin/env python3
"""
Extrae transcripciones desde el espejo JSONL y SQLite FTS5 de OpenFang.

Estado: PLACEHOLDER — ajustar rutas y esquema segun version del binario OpenFang.

Uso previsto:
    uv run python analisis_tsne/src/extraer_jsonl.py
"""

from __future__ import annotations

import os
from pathlib import Path


def resolver_openfang_home() -> Path:
    return Path(os.environ.get("OPENFANG_HOME", "./openfang/data")).resolve()


def main() -> None:
    home = resolver_openfang_home()
    print("Extraccion historial OpenFang — placeholder")
    print(f"  OPENFANG_HOME: {home}")
    print()
    print("TODO: leer JSONL de sesiones y/o consultar SQLite FTS5.")
    print("TODO: exportar CSV/Parquet a analisis_tsne/output/sesiones.parquet")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
