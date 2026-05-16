"""
Reglas de dominio del agente M2 expresadas como funciones puras y DTOs inmutables.

Centraliza normalizacion de ``session_id``, ventana de historial (dias y turnos) y topes de
recuperacion RAG para poder probarlas sin leer entorno ni abrir conexiones (decision-6,
sub-decision 5: puertos explicitos solo donde hay reglas estables reutilizables).

**Criterio YAGNI (decision-6):** no introducir Protocol/ABC genericos sin un segundo consumidor
del mismo caso de uso fuera del borde HTTP; este modulo son datos y funciones, no interfaces
``por si acaso``.

Los valores minimo/maximo se alinean con :class:`~src.api.configuracion.Configuracion`
(``pydantic-settings``); la lectura de ``.env`` permanece en el borde (FastAPI / settings).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

# --- Historial conversacional (ventana temporal + tope de turnos) ---
HISTORIAL_DIAS_MIN: int = 1
HISTORIAL_DIAS_MAX: int = 365
HISTORIAL_TURNOS_MIN: int = 1
HISTORIAL_TURNOS_MAX: int = 200

# Defaults alineados a ``Configuracion`` cuando el caller no inyecta un DTO.
HISTORIAL_DIAS_DEFECTO: int = 7
HISTORIAL_TURNOS_DEFECTO: int = 20

# --- RAG denso: fragmentos finales al compositor (``rag_top_k`` / k final) ---
RAG_TOP_K_FINAL_MIN: int = 1
RAG_TOP_K_FINAL_MAX: int = 50

# --- RAG: candidatos iniciales a Qdrant antes de MMR/rerank (``rag_top_k_inicial``) ---
RAG_TOP_K_INICIAL_MIN: int = 1
RAG_TOP_K_INICIAL_MAX: int = 200


@dataclass(frozen=True, slots=True)
class LimitesHistorial:
    """Politica de ventana de historial persistido (dias hacia atras y turnos humanos)."""

    dias_max: int
    turnos_max: int


LIMITES_HISTORIAL_POR_DEFECTO = LimitesHistorial(
    dias_max=HISTORIAL_DIAS_DEFECTO,
    turnos_max=HISTORIAL_TURNOS_DEFECTO,
)


def normalizar_session_id(valor: str) -> str:
    """
    Convierte el identificador de sesion al UUID en texto exigido por LangChain Postgres.

    Acepta ``user:{uuid}`` (canonico del producto) o el UUID solo. Espacios laterales se
    ignoran. Cadena vacia o no parseable: ``ValueError``.
    """
    s = (valor or "").strip()
    if not s:
        raise ValueError(
            "session_id no puede estar vacio (se esperaba UUID o formato canonico user:{uuid})."
        )
    if s.lower().startswith("user:"):
        s = s[5:].strip()
    if not s:
        raise ValueError(
            "session_id no puede estar vacio tras quitar el prefijo user: "
            "(se esperaba UUID valido)."
        )
    try:
        return str(uuid.UUID(s))
    except ValueError as exc:
        raise ValueError(
            "session_id debe ser un UUID valido o el formato canonico user:{uuid} "
            f"(task-47). Valor recibido no parseable: {valor!r}"
        ) from exc


# Retrocompat con nombre historico usado en memoria y rutas HTTP.
normalizar_session_id_postgres_langchain = normalizar_session_id


def _acotar_entero(valor: int, minimo: int, maximo: int) -> int:
    return max(minimo, min(maximo, int(valor)))


def coercionar_historial_dias_max(dias: int) -> int:
    """Acota dias de ventana de historial al rango permitido por producto."""
    return _acotar_entero(dias, HISTORIAL_DIAS_MIN, HISTORIAL_DIAS_MAX)


def coercionar_historial_turnos_max(turnos: int) -> int:
    """Acota el tope de turnos humanos visibles en memoria/router."""
    return _acotar_entero(turnos, HISTORIAL_TURNOS_MIN, HISTORIAL_TURNOS_MAX)


def construir_limites_historial(dias_max: int, turnos_max: int) -> LimitesHistorial:
    """Construye DTO inmutable con valores acotados (regla de dominio)."""
    return LimitesHistorial(
        dias_max=coercionar_historial_dias_max(dias_max),
        turnos_max=coercionar_historial_turnos_max(turnos_max),
    )


def asegurar_historial_dias_max_o_error(dias: int) -> int:
    """Valida estricta; lanza ``ValueError`` si ``dias`` queda fuera de rango."""
    v = int(dias)
    if HISTORIAL_DIAS_MIN <= v <= HISTORIAL_DIAS_MAX:
        return v
    raise ValueError(
        f"historial_dias_max debe estar entre {HISTORIAL_DIAS_MIN} y {HISTORIAL_DIAS_MAX}."
    )


def asegurar_historial_turnos_max_o_error(turnos: int) -> int:
    v = int(turnos)
    if HISTORIAL_TURNOS_MIN <= v <= HISTORIAL_TURNOS_MAX:
        return v
    raise ValueError(
        f"historial_turnos_max debe estar entre {HISTORIAL_TURNOS_MIN} y {HISTORIAL_TURNOS_MAX}."
    )


def coercionar_top_k_final(top_k: int) -> int:
    """Acota ``rag_top_k`` (tamano final deseado de fragmentos al compositor, k final)."""
    return _acotar_entero(top_k, RAG_TOP_K_FINAL_MIN, RAG_TOP_K_FINAL_MAX)


def coercionar_top_k_inicial(k_inicial: int) -> int:
    """Acota candidatos pedidos a Qdrant antes de MMR/rerank (k inicial)."""
    return _acotar_entero(k_inicial, RAG_TOP_K_INICIAL_MIN, RAG_TOP_K_INICIAL_MAX)


def asegurar_top_k_final_o_error(top_k: int) -> int:
    v = int(top_k)
    if RAG_TOP_K_FINAL_MIN <= v <= RAG_TOP_K_FINAL_MAX:
        return v
    raise ValueError(
        f"rag_top_k (k final) debe estar entre {RAG_TOP_K_FINAL_MIN} y {RAG_TOP_K_FINAL_MAX}."
    )


def asegurar_top_k_inicial_o_error(k_inicial: int) -> int:
    v = int(k_inicial)
    if RAG_TOP_K_INICIAL_MIN <= v <= RAG_TOP_K_INICIAL_MAX:
        return v
    raise ValueError(
        "rag_top_k_inicial (k inicial) debe estar entre "
        f"{RAG_TOP_K_INICIAL_MIN} y {RAG_TOP_K_INICIAL_MAX}."
    )


__all__ = [
    "HISTORIAL_DIAS_DEFECTO",
    "HISTORIAL_DIAS_MAX",
    "HISTORIAL_DIAS_MIN",
    "HISTORIAL_TURNOS_DEFECTO",
    "HISTORIAL_TURNOS_MAX",
    "HISTORIAL_TURNOS_MIN",
    "LIMITES_HISTORIAL_POR_DEFECTO",
    "LimitesHistorial",
    "RAG_TOP_K_FINAL_MAX",
    "RAG_TOP_K_FINAL_MIN",
    "RAG_TOP_K_INICIAL_MAX",
    "RAG_TOP_K_INICIAL_MIN",
    "asegurar_historial_dias_max_o_error",
    "asegurar_historial_turnos_max_o_error",
    "asegurar_top_k_final_o_error",
    "asegurar_top_k_inicial_o_error",
    "construir_limites_historial",
    "coercionar_historial_dias_max",
    "coercionar_historial_turnos_max",
    "coercionar_top_k_final",
    "coercionar_top_k_inicial",
    "normalizar_session_id",
    "normalizar_session_id_postgres_langchain",
]
