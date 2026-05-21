"""Pruebas unitarias de reglas puras del agente M2 (``src.agentes.reglas``)."""

from __future__ import annotations

import uuid

import pytest

from src.agentes.reglas import (
    HISTORIAL_DIAS_MAX,
    HISTORIAL_DIAS_MIN,
    HISTORIAL_TURNOS_MAX,
    RAG_TOP_K_FINAL_MAX,
    RAG_TOP_K_INICIAL_MAX,
    asegurar_historial_dias_max_o_error,
    asegurar_top_k_final_o_error,
    asegurar_top_k_inicial_o_error,
    construir_limites_historial,
    coercionar_top_k_final,
    coercionar_top_k_inicial,
    normalizar_session_id,
)


def test_normalizar_session_id_user_prefijo() -> None:
    u = uuid.uuid4()
    assert normalizar_session_id(f"  user:{u}  ") == str(u)


def test_normalizar_session_id_uuid_solo() -> None:
    u = uuid.uuid4()
    assert normalizar_session_id(str(u)) == str(u)


def test_normalizar_session_id_vacio() -> None:
    with pytest.raises(ValueError, match="vacio"):
        normalizar_session_id("")
    with pytest.raises(ValueError, match="vacio"):
        normalizar_session_id("   ")
    with pytest.raises(ValueError, match="vacio"):
        normalizar_session_id("user:   ")


def test_normalizar_session_id_invalido() -> None:
    with pytest.raises(ValueError, match="no parseable"):
        normalizar_session_id("no-es-uuid")


def test_coercionar_top_k_inicial_extremos() -> None:
    assert coercionar_top_k_inicial(0) == 1
    assert coercionar_top_k_inicial(9999) == RAG_TOP_K_INICIAL_MAX
    assert coercionar_top_k_inicial(15) == 15


def test_coercionar_top_k_final_extremos() -> None:
    assert coercionar_top_k_final(0) == 1
    assert coercionar_top_k_final(100) == RAG_TOP_K_FINAL_MAX
    assert coercionar_top_k_final(5) == 5


def test_asegurar_top_k_fuera_de_rango() -> None:
    with pytest.raises(ValueError):
        asegurar_top_k_inicial_o_error(0)
    with pytest.raises(ValueError):
        asegurar_top_k_final_o_error(0)


def test_construir_limites_historial_acota() -> None:
    lim = construir_limites_historial(0, 500)
    assert lim.dias_max == HISTORIAL_DIAS_MIN
    assert lim.turnos_max == HISTORIAL_TURNOS_MAX


def test_asegurar_historial_dias_max_o_error() -> None:
    assert asegurar_historial_dias_max_o_error(HISTORIAL_DIAS_MAX) == HISTORIAL_DIAS_MAX
    with pytest.raises(ValueError):
        asegurar_historial_dias_max_o_error(0)
