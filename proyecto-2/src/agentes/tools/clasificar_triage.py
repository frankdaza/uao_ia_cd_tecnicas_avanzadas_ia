"""Tool ``clasificar_triage`` (severidad estructurada)."""

from __future__ import annotations

from langchain_core.tools import tool

from src.agentes.tools.esquemas import EntradaClasificarTriage, SalidaClasificarTriage

_RED_FLAGS = (
    "fiebre alta",
    "fiebre",
    "sangrado abundante",
    "sangrado",
    "dificultad para respirar",
    "no puedo respirar",
    "dolor intenso",
    "dolor muy fuerte",
    "confusion",
    "desmayo",
    "hinchazon severa",
)

_SEGUIMIENTO = (
    "dolor",
    "molestia",
    "hinchazon",
    "nausea",
    "vomito",
    "herida",
    "temperatura",
)


def _clasificar_heuristica(texto: str) -> SalidaClasificarTriage:
    t = texto.lower()
    for frase in _RED_FLAGS:
        if frase in t:
            return SalidaClasificarTriage(
                severidad="urgente",
                rationale=f"Se detectaron posibles signos de alarma ({frase}).",
            )
    for frase in _SEGUIMIENTO:
        if frase in t:
            return SalidaClasificarTriage(
                severidad="seguimiento",
                rationale=f"Sintoma que requiere seguimiento clinico ({frase}).",
            )
    return SalidaClasificarTriage(
        severidad="info",
        rationale="Consulta informativa sin red flags evidentes en el texto.",
    )


@tool("clasificar_triage", args_schema=EntradaClasificarTriage)
def clasificar_triage(
    sintomas_descritos: str,
    mensaje_paciente: str | None = None,
) -> SalidaClasificarTriage:
    """
    Clasifica la severidad del triage: info, seguimiento o urgente.

    Si la severidad es urgente, el agente debe invocar ``escalar_a_equipo`` (sujeto a HITL).
    """
    texto = sintomas_descritos
    if mensaje_paciente:
        texto = f"{sintomas_descritos} {mensaje_paciente}"
    return _clasificar_heuristica(texto)
