"""Resolucion de caso activo desde ``session_id`` Telegram."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.contexto import parsear_session_telegram
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram


@dataclass(frozen=True)
class ContextoCasoActivo:
    """Datos del caso vinculado al chat."""

    caso_id: uuid.UUID
    tipo_procedimiento_id: uuid.UUID
    paciente_nombre: str
    nombre_procedimiento: str
    fecha_cirugia: date
    notas_especificas: str | None


async def resolver_caso_activo_por_session(
    sesion: AsyncSession,
    session_id: str,
) -> ContextoCasoActivo | None:
    """Obtiene el caso activo asociado a ``telegram:{chat_id}``."""
    sesion_tg = parsear_session_telegram(session_id)
    if sesion_tg is None:
        return None

    repo_v = RepositorioVinculosTelegram(sesion)
    vinculo = await repo_v.obtener_vinculado_por_chat_id(sesion_tg.chat_id)
    if vinculo is None:
        return None

    repo_c = RepositorioCasosPostoperatorio(sesion)
    caso = await repo_c.obtener_por_id(vinculo.caso_id)
    if caso is None or caso.estado != "activo":
        return None

    repo_t = RepositorioTiposProcedimiento(sesion)
    tipo = await repo_t.obtener_por_id(caso.tipo_procedimiento_id)
    nombre_proc = tipo.nombre if tipo else "Procedimiento"

    return ContextoCasoActivo(
        caso_id=caso.id,
        tipo_procedimiento_id=caso.tipo_procedimiento_id,
        paciente_nombre=caso.paciente_nombre,
        nombre_procedimiento=nombre_proc,
        fecha_cirugia=caso.fecha_cirugia,
        notas_especificas=caso.notas_especificas,
    )


async def resumen_caso_para_prompt(
    sesion: AsyncSession,
    session_id: str,
) -> str | None:
    """Texto para inyectar en ``dynamic_prompt`` via contexto."""
    ctx = await resolver_caso_activo_por_session(sesion, session_id)
    if ctx is None:
        return None
    partes = [
        f"Paciente: {ctx.paciente_nombre}.",
        f"Procedimiento: {ctx.nombre_procedimiento}.",
        f"Fecha de cirugia: {ctx.fecha_cirugia.isoformat()}.",
    ]
    if ctx.notas_especificas:
        partes.append(f"Notas del caso: {ctx.notas_especificas}")
    return " ".join(partes)
