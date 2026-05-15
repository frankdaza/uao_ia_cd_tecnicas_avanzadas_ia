"""Pruebas de heuristicas de metadata para payload Qdrant (TASK-69)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.rag import extractor_metadata as em


@dataclass
class _NodoPrueba:
    metadata: dict[str, Any]
    texto: str

    def get_content(self) -> str:
        return self.texto


def test_inferir_tipo_ficha_medico() -> None:
    assert em.inferir_tipo_pagina("directorio-medico", "x/directorio-medico-juan-perez.md") == "ficha_medico"


def test_inferir_tipo_servicio() -> None:
    assert em.inferir_tipo_pagina("servicios", "servicios-gastroenterologia-pediatrica.md") == "servicio"


def test_inferir_tipo_sede() -> None:
    assert em.inferir_tipo_pagina("sedes", "sedes-sede-alfaguara.md") == "sede"


def test_inferir_tipo_institucional_y_subtipo_mision() -> None:
    ruta = "la-fundacion-mision.md"
    assert em.inferir_tipo_pagina("la-fundacion", ruta) == "institucional"
    assert em.inferir_subtipo(ruta) == "mision"


def test_inferir_tipo_educacion() -> None:
    assert em.inferir_tipo_pagina("educacion", "educacion-lactancia-materna.md") == "educacion"


def test_extraer_nombre_medico_desde_titulo() -> None:
    titulo = "Ana Maria Gomez Bedoya - Fundación Valle del Lili"
    assert em.extraer_nombre_medico(titulo, None) == "Ana Maria Gomez Bedoya"


def test_extraer_especialidades_desde_fm_lista() -> None:
    fm = {"especialidades": ["Pediatría", "Pediatría"]}
    assert em.extraer_especialidades("# cuerpo\n", fm) == ["Pediatria"]


def test_extraer_especialidades_desde_primer_h2() -> None:
    cuerpo = "## Gastroenterologia pediatrica\n\nTexto."
    assert em.extraer_especialidades(cuerpo, {}) == ["Gastroenterologia Pediatrica"]


def test_extraer_especialidades_ficha_omite_h2_generico_recomendaciones() -> None:
    cuerpo = """## Otros Especialistas Que Te Pueden Interesar

- [Link](x)

## Cardiologia

Texto ficha.
"""
    ruta = "valledellili-org/directorio-medico-juan-perez.md"
    assert em.extraer_especialidades(cuerpo, {}, ruta) == ["Cardiologia"]


def test_extraer_sedes_lista_y_marcadores() -> None:
    cuerpo = """
### Sedes

- Sede Alfaguara
- Sede Valle del Lili

Mas texto.
"""
    assert em.extraer_sedes(cuerpo, {}) == ["Sede Alfaguara", "Sede Valle del Lili"]


def test_extraer_sedes_marcas_tequendama_y_av_estacion() -> None:
    assert "Sede Tequendama" in em.extraer_sedes("Atencion en **Sede Tequendama**.", None)
    assert "Sede Av. Estación" in em.extraer_sedes("Como llegar a la Sede Av. Estación.", None)


def test_extraer_tags_fm_y_by_tag() -> None:
    fm = {"tags": ["pediatria"]}
    cuerpo = "Enlace [t](https://x.org/lista?by_tag=bienestar-infant)"
    assert em.extraer_tags(fm, cuerpo) == ["pediatria", "bienestar-infant"]


def test_construir_headings_path_con_header_path() -> None:
    nodo = _NodoPrueba(
        metadata={"header_path": "/Doc/SecA/"},
        texto="### Sub1\n\ntexto",
    )
    assert em.construir_headings_path(nodo) == "Doc > SecA > Sub1"


def test_construir_headings_path_compat_header_123() -> None:
    nodo = _NodoPrueba(
        metadata={"Header_1": "A", "Header_2": "B"},
        texto="cuerpo",
    )
    assert em.construir_headings_path(nodo) == "A > B"


def test_extraer_h1_h2_h3() -> None:
    nodo = _NodoPrueba(metadata={"header_path": "/Uno/Dos/"}, texto="### Tres\n\nx")
    h1, h2, h3 = em.extraer_h1_h2_h3_desde_nodo(nodo)
    assert h1 == "Uno"
    assert h2 == "Dos"
    assert h3 == "Tres"


def test_sin_metadata_extraible_listas_vacias() -> None:
    assert em.extraer_especialidades("Texto plano sin encabezados.", None) == []
    assert em.extraer_sedes("Sin sedes conocidas.", None) == []
    assert em.extraer_tags(None, "") == []