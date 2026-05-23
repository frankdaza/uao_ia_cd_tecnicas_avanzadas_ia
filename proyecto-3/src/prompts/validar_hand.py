"""Validacion estatica del manifesto Hand taam_lili_hand (HAND.toml, SKILL, playbooks)."""

from __future__ import annotations

import tomllib
from pathlib import Path

EVERY_SECS_DEMO = 30
TZ_DEMO = "America/Bogota"
NOMBRE_HAND = "taam_lili_hand"

PALABRAS_ALARMA_CANONICAS = (
    "dolor intenso",
    "fiebre alta",
    "sangrado abundante",
    "dificultad respiratoria",
)

CLAVES_PROMPTS = (
    "recordatorio_postoperatorio",
    "requerir_evidencia_texto",
)


def ruta_hand_dir(raiz: Path | None = None) -> Path:
    """Directorio del Hand bajo proyecto-3."""
    base = raiz or Path(__file__).resolve().parents[2]
    return base / "openfang" / "hands" / "taam_lili_hand"


def cargar_hand_toml(raiz: Path | None = None) -> dict:
    ruta = ruta_hand_dir(raiz) / "HAND.toml"
    if not ruta.is_file():
        msg = f"Falta {ruta}"
        raise FileNotFoundError(msg)
    return tomllib.loads(ruta.read_text(encoding="utf-8"))


def validar_hand_manifest(raiz: Path | None = None) -> list[str]:
    """Devuelve lista de faltantes; vacia si el manifesto cumple reglas minimas."""
    faltantes: list[str] = []
    hand_dir = ruta_hand_dir(raiz)
    cfg = cargar_hand_toml(raiz)

    hand = cfg.get("hand", {})
    if hand.get("name") != NOMBRE_HAND:
        faltantes.append(f"hand.name == {NOMBRE_HAND!r}")

    schedule = cfg.get("schedule", {})
    if schedule.get("every_secs") != EVERY_SECS_DEMO:
        faltantes.append(f"schedule.every_secs == {EVERY_SECS_DEMO}")
    if schedule.get("tz") != TZ_DEMO:
        faltantes.append(f"schedule.tz == {TZ_DEMO!r}")

    capabilities = cfg.get("capabilities", {})
    for clave in CLAVES_PROMPTS:
        if not capabilities.get(clave):
            faltantes.append(f"capabilities.{clave}")

    guardrails = cfg.get("guardrails", {})
    if not guardrails.get("no_diagnostico"):
        faltantes.append("guardrails.no_diagnostico")
    if not guardrails.get("disclaimer_obligatorio"):
        faltantes.append("guardrails.disclaimer_obligatorio")
    lista_alarma = guardrails.get("escalar_palabras_alarma", [])
    if not isinstance(lista_alarma, list) or not lista_alarma:
        faltantes.append("guardrails.escalar_palabras_alarma (lista no vacia)")
    else:
        for frase in PALABRAS_ALARMA_CANONICAS:
            if frase not in lista_alarma:
                faltantes.append(f"escalar_palabras_alarma incluye {frase!r}")

    channel = cfg.get("channel", {})
    if channel.get("default") != "telegram":
        faltantes.append("channel.default == telegram")

    prompts = cfg.get("prompts", {})
    for clave in CLAVES_PROMPTS:
        rel = prompts.get(clave)
        if not rel:
            faltantes.append(f"prompts.{clave}")
            continue
        ruta_playbook = hand_dir / rel
        if not ruta_playbook.is_file():
            faltantes.append(f"archivo playbook {rel}")
        elif not ruta_playbook.read_text(encoding="utf-8").strip():
            faltantes.append(f"playbook vacio {rel}")

    return faltantes


def validar_skill_md(raiz: Path | None = None) -> list[str]:
    """Comprueba contenido minimo de SKILL.md."""
    faltantes: list[str] = []
    ruta = ruta_hand_dir(raiz) / "SKILL.md"
    if not ruta.is_file():
        return ["SKILL.md"]
    texto = ruta.read_text(encoding="utf-8").lower()
    for fragmento in (
        "telegram",
        "every_secs",
        "30",
        "uc6",
        "uc7",
        "prompts/",
        "no diagnosticar",
    ):
        if fragmento not in texto:
            faltantes.append(f"SKILL.md contiene {fragmento!r}")
    return faltantes
