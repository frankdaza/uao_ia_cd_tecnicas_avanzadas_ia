#!/usr/bin/env python3
"""
Ingesta del corpus del workspace hacia la memoria de OpenFang (Vector Store + KV).

Estado: PLACEHOLDER — implementar cuando el binario OpenFang y su API/CLI
de ingesta esten fijados en el entorno del equipo.

Uso previsto:
    uv run python ingesta/indexar_corpus_openfang.py
"""

from __future__ import annotations

import os
from pathlib import Path


def resolver_raiz_workspace() -> Path:
    """Resuelve UAO_WORKSPACE_ROOT o la raiz del monorepo."""
    if raiz := os.environ.get("UAO_WORKSPACE_ROOT"):
        return Path(raiz).resolve()
    # proyecto-3/ingesta -> repo root
    return Path(__file__).resolve().parents[2]


def main() -> None:
    raiz = resolver_raiz_workspace()
    markdown = raiz / "data" / "markdown"
    taam_pdf = raiz / "data" / "taam"

    print("Ingesta OpenFang — placeholder")
    print(f"  Workspace: {raiz}")
    print(f"  Markdown:  {markdown} (existe={markdown.is_dir()})")
    print(f"  TAAM PDF:  {taam_pdf} (existe={taam_pdf.is_dir()})")
    print()
    print("TODO: conectar con CLI/API OpenFang para indexar chunks.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
