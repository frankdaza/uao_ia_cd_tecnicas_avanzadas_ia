"""
Memoria conversacional con ``PostgresChatMessageHistory`` (langchain-postgres).

La tabla ``chat_history`` se crea en runtime con ``create_tables`` (no Alembic).
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, messages_from_dict
from langchain_postgres import PostgresChatMessageHistory
from psycopg import sql

from src.api.configuracion import obtener_configuracion

logger = logging.getLogger(__name__)

TABLA_HISTORIAL_CHAT_DEFECTO = "chat_history"


class MemoriaConexionError(RuntimeError):
    """Fallo al abrir PostgreSQL para la memoria conversacional."""


def normalizar_session_id_postgres_langchain(session_id: str) -> str:
    """
    Convierte el identificador de sesion al UUID en texto exigido por LangChain.

    ``PostgresChatMessageHistory`` (langchain-postgres 0.0.17) valida que
    ``session_id`` sea un UUID parseable. El helper ``sesion_id_memoria_langchain``
    devuelve ``user:{uuid}``; aqui se acepta ese formato o el UUID solo.
    """
    s = session_id.strip()
    if s.lower().startswith("user:"):
        s = s[5:].strip()
    try:
        return str(uuid.UUID(s))
    except ValueError as exc:
        raise ValueError(
            "session_id debe ser un UUID valido o el formato canonico user:{uuid} "
            f"(task-47). Valor recibido no parseable: {session_id!r}"
        ) from exc


def conectar_memoria_sync(conninfo: str) -> psycopg.Connection:
    """
    Abre una conexion sync con mensajes de error en español latinoamericano.

    No registra ``conninfo`` ni contraseñas.
    """
    try:
        return psycopg.connect(conninfo, autocommit=False)
    except psycopg.OperationalError as exc:
        raise MemoriaConexionError(
            "No se pudo conectar a PostgreSQL para la memoria conversacional. "
            "Verifica que el servidor este en marcha y las variables de entorno "
            "de base de datos (host, puerto, usuario y nombre de base)."
        ) from exc
    except psycopg.Error as exc:
        raise MemoriaConexionError(
            "Error inesperado al conectar con PostgreSQL para la memoria conversacional."
        ) from exc


def inicializar_esquema_memoria_chat(
    conninfo: str,
    *,
    tabla: str = TABLA_HISTORIAL_CHAT_DEFECTO,
) -> None:
    """
    Crea indice y tabla de historial si no existen (idempotente).

    Invocar una vez al arranque de la aplicacion (p. ej. lifespan FastAPI).
    """
    if not re.match(r"^\w+$", tabla):
        raise ValueError("Nombre de tabla invalido para historial de chat.")
    conn = conectar_memoria_sync(conninfo)
    try:
        PostgresChatMessageHistory.create_tables(conn, tabla)
    finally:
        conn.close()
    logger.info(
        "Esquema de memoria conversacional listo (tabla %s verificada o creada).",
        tabla,
    )


def crear_memoria_usuario(session_id: str, conninfo: str) -> MemoriaUsuario:
    """
    Fabrica una ``MemoriaUsuario`` con conexion propia.

    El llamador debe invocar :meth:`MemoriaUsuario.cerrar` al terminar o usar la
    instancia como gestor de contexto (``with``).
    """
    conn = conectar_memoria_sync(conninfo)
    return MemoriaUsuario(
        session_id,
        conn,
        cerrar_conexion_al_salir=True,
    )


def aplicar_tope_turnos_ultimos(
    mensajes: list[BaseMessage],
    turnos_max: int,
) -> list[BaseMessage]:
    """
    Conserva solo los ultimos turnos contando desde mensajes humanos hacia atras.

    Un turno se asocia a cada :class:`HumanMessage`. Si no hay humanos,
    conserva como maximo los ultimos ``2 * turnos_max`` mensajes (heuristica).
    """
    if turnos_max <= 0 or not mensajes:
        return mensajes
    tomados: list[BaseMessage] = []
    humanos = 0
    for m in reversed(mensajes):
        tomados.append(m)
        if isinstance(m, HumanMessage):
            humanos += 1
            if humanos >= turnos_max:
                break
    if humanos == 0 and len(mensajes) > turnos_max * 2:
        return mensajes[-(turnos_max * 2) :]
    return list(reversed(tomados))


class MemoriaUsuario:
    """
    Memoria persistente por sesion sobre ``PostgresChatMessageHistory``.

    El ``session_id`` debe alinearse con ``sesion_id_memoria_langchain`` (task-47):
    formato ``user:{uuid}`` o el UUID en texto; internamente se normaliza para
    LangChain Postgres, que persiste ``session_id`` como tipo UUID.
    """

    def __init__(
        self,
        session_id: str,
        sync_connection: psycopg.Connection,
        *,
        tabla: str = TABLA_HISTORIAL_CHAT_DEFECTO,
        dias_max_defecto: int | None = None,
        turnos_max_defecto: int | None = None,
        cerrar_conexion_al_salir: bool = False,
    ) -> None:
        self._session_uuid_txt = normalizar_session_id_postgres_langchain(session_id)
        self._conn = sync_connection
        self._tabla = tabla
        self._cerrar_conn = cerrar_conexion_al_salir
        cfg = obtener_configuracion()
        self._dias_max_defecto = (
            dias_max_defecto if dias_max_defecto is not None else cfg.historial_dias_max
        )
        self._turnos_max_defecto = (
            turnos_max_defecto
            if turnos_max_defecto is not None
            else cfg.historial_turnos_max
        )
        self._lc = PostgresChatMessageHistory(
            tabla,
            self._session_uuid_txt,
            sync_connection=sync_connection,
        )

    def cerrar(self) -> None:
        """Cierra la conexion si esta instancia la abrio con ``crear_memoria_usuario``."""
        if self._cerrar_conn and not self._conn.closed:
            self._conn.close()

    def __enter__(self) -> MemoriaUsuario:
        return self

    def __exit__(self, *args: object) -> None:
        self.cerrar()

    def cargar_ventana(
        self,
        dias_max: int | None = None,
        turnos_max: int | None = None,
    ) -> list[BaseMessage]:
        """
        Mensajes persistidos acotados por antiguedad y cantidad de turnos.

        Filtra por ``created_at >= ahora_utc - dias_max`` usando la columna que
        define el esquema de LangChain (no expuesta en ``get_messages``).
        """
        dias = self._dias_max_defecto if dias_max is None else dias_max
        turnos = self._turnos_max_defecto if turnos_max is None else turnos_max
        if dias < 1:
            dias = 1
        if turnos < 1:
            turnos = 1
        cutoff = datetime.now(tz=UTC) - timedelta(days=dias)
        query = sql.SQL(
            "SELECT message FROM {tbl} WHERE session_id = %s "
            "AND created_at >= %s ORDER BY id"
        ).format(tbl=sql.Identifier(self._tabla))
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, (self._session_uuid_txt, cutoff))
                filas = [fila[0] for fila in cur.fetchall()]
        except psycopg.Error as exc:
            raise MemoriaConexionError(
                "No se pudo leer el historial de chat desde PostgreSQL. "
                "Verifica conectividad y que el esquema de memoria este creado."
            ) from exc
        mensajes = messages_from_dict(filas)
        return aplicar_tope_turnos_ultimos(mensajes, turnos)

    def agregar_humano(self, texto: str) -> None:
        """Persiste un turno humano (no registra el contenido en logs)."""
        try:
            self._lc.add_messages([HumanMessage(content=texto)])
        except psycopg.Error as exc:
            raise MemoriaConexionError(
                "No se pudo guardar el mensaje del usuario en PostgreSQL."
            ) from exc

    def agregar_ai(self, texto: str, metadata: dict | None = None) -> None:
        """Persiste la respuesta del asistente; ``metadata`` va a ``additional_kwargs``."""
        extra = metadata if metadata is not None else {}
        try:
            self._lc.add_messages([AIMessage(content=texto, additional_kwargs=extra)])
        except psycopg.Error as exc:
            raise MemoriaConexionError(
                "No se pudo guardar la respuesta del asistente en PostgreSQL."
            ) from exc
