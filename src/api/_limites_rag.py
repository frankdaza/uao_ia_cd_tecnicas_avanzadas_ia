"""Limites numericos compartidos del pipeline RAG y parametros admin relacionados."""

from __future__ import annotations

from dataclasses import dataclass

from src.agentes.reglas import (
    HISTORIAL_TURNOS_MAX,
    HISTORIAL_TURNOS_MIN,
    RAG_TOP_K_FINAL_MAX,
    RAG_TOP_K_FINAL_MIN,
    RAG_TOP_K_INICIAL_MAX,
    RAG_TOP_K_INICIAL_MIN,
)


@dataclass(frozen=True)
class LimiteRag:
    """Rango cerrado [minimo, maximo] y valor por defecto documentado (p. ej. migraciones)."""

    minimo: float | int
    maximo: float | int
    defecto: float | int


LIMITES_RAG: dict[str, LimiteRag] = {
    "rag_top_k": LimiteRag(RAG_TOP_K_FINAL_MIN, RAG_TOP_K_FINAL_MAX, 5),
    "rag_top_k_inicial": LimiteRag(RAG_TOP_K_INICIAL_MIN, RAG_TOP_K_INICIAL_MAX, 20),
    "rag_score_minimo": LimiteRag(0.0, 1.0, 0.25),
    "rag_mmr_lambda": LimiteRag(0.0, 1.0, 0.5),
    "rag_reranker_top_n_entrada": LimiteRag(1, 50, 10),
    "rag_reranker_batch_size": LimiteRag(1, 256, 16),
}

LIMITE_HISTORIAL_TURNOS_MAX = LimiteRag(HISTORIAL_TURNOS_MIN, HISTORIAL_TURNOS_MAX, 20)

LIMITES_CONFIG_ADMIN_NUMERICOS: dict[str, LimiteRag] = {
    **LIMITES_RAG,
    "historial_turnos_max": LIMITE_HISTORIAL_TURNOS_MAX,
}


def clamp_valor_admin_numerico(valor: int | float, campo: str) -> tuple[int | float, bool]:
    """
    Acota ``valor`` al rango del campo y devuelve si hubo recorte.

    Parameters
    ----------
    campo:
        Clave en :data:`LIMITES_CONFIG_ADMIN_NUMERICOS` (p. ej. ``rag_top_k``).
    """
    limite = LIMITES_CONFIG_ADMIN_NUMERICOS[campo]
    if isinstance(limite.minimo, int) and isinstance(limite.maximo, int) and not isinstance(valor, bool):
        original = int(valor)
        acotado = int(max(limite.minimo, min(limite.maximo, original)))
        return acotado, acotado != original
    original_f = float(valor)
    acotado_f = float(max(float(limite.minimo), min(float(limite.maximo), original_f)))
    hubo = abs(acotado_f - original_f) > 1e-12
    return acotado_f, hubo


def asegurar_rango_parche_numerico(campo: str, valor: int | float) -> None:
    """Valida que ``valor`` este dentro del rango permitido (PATCH admin); lanza ``ValueError`` si no."""
    limite = LIMITES_CONFIG_ADMIN_NUMERICOS[campo]
    if isinstance(limite.minimo, int) and isinstance(limite.maximo, int) and not isinstance(valor, bool):
        v = int(valor)
        if int(limite.minimo) <= v <= int(limite.maximo):
            return
    else:
        v = float(valor)
        if float(limite.minimo) <= v <= float(limite.maximo):
            return
    msg = f"{campo} debe estar entre {limite.minimo} y {limite.maximo}."
    raise ValueError(msg)


__all__ = [
    "LIMITES_CONFIG_ADMIN_NUMERICOS",
    "LIMITES_RAG",
    "LIMITE_HISTORIAL_TURNOS_MAX",
    "LimiteRag",
    "asegurar_rango_parche_numerico",
    "clamp_valor_admin_numerico",
]
