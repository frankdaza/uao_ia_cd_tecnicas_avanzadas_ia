"""
Memoria conversacional con ``PostgresChatMessageHistory`` (langchain-postgres).

La tabla ``chat_history`` se crea en runtime con ``create_tables`` (no Alembic).

Flujo resumido (historial + PostgreSQL):

1. **Arranque de la app**: ``inicializar_esquema_memoria_chat`` abre una conexion
   sync, llama a ``PostgresChatMessageHistory.create_tables`` y asegura la tabla
   ``chat_history`` (y lo que el esquema de LangChain requiera). No va en
   migraciones Alembic del dominio de usuarios.

2. **Identificador de sesion**: el producto usa ``user:{uuid}`` (ver
   ``sesion_id_memoria_langchain``). ``normalizar_session_id_postgres_langchain``
   lo reduce al UUID en texto porque LangChain valida y persiste ``session_id``
   como UUID en Postgres.

3. **Por peticion del agente**: el endpoint toma una conexion del pool
   ``psycopg`` y construye ``MemoriaUsuario``, que envuelve
   ``PostgresChatMessageHistory`` sobre esa conexion y la tabla por defecto
   ``chat_history``.

4. **Lectura (ventana)**: ``cargar_ventana`` consulta filas de la sesion con
   ``created_at`` dentro de los ultimos ``historial_dias_max`` (config), ordena
   por ``id``, reconstruye mensajes con ``messages_from_dict`` y recorta a los
   ultimos N turnos humanos con ``aplicar_tope_turnos_ultimos`` (tope tambien
   acotado por config o por el bundle de runtime del agente).

5. **Escritura (turno)**: al cerrar un turno del grafo, ``agregar_humano`` y
   ``agregar_ai`` delegan en ``add_messages`` de LangChain, que inserta en
   ``chat_history`` el JSON del mensaje (humano primero, luego respuesta AI;
   metadata opcional en ``additional_kwargs`` del AI).

6. **Utilidades HTTP**: ``consultar_max_created_at_chat_pool`` apoya el login
   (ultimo mensaje); ``borrar_ultimo_turno_en_pool`` elimina hasta las dos
   filas mas recientes de un intercambio para deshacer el ultimo turno.

La conexion es **sincrona** (``psycopg``); las rutas async del API envuelven
estas llamadas en ``asyncio.to_thread`` o abren el pool dentro de un bloque
sync acotado para no bloquear el loop largo.
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
from psycopg_pool import ConnectionPool

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


def consultar_max_created_at_chat_pool(pool: ConnectionPool, session_uuid_txt: str) -> datetime | None:
    """Lee ``MAX(created_at)`` en ``chat_history`` usando una conexion del pool."""
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(created_at) FROM chat_history WHERE session_id = %s::uuid",
                    (session_uuid_txt,),
                )
                row = cur.fetchone()
    except psycopg.Error:
        return None
    if not row or row[0] is None:
        return None
    return row[0]


def borrar_ultimo_turno_en_pool(pool: ConnectionPool, session_id: str) -> int:
    """
    Elimina las ultimas filas del historial (hasta dos: respuesta AI y pregunta human).

    Orden esperado de insercion en un turno completo: ``HumanMessage`` luego ``AIMessage``.
    Se borran por ``id`` descendente (las dos mas recientes). Retorna filas eliminadas.
    """
    uuid_txt = normalizar_session_id_postgres_langchain(session_id)
    with pool.connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM chat_history WHERE session_id = %s::uuid ORDER BY id DESC LIMIT 2",
                    (uuid_txt,),
                )
                ids = [row[0] for row in cur.fetchall()]
                if not ids:
                    conn.commit()
                    return 0
                if len(ids) == 1:
                    cur.execute("DELETE FROM chat_history WHERE id = %s", (ids[0],))
                else:
                    cur.execute("DELETE FROM chat_history WHERE id IN (%s, %s)", (ids[0], ids[1]))
                n = cur.rowcount
            conn.commit()
            return int(n)
        except psycopg.Error:
            conn.rollback()
            raise


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
        """Cierra la conexion si se construyo con ``cerrar_conexion_al_salir=True``."""
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
