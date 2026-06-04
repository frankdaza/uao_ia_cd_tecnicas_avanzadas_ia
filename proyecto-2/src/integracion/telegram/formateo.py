"""Conversion de Markdown del agente a HTML compatible con ``parse_mode=HTML`` de Telegram."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

import markdown as markdown_lib

# Tags admitidos por Bot API (HTML parse mode); ``strong`` se normaliza a ``b``.
_ETIQUETAS_INLINE_PERMITIDAS = frozenset(
    {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "code", "a"}
)
_PATRON_MARKDOWN = re.compile(
    r"(^#{1,6}\s|\*\*|^[\-\*]\s|^\d+\.\s)",
    re.MULTILINE,
)
_RE_LINEA_VIÑETA_VACIA = re.compile(r"^[\s•]*•[\s•]*$")


def es_markdown_probable(texto: str) -> bool:
    """Heuristica: evita parse_mode en mensajes de sistema planos."""
    return _PATRON_MARKDOWN.search(texto) is not None


def markdown_a_html_telegram(texto: str) -> str:
    """
    Convierte Markdown simple a HTML seguro para Telegram.

    Encabezados y listas se normalizan a negritas y lineas con viñeta.
    """
    limpio = texto.strip()
    if not limpio:
        return ""

    convertidor = markdown_lib.Markdown(
        extensions=["sane_lists", "fenced_code"],
        output_format="html",
    )
    html_generado = convertidor.convert(limpio)
    convertidor.reset()
    return _limpiar_salida_telegram(_html_a_telegram(html_generado))


def _html_a_telegram(fragmento: str) -> str:
    """Transforma HTML generado por ``markdown`` al subconjunto de Telegram."""
    parser = _ParserHtmlTelegram()
    parser.feed(fragmento)
    parser.close()
    return "".join(parser.partes)


def _limpiar_salida_telegram(texto: str) -> str:
    """Elimina viñetas huerfanas y normaliza saltos de linea."""
    texto = texto.replace("<strong>", "<b>").replace("</strong>", "</b>")
    lineas: list[str] = []
    for linea in texto.splitlines():
        if _RE_LINEA_VIÑETA_VACIA.match(linea.strip()):
            continue
        # Viñeta seguida solo de espacios en la misma linea
        if re.match(r"^[\s•]*•\s*$", linea):
            continue
        lineas.append(linea.rstrip())
    unido = "\n".join(lineas)
    unido = re.sub(r"\n{3,}", "\n\n", unido)
    return unido.strip()


def _normalizar_etiqueta_inline(nombre: str) -> str:
    if nombre == "strong":
        return "b"
    return nombre


class _ParserHtmlTelegram(HTMLParser):
    """Serializa HTML a texto con etiquetas permitidas por Telegram."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._pila: list[str] = []
        self._profundidad_ul = 0
        self._en_li = False
        self._bullet_emitido_en_li = False
        self._li_cabecera_seccion = False
        self._li_tuvo_marca_inline = False
        self._li_titulo_negrita = False

    def _indent_lista(self) -> str:
        if self._profundidad_ul <= 1:
            return ""
        return "  " * (self._profundidad_ul - 1)

    def _emitir_viñeta_si_hace_falta(self) -> None:
        if not self._en_li or self._bullet_emitido_en_li or self._li_cabecera_seccion:
            return
        self.partes.append(f"{self._indent_lista()}• ")
        self._bullet_emitido_en_li = True

    def _abrir_inline(self, nombre: str, attrs: list[tuple[str, str | None]]) -> None:
        etiqueta = _normalizar_etiqueta_inline(nombre)
        if etiqueta == "a":
            href = ""
            for clave, valor in attrs:
                if clave == "href" and valor:
                    href = html.escape(valor, quote=True)
                    break
            if href:
                self.partes.append(f'<a href="{href}">')
                self._pila.append("a")
            return
        if etiqueta in _ETIQUETAS_INLINE_PERMITIDAS:
            if self._en_li and etiqueta == "b" and not self._bullet_emitido_en_li:
                self._li_tuvo_marca_inline = True
                if not self._li_cabecera_seccion and self._profundidad_ul <= 1:
                    # Titulo de fase en li de primer nivel: negrita sin viñeta.
                    self._li_titulo_negrita = True
                    self.partes.append("<b>")
                    self._pila.append("b")
                    return
            self._emitir_viñeta_si_hace_falta()
            self.partes.append(f"<{etiqueta}>")
            self._pila.append(etiqueta)

    def _cerrar_inline(self, nombre: str) -> None:
        etiqueta = _normalizar_etiqueta_inline(nombre)
        if etiqueta not in _ETIQUETAS_INLINE_PERMITIDAS:
            return
        if self._pila and self._pila[-1] == etiqueta:
            self._pila.pop()
            self.partes.append(f"</{etiqueta}>")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        nombre = tag.lower()
        if nombre in {"ul", "ol"}:
            if (
                self._en_li
                and not self._bullet_emitido_en_li
                and self._li_tuvo_marca_inline
            ):
                self._li_cabecera_seccion = True
                if self.partes and not self.partes[-1].endswith("\n"):
                    self.partes.append("\n")
            self._profundidad_ul += 1
            return

        if nombre == "li":
            self._en_li = True
            self._bullet_emitido_en_li = False
            self._li_cabecera_seccion = False
            self._li_tuvo_marca_inline = False
            self._li_titulo_negrita = False
            return

        if nombre in _ETIQUETAS_INLINE_PERMITIDAS:
            self._abrir_inline(nombre, attrs)
            return

        if nombre in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.partes.append("<b>")
            self._pila.append("b")
            return

        if nombre == "pre":
            self.partes.append("<pre>")
            self._pila.append("pre")
            return

        if nombre == "br":
            self.partes.append("\n" if self._en_li else "\n\n")
            return

        if nombre == "p" and not self._en_li:
            if self.partes and not self.partes[-1].endswith("\n\n"):
                self.partes.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        nombre = tag.lower()
        if nombre in {"ul", "ol"}:
            self._profundidad_ul = max(0, self._profundidad_ul - 1)
            return

        if nombre == "li":
            if self.partes and not self.partes[-1].endswith("\n"):
                self.partes.append("\n")
            self._en_li = False
            self._bullet_emitido_en_li = False
            self._li_cabecera_seccion = False
            self._li_tuvo_marca_inline = False
            self._li_titulo_negrita = False
            return

        if nombre == "p":
            if not self._en_li:
                self.partes.append("\n\n")
            return

        if nombre in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            if self._pila and self._pila[-1] == "b":
                self._pila.pop()
            self.partes.append("</b>\n\n")
            return

        if nombre in _ETIQUETAS_INLINE_PERMITIDAS:
            self._cerrar_inline(nombre)
            return

        if nombre == "pre" and self._pila and self._pila[-1] == "pre":
            self._pila.pop()
            self.partes.append("</pre>")

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._pila and self._pila[-1] == "pre":
            self.partes.append(html.escape(data))
            return
        texto = data
        if not texto.strip():
            return
        if self._en_li and not self._li_titulo_negrita:
            if self._li_cabecera_seccion:
                if self._profundidad_ul >= 2:
                    self._emitir_viñeta_si_hace_falta()
            else:
                self._emitir_viñeta_si_hace_falta()
        self.partes.append(html.escape(texto))
