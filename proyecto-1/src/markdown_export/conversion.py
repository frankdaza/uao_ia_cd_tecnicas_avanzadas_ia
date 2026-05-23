"""
Conversion de HTML (``data/raw/``) a Markdown con front matter YAML.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml
from bs4 import BeautifulSoup
from markdownify import ATX, markdownify as html_a_markdown

# Selectores tipicos de avisos de cookies (ademas de nav/header/footer en ``limpiar_html``).
_SELECTORES_COOKIES: tuple[str, ...] = (
    ".cookie",
    "#cookie-banner",
    '[class*="cookie"]',
)


@dataclass
class ContenidoMarkdown:
    """
    Par front matter (dict serializable) + cuerpo Markdown.

    Example:
        >>> ContenidoMarkdown(
        ...     front_matter={"source_url": "https://e.org/a", "titulo": "A"},
        ...     cuerpo="Hola",
        ... ).serializar()[:3]
        '---'
    """

    front_matter: dict[str, Any]
    cuerpo: str

    def serializar(self) -> str:
        """Arma el texto ``---`` + YAML + ``---`` + cuerpo."""
        cuerpo_limpio = self.cuerpo.rstrip() + "\n"
        yml = yaml.safe_dump(
            self.front_matter,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).rstrip()
        return f"---\n{yml}\n---\n\n{cuerpo_limpio}"


def _fecha_solo_cadena(fecha_iso: str) -> str:
    """
    Toma el campo ``fecha_extraccion`` del sidecar (suele ser ISO-8601) y
    devuelve ``YYYY-MM-DD`` para el front matter.
    """
    s = (fecha_iso or "").strip()
    if "T" in s:
        return s.split("T", 1)[0]
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s or "1970-01-01"


def extraer_titulo(soup: BeautifulSoup, slug_respaldo: str) -> str:
    """
    Usa ``<title>`` si existe; si no, el primer ``<h1>``; si no, *slug_respaldo*.

    Example:
        Con ``<title>Mi página</title>`` el resultado es ``"Mi página"``; sin
        título ni h1, se devuelve *slug_respaldo*.
    """
    t = None
    if soup.title and soup.title.string:
        t = soup.title.get_text(strip=True)
    if not t:
        h1 = soup.find("h1")
        if h1:
            t = h1.get_text(strip=True)
    if not t:
        t = slug_respaldo
    return t


def derivar_seccion(url: str) -> str:
    """
    Primer segmento de la ruta, sin slash inicial/final. La raiz es ``inicio``.

    Example:
        ``https://valledellili.org/quienes-somos/historia`` arroja
        ``"quienes-somos"``; la URL raíz de sitio, ``"inicio"``.
    """
    p = urlparse(url)
    ruta = (p.path or "/").strip("/")
    if not ruta:
        return "inicio"
    return unquote(ruta.split("/")[0].lower() or "inicio")


def limpiar_html(soup: BeautifulSoup) -> None:
    """
    Elimina ruido antes de *markdownify*: ``script``/``style``/``nav``/banners, etc.
    Retira contenido no textual (medios/decorative) pensado para RAG solo con texto.

    Example:
        Un ``<nav>...</nav>`` y un div ``#cookie-banner`` se eliminan por completo
        antes de convertir el resto a Markdown.
    """
    for nombre in ("script", "style", "noscript", "iframe"):
        for tag in soup.find_all(nombre):
            tag.decompose()
    for nombre in ("nav", "header", "footer"):
        for tag in soup.find_all(nombre):
            tag.decompose()
    for sel in _SELECTORES_COOKIES:
        for tag in soup.select(sel):
            tag.decompose()
    _quitar_medios_y_graficos(soup)
    _rellenar_enlaces_sin_texto_visible(soup)


def _quitar_medios_y_graficos(soup: BeautifulSoup) -> None:
    """Elimina imagenes y medios embedding; objetos externos sin texto util."""
    for nombre in ("img", "svg", "canvas"):
        for tag in soup.find_all(nombre):
            tag.decompose()
    for nombre in ("picture", "video", "audio"):
        for tag in soup.find_all(nombre):
            tag.decompose()
    for tag in soup.find_all("source"):
        tag.decompose()
    for nombre in ("object", "embed"):
        for tag in soup.find_all(nombre):
            tag.decompose()


def _texto_fallback_enlace(href: str) -> str:
    """Texto corto para un ``<a href>`` vacio cuando se quitaron hijos graficos."""
    p = urlparse(href)
    netloc = (p.netloc or "").lower().removeprefix("www.")
    if netloc:
        base = netloc.split(".")[0]
        return base.capitalize() if len(base) > 1 else netloc or "Enlace"
    ruta = (p.path or "/").strip("/")
    ultimo = ruta.split("/")[-1] if ruta else ""
    texto = unquote(ultimo).replace("-", " ").replace("_", " ").strip(". ")
    return texto[:120] if texto else "Enlace"


def _rellenar_enlaces_sin_texto_visible(soup: BeautifulSoup) -> None:
    """
    Si un anchor quedo sin texto despues de quitar medios, sintetiza una etiqueta
    leyible (titulo, nombre de recurso); si no puede, elimina el anchor.
    """
    for a in list(soup.find_all("a", href=True)):
        href = str(a.get("href", "")).strip()
        texto_visible = a.get_text(strip=True)
        if texto_visible:
            continue
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            a.decompose()
            continue
        nuevo = (a.get("title") or a.get("aria-label") or "").strip()
        if not nuevo:
            nuevo = _texto_fallback_enlace(href)
        nuevo = re.sub(r"\s+", " ", nuevo).strip() or _texto_fallback_enlace(href)
        a.clear()
        a.string = nuevo


_RE_MD_SOLO_IMG = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
_RE_MD_ANIDA_IMG_LINK = re.compile(
    r"^\s*\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)\s*$",
)


def _depurar_cuerpo_markdown_kb(markdown_bruto: str) -> str:
    """
    Quita restos tipicos de lineas solo-imagen despues del HTML (marcado raro o
    *markdownify* sobre fragmentos vacios).
    """
    salida: list[str] = []
    for line in markdown_bruto.splitlines():
        si = line.strip()
        if not si:
            salida.append("")
            continue
        if _RE_MD_SOLO_IMG.match(si) or _RE_MD_ANIDA_IMG_LINK.match(si):
            continue
        salida.append(line)
    texto = "\n".join(salida)
    return texto


def _normalizar_lineas_en_blanco(texto: str) -> str:
    """Como maximo dos saltos consecutivos (sin dejar >2 lineas vacias)."""
    t = re.sub(r"\n{3,}", "\n\n", texto)
    t = t.strip() + "\n" if t.strip() else ""
    return t


def _html_a_cuerpo_md(html_fragmento: str) -> str:
    return html_a_markdown(
        html_fragmento,
        heading_style=ATX,
        bullets="-",
    ).strip()


def convertir_html_a_md(ruta_html: Path, ruta_metadata: Path) -> ContenidoMarkdown:
    """
    Lee un ``.html`` y su sidecar (JSON) y produce :class:`ContenidoMarkdown`.

    El sidecar debe incluir al menos: ``url``, ``fecha_extraccion``, ``hash_sha256``,
    como en la salida de :mod:`src.scraping.descarga`.

    Example:
        ``convertir_html_a_md(Path("x.html"), Path("x.json")).serializar()``
        devuelve el archivo completo con bloque ``---`` YAML y cuerpo Markdown.
    """
    cuerpo_bytes = ruta_html.read_bytes()
    texto_html = cuerpo_bytes.decode("utf-8", errors="replace")
    meta: dict[str, Any] = json.loads(
        ruta_metadata.read_text(encoding="utf-8"),
    )
    url = str(meta.get("url", ""))
    hash_sha = str(meta.get("hash_sha256", ""))
    fecha_e = str(meta.get("fecha_extraccion", ""))
    soup = BeautifulSoup(texto_html, "html.parser")
    slug = ruta_html.stem
    titulo = extraer_titulo(soup, slug)
    limpiar_html(soup)
    raiz = soup.body if soup.body is not None else soup
    cuerpo = _html_a_cuerpo_md(str(raiz))
    cuerpo = _depurar_cuerpo_markdown_kb(cuerpo)
    cuerpo = _normalizar_lineas_en_blanco(cuerpo)
    front = {
        "source_url": url,
        "titulo": titulo,
        "seccion": derivar_seccion(url),
        "fecha_extraccion": _fecha_solo_cadena(fecha_e),
        "idioma": "es",
        "hash": hash_sha,
    }
    return ContenidoMarkdown(front_matter=front, cuerpo=cuerpo)


def escribir_markdown(contenido: ContenidoMarkdown, ruta_destino: Path) -> None:
    """
    Escribe UTF-8 y crea directorios padre si hace falta.

    Example:
        ``escribir_markdown(cm, Path("data/markdown/sitio/slug.md"))`` vuelca
        ``cm.serializar()`` en disco.
    """
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    ruta_destino.write_text(contenido.serializar(), encoding="utf-8")
