"""Prompt del sistema y middleware ``dynamic_prompt``."""

from __future__ import annotations

from langchain.agents.middleware import ModelRequest, dynamic_prompt

from src.agentes.contexto import obtener_session_id_runtime

_DISCLAIMER = (
    "Este asistente de seguimiento postoperatorio no reemplaza a su medico tratante. "
    "Ante urgencias reales (dolor intenso, sangrado abundante, fiebre alta, dificultad "
    "para respirar), acuda de inmediato a servicios de emergencia."
)

_INSTRUCCIONES_BASE = (
    "Eres el bot de seguimiento postoperatorio de la Fundacion Valle del Lili (TAAM). "
    "Usa siempre las herramientas disponibles para consultar protocolo, FAQs, contexto "
    "del caso y clasificar triage; no inventes indicaciones medicas. "
    "Si una herramienta falla, responde con cortesia que el equipo revisara su consulta. "
    "Si no hay resultados de protocolo, indique consultar al equipo tratante. "
    "Cuando ``clasificar_triage`` devuelva severidad ``urgente``, debe llamar "
    "``escalar_a_equipo`` antes de cerrar la respuesta. "
    "Formatea las respuestas al paciente en Markdown simple: secciones con ###, "
    "listas con guion (-) y enfasis con **negrita**. "
    "Si una viñeta tiene subpuntos (fases o subitems), indenta cada subitem con "
    "dos espacios bajo el guion (``  -``)."
)


@dynamic_prompt
def prompt_dinamico_taam(request: ModelRequest) -> str:
    """Inyecta disclaimer, datos del caso (precargados) y session_id."""
    partes = [_DISCLAIMER, _INSTRUCCIONES_BASE]
    ctx = request.runtime.context
    session_id = ctx.get("session_id") or obtener_session_id_runtime()
    partes.append(f"Identificador de sesion: {session_id}.")

    resumen = ctx.get("resumen_caso")
    if resumen:
        partes.append(resumen)
    elif ctx.get("sin_vinculo"):
        partes.append(
            "No hay caso postoperatorio vinculado a este chat. "
            "Oriente al paciente a usar el codigo de emparejamiento entregado por el equipo."
        )

    return "\n\n".join(partes)


PROMPT_SISTEMA_ESTATICO = f"{_DISCLAIMER}\n\n{_INSTRUCCIONES_BASE}"
