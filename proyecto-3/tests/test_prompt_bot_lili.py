"""Pruebas estaticas del prompt Bot Lili (system.md y agent.toml)."""

from __future__ import annotations

from pathlib import Path

from src.prompts.validar import (
    extraer_system_prompt_de_agent_toml,
    leer_prompt_desde_system_md,
    normalizar_prompt,
    rutas_prompt_proyecto,
    validar_prompt_sistema,
)

_RAIZ = Path(__file__).resolve().parents[1]


def test_system_md_existe_y_valida() -> None:
    system_md, _ = rutas_prompt_proyecto(_RAIZ)
    assert system_md.is_file()
    prompt = leer_prompt_desde_system_md(system_md)
    faltantes = validar_prompt_sistema(prompt)
    assert faltantes == [], f"Faltan en system.md: {faltantes}"


def test_agent_toml_system_prompt_sincronizado() -> None:
    system_md, agent_toml = rutas_prompt_proyecto(_RAIZ)
    desde_md = normalizar_prompt(leer_prompt_desde_system_md(system_md))
    contenido = agent_toml.read_text(encoding="utf-8")
    desde_toml = normalizar_prompt(extraer_system_prompt_de_agent_toml(contenido))
    assert desde_md == desde_toml, "Ejecuta scripts/sincronizar_prompt_agente.py"


def test_secciones_clave_en_prompt() -> None:
    system_md, _ = rutas_prompt_proyecto(_RAIZ)
    texto = leer_prompt_desde_system_md(system_md).lower()
    for fragmento in (
        "## rol",
        "## uso de memoria",
        "## citas al corpus",
        "## disclaimer",
        "## limites",
        "## senales de alarma",
    ):
        assert fragmento in texto, f"Falta seccion {fragmento}"


def test_disclaimer_verificable() -> None:
    system_md, _ = rutas_prompt_proyecto(_RAIZ)
    prompt = leer_prompt_desde_system_md(system_md).lower()
    assert "no reemplaza" in prompt
    assert "medico tratante" in prompt
