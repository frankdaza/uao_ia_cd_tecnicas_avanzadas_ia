#!/usr/bin/env python3
"""
Genera embeddings OpenAI para transcripciones extraidas (t-SNE / UMAP).

Uso:
    cd proyecto-3
    uv run python analisis_tsne/src/vectorizar.py
    uv run python analisis_tsne/src/vectorizar.py --por-turno
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.configuracion import obtener_configuracion  # noqa: E402
from src.openfang.vectorizacion_tsne import (  # noqa: E402
    SinDatosVectorizacion,
    cargar_sesiones_parquet,
    guardar_artefactos,
    vectorizar_dataframe,
)

if TYPE_CHECKING:
    from openai import OpenAI

_OUTPUT = ROOT / "analisis_tsne" / "output"
_ENTRADA_DEFAULT = _OUTPUT / "sesiones.parquet"
_VECTORES_DEFAULT = _OUTPUT / "vectores.npy"
_METADATOS_DEFAULT = _OUTPUT / "metadatos.parquet"


def _configurar_logging(nivel: str) -> None:
    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )


def main(
    argv: list[str] | None = None,
    *,
    cliente_factory: Callable[[str], OpenAI] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Vectoriza sesiones.parquet con OpenAI embeddings (t-SNE)"
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=_ENTRADA_DEFAULT,
        help="Parquet de sesiones (default: analisis_tsne/output/sesiones.parquet)",
    )
    parser.add_argument(
        "--salida-vectores",
        type=Path,
        default=_VECTORES_DEFAULT,
        help="Ruta vectores.npy",
    )
    parser.add_argument(
        "--salida-metadatos",
        type=Path,
        default=_METADATOS_DEFAULT,
        help="Ruta metadatos.parquet",
    )
    parser.add_argument(
        "--por-turno",
        action="store_true",
        help="Un embedding por turno (default: una transcripcion por session_id)",
    )
    parser.add_argument(
        "--tam-lote",
        type=int,
        default=32,
        help="Tamano de lote para la API de embeddings",
    )
    parser.add_argument(
        "--modelo",
        type=str,
        default=None,
        help="Modelo OpenAI (default: OPENAI_EMBEDDING_MODEL)",
    )
    args = parser.parse_args(argv)

    cfg = obtener_configuracion()
    _configurar_logging(cfg.log_level)
    logger = logging.getLogger(__name__)

    try:
        df = cargar_sesiones_parquet(args.entrada)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if df.empty:
        print("sin_datos: parquet de entrada vacio", file=sys.stderr)
        return 1

    modelo = (args.modelo or cfg.openai_embedding_model).strip()
    modo = "turno" if args.por_turno else "sesion"

    try:
        from src.openfang.vectorizacion_tsne import preparar_unidades_embedding

        preparar_unidades_embedding(df, por_turno=args.por_turno)
    except SinDatosVectorizacion as exc:
        print(f"sin_datos: {exc}", file=sys.stderr)
        return 1

    api_key = cfg.exigir_openai_api_key()

    if cliente_factory is None:
        from openai import OpenAI

        def cliente_factory(clave: str) -> OpenAI:
            return OpenAI(api_key=clave)

    cliente = cliente_factory(api_key)

    try:
        vectores, metadatos = vectorizar_dataframe(
            df,
            cliente,
            modelo,
            por_turno=args.por_turno,
            tam_lote=args.tam_lote,
        )
    except SinDatosVectorizacion as exc:
        print(f"sin_datos: {exc}", file=sys.stderr)
        return 1

    guardar_artefactos(
        vectores,
        metadatos,
        ruta_vectores=args.salida_vectores,
        ruta_metadatos=args.salida_metadatos,
    )

    logger.info(
        "Vectorizacion completada: modo=%s modelo=%s unidades=%d dim=%d -> %s, %s",
        modo,
        modelo,
        vectores.shape[0],
        vectores.shape[1],
        args.salida_vectores,
        args.salida_metadatos,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
