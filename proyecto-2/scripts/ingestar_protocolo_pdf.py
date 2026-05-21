"""
Ingesta protocolos PDF del catalogo TAAM hacia Qdrant (coleccion taam_protocolos).

Uso:
    uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>
    uv run python -m scripts.ingestar_protocolo_pdf --todos-pendientes
    uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid> --forzar
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid

from src.configuracion import obtener_configuracion
from src.ingesta.protocolo_pdf import ingestar_pendientes, ingestar_tipo_procedimiento
from src.persistencia.motor import crear_motor_async, crear_session_factory

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingesta PDF de protocolos TAAM a Qdrant (LangChain + RecursiveCharacterTextSplitter)."
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--tipo-id", type=uuid.UUID, help="UUID del tipo_procedimiento.")
    grupo.add_argument(
        "--todos-pendientes",
        action="store_true",
        help="Procesa filas con indexacion_estado=pendiente.",
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Re-indexa aunque indexacion_estado=ok (mismo hash).",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=50,
        help="Maximo de pendientes con --todos-pendientes.",
    )
    return parser.parse_args()


def _imprimir_resultado(res) -> None:
    estado = "NOOP" if res.noop else "OK"
    print(
        f"[{estado}] tipo_id={res.tipo_id} paginas={res.paginas} "
        f"chunks={res.chunks} version={res.version} — {res.mensaje}"
    )


async def _main_async(args: argparse.Namespace) -> int:
    cfg = obtener_configuracion()
    motor = crear_motor_async(cfg.url_base_datos_async())
    factory = crear_session_factory(motor)
    try:
        if args.todos_pendientes:
            resultados = await ingestar_pendientes(
                factory,
                cfg=cfg,
                limite=args.limite,
                forzar=args.forzar,
            )
            if not resultados:
                print("No hay procedimientos pendientes de indexacion.")
                return 0
            for res in resultados:
                _imprimir_resultado(res)
            errores = sum(1 for r in resultados if not r.noop and r.chunks == 0 and "Error" in r.mensaje)
            return 1 if errores else 0

        async with factory() as sesion:
            res = await ingestar_tipo_procedimiento(
                sesion,
                args.tipo_id,
                cfg=cfg,
                forzar=args.forzar,
            )
        _imprimir_resultado(res)
        if res.noop:
            return 0
        if "Error" in res.mensaje or res.chunks == 0 and res.paginas > 0:
            return 1
        if res.chunks == 0:
            return 1
        return 0
    finally:
        await motor.dispose()


def main() -> None:
    args = _parse_args()
    codigo = asyncio.run(_main_async(args))
    sys.exit(codigo)


if __name__ == "__main__":
    main()
