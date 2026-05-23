#!/usr/bin/env python3
"""
Semilla datos demo TAAM para sustentacion (TASK-114).

Uso (tras ``alembic upgrade head`` y ``STAFF_JWT_SECRET`` en .env):

    cd proyecto-2
    uv run python -m scripts.sembrar_demo_taam
    uv run python -m scripts.sembrar_demo_taam --con-ingesta
    uv run python -m scripts.sembrar_demo_taam --sin-conversacion
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from src.configuracion import obtener_configuracion
from src.ingesta.protocolo_pdf import ingestar_tipo_procedimiento
from src.persistencia.motor import crear_motor_async, crear_session_factory
from src.persistencia.semilla_demo_taam import sembrar_demo_taam

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Semilla demo TAAM: staff, COLE-LAP-001, casos PAC-DEMO-001/002, alerta y hilo."
    )
    parser.add_argument(
        "--con-ingesta",
        action="store_true",
        help="Tras sembrar, ejecuta ingesta PDF -> Qdrant (requiere OPENAI_API_KEY y Qdrant).",
    )
    parser.add_argument(
        "--sin-conversacion",
        action="store_true",
        help="No escribe historial en checkpointer LangGraph.",
    )
    return parser.parse_args()


async def _main_async(args: argparse.Namespace) -> int:
    cfg = obtener_configuracion()
    if not (cfg.staff_jwt_secret or "").strip():
        raise SystemExit(
            "Defina STAFF_JWT_SECRET en .env antes de sembrar (ver .env.example)."
        )

    motor = crear_motor_async(cfg.url_base_datos_async())
    factory = crear_session_factory(motor)
    try:
        resultado = await sembrar_demo_taam(
            factory,
            cfg,
            sembrar_conversacion=not args.sin_conversacion,
        )
        for linea in resultado.mensajes:
            logger.info("%s", linea)

        if args.con_ingesta:
            async with factory() as sesion:
                res = await ingestar_tipo_procedimiento(
                    sesion,
                    resultado.tipo_procedimiento_id,
                    cfg=cfg,
                    forzar=True,
                )
                await sesion.commit()
            logger.info(
                "Ingesta Qdrant: chunks=%s version=%s — %s",
                res.chunks,
                res.version,
                res.mensaje,
            )
    finally:
        await motor.dispose()

    print(
        "Demo TAAM listo. Procedimiento COLE-LAP-001; casos PAC-DEMO-001 y PAC-DEMO-002. "
        "Codigo emparejamiento caso B: DEMO2X. Ver backlog/docs/usecases/GUION-DEMO-TAAM.md"
    )
    return 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parse_args()
    try:
        raise SystemExit(asyncio.run(_main_async(args)))
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("Error al sembrar demo TAAM: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
