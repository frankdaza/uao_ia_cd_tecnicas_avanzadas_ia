"""
CLI del crawler: orquesta GestorRobots y Crawler y escribe registro en data/raw/_log.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import TextIO
from urllib.parse import urlparse

from dotenv import load_dotenv

from src.scraping.descarga import (
    DIRECTORIO_CRUDO_POR_DEFECTO,
    ConfiguracionCrawler,
    Crawler,
    ResultadoDescarga,
)
from src.scraping.robots import USER_AGENT_DEFECTO, GestorRobots

RUTA_LOG_DEFECTO = Path("data/raw/_log.jsonl")
URL_INICIO_DEFECTO = "https://valledellili.org/"


@dataclass
class ConteoResumen:
    """Contadores de una corrida (parcial o completa)."""

    descargadas: int = 0
    omitidas_por_robots: int = 0
    omitidas_por_hash: int = 0
    errores: int = 0

    def actualizar_por_resultado(self, r: ResultadoDescarga) -> None:
        if r.error is not None:
            self.errores += 1
        elif r.omitido_por_robots:
            self.omitidas_por_robots += 1
        elif r.http_status == 200 and r.omitido_por_hash:
            self.omitidas_por_hash += 1
        elif r.http_status == 200:
            self.descargadas += 1
        else:
            self.errores += 1


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    """Argumentos de linea de comandos con valores por defecto alineados a ConfiguracionCrawler."""
    p = argparse.ArgumentParser(
        description="Rastreo BFS (valledellili.org) hacia data/raw/valledellili-org/.",
    )
    p.add_argument(
        "--url-inicio",
        default=None,
        help="URL semilla; si se omite, se usa URL_BASE_SITIO en .env o el defecto del proyecto.",
    )
    p.add_argument(
        "--max-paginas",
        type=int,
        default=200,
        help="Maximo de respuestas 200 (nuevas u omitidas por hash) hacia el limite (defecto: 200).",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Pausa minima en segundos entre solicitudes, ademas del Crawl-delay de robots (defecto: 1.5).",
    )
    p.add_argument(
        "--profundidad-maxima",
        type=int,
        default=5,
        help="Niveles de enlaces internos a seguir (defecto: 5).",
    )
    p.add_argument(
        "--dominio-permitido",
        default="valledellili.org",
        help="Solo se enlaces de este host (defecto: valledellili.org).",
    )
    p.add_argument(
        "--directorio-salida",
        type=Path,
        default=None,
        help="Carpeta para .html y .json (defecto: data/raw/valledellili-org/).",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout HTTP en segundos (defecto: 30).",
    )
    p.add_argument(
        "--reintentos",
        type=int,
        default=3,
        help="Reintentos en fallo de red (defecto: 3).",
    )
    p.add_argument(
        "--user-agent",
        default=None,
        help="User-Agent; defecto: el del modulo robots o USER_AGENT en .env.",
    )
    p.add_argument(
        "--archivo-log",
        type=Path,
        default=RUTA_LOG_DEFECTO,
        help="Ruta del JSONL de registro; se añade al final (defecto: data/raw/_log.jsonl).",
    )
    return p.parse_args(argv)


def _resolver_url_inicio(explicita: str | None) -> str:
    if explicita:
        return explicita.strip()
    env = os.getenv("URL_BASE_SITIO")
    if env and env.strip():
        return env.strip()
    return URL_INICIO_DEFECTO


def _resolver_user_agent(explicito: str | None) -> str:
    if explicito:
        return explicito
    env = os.getenv("USER_AGENT")
    if env and env.strip():
        return env.strip()
    return USER_AGENT_DEFECTO


def escribir_log(
    manejador: TextIO,
    instante: datetime,
    r: ResultadoDescarga,
) -> None:
    """Una linea JSON por resultado (append al archivo de registro)."""
    reg = {
        "timestamp": instante.replace(microsecond=0).isoformat(),
        "url": r.url,
        "http_status": r.http_status,
        "hash_sha256": r.hash_sha256,
        "omitido_por_robots": r.omitido_por_robots,
        "omitido_por_hash": r.omitido_por_hash,
        "error": r.error,
    }
    manejador.write(json.dumps(reg, ensure_ascii=False) + "\n")
    manejador.flush()


def _linea_stdout(r: ResultadoDescarga) -> str:
    if r.error is not None:
        return f"[ERROR] {r.url} -> {r.error}"
    if r.omitido_por_robots:
        return f"[OMIT robots] {r.url}"
    if r.http_status != 200:
        return f"[ERROR] {r.url} -> HTTP {r.http_status}"
    if r.omitido_por_hash and r.ruta_html is not None:
        return f"[OMIT hash] {r.url} -> {r.ruta_html.name}"
    if r.ruta_html is not None:
        return f"[OK] {r.url} -> {r.ruta_html.name}"
    return f"[?] {r.url}"


def _duracion_legible(segundos: float) -> str:
    s = int(round(segundos))
    h, resto = divmod(s, 3600)
    m, sec = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def imprimir_resumen(
    conteo: ConteoResumen,
    segundos: float,
    salida: TextIO = sys.stdout,
) -> None:
    salida.write("\nResumen:\n")
    salida.write(f"  descargadas: {conteo.descargadas}\n")
    salida.write(f"  omitidas_por_robots: {conteo.omitidas_por_robots}\n")
    salida.write(f"  omitidas_por_hash: {conteo.omitidas_por_hash}\n")
    salida.write(f"  errores: {conteo.errores}\n")
    salida.write(f"  duración: {_duracion_legible(segundos)}\n")


def _url_base_robots_desde_inicio(url_inicio: str) -> str:
    """Origen `scheme://netloc/` para robots.txt, alineado al dominio del semilla."""
    p = urlparse(url_inicio.strip())
    if p.scheme and p.netloc:
        return f"{p.scheme}://{p.netloc}/"
    return URL_INICIO_DEFECTO


def ejecutar_scraping(
    url_base_robots: str,
    config: ConfiguracionCrawler,
    ruta_log: Path,
) -> tuple[ConteoResumen, float, bool]:
    """
    Ejecuta el crawler, appendea al log y acumula contadores.

    Devuelve:
        Tupla ``(conteo, duracion_s, interrumpido_por_teclado)``.
    """
    gestor = GestorRobots(url_base=url_base_robots, user_agent=config.user_agent)
    crawler = Crawler(config, gestor)
    t0 = monotonic()
    conteo = ConteoResumen()
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    interrumpido = False
    try:
        with open(ruta_log, "a", encoding="utf-8") as f_log:
            try:
                for r in crawler.ejecutar():
                    instante_utc = datetime.now(timezone.utc)
                    escribir_log(f_log, instante_utc, r)
                    print(_linea_stdout(r), flush=True)
                    conteo.actualizar_por_resultado(r)
            except KeyboardInterrupt:
                interrumpido = True
    finally:
        crawler.cerrar_sesion()
    return conteo, monotonic() - t0, interrumpido


def main() -> int:
    load_dotenv()
    ns = parsear_argumentos()
    url_inicio = _resolver_url_inicio(ns.url_inicio)
    user_agent = _resolver_user_agent(ns.user_agent)
    dir_salida = (
        ns.directorio_salida
        if ns.directorio_salida is not None
        else DIRECTORIO_CRUDO_POR_DEFECTO
    )
    config = ConfiguracionCrawler(
        url_inicio=url_inicio,
        max_paginas=ns.max_paginas,
        profundidad_maxima=ns.profundidad_maxima,
        delay_segundos=ns.delay,
        user_agent=user_agent,
        timeout=ns.timeout,
        reintentos=ns.reintentos,
        directorio_salida=Path(dir_salida),
        dominio_permitido=ns.dominio_permitido,
    )
    base_robots = _url_base_robots_desde_inicio(url_inicio)
    conteo, dur, interrumpido = ejecutar_scraping(
        base_robots,
        config,
        ns.archivo_log,
    )
    if interrumpido:
        print(
            "\nInterrupcion por teclado (Ctrl+C). Resumen parcial:",
            file=sys.stderr,
        )
    imprimir_resumen(conteo, dur)
    return 130 if interrumpido else 0


if __name__ == "__main__":
    raise SystemExit(main())