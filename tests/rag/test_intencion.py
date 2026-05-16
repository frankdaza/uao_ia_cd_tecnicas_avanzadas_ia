"""Pruebas de heuristica de intencion (TASK-70)."""

from __future__ import annotations

import pytest

from src.rag.runtime.intencion import inferir_filtros_tipo_pagina_para_rag, inferir_intencion


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("¿Cuál es la política de calidad?", "factual"),
        ("Explique el modelo de atencion", "factual"),
        ("Que hace gastro pediatrica segun la web", "factual"),
        ("Cuentame algo sobre la fundacion", "factual"),
        ("Horario de visitas en UCI", "factual"),
        ("Lista los pediatras del directorio", "listado"),
        ("Enumera todos los servicios de oncologia", "listado"),
        ("Dame todos los medicos de cardiologia", "listado"),
        ("TODAS LAS SEDES con laboratorio", "listado"),
        ("Qué médicos atienden en urgencias pediatricas", "listado"),
        ("¿Cuántos pediatras hay?", "conteo"),
        ("Cuantas fichas hay de oncologia", "conteo"),
        ("NUMERO DE medicos en el directorio", "conteo"),
        ("Cantidad de servicios de imagen", "conteo"),
        ("¿CUÁNTAS enfermeras hay?", "conteo"),
        ("¿Cuánto cuesta una consulta?", "factual"),
        ("Cuanto tardan los resultados", "factual"),
        ("LISTADO de precios de laboratorio", "listado"),
    ],
)
def test_inferir_intencion_casos(texto: str, esperado: str) -> None:
    assert inferir_intencion(texto) == esperado


def test_inferir_intencion_vacio() -> None:
    assert inferir_intencion("") == "factual"
    assert inferir_intencion("   ") == "factual"


def test_filtros_tipo_pagina_mision() -> None:
    assert inferir_filtros_tipo_pagina_para_rag("¿Cuál es la misión institucional?") == [
        "institucional",
    ]


def test_filtros_tipo_pagina_sin_match() -> None:
    assert inferir_filtros_tipo_pagina_para_rag("Telefono PBX") is None


def test_filtros_tipo_pagina_sede() -> None:
    assert inferir_filtros_tipo_pagina_para_rag("Dame toda la información de tus sedes") == [
        "sede",
    ]
    assert inferir_filtros_tipo_pagina_para_rag("¿Dónde están las sedes?") == ["sede"]


def test_inferir_intencion_informacion_sedes_es_listado() -> None:
    assert inferir_intencion("Dame toda la información de tus sedes") == "listado"


def test_inferir_intencion_cuántas_sedes_es_conteo() -> None:
    assert inferir_intencion("¿Cuántas sedes hay?") == "conteo"
