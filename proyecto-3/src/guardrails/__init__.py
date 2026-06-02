"""Guardrails clinicos TAAM (Ruta B)."""

from src.guardrails.escalacion_clinica import (
    MENSAJE_URGENCIA,
    MOTIVO_ESCALADO_CLINICO,
    PALABRAS_ALARMA,
    ResultadoEscalacion,
    debe_escalar,
    evaluar_entrada_usuario,
    frase_alarma_detectada,
    marcar_escalacion,
    palabras_alarma_desde_hand,
    redactar_mensaje_urgencia,
    validar_mensaje_urgencia,
)

__all__ = [
    "MENSAJE_URGENCIA",
    "MOTIVO_ESCALADO_CLINICO",
    "PALABRAS_ALARMA",
    "ResultadoEscalacion",
    "debe_escalar",
    "evaluar_entrada_usuario",
    "frase_alarma_detectada",
    "marcar_escalacion",
    "palabras_alarma_desde_hand",
    "redactar_mensaje_urgencia",
    "validar_mensaje_urgencia",
]
