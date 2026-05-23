"""
Limpieza determinista del corpus Markdown: plantillas, hubs y ruido repetido.

Escribe un arbol derivado bajo data/processed/markdown_limpio/ listo para
scripts.indexar_corpus_qdrant sin modificar data/markdown/.

Ejecucion desde la raiz del repositorio:

    uv run python -m scripts.limpiar_corpus_markdown
    uv run python -m scripts.limpiar_corpus_markdown --help
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.agrupar_corpus_markdown import parsear_front_matter_yaml
from src.rutas_workspace import encontrar_raiz_proyecto, encontrar_raiz_repo

logger = logging.getLogger(__name__)


def _posix_rel_seguro(hijo: Path, raiz: Path) -> str:
    hr = hijo.resolve()
    rr = raiz.resolve()
    try:
        return hr.relative_to(rr).as_posix()
    except ValueError:
        return hr.as_posix()


def extraer_front_matter_literal(
    texto_completo: str,
) -> tuple[str | None, str, str | None]:
    """
    Separa el bloque YAML literal (sin delimitadores externos) y el cuerpo.

    Retorna ``(bloque_yaml_literal|None, cuerpo, mensaje_error|None)``.
    """
    if not texto_completo.startswith("---\n"):
        return None, "", "no comienza con front matter ---"
    resto = texto_completo[4:]
    fin = resto.find("\n---\n")
    if fin <= 0:
        return None, "", "no se encontro cierre del front matter ---"
    bloque_literal = resto[:fin]
    cuerpo = resto[fin + 5 :]
    return bloque_literal, cuerpo, None


def armar_markdown_salida(bloque_front_literal: str, cuerpo: str) -> str:
    """Reconstruye el .md preservando el front matter tal cual se leyo."""
    return f"---\n{bloque_front_literal}\n---\n{cuerpo}"


def hash_contenido_salida(texto_completo: str) -> str:
    return hashlib.sha256(texto_completo.encode("utf-8")).hexdigest()


@dataclass
class ReglaBloque:
    nombre: str
    regex_inicio: re.Pattern[str]
    regex_fin: re.Pattern[str] | None
    hasta_proximo_h2: bool
    hasta_eof: bool


@dataclass
class ReglaLinea:
    nombre: str
    regex: re.Pattern[str]


@dataclass
class ConfigLimpieza:
    version: int
    excluir_archivos: list[str]
    remover_bloques: list[ReglaBloque]
    remover_lineas: list[ReglaLinea]
    minimo_caracteres_utiles: int


def _relativo_seguro(ruta: Path, base: Path) -> Path:
    hr = ruta.resolve()
    br = base.resolve()
    try:
        rel = hr.relative_to(br)
    except ValueError:
        # Entrada fuera del arbol del repo: no hay relative_to estable.
        rel = hr
    if any(p == ".." for p in rel.parts):
        raise ValueError("ruta fuera del directorio permitido")
    return rel


def _asegurar_limpiar_salida_segura(salida: Path) -> None:
    resuelta = salida.resolve()
    partes = {p.lower() for p in resuelta.parts}
    if "markdown_limpio" not in partes:
        raise ValueError(
            "refuse limpiar: la ruta de salida debe contener el segmento "
            "'markdown_limpio' (medida de seguridad)."
        )


def _cargar_reglas_desde_dict(data: dict[str, Any]) -> ConfigLimpieza:
    if not isinstance(data, dict):
        raise ValueError("configuracion: raiz debe ser un mapping YAML")

    ver = data.get("version")
    if not isinstance(ver, int) or ver < 1:
        raise ValueError("configuracion: 'version' debe ser un entero >= 1")

    raw_ex = data.get("excluir_archivos")
    if not isinstance(raw_ex, list):
        raise ValueError("configuracion: 'excluir_archivos' debe ser una lista")
    excluir: list[str] = []
    for i, p in enumerate(raw_ex):
        if not isinstance(p, str) or not p.strip():
            raise ValueError(
                f"excluir_archivos[{i}]: cada patron debe ser texto no vacio"
            )
        excluir.append(p.strip())

    min_chars = data.get("minimo_caracteres_utiles")
    if not isinstance(min_chars, int) or min_chars < 0:
        raise ValueError(
            "configuracion: 'minimo_caracteres_utiles' debe ser un entero >= 0"
        )

    raw_bl = data.get("remover_bloques")
    if not isinstance(raw_bl, list):
        raise ValueError("configuracion: 'remover_bloques' debe ser una lista")
    bloques: list[ReglaBloque] = []
    for i, item in enumerate(raw_bl):
        if not isinstance(item, dict):
            raise ValueError(f"remover_bloques[{i}]: cada entrada debe ser un mapping")
        try:
            nombre = str(item["nombre"]).strip()
            rinicio = str(item["regex_inicio"]).strip()
        except KeyError as exc:
            raise ValueError(
                f"remover_bloques[{i}]: falta clave obligatoria {exc}"
            ) from exc
        if not nombre or not rinicio:
            raise ValueError(
                f"remover_bloques[{i}]: nombre y regex_inicio no pueden quedar vacios"
            )
        rfin_raw = item.get("regex_fin")
        hasta_h2 = bool(item.get("hasta_proximo_h2"))
        hasta_eof = bool(item.get("hasta_eof"))
        if (
            sum(
                x
                for x in [
                    rfin_raw is not None and str(rfin_raw).strip() != "",
                    hasta_h2,
                    hasta_eof,
                ]
            )
            > 1
        ):
            raise ValueError(
                f"remover_bloques[{i}] ({nombre}): use solo una de "
                "regex_fin, hasta_proximo_h2 o hasta_eof"
            )
        if not rfin_raw and not hasta_h2 and not hasta_eof:
            raise ValueError(
                f"remover_bloques[{i}] ({nombre}): debe definirse "
                "regex_fin, hasta_proximo_h2: true o hasta_eof: true"
            )
        rfin_pat: re.Pattern[str] | None = None
        if rfin_raw is not None and str(rfin_raw).strip():
            rfin_pat = re.compile(str(rfin_raw).strip(), re.MULTILINE | re.IGNORECASE)
        try:
            rinicio_pat = re.compile(rinicio, re.MULTILINE | re.IGNORECASE)
        except re.error as exc:
            raise ValueError(
                f"remover_bloques[{i}] ({nombre}): regex_inicio invalida: {exc}"
            ) from exc
        bloques.append(
            ReglaBloque(
                nombre=nombre,
                regex_inicio=rinicio_pat,
                regex_fin=rfin_pat,
                hasta_proximo_h2=hasta_h2,
                hasta_eof=hasta_eof,
            )
        )

    raw_ln = data.get("remover_lineas")
    if not isinstance(raw_ln, list):
        raise ValueError("configuracion: 'remover_lineas' debe ser una lista")
    lineas: list[ReglaLinea] = []
    for i, item in enumerate(raw_ln):
        if not isinstance(item, dict):
            raise ValueError(f"remover_lineas[{i}]: cada entrada debe ser un mapping")
        try:
            nombre = str(item["nombre"]).strip()
            rlinea = str(item["regex"]).strip()
        except KeyError as exc:
            raise ValueError(
                f"remover_lineas[{i}]: falta clave obligatoria {exc}"
            ) from exc
        if not nombre or not rlinea:
            raise ValueError(
                f"remover_lineas[{i}]: nombre y regex no pueden quedar vacios"
            )
        try:
            lineas.append(
                ReglaLinea(
                    nombre=nombre,
                    regex=re.compile(rlinea, re.MULTILINE | re.IGNORECASE),
                )
            )
        except re.error as exc:
            raise ValueError(
                f"remover_lineas[{i}] ({nombre}): regex invalida: {exc}"
            ) from exc

    return ConfigLimpieza(
        version=ver,
        excluir_archivos=excluir,
        remover_bloques=bloques,
        remover_lineas=lineas,
        minimo_caracteres_utiles=min_chars,
    )


def cargar_configuracion_limpieza(ruta: Path) -> ConfigLimpieza:
    texto = ruta.read_text(encoding="utf-8")
    data = yaml.safe_load(texto)
    if data is None:
        raise ValueError(f"YAML vacio: {ruta}")
    if not isinstance(data, dict):
        raise ValueError(f"YAML raiz invalido en {ruta}")
    return _cargar_reglas_desde_dict(data)


def _remover_bloques_cuerpo(
    cuerpo: str, reglas: list[ReglaBloque], bytes_por_regla: dict[str, int]
) -> str:
    texto = cuerpo
    for regla in reglas:
        antes = texto
        texto = _aplicar_regla_bloque(texto, regla)
        delta = len(antes) - len(texto)
        if delta > 0:
            bytes_por_regla[regla.nombre] = bytes_por_regla.get(regla.nombre, 0) + delta
    return texto


def _aplicar_regla_bloque(texto: str, regla: ReglaBloque) -> str:
    salida: list[str] = []
    pos = 0
    while pos < len(texto):
        m = regla.regex_inicio.search(texto, pos)
        if not m:
            salida.append(texto[pos:])
            break
        salida.append(texto[pos : m.start()])
        fin_corte = _fin_bloque(texto, m, regla)
        pos = fin_corte
    return "".join(salida)


def _fin_bloque(texto: str, m: re.Match[str], regla: ReglaBloque) -> int:
    desde = m.end()
    if regla.regex_fin:
        mfin = regla.regex_fin.search(texto, desde)
        if mfin:
            return mfin.start()
        return len(texto)
    if regla.hasta_proximo_h2:
        m2 = re.search(r"^##\s", texto[desde:], re.MULTILINE)
        if m2:
            return desde + m2.start()
        return len(texto)
    if regla.hasta_eof:
        return len(texto)
    return desde


def _remover_lineas_cuerpo(
    cuerpo: str, reglas: list[ReglaLinea], bytes_por_regla: dict[str, int]
) -> str:
    lineas = cuerpo.splitlines(keepends=True)
    salida: list[str] = []
    for linea in lineas:
        quitar = False
        for regla in reglas:
            if regla.regex.search(linea):
                delta = len(linea.encode("utf-8"))
                bytes_por_regla[regla.nombre] = (
                    bytes_por_regla.get(regla.nombre, 0) + delta
                )
                quitar = True
                break
        if not quitar:
            salida.append(linea)
    return "".join(salida)


def _debe_excluir(nombre_archivo: str, patrones: list[str]) -> bool:
    return any(fnmatch.fnmatch(nombre_archivo, p) for p in patrones)


@dataclass
class EstadisticasLimpieza:
    archivos_leidos: int = 0
    archivos_excluidos: int = 0
    archivos_descartados_por_minimo: int = 0
    archivos_escritos: int = 0
    archivos_omitidos_sin_cambio: int = 0
    archivos_omitidos_yaml: int = 0
    bytes_removidos_por_regla: dict[str, int] = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)


def ejecutar_limpieza(
    raiz: Path,
    entrada: Path,
    salida: Path,
    cfg: ConfigLimpieza,
    *,
    limpiar_salida: bool,
    limit: int | None,
) -> EstadisticasLimpieza:
    stats = EstadisticasLimpieza()
    if not entrada.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {entrada}")

    if limpiar_salida:
        _asegurar_limpiar_salida_segura(salida)
        if salida.exists():
            shutil.rmtree(salida)
    salida.mkdir(parents=True, exist_ok=True)

    rutas_md = sorted(entrada.rglob("*.md"))
    if limit is not None and limit >= 0:
        rutas_md = rutas_md[:limit]

    for ruta in rutas_md:
        rel = _relativo_seguro(ruta, entrada)
        nombre = rel.name
        stats.archivos_leidos += 1

        if _debe_excluir(nombre, cfg.excluir_archivos):
            stats.archivos_excluidos += 1
            continue

        try:
            texto_completo = ruta.read_text(encoding="utf-8")
        except OSError as exc:
            stats.archivos_omitidos_yaml += 1
            msg = f"{rel.as_posix()}: lectura fallida ({exc})"
            stats.advertencias.append(msg)
            logger.warning(msg)
            continue

        fm_literal, cuerpo, err_fm = extraer_front_matter_literal(texto_completo)
        if fm_literal is None or err_fm:
            stats.archivos_omitidos_yaml += 1
            msg = f"{rel.as_posix()}: {err_fm or 'front matter invalido'}"
            stats.advertencias.append(msg)
            logger.warning(msg)
            continue

        _fm, _, err_parse = parsear_front_matter_yaml(texto_completo)
        if _fm is None or err_parse:
            stats.archivos_omitidos_yaml += 1
            msg = (
                f"{rel.as_posix()}: {err_parse or 'YAML de front matter no parseable'}"
            )
            stats.advertencias.append(msg)
            logger.warning(msg)
            continue

        bytes_por_regla: dict[str, int] = {}
        cuerpo_limpio = _remover_bloques_cuerpo(
            cuerpo, cfg.remover_bloques, bytes_por_regla
        )
        cuerpo_limpio = _remover_lineas_cuerpo(
            cuerpo_limpio, cfg.remover_lineas, bytes_por_regla
        )

        for k, v in bytes_por_regla.items():
            stats.bytes_removidos_por_regla[k] = (
                stats.bytes_removidos_por_regla.get(k, 0) + v
            )

        util = len(cuerpo_limpio.strip())
        if util < cfg.minimo_caracteres_utiles:
            stats.archivos_descartados_por_minimo += 1
            destino = salida / rel
            if destino.is_file():
                destino.unlink()
            continue

        texto_nuevo = armar_markdown_salida(fm_literal, cuerpo_limpio)
        nuevo_hash = hash_contenido_salida(texto_nuevo)

        destino = salida / rel
        destino.parent.mkdir(parents=True, exist_ok=True)

        if destino.is_file():
            existente = destino.read_text(encoding="utf-8")
            if hash_contenido_salida(existente) == nuevo_hash:
                stats.archivos_omitidos_sin_cambio += 1
                continue

        destino.write_text(texto_nuevo, encoding="utf-8")
        stats.archivos_escritos += 1

    manifest: dict[str, Any] = {
        "version": cfg.version,
        "fecha_limpieza": datetime.now(timezone.utc).isoformat(),
        "entrada_posix": _posix_rel_seguro(entrada, raiz),
        "salida_posix": _posix_rel_seguro(salida, raiz),
        "archivos_leidos": stats.archivos_leidos,
        "archivos_excluidos": stats.archivos_excluidos,
        "archivos_descartados_por_minimo": stats.archivos_descartados_por_minimo,
        "archivos_escritos": stats.archivos_escritos,
        "archivos_omitidos_sin_cambio": stats.archivos_omitidos_sin_cambio,
        "archivos_omitidos_front_matter": stats.archivos_omitidos_yaml,
        "bytes_removidos_por_regla": dict(
            sorted(stats.bytes_removidos_por_regla.items())
        ),
        "advertencias": stats.advertencias,
    }
    manifest_path = salida / "_manifest_limpieza.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return stats


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    ws = encontrar_raiz_repo()
    proj = encontrar_raiz_proyecto()
    cfg_def = proj / "config" / "limpieza_corpus_valledellili.yaml"
    ent_def = ws / "data" / "markdown" / "valledellili-org"
    sal_def = ws / "data" / "processed" / "markdown_limpio" / "valledellili-org"

    p = argparse.ArgumentParser(
        description=(
            "Limpia plantillas y ruido repetido del corpus Markdown y escribe un arbol derivado "
            "para indexar con scripts.indexar_corpus_qdrant."
        ),
    )
    p.add_argument(
        "--config",
        type=Path,
        default=cfg_def,
        help="Ruta al YAML de reglas (defecto: config/limpieza_corpus_valledellili.yaml).",
    )
    p.add_argument(
        "--entrada",
        type=Path,
        default=ent_def,
        help="Directorio raiz del corpus Markdown de entrada.",
    )
    p.add_argument(
        "--salida",
        type=Path,
        default=sal_def,
        help="Directorio raiz de salida (defecto: data/processed/markdown_limpio/valledellili-org).",
    )
    p.add_argument(
        "--limpiar-salida",
        action="store_true",
        help=(
            "Elimina por completo el directorio --salida antes de escribir. "
            "Solo permitido si la ruta resuelta contiene el segmento 'markdown_limpio'."
        ),
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Procesa como maximo N archivos .md (orden por ruta).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logs de depuracion en stderr.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    ws = encontrar_raiz_repo()
    proj = encontrar_raiz_proyecto()
    entrada = args.entrada
    salida = args.salida
    config_path = args.config

    if not config_path.is_absolute():
        config_path = (proj / config_path).resolve()
    if not entrada.is_absolute():
        entrada = (ws / entrada).resolve()
    if not salida.is_absolute():
        salida = (ws / salida).resolve()

    cfg = cargar_configuracion_limpieza(config_path)
    stats = ejecutar_limpieza(
        ws,
        entrada,
        salida,
        cfg,
        limpiar_salida=args.limpiar_salida,
        limit=args.limit,
    )

    print("")
    print("=== Limpieza Markdown ===")
    print(f"  Archivos .md considerados:        {stats.archivos_leidos}")
    print(f"  Excluidos por patron:             {stats.archivos_excluidos}")
    print(
        f"  Descartados por minimo util:      {stats.archivos_descartados_por_minimo}"
    )
    print(f"  Escritos:                         {stats.archivos_escritos}")
    print(f"  Omitidos sin cambio (hash):     {stats.archivos_omitidos_sin_cambio}")
    print(f"  Omitidos (YAML / lectura):      {stats.archivos_omitidos_yaml}")
    print(f"  Salida:                           {salida}")
    print(f"  Manifiesto:                       {salida / '_manifest_limpieza.json'}")
    if stats.bytes_removidos_por_regla:
        print("")
        print("Bytes removidos por regla (UTF-8, aprox.):")
        for nombre_regla, bcount in sorted(stats.bytes_removidos_por_regla.items()):
            print(f"  - {nombre_regla}: {bcount}")
    if stats.advertencias:
        print("")
        print("Advertencias:")
        for a in stats.advertencias[:30]:
            print(f"  - {a}")
        if len(stats.advertencias) > 30:
            print(f"  ... y {len(stats.advertencias) - 30} mas")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
