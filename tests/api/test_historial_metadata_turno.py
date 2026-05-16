"""Serializacion de historial con metadata_turno (TASK-94)."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.api.routers.sesiones import _serializar_mensaje_lc


def test_serializar_ai_con_metadata_turno_completo() -> None:
    msg = AIMessage(
        content="Respuesta",
        additional_kwargs={
            "metadata_turno": {
                "motor": "agente",
                "herramienta_efectiva": "faq_estructurada",
                "pensamientos": [
                    {
                        "tipo": "decision_router",
                        "herramienta": "faq_estructurada",
                        "razon_breve": "Razon corta.",
                    }
                ],
                "fuentes": [],
                "recortado": False,
            }
        },
    )
    item = _serializar_mensaje_lc(msg)
    assert item.rol == "ai"
    assert item.contenido == "Respuesta"
    assert item.metadata_turno is not None
    assert item.metadata_turno.herramienta_efectiva == "faq_estructurada"
    assert len(item.metadata_turno.pensamientos) == 1


def test_serializar_ai_legacy_solo_tool() -> None:
    msg = AIMessage(
        content="Hola",
        additional_kwargs={"tool": "rag_denso", "fuentes": []},
    )
    item = _serializar_mensaje_lc(msg)
    assert item.metadata_turno is not None
    assert item.metadata_turno.herramienta_efectiva == "rag_denso"
    assert item.metadata_turno.pensamientos == []


def test_serializar_ai_sin_additional_kwargs() -> None:
    msg = AIMessage(content="Solo texto")
    item = _serializar_mensaje_lc(msg)
    assert item.metadata_turno is None


def test_serializar_humano_sin_metadata() -> None:
    item = _serializar_mensaje_lc(HumanMessage(content="Pregunta"))
    assert item.rol == "human"
    assert item.metadata_turno is None
