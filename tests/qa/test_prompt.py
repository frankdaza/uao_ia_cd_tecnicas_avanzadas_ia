"""Pruebas del prompt de sistema y la composición de mensajes para Ollama."""

from __future__ import annotations

from src.qa.prompt import PROMPT_SISTEMA_DEFECTO, componer_mensajes


def test_prompt_contiene_frase_clave() -> None:
    assert "No tengo información suficiente" in PROMPT_SISTEMA_DEFECTO


def test_prompt_es_espanol_colombiano() -> None:
    p = PROMPT_SISTEMA_DEFECTO
    assert "Fundación Valle del Lili" in p
    assert "español colombiano" in p
    assert "parcero" in p.lower()
    # Evita marcas típicas de otros dialectos (p. ej. peninsular "vosotros")
    assert "vosotros" not in p.lower()


def test_componer_mensajes_estructura() -> None:
    md = "# Guía\n\nTexto de prueba."
    lista = componer_mensajes(
        "Instrucción corta",
        md,
        "¿Qué dice el documento?",
        metadata_documento={"source_url": "https://ejemplo.org/doc"},
    )
    assert len(lista) == 2
    assert lista[0]["role"] == "system"
    assert lista[1]["role"] == "user"
    assert md in lista[0]["content"]
    assert lista[1]["content"] == "¿Qué dice el documento?"
    assert "https://ejemplo.org/doc" in lista[0]["content"]


def test_componer_mensajes_sin_truncar() -> None:
    grande = "x" * 50_000
    msgs = componer_mensajes(PROMPT_SISTEMA_DEFECTO, grande, "Pregunta")
    system = msgs[0]["content"]
    assert len(system) >= 50_000 + len(PROMPT_SISTEMA_DEFECTO)
    assert grande in system
    assert "..." not in system  # no recorte con elipsis en este módulo
    # Integridad: mismos 50_000 caracteres
    inicio = system.index("x" * 20)
    assert system[inicio : inicio + 50_000] == grande
