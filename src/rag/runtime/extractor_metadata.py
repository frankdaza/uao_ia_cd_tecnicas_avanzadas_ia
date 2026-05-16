"""
Heuristicas puras para enriquecer el payload Qdrant a partir de Markdown y front matter.

Los nombres publicos siguen el contrato de TASK-69; las funciones son deterministas
y aptas para pruebas unitarias sin Qdrant ni embeddings.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

# Marcadores de sede conocidos en el sitio (orden: cadenas largas primero).
_SEDES_CONOCIDAS: tuple[str, ...] = (
    "Sede Valle del Lili",
    "Sede Av. Estación",
    "Sede Alfaguara",
    "Sede Limonar",
    "Sede Ciudad Jardin",
    "Sede Caicedonia",
    "Sede Tequendama",
)

_RE_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_RE_BY_TAG = re.compile(r"[?&]by_tag=([^&)\s]+)", re.IGNORECASE)

_PARTICULAS_ES = frozenset(
    {"de", "del", "la", "las", "el", "los", "y", "en", "a", "al", "o"}
)


def _sin_tildes(texto: str) -> str:
    """Normaliza a caracteres base ASCII (titulos comparables, sin ene/tildes)."""
    nk = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nk if unicodedata.category(c) != "Mn")


def normalizar_etiqueta_titulo(texto: str) -> str:
    """
    Convierte una etiqueta legible a forma titulo sin tildes (p. ej. ``Pediatria``).

    Se usa para ``especialidad``, sedes y nombres derivados de encabezados.
    """
    limpio = " ".join(texto.strip().split())
    if not limpio:
        return ""
    base = _sin_tildes(limpio)
    partes: list[str] = []
    for i, palabra in enumerate(base.split()):
        pl = palabra.lower()
        if i > 0 and pl in _PARTICULAS_ES:
            partes.append(pl)
        else:
            partes.append(palabra[:1].upper() + palabra[1:].lower() if palabra else "")
    return " ".join(partes)


def inferir_tipo_pagina(seccion: str, nombre_archivo: str) -> str:
    """
    Clasifica el documento en un ``tipo_pagina`` estable para filtros en Qdrant.

    Args:
        seccion: Valor ``seccion`` del front matter (slug de seccion del sitio).
        nombre_archivo: Ruta completa o solo nombre de archivo ``*.md``.
    """
    base = Path(nombre_archivo).stem.lower()
    sec = (seccion or "").strip().lower()

    if base.startswith("directorio-medico-"):
        return "ficha_medico"
    if base.startswith("servicios-"):
        return "servicio"
    if base.startswith("sedes-"):
        return "sede"
    if "educacion" in base or sec == "educacion":
        return "educacion"
    if base.startswith("investigacion") or sec == "investigacion":
        return "investigacion"
    if base.startswith("revista-") or sec == "revista":
        return "revista"
    if base.startswith("eventos-") or base.startswith("evento-") or sec == "eventos":
        return "evento"
    if (
        base.startswith("programa-")
        or base.startswith("programas-")
        or "programa" in sec
    ):
        return "programa"
    if base.startswith("la-fundacion-") or base.startswith("nuestra-fundacion-"):
        return "institucional"
    if base.startswith("conoce-el-programa-"):
        return "programa"
    return "otro"


def inferir_subtipo(nombre_archivo: str) -> str | None:
    """Subtipo fino para paginas institucionales (mision, vision, valores, ...)."""
    base = Path(nombre_archivo).stem.lower()
    if "mision" in base:
        return "mision"
    if "vision" in base:
        return "vision"
    if "valores" in base:
        return "valores"
    return None


def extraer_nombre_medico(titulo: str, fm: dict[str, Any] | None) -> str | None:
    """
    Obtiene el nombre canonico del medico en fichas del directorio.

    Prioriza el titulo antes del sufijo institucional o el ``titulo`` del front matter.
    """
    raw = (titulo or "").strip()
    if not raw and fm:
        raw = str(fm.get("titulo") or "").strip()
    if not raw:
        return None
    for sep in (" - Fundación Valle del Lili", " - Fundacion Valle del Lili"):
        if sep in raw:
            raw = raw.split(sep, 1)[0].strip()
            break
    if not raw:
        return None
    return normalizar_etiqueta_titulo(raw)


def _es_h2_basura_listado_relacionado(titulo_h2: str) -> bool:
    """Encabezados de navegacion lateral / recomendaciones, no la especialidad clinica."""
    b = _sin_tildes(titulo_h2).lower()
    if "otros especialistas" in b:
        return True
    if "te pueden interesar" in b or "te puede interesar" in b:
        return True
    if "especialistas relacionados" in b:
        return True
    return False


def extraer_especialidades(
    cuerpo: str,
    fm: dict[str, Any] | None,
    nombre_archivo: str | None = None,
) -> list[str]:
    """
    Lista de especialidades normalizadas (sin duplicados, orden de aparicion).

    Lee claves comunes del front matter y encabezados ``##`` del cuerpo.
    En fichas ``directorio-medico-*.md`` omite el primer ``##`` generico del sitio
    (p. ej. «Otros especialistas…») y usa el siguiente encabezado util si existe.
    """
    salida: list[str] = []
    visto: set[str] = set()

    def agregar(valor: str) -> None:
        n = normalizar_etiqueta_titulo(valor)
        if not n:
            return
        clave = n.lower()
        if clave in visto:
            return
        visto.add(clave)
        salida.append(n)

    if fm:
        for clave in ("especialidades", "especialidad", "tags_clinicos"):
            raw = fm.get(clave)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str):
                        agregar(item)
            elif isinstance(raw, str) and raw.strip():
                agregar(raw)

    es_ficha = False
    if nombre_archivo:
        base = Path(nombre_archivo).stem.lower()
        es_ficha = base.startswith("directorio-medico-")

    for m in _RE_HEADING.finditer(cuerpo or ""):
        if len(m.group(1)) != 2:
            continue
        tit = normalizar_etiqueta_titulo(m.group(2))
        if not tit:
            continue
        if es_ficha and _es_h2_basura_listado_relacionado(tit):
            continue
        agregar(tit)
        break

    return salida


def _sedes_bajo_heading(cuerpo: str) -> list[str]:
    """Busca lista bajo un encabezado tipo ``### Sedes``."""
    salida: list[str] = []
    patron = re.compile(
        r"^#{3,6}\s+Sedes\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    m = patron.search(cuerpo or "")
    if not m:
        return salida
    resto = cuerpo[m.end() :]
    for linea in resto.splitlines():
        s = linea.strip()
        if not s:
            if salida:
                break
            continue
        if s.startswith("#"):
            break
        if s.startswith(("- ", "* ", "+ ")):
            item = s.lstrip("-*+ ").strip()
            if item:
                salida.append(normalizar_etiqueta_titulo(item))
        else:
            if salida:
                break
    return salida


def extraer_sedes(cuerpo: str, fm: dict[str, Any] | None) -> list[str]:
    """Sedes mencionadas en listas dedicadas o como subcadenas conocidas."""
    salida: list[str] = []
    visto: set[str] = set()

    def agregar(valor: str) -> None:
        n = normalizar_etiqueta_titulo(valor)
        if not n:
            return
        clave = n.lower()
        if clave in visto:
            return
        visto.add(clave)
        salida.append(n)

    if fm:
        raw = fm.get("sedes")
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    agregar(item)
        elif isinstance(raw, str) and raw.strip():
            agregar(raw)

    for s in _sedes_bajo_heading(cuerpo or ""):
        agregar(s)

    texto = cuerpo or ""
    for marca in _SEDES_CONOCIDAS:
        if marca in texto:
            clave = marca.lower()
            if clave not in visto:
                visto.add(clave)
                salida.append(marca)

    return salida


def extraer_tags(fm: dict[str, Any] | None, cuerpo: str) -> list[str]:
    """Etiquetas desde front matter o enlaces ``by_tag`` del cuerpo."""
    salida: list[str] = []
    visto: set[str] = set()

    def agregar(valor: str) -> None:
        t = valor.strip().lower().replace(" ", "-")
        if not t or t in visto:
            return
        visto.add(t)
        salida.append(t)

    if fm:
        raw = fm.get("tags")
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    agregar(item)
        elif isinstance(raw, str) and raw.strip():
            for parte in raw.split(","):
                agregar(parte)

    for m in _RE_BY_TAG.finditer(cuerpo or ""):
        agregar(m.group(1))

    return salida


def construir_headings_path(nodo: Any) -> str:
    """
    Ruta legible de encabezados para el chunk (separador `` > ``).

    Soporta metadatos de ``MarkdownNodeParser`` modernos (``header_path``) y
    el esquema historico ``Header_1`` / ``Header_2`` / ``Header_3``.
    """
    meta: dict[str, Any] = getattr(nodo, "metadata", None) or {}
    niveles: list[str] = []
    for k in ("Header_1", "Header_2", "Header_3"):
        v = meta.get(k)
        if v:
            niveles.append(str(v).strip())
    if niveles:
        return " > ".join(niveles)

    hp = meta.get("header_path")
    if isinstance(hp, str) and hp.strip():
        raw = hp.strip().strip("/")
        niveles = [p.strip() for p in raw.split("/") if p.strip()]

    texto = (getattr(nodo, "get_content", lambda: "")() or "").strip()
    primera = texto.split("\n", 1)[0].strip() if texto else ""
    m = re.match(r"^(#{1,6})\s+(.+)$", primera)
    if m:
        tit = m.group(2).strip()
        nivel = len(m.group(1))
        if nivel > len(niveles) and tit:
            if not niveles or tit.lower() != niveles[-1].lower():
                niveles.append(tit)
    return " > ".join(niveles)


def extraer_h1_h2_h3_desde_nodo(nodo: Any) -> tuple[str | None, str | None, str | None]:
    """Deriva ``h1``/``h2``/``h3`` a partir de ``construir_headings_path``."""
    path = construir_headings_path(nodo)
    if not path:
        return None, None, None
    partes = [p.strip() for p in path.split(" > ") if p.strip()]
    if not partes:
        return None, None, None
    if len(partes) == 1:
        return partes[0], None, None
    if len(partes) == 2:
        return partes[0], partes[1], None
    return partes[0], partes[1], " > ".join(partes[2:])
