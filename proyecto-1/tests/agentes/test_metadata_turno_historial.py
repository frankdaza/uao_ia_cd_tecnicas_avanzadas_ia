"""Pruebas de construccion y normalizacion de metadata_turno (TASK-94)."""

from __future__ import annotations

from src.agentes.metadata_turno_historial import (
    construir_metadata_turno_para_persistencia,
    normalizar_metadata_turno_desde_additional_kwargs,
)


def test_construir_incluye_pensamientos_y_herramienta() -> None:
    state = {
        "tool_decidida": "faq_estructurada",
        "fuentes": [],
        "pensamientos": [
            {
                "tipo": "decision_router",
                "herramienta": "faq_estructurada",
                "razon_breve": "Seleccion via binding.",
            },
            {
                "tipo": "ejecucion_tool",
                "herramienta": "faq_estructurada",
                "razon_breve": "Tool ejecutada.",
            },
        ],
    }
    meta = construir_metadata_turno_para_persistencia(state)
    assert meta["motor"] == "agente"
    assert meta["herramienta_efectiva"] == "faq_estructurada"
    assert len(meta["pensamientos"]) == 2
    assert meta["fuentes"] == []


def test_normalizar_desde_legacy_tool_y_fuentes() -> None:
    raw = {
        "tool": "rag_denso",
        "fuentes": [{"archivo": "politica.md", "titulo": "Politica", "score": 0.5}],
    }
    n = normalizar_metadata_turno_desde_additional_kwargs(raw)
    assert n is not None
    assert n["herramienta_efectiva"] == "rag_denso"
    assert len(n["fuentes"]) == 1
    assert n["pensamientos"] == []


def test_normalizar_sin_metadata_devuelve_none() -> None:
    assert normalizar_metadata_turno_desde_additional_kwargs({}) is None
    assert normalizar_metadata_turno_desde_additional_kwargs(None) is None


def test_normalizar_metadata_turno_listas_null_a_vacias() -> None:
    """JSON legacy puede traer pensamientos/fuentes null dentro del dict."""
    raw = {
        "metadata_turno": {
            "motor": "agente",
            "herramienta_efectiva": "rag_denso",
            "pensamientos": None,
            "fuentes": None,
        }
    }
    n = normalizar_metadata_turno_desde_additional_kwargs(raw)
    assert n is not None
    assert n["pensamientos"] == []
    assert n["fuentes"] == []


def test_normalizar_prefiere_metadata_turno_explicito() -> None:
    raw = {
        "tool": "faq_estructurada",
        "fuentes": [],
        "metadata_turno": {
            "motor": "agente",
            "herramienta_efectiva": "rag_denso",
            "pensamientos": [],
            "fuentes": [{"archivo": "x.md", "score": 0.1}],
        },
    }
    n = normalizar_metadata_turno_desde_additional_kwargs(raw)
    assert n is not None
    assert n["herramienta_efectiva"] == "rag_denso"
    assert len(n["fuentes"]) == 1
