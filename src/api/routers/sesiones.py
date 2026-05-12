"""Endpoints de sesion de usuario (Modulo 2): inicio, historial y cierre."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import psycopg
from fastapi import APIRouter, Depends, Response
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.memoria.historial import crear_memoria_usuario, normalizar_session_id_postgres_langchain
from src.api.configuracion import obtener_configuracion
from src.api.dependencias import NOMBRE_COOKIE_SESION, obtener_sesion_db, obtener_usuario_actual
from src.api.esquemas import (
    MensajeHistorialItem,
    PeticionInicioSesion,
    RespuestaCierreSesion,
    RespuestaHistorialSesion,
    RespuestaInicioSesion,
)
from src.persistencia.modelos import Usuario
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain
from src.persistencia.repositorios.usuarios import RepositorioUsuarios

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sesiones"])

_SEGUNDOS_COOKIE_SESION = 60 * 60 * 24 * 30


def _consultar_max_created_at_chat(conninfo: str, session_uuid_txt: str) -> datetime | None:
    """Lee ``MAX(created_at)`` en ``chat_history`` sin bloquear el loop async."""
    try:
        conn = psycopg.connect(conninfo, connect_timeout=5)
    except psycopg.Error:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(created_at) FROM chat_history WHERE session_id = %s::uuid",
                (session_uuid_txt,),
            )
            row = cur.fetchone()
    except psycopg.Error:
        return None
    finally:
        conn.close()
    if not row or row[0] is None:
        return None
    return row[0]


def _serializar_mensaje_lc(mensaje: BaseMessage) -> MensajeHistorialItem:
    if isinstance(mensaje, HumanMessage):
        rol = "human"
    elif isinstance(mensaje, AIMessage):
        rol = "ai"
    elif isinstance(mensaje, SystemMessage):
        rol = "system"
    else:
        rol = "tool"
    contenido = mensaje.content if isinstance(mensaje.content, str) else str(mensaje.content)
    return MensajeHistorialItem(rol=rol, contenido=contenido, creado_en=None)


async def _cargar_mensajes_desde_memoria(session_id_canonico: str) -> list[MensajeHistorialItem]:
    cfg = obtener_configuracion()

    def _sync_load() -> list[MensajeHistorialItem]:
        with crear_memoria_usuario(session_id_canonico, cfg.url_base_datos_sync()) as memoria:
            mensajes_lc = memoria.cargar_ventana()
            return [_serializar_mensaje_lc(m) for m in mensajes_lc]

    return await asyncio.to_thread(_sync_load)


@router.post("/sesiones", response_model=RespuestaInicioSesion)
async def iniciar_sesion(
    cuerpo: PeticionInicioSesion,
    respuesta: Response,
    sesion: AsyncSession = Depends(obtener_sesion_db),
) -> RespuestaInicioSesion:
    """
    Crea o reutiliza un usuario por documento, actualiza ``last_login`` y fija la cookie de sesion.
    """
    repo = RepositorioUsuarios(sesion)
    usuario, ya_existia = await repo.obtener_o_crear(
        cuerpo.documento_identidad.strip(),
        cuerpo.nombre.strip(),
    )
    await repo.actualizar_last_login(usuario.id)
    session_id = sesion_id_memoria_langchain(usuario.id)
    uuid_txt = normalizar_session_id_postgres_langchain(session_id)
    cfg = obtener_configuracion()
    ultimo = await asyncio.to_thread(
        _consultar_max_created_at_chat,
        cfg.url_base_datos_sync(),
        uuid_txt,
    )
    respuesta.set_cookie(
        key=NOMBRE_COOKIE_SESION,
        value=session_id,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=_SEGUNDOS_COOKIE_SESION,
    )
    logger.info(
        "Sesion iniciada para usuario_id=%s ya_existia=%s",
        usuario.id,
        ya_existia,
    )
    return RespuestaInicioSesion(
        usuario_id=usuario.id,
        session_id=session_id,
        nombre=usuario.nombre,
        ya_existia=ya_existia,
        ultimo_mensaje_at=ultimo,
    )


@router.get("/sesiones/actual/historial", response_model=RespuestaHistorialSesion)
async def historial_sesion_actual(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> RespuestaHistorialSesion:
    """Devuelve mensajes persistidos en orden cronologico para repintar el chat."""
    session_id = sesion_id_memoria_langchain(usuario.id)
    mensajes = await _cargar_mensajes_desde_memoria(session_id)
    return RespuestaHistorialSesion(mensajes=mensajes)


@router.post("/sesiones/cerrar", response_model=RespuestaCierreSesion)
async def cerrar_sesion(respuesta: Response) -> RespuestaCierreSesion:
    """
    Operacion idempotente: elimina la cookie de sesion en la respuesta.

    No invalida filas en base de datos; el frontend deja de enviar credenciales.
    """
    logger.info("Solicitud de cierre de sesion registrada.")
    respuesta.delete_cookie(key=NOMBRE_COOKIE_SESION, path="/")
    return RespuestaCierreSesion()
