"""Pruebas de conversion Markdown → HTML para Telegram."""

from __future__ import annotations

import re

import pytest

from src.integracion.telegram.formateo import (
    es_markdown_probable,
    markdown_a_html_telegram,
)

_TEXTO_POSTOPERATORIO = """\
Aquí tienes algunas recomendaciones y cuidados postoperatorios tras tu apendicectomía:

### Recomendaciones Generales:
- **Reposo**: Mantén reposo absoluto las primeras 24 horas.
- **Dieta**: Inicia con líquidos claros si hay tolerancia y luego sigue una dieta blanda durante los primeros 5 días. Evita frituras, picantes y alcohol.
- **Movilización**: Comienza a caminar desde el primer día, pero evita levantar más de 5 kg durante 4 semanas.
- **Higiene**: Puedes ducharte a partir de las 48 horas, protegiendo la herida. No te sumerjas en agua (baños de inmersión).

### Cuidado de la Herida:
- Limpia la herida con suero fisiológico una vez al día y mantenla seca. No retires las costras.

### Signos de Alarma:
Acude a Urgencias INMEDIATAMENTE si presentas:
- Fiebre > 38.5 °C persistente más de 24 horas.
"""

_TEXTO_FASES_ANIDADAS = """\
### Cuidados Postoperatorios para tu Apendicectomía

**Fases de Recuperación Esperada**

- **0 – 24 h:**
    - Reposo absoluto.
    - Náuseas leves por anestesia son normales.
    - Inicio de líquidos claros si hay tolerancia.
- **1 – 3 días:**
    - Dieta blanda progresiva.
    - Movilización supervisada.
- **1 – 2 semanas:**
    - Retiro de puntos.
"""

_TEXTO_LISTA_PLANA = """\
- **0 – 24 h:**
- Reposo absoluto.
- Inicio de líquidos claros si hay tolerancia.
- **1 – 3 días:**
- Dieta blanda progresiva.
"""


def _lineas_viñeta_vacias(salida: str) -> list[str]:
    vacias: list[str] = []
    for linea in salida.splitlines():
        texto = linea.strip()
        if texto in ("•", "• "):
            vacias.append(linea)
        if re.match(r"^•\s*$", texto):
            vacias.append(linea)
    return vacias


def _lineas_viñeta_sin_texto(salida: str) -> list[str]:
    """Lineas que empiezan por viñeta pero no tienen contenido util despues."""
    malas: list[str] = []
    for linea in salida.splitlines():
        texto = linea.strip()
        if texto.startswith("•") and len(texto) <= 1:
            malas.append(linea)
        if re.match(r"^•\s*$", texto):
            malas.append(linea)
    return malas


def test_es_markdown_probable_detecta_encabezados_y_listas() -> None:
    assert es_markdown_probable(_TEXTO_POSTOPERATORIO) is True
    assert es_markdown_probable("Hola, use /start CODIGO para vincular.") is False


def test_markdown_a_html_telegram_sin_simbolos_crudos() -> None:
    html = markdown_a_html_telegram(_TEXTO_POSTOPERATORIO)
    assert "###" not in html
    assert "**" not in html
    assert "<b>" in html
    assert "Recomendaciones Generales" in html
    assert "• " in html or "Reposo" in html


def test_markdown_a_html_telegram_escapa_menor_que() -> None:
    html = markdown_a_html_telegram("Valor lab: < 5 mg/dL")
    assert "<" not in html or "&lt;" in html
    assert "5 mg/dL" in html


def test_markdown_a_html_telegram_sin_etiquetas_no_permitidas() -> None:
    html = markdown_a_html_telegram(_TEXTO_POSTOPERATORIO)
    prohibidas = re.findall(r"<(/?)(h[1-6]|ul|ol|p|div|li)\b", html, flags=re.I)
    assert prohibidas == []


def test_markdown_a_html_telegram_sin_strong() -> None:
    html = markdown_a_html_telegram(_TEXTO_FASES_ANIDADAS)
    assert "<strong>" not in html
    assert "</strong>" not in html


@pytest.mark.parametrize(
    "markdown",
    [_TEXTO_FASES_ANIDADAS, _TEXTO_LISTA_PLANA, _TEXTO_POSTOPERATORIO],
)
def test_sin_viñetas_vacias(markdown: str) -> None:
    salida = markdown_a_html_telegram(markdown)
    assert _lineas_viñeta_vacias(salida) == []
    assert _lineas_viñeta_sin_texto(salida) == []


def test_fases_anidadas_titulo_sin_viñeta_delante() -> None:
    salida = markdown_a_html_telegram(_TEXTO_FASES_ANIDADAS)
    assert "<b>0 – 24 h:</b>" in salida
    assert "• <b>0 – 24 h:</b>" not in salida
    assert "  • Reposo absoluto." in salida


def test_lista_plana_cada_viñeta_con_texto() -> None:
    salida = markdown_a_html_telegram(_TEXTO_LISTA_PLANA)
    for linea in salida.splitlines():
        if linea.strip().startswith("•"):
            assert len(linea.strip()) > 2
