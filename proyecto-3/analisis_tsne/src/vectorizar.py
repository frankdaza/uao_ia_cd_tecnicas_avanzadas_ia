#!/usr/bin/env python3
"""
Genera embeddings OpenAI para transcripciones extraidas (t-SNE / UMAP).

Estado: PLACEHOLDER — requiere salida de extraer_jsonl.py implementada.

Uso previsto:
    uv run python analisis_tsne/src/vectorizar.py
"""

from __future__ import annotations

import os


def main() -> None:
    modelo = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    print("Vectorizacion — placeholder")
    print(f"  Modelo embeddings: {modelo}")
    print()
    print("TODO: cargar analisis_tsne/output/sesiones.parquet")
    print("TODO: llamar API OpenAI embeddings y guardar analisis_tsne/output/vectores.npy")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
