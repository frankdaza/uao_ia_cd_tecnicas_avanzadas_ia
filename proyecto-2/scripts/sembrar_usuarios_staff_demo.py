#!/usr/bin/env python3
"""
Semilla usuarios staff demo en Postgres TAAM (TASK-105).

Uso (tras ``alembic upgrade head``):

    cd proyecto-2
    uv run python -m scripts.sembrar_usuarios_staff_demo
"""

from __future__ import annotations

import asyncio
import logging

from src.configuracion import obtener_configuracion
from src.persistencia.motor import crear_motor_async, crear_session_factory
from src.persistencia.semilla_staff_demo import sembrar_usuarios_staff_demo

logger = logging.getLogger(__name__)


async def _main() -> None:
    cfg = obtener_configuracion()
    if not (cfg.staff_jwt_secret or "").strip():
        raise SystemExit(
            "Defina STAFF_JWT_SECRET en .env antes de sembrar usuarios staff."
        )

    motor = crear_motor_async(cfg.url_base_datos_async())
    factory = crear_session_factory(motor)
    async with factory() as sesion:
        emails = await sembrar_usuarios_staff_demo(sesion, cfg)
        await sesion.commit()
    await motor.dispose()
    logger.info("Usuarios staff demo listos: %s", ", ".join(emails))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
