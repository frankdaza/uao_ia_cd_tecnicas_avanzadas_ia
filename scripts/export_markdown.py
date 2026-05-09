"""
Exporta ``data/raw/valledellili-org/*.html`` + sidecars JSON a Markdown en
``data/markdown/valledellili-org/``, con omision por hash (idempotencia).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

import yaml

from src.markdown_export.conversion import convertir_html_a_md, escribir_markdown

DIRECTORIO_RAW = Path("data/raw/valledellili-org")
DIRECTORIO_MARKDOWN = Path("data/markdown/valledellili-org")
MENSAJE_SIN_HTML = "No hay HTML descargado; corre scripts.scrape primero"


@dataclass
class ResumenExport:
    """Contadores al finalizar el lote."""

    creados: int = 0
    actualizados: int = 0
    omitidos_por_hash: int = 0
    errores: int = 0


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Regenera Markdown con front matter desde HTML y JSON en data/raw/."
        ),
    )
    p.add_argument(
        "--forzar",
        action="store_true",
        help="Reescribe todos los .md aunque el hash coincida con el sidecar.",
    )
    p.add_argument(
        "--solo-uno",
        metavar="SLUG",
        default=None,
        help="Solo procesa el .html cuyo nombre base coincide con SLUG (depuracion).",
    )
    return p.parse_args(argv)


def leer_hash_front_matter_existente(ruta_md: Path) -> str | None:
    """Devuelve el campo ``hash`` del YAML si el archivo es legible; si no, ``None``."""
    if not ruta_md.is_file():
        return None
    texto = ruta_md.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        return None
    rest = texto[4:]
    fin = rest.find("\n---\n")
    if fin <= 0:
        return None
    try:
        fm = yaml.safe_load(rest[:fin])
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    h = fm.get("hash")
    if h is None:
        return None
    return str(h)


def _hash_desde_sidecar(ruta_json: Path) -> str:
    meta = json.loads(ruta_json.read_text(encoding="utf-8"))
    return str(meta.get("hash_sha256", ""))


def procesar_archivo(
    ruta_html: Path,
    ruta_destino_md: Path,
    *,
    forzar: bool,
    resumen: ResumenExport,
) -> None:
    ruta_json = ruta_html.with_suffix(".json")
    if not ruta_json.is_file():
        resumen.errores += 1
        print(
            f"[{ruta_html.name}] falta sidecar {ruta_json.name}",
            file=sys.stderr,
        )
        return
    try:
        hash_sidecar = _hash_desde_sidecar(ruta_json)
    except (json.JSONDecodeError, OSError) as e:
        resumen.errores += 1
        print(f"[{ruta_html.name}] sidecar invalido: {e}", file=sys.stderr)
        return

    existia_antes = ruta_destino_md.is_file()
    if not forzar and existia_antes:
        hash_md = leer_hash_front_matter_existente(ruta_destino_md)
        if hash_md is not None and hash_md == hash_sidecar:
            resumen.omitidos_por_hash += 1
            return

    try:
        contenido = convertir_html_a_md(ruta_html, ruta_json)
        escribir_markdown(contenido, ruta_destino_md)
    except Exception as e:
        resumen.errores += 1
        print(f"[{ruta_html.name}] {e}", file=sys.stderr)
        return

    if existia_antes:
        resumen.actualizados += 1
    else:
        resumen.creados += 1


def listar_html_en_crudo(directorio: Path) -> list[Path]:
    """Lista ``*.html`` bajo el directorio de crudo, ordenados por nombre."""
    return sorted(p for p in directorio.glob("*.html") if p.is_file())


def exportar_todo(*, forzar: bool, rutas_html: list[Path]) -> ResumenExport:
    """Procesa cada HTML y acumula contadores (no sale del proceso por errores parciales)."""
    resumen = ResumenExport()
    DIRECTORIO_MARKDOWN.mkdir(parents=True, exist_ok=True)
    for ruta_html in rutas_html:
        destino = DIRECTORIO_MARKDOWN / f"{ruta_html.stem}.md"
        procesar_archivo(ruta_html, destino, forzar=forzar, resumen=resumen)
    return resumen


def imprimir_resumen(resumen: ResumenExport, salida: TextIO = sys.stdout) -> None:
    salida.write("\nResumen:\n")
    salida.write(f"  creados: {resumen.creados}\n")
    salida.write(f"  actualizados: {resumen.actualizados}\n")
    salida.write(f"  omitidos_por_hash: {resumen.omitidos_por_hash}\n")
    salida.write(f"  errores: {resumen.errores}\n")


def main() -> int:
    ns = parsear_argumentos()
    if not DIRECTORIO_RAW.is_dir():
        print(MENSAJE_SIN_HTML, file=sys.stderr)
        return 1
    htmls = listar_html_en_crudo(DIRECTORIO_RAW)
    if not htmls:
        print(MENSAJE_SIN_HTML, file=sys.stderr)
        return 1
    if ns.solo_uno is not None:
        slug = ns.solo_uno.strip()
        filtrados = [p for p in htmls if p.stem == slug]
        if not filtrados:
            print(f"No hay HTML con slug {slug!r}", file=sys.stderr)
            return 1
        htmls = filtrados
    resumen = exportar_todo(forzar=ns.forzar, rutas_html=htmls)
    imprimir_resumen(resumen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
