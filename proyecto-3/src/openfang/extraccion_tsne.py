"""Extraccion de turnos conversacionales OpenFang para pipeline t-SNE."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from pathlib import Path

import pandas as pd

from src.openfang.historial_jsonl import extraer_session_id, iterar_registros_jsonl
from src.openfang.marcas_tiempo import extraer_marca_tiempo, marca_tiempo_a_iso

logger = logging.getLogger(__name__)

COLUMNAS_PARQUET = (
    "session_id",
    "turno",
    "rol",
    "texto",
    "timestamp",
    "canal",
)

_SCOPES_EPISODICOS = ("episodic", "conversation", "conversational")
_MAPA_ROLES = {
    "human": "user",
    "ai": "assistant",
    "bot": "assistant",
}


def _normalizar_rol(valor: object) -> str | None:
    if not isinstance(valor, str):
        return None
    rol = valor.strip().lower()
    if not rol:
        return None
    rol = _MAPA_ROLES.get(rol, rol)
    if rol in {"user", "assistant", "system"}:
        return rol
    if rol in {"human", "ai"}:
        return _MAPA_ROLES[rol]
    return None


def _extraer_texto(registro: dict) -> str:
    for clave in ("content", "texto", "text", "message"):
        valor = registro.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ""


def _extraer_canal(registro: dict, session_id: str) -> str:
    canal = registro.get("channel") or registro.get("canal")
    if isinstance(canal, str) and canal.strip():
        return canal.strip().lower()
    if ":" in session_id:
        return session_id.split(":", 1)[0].lower()
    return "desconocido"


def es_turno_tsne(registro: dict) -> bool:
    """Turnos utiles para clustering: user, assistant o system."""
    rol = registro.get("role") or registro.get("rol") or registro.get("type") or ""
    if not isinstance(rol, str):
        return False
    rol_norm = _normalizar_rol(rol)
    return rol_norm in {"user", "assistant", "system"}


def normalizar_turno(
    registro: dict,
    *,
    ruta_origen: str,
    fuente: str = "jsonl",
) -> dict | None:
    """Mapea un evento JSONL/SQLite a fila tabular o None si no aplica."""
    if not es_turno_tsne(registro):
        return None
    session_id = extraer_session_id(registro)
    if not session_id:
        return None
    texto = _extraer_texto(registro)
    if not texto:
        return None
    rol = _normalizar_rol(registro.get("role") or registro.get("rol") or registro.get("type"))
    if rol is None:
        return None
    marca = extraer_marca_tiempo(registro)
    return {
        "session_id": session_id,
        "turno": 0,
        "rol": rol,
        "texto": texto,
        "timestamp": marca_tiempo_a_iso(marca),
        "canal": _extraer_canal(registro, session_id),
        "fuente": fuente,
        "ruta_origen": ruta_origen,
        "_marca_orden": marca,
    }


def _texto_normalizado_clave(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip().lower())


def dataframe_desde_jsonl(
    raiz: Path,
    *,
    incluir_audit: bool = False,
) -> pd.DataFrame:
    """Recorre JSONL bajo OPENFANG_HOME (y logs/sessions.jsonl si existe)."""
    filas: list[dict] = []
    if not raiz.is_dir():
        return pd.DataFrame(columns=list(COLUMNAS_PARQUET))

    for ruta, registro in iterar_registros_jsonl(raiz, incluir_audit=incluir_audit):
        fila = normalizar_turno(registro, ruta_origen=str(ruta), fuente="jsonl")
        if fila is not None:
            filas.append(fila)

    agregado = raiz / "logs" / "sessions.jsonl"
    if agregado.is_file():
        try:
            contenido = agregado.read_text(encoding="utf-8")
        except OSError:
            logger.warning("No se pudo leer JSONL agregado: %s", agregado)
        else:
            for linea in contenido.splitlines():
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    registro = json.loads(linea)
                except json.JSONDecodeError:
                    continue
                if isinstance(registro, dict):
                    fila = normalizar_turno(
                        registro,
                        ruta_origen=str(agregado),
                        fuente="jsonl",
                    )
                    if fila is not None:
                        filas.append(fila)

    return _filas_a_dataframe(filas)


def _session_id_desde_metadata(metadata_raw: object) -> str | None:
    if not isinstance(metadata_raw, str) or not metadata_raw.strip():
        return None
    try:
        meta = json.loads(metadata_raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(meta, dict):
        return None
    for clave in ("session_id", "sessionId", "session"):
        valor = meta.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None


def _fila_desde_memoria_episodica(
    row: sqlite3.Row,
    *,
    ruta_db: str,
) -> dict | None:
    scope = row["scope"] if "scope" in row.keys() else ""
    if str(scope).lower() not in _SCOPES_EPISODICOS:
        return None
    content = row["content"] if "content" in row.keys() else ""
    if not isinstance(content, str) or not content.strip():
        return None
    metadata_raw = row["metadata"] if "metadata" in row.keys() else "{}"
    session_id = _session_id_desde_metadata(metadata_raw)
    if not session_id:
        return None
    created = row["created_at"] if "created_at" in row.keys() else ""
    registro = {
        "session_id": session_id,
        "role": "assistant",
        "content": content.strip(),
        "created_at": created,
    }
    fila = normalizar_turno(registro, ruta_origen=ruta_db, fuente="sqlite")
    return fila


def _listar_tablas_fts(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    )
    nombres: list[str] = []
    for nombre, sql in cursor.fetchall():
        if sql and "fts5" in sql.lower():
            nombres.append(str(nombre))
    return nombres


def dataframe_desde_sqlite(ruta_db: Path) -> tuple[pd.DataFrame, bool]:
    """
    Extrae turnos episodicos desde openfang.db.

    Returns:
        (dataframe, fts5_encontrado)
    """
    if not ruta_db.is_file():
        return pd.DataFrame(columns=list(COLUMNAS_PARQUET)), False

    filas: list[dict] = []
    fts5_encontrado = False
    conn = sqlite3.connect(str(ruta_db))
    conn.row_factory = sqlite3.Row
    try:
        tablas_fts = _listar_tablas_fts(conn)
        if tablas_fts:
            fts5_encontrado = True
            logger.info("Tablas FTS5 detectadas: %s", ", ".join(tablas_fts))

        try:
            cursor = conn.execute(
                """
                SELECT content, metadata, created_at, scope
                FROM memories
                WHERE deleted = 0 AND lower(scope) IN (?, ?, ?)
                """,
                _SCOPES_EPISODICOS,
            )
        except sqlite3.Error:
            logger.debug("Tabla memories no disponible o sin columnas esperadas")
        else:
            for row in cursor.fetchall():
                fila = _fila_desde_memoria_episodica(row, ruta_db=str(ruta_db))
                if fila is not None:
                    filas.append(fila)
    finally:
        conn.close()

    return _filas_a_dataframe(filas), fts5_encontrado


def fusionar_fuentes(df_jsonl: pd.DataFrame, df_sqlite: pd.DataFrame) -> pd.DataFrame:
    """Une fuentes deduplicando por session_id + texto normalizado (prefiere JSONL)."""
    if df_jsonl.empty and df_sqlite.empty:
        return pd.DataFrame(columns=list(COLUMNAS_PARQUET))
    if df_sqlite.empty:
        base = df_jsonl.copy()
    elif df_jsonl.empty:
        base = df_sqlite.copy()
    else:
        claves_jsonl = {
            (row["session_id"], _texto_normalizado_clave(row["texto"]))
            for _, row in df_jsonl.iterrows()
        }
        extras = []
        for _, row in df_sqlite.iterrows():
            clave = (row["session_id"], _texto_normalizado_clave(row["texto"]))
            if clave not in claves_jsonl:
                extras.append(row.to_dict())
        base = pd.concat(
            [df_jsonl, pd.DataFrame(extras)],
            ignore_index=True,
        ) if extras else df_jsonl.copy()

    return asignar_turnos(base)


def asignar_turnos(df: pd.DataFrame) -> pd.DataFrame:
    """Numera turno 1..N por session_id ordenado por timestamp."""
    if df.empty:
        return pd.DataFrame(columns=list(COLUMNAS_PARQUET))

    trabajo = df.copy()
    if "_marca_orden" not in trabajo.columns:
        trabajo["_marca_orden"] = pd.to_datetime(
            trabajo["timestamp"],
            utc=True,
            errors="coerce",
        )

    filas_ordenadas: list[dict] = []
    for session_id, grupo in trabajo.groupby("session_id", sort=False):
        ordenado = grupo.sort_values(
            by=["_marca_orden", "timestamp"],
            na_position="last",
        )
        for turno, (_idx, row) in enumerate(ordenado.iterrows(), start=1):
            filas_ordenadas.append(
                {
                    "session_id": session_id,
                    "turno": turno,
                    "rol": row["rol"],
                    "texto": row["texto"],
                    "timestamp": row["timestamp"],
                    "canal": row["canal"],
                }
            )

    return pd.DataFrame(filas_ordenadas, columns=list(COLUMNAS_PARQUET))


def _filas_a_dataframe(filas: list[dict]) -> pd.DataFrame:
    if not filas:
        return pd.DataFrame(columns=list(COLUMNAS_PARQUET))
    df = pd.DataFrame(filas)
    columnas = [c for c in COLUMNAS_PARQUET if c in df.columns]
    extras = ["_marca_orden", "fuente", "ruta_origen"]
    for col in extras:
        if col in df.columns:
            columnas.append(col)
    return df[columnas] if columnas else pd.DataFrame(columns=list(COLUMNAS_PARQUET))


def construir_dataframe_completo(
    raiz_openfang: Path,
    ruta_db: Path,
    *,
    incluir_audit: bool = False,
    solo_jsonl: bool = False,
) -> tuple[pd.DataFrame, bool]:
    """
    Construye el dataset final.

    Returns:
        (dataframe, fts5_ausente) — fts5_ausente True si no hubo SQLite util.
    """
    df_jsonl = dataframe_desde_jsonl(raiz_openfang, incluir_audit=incluir_audit)
    fts5_ausente = False

    if solo_jsonl or not ruta_db.is_file():
        fts5_ausente = True
        df_sqlite = pd.DataFrame(columns=list(COLUMNAS_PARQUET))
        fts5_encontrado = False
    else:
        df_sqlite, fts5_encontrado = dataframe_desde_sqlite(ruta_db)
        if df_sqlite.empty and not fts5_encontrado:
            fts5_ausente = True

    df = fusionar_fuentes(df_jsonl, df_sqlite)
    return df, fts5_ausente


def escribir_parquet(df: pd.DataFrame, ruta_salida: Path) -> None:
    """Persiste parquet con esquema fijo."""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    salida = df[list(COLUMNAS_PARQUET)] if not df.empty else pd.DataFrame(columns=list(COLUMNAS_PARQUET))
    salida.to_parquet(ruta_salida, index=False)
