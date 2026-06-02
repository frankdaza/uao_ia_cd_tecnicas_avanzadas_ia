"""Prompts y validacion estatica Bot Lili (Ruta B)."""

from src.prompts.validar import (
    DISCLAIMER_MINIMO,
    extraer_system_prompt_de_agent_toml,
    normalizar_prompt,
    validar_prompt_sistema,
)
from src.prompts.validar_hand import (
    EVERY_SECS_DEMO,
    PALABRAS_ALARMA_CANONICAS,
    validar_hand_manifest,
    validar_skill_md,
)

__all__ = [
    "DISCLAIMER_MINIMO",
    "EVERY_SECS_DEMO",
    "PALABRAS_ALARMA_CANONICAS",
    "extraer_system_prompt_de_agent_toml",
    "normalizar_prompt",
    "validar_hand_manifest",
    "validar_prompt_sistema",
    "validar_skill_md",
]
