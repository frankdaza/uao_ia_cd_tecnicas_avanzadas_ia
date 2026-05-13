"""Pruebas del prompt de sistema y la composición de mensajes para Ollama."""

from __future__ import annotations

from pathlib import Path

from src.qa.documento_contexto import DocumentoContexto
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO, componer_mensajes, componer_mensajes_multi


def test_prompt_contiene_frase_clave() -> None:
    assert "No tengo información suficiente" in PROMPT_SISTEMA_DEFECTO


def test_prompt_es_espanol_institucional() -> None:
    p = PROMPT_SISTEMA_DEFECTO
    assert "Fundación Valle del Lili" in p
    assert "español formal" in p
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
    assert "CONTEXTO (1 documento ordenado por relevancia)" in lista[0]["content"]
    assert "[DOCUMENTO 1]" in lista[0]["content"]


def test_componer_mensajes_multi_tres_documentos_y_separadores() -> None:
    docs = [
        DocumentoContexto(
            Path("a.md"),
            "Titulo A",
            "https://a.example/doc",
            "Cuerpo alpha",
            3.0,
        ),
        DocumentoContexto(
            Path("b.md"),
            "Titulo B",
            "https://b.example/doc",
            "Cuerpo beta",
            2.0,
        ),
        DocumentoContexto(
            Path("c.md"),
            "Titulo C",
            "",
            "Cuerpo gamma",
            1.0,
        ),
    ]
    msgs = componer_mensajes_multi("SYS", docs, "pregunta usuario")
    sistema = msgs[0]["content"]
    assert "[DOCUMENTO 1]" in sistema
    assert "[DOCUMENTO 2]" in sistema
    assert "[DOCUMENTO 3]" in sistema
    assert "CONTEXTO (3 documentos ordenados por relevancia)" in sistema
    assert sistema.count("---") >= 2
    assert "Cuerpo alpha" in sistema and "Cuerpo beta" in sistema and "Cuerpo gamma" in sistema
    assert "sin URL" in sistema
    assert msgs[1]["content"] == "pregunta usuario"


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
