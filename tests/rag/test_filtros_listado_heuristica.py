"""Heuristica de filtros para listar_estructurado (catalogo de sedes vs directorio)."""

from __future__ import annotations

import pytest

from src.rag.runtime.filtros_listado_heuristica import extraer_filtros_listado_desde_pregunta


@pytest.mark.parametrize(
    ("pregunta", "esperado"),
    [
        (
            "Dame toda la información de tus sedes",
            {"tipo_pagina": "sede"},
        ),
        (
            "¿Cuáles son las sedes de la fundación?",
            {"tipo_pagina": "sede"},
        ),
        (
            "Ubicaciones de la fundación y horarios",
            {"tipo_pagina": "sede"},
        ),
        (
            "¿Dónde están las sedes?",
            {"tipo_pagina": "sede"},
        ),
    ],
)
def test_catalogo_sedes_sin_directorio(pregunta: str, esperado: dict) -> None:
    assert extraer_filtros_listado_desde_pregunta(pregunta) == esperado


def test_directorio_por_sede_no_es_catalogo_institucional() -> None:
    out = extraer_filtros_listado_desde_pregunta(
        "Lista los pediatras que atienden en Sede Limonar",
    )
    assert out.get("tipo_pagina") == "ficha_medico"
    assert "Sede Limonar" in (out.get("sedes") or [])


def test_servicios_oncologia_no_lo_sobrescribe_catalogo_ambiguo() -> None:
    out = extraer_filtros_listado_desde_pregunta("Lista todos los servicios de oncologia")
    assert out.get("tipo_pagina") == "servicio"


@pytest.mark.parametrize(
    "pregunta",
    [
        "Dame toda la información sobre todos los cardiólogos del directorio médico",
        "Listado de cardiologos en el directorio",
        "¿Cuántos médicos de cardiología hay?",
    ],
)
def test_directorio_detecta_cardiologia_con_tilde_o_plural(pregunta: str) -> None:
    out = extraer_filtros_listado_desde_pregunta(pregunta)
    assert out.get("tipo_pagina") == "ficha_medico"
    assert out.get("especialidad") == "Cardiologia"
