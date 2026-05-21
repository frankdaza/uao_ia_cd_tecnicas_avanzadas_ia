"""
Agrupa archivos Markdown del corpus por patrones configurables y escribe un arbol
derivado listo para scripts.indexar_corpus_qdrant.

Ejecucion desde la raiz del repositorio:

    uv run python -m scripts.agrupar_corpus_markdown
    uv run python -m scripts.agrupar_corpus_markdown --help
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _posix_rel_seguro(hijo: Path, raiz: Path) -> str:
    hr = hijo.resolve()
    rr = raiz.resolve()
    try:
        return hr.relative_to(rr).as_posix()
    except ValueError:
        return hr.as_posix()


from src.rutas_workspace import encontrar_raiz_repo, encontrar_raiz_proyecto

def parsear_front_matter_yaml(
    texto_completo: str,
) -> tuple[dict | None, str, str | None]:
    """
    Parser minimo de front matter entre delimitadores ``---``.

    Retorna ``(front_matter_dict|None, cuerpo, mensaje_error|None)``.
    """
    if not texto_completo.startswith("---\n"):
        return None, "", "no comienza con front matter ---"
    resto = texto_completo[4:]
    fin = resto.find("\n---\n")
    if fin <= 0:
        return None, "", "no se encontro cierre del front matter ---"
    bloque_yaml = resto[:fin]
    cuerpo = resto[fin + 5 :]
    try:
        fm = yaml.safe_load(bloque_yaml)
    except yaml.YAMLError as exc:
        return None, "", f"YAML invalido: {exc}"
    if fm is None:
        return {}, cuerpo, None
    if not isinstance(fm, dict):
        return None, cuerpo, "front matter no es un mapping YAML"
    return fm, cuerpo, None


@dataclass
class GrupoConfig:
    """Una regla de agrupacion cargada desde YAML."""

    id: str
    patrones_nombre: list[str]
    archivo_salida: str
    titulo: str
    seccion: str
    source_url_canonica: str = ""

    @property
    def patron_nombre_manifest(self) -> str | list[str]:
        """Representacion en manifiesto: string si hay un solo patron, lista si hay varios."""
        if len(self.patrones_nombre) == 1:
            return self.patrones_nombre[0]
        return list(self.patrones_nombre)

    @property
    def patron_nombre_etiqueta(self) -> str:
        """Texto unico para logs y front matter (varios patrones unidos)."""
        return " | ".join(self.patrones_nombre)


@dataclass
class EstadisticasAgrupacion:
    archivos_leidos: int = 0
    archivos_en_grupos: int = 0
    archivos_copiados: int = 0
    archivos_grupo_omitidos_yaml: int = 0
    grupos_escritos: int = 0
    advertencias: list[str] = field(default_factory=list)


def _cargar_grupos_desde_yaml(data: Any) -> list[GrupoConfig]:
    if not isinstance(data, dict):
        raise ValueError("configuracion: raiz debe ser un mapping YAML")
    raw = data.get("grupos")
    if not isinstance(raw, list) or not raw:
        raise ValueError("configuracion: clave 'grupos' debe ser una lista no vacia")
    salida: list[GrupoConfig] = []
    vistos_salida: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"grupos[{i}]: cada entrada debe ser un mapping")
        try:
            gid = str(item["id"]).strip()
            raw_patron = item["patron_nombre"]
            arch = str(item["archivo_salida"]).strip()
            titulo = str(item["titulo"]).strip()
            seccion = str(item["seccion"]).strip()
        except KeyError as exc:
            raise ValueError(f"grupos[{i}]: falta clave obligatoria {exc}") from exc
        if isinstance(raw_patron, str):
            patrones = [p for p in [raw_patron.strip()] if p]
        elif isinstance(raw_patron, list):
            patrones = [str(p).strip() for p in raw_patron if str(p).strip()]
        else:
            raise ValueError(
                f"grupos[{i}]: patron_nombre debe ser texto o lista de textos, "
                f"se obtuvo {type(raw_patron).__name__}"
            )
        if not patrones:
            raise ValueError(f"grupos[{i}]: patron_nombre no puede quedar vacio")
        if not gid or not arch or not titulo:
            raise ValueError(
                f"grupos[{i}]: id, patron_nombre, archivo_salida y titulo no pueden quedar vacios"
            )
        suc = str(item.get("source_url_canonica") or "").strip()
        if arch in vistos_salida:
            raise ValueError(f"archivo_salida duplicado en configuracion: {arch}")
        vistos_salida.add(arch)
        salida.append(
            GrupoConfig(
                id=gid,
                patrones_nombre=patrones,
                archivo_salida=arch,
                titulo=titulo,
                seccion=seccion,
                source_url_canonica=suc,
            )
        )
    return salida


def cargar_configuracion_grupos(ruta: Path) -> tuple[dict[str, Any], list[GrupoConfig]]:
    texto = ruta.read_text(encoding="utf-8")
    data = yaml.safe_load(texto)
    if data is None:
        raise ValueError(f"YAML vacio: {ruta}")
    grupos = _cargar_grupos_desde_yaml(data)
    return data if isinstance(data, dict) else {}, grupos


def _grupo_que_coincide(
    nombre_archivo: str, grupos: list[GrupoConfig]
) -> GrupoConfig | None:
    for g in grupos:
        for patron in g.patrones_nombre:
            if fnmatch.fnmatch(nombre_archivo, patron):
                return g
    return None


def _relativo_seguro(ruta: Path, base: Path) -> Path:
    hr = ruta.resolve()
    br = base.resolve()
    try:
        rel = hr.relative_to(br)
    except ValueError:
        rel = hr
    if any(p == ".." for p in rel.parts):
        raise ValueError("ruta fuera del directorio permitido")
    return rel


def _asegurar_limpiar_salida_segura(salida: Path) -> None:
    resuelta = salida.resolve()
    partes = {p.lower() for p in resuelta.parts}
    if "markdown_agrupado" not in partes:
        raise ValueError(
            "refuse limpiar: la ruta de salida debe contener el segmento "
            "'markdown_agrupado' (medida de seguridad)."
        )


def ejecutar_agrupacion(
    raiz: Path,
    entrada: Path,
    salida: Path,
    grupos: list[GrupoConfig],
    *,
    solo_grupos: bool,
    limpiar_salida: bool,
) -> EstadisticasAgrupacion:
    stats = EstadisticasAgrupacion()
    if not entrada.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {entrada}")

    if limpiar_salida:
        _asegurar_limpiar_salida_segura(salida)
        if salida.exists():
            shutil.rmtree(salida)
    salida.mkdir(parents=True, exist_ok=True)

    rutas_md = sorted(entrada.rglob("*.md"))
    stats.archivos_leidos = len(rutas_md)

    asignacion_grupo: dict[str, list[Path]] = {g.id: [] for g in grupos}
    rutas_sin_grupo: list[Path] = []

    for ruta in rutas_md:
        rel = _relativo_seguro(ruta, entrada)
        nombre = rel.name
        grupo = _grupo_que_coincide(nombre, grupos)
        if grupo is None:
            rutas_sin_grupo.append(ruta)
        else:
            asignacion_grupo[grupo.id].append(ruta)

    manifest: dict[str, Any] = {
        "version": 1,
        "fecha_agrupacion": date.today().isoformat(),
        "entrada_posix": _posix_rel_seguro(entrada, raiz),
        "salida_posix": _posix_rel_seguro(salida, raiz),
        "solo_grupos": solo_grupos,
        "grupos": {},
        "archivos_copiados": [],
    }

    for grupo in grupos:
        miembros = sorted(asignacion_grupo[grupo.id], key=lambda p: p.as_posix())
        if not miembros:
            manifest["grupos"][grupo.id] = {
                "patron_nombre": grupo.patron_nombre_manifest,
                "archivo_salida": grupo.archivo_salida,
                "archivos_origen": [],
            }
            stats.advertencias.append(
                f"Grupo '{grupo.id}': sin archivos que coincidan con {grupo.patrones_nombre!r}"
            )
            continue

        bloques: list[str] = []
        encabezado_doc = (
            f"# {grupo.titulo}\n\n"
            "Los fragmentos siguientes provienen de paginas distintas del sitio. "
            "Cada seccion conserva la URL de origen cuando estaba en el front matter.\n"
        )
        bloques.append(encabezado_doc)

        for origen in miembros:
            rel_o = _relativo_seguro(origen, entrada).as_posix()
            try:
                texto_completo = origen.read_text(encoding="utf-8")
            except OSError as exc:
                stats.archivos_grupo_omitidos_yaml += 1
                msg = f"{rel_o}: lectura fallida ({exc})"
                stats.advertencias.append(msg)
                logger.warning(msg)
                continue

            fm, cuerpo, err = parsear_front_matter_yaml(texto_completo)
            if fm is None or err:
                stats.archivos_grupo_omitidos_yaml += 1
                msg = f"{rel_o}: {err or 'front matter invalido'}"
                stats.advertencias.append(msg)
                logger.warning(msg)
                continue

            titulo_origen = str(fm.get("titulo") or "").strip()
            url_origen = str(fm.get("source_url") or "").strip()
            slug = origen.stem
            seccion_md = f"## Origen: {slug}\n\n"
            if titulo_origen:
                seccion_md += f"**Titulo original:** {titulo_origen}\n\n"
            if url_origen:
                seccion_md += f"**URL:** {url_origen}\n\n"
            cuerpo_limpio = (cuerpo or "").strip()
            if not cuerpo_limpio:
                seccion_md += "_Cuerpo vacio en el archivo fuente._\n"
            else:
                seccion_md += cuerpo_limpio + "\n"
            bloques.append(seccion_md + "\n\n")

        if len(bloques) <= 1:
            stats.advertencias.append(
                f"Grupo '{grupo.id}': no quedo contenido valido tras omitir fuentes; no se escribe salida."
            )
            manifest["grupos"][grupo.id] = {
                "patron_nombre": grupo.patron_nombre_manifest,
                "archivo_salida": grupo.archivo_salida,
                "archivos_origen": [_posix_rel_seguro(p, raiz) for p in miembros],
            }
            continue

        cuerpo_final = "\n".join(bloques).strip() + "\n"
        fm_salida: dict[str, Any] = {
            "titulo": grupo.titulo,
            "seccion": grupo.seccion,
            "source_url": grupo.source_url_canonica,
            "fecha_agrupacion": date.today().isoformat(),
            "agrupacion_grupo_id": grupo.id,
            "agrupacion_num_fuentes": len(miembros),
            "agrupacion_patron": grupo.patron_nombre_etiqueta,
        }

        yaml_fm = yaml.safe_dump(
            fm_salida,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).strip()
        contenido_md = f"---\n{yaml_fm}\n---\n\n{cuerpo_final}"

        destino = salida / grupo.archivo_salida
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido_md, encoding="utf-8")
        stats.grupos_escritos += 1
        stats.archivos_en_grupos += len(miembros)

        manifest["grupos"][grupo.id] = {
            "patron_nombre": grupo.patron_nombre_manifest,
            "archivo_salida": grupo.archivo_salida,
            "archivos_origen": [_posix_rel_seguro(p, raiz) for p in miembros],
        }

    if not solo_grupos:
        for ruta in sorted(rutas_sin_grupo, key=lambda p: p.as_posix()):
            rel = _relativo_seguro(ruta, entrada)
            destino = salida / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ruta, destino)
            stats.archivos_copiados += 1
            manifest["archivos_copiados"].append(
                {
                    "desde": _posix_rel_seguro(ruta, raiz),
                    "hasta": _posix_rel_seguro(destino, raiz),
                }
            )

    manifest_path = salida / "_manifest_agrupacion.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return stats


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    ws = encontrar_raiz_repo()
    proj = encontrar_raiz_proyecto()
    cfg_def = proj / "config" / "agrupacion_corpus_valledellili.yaml"
    ent_def = ws / "data" / "markdown" / "valledellili-org"
    sal_def = ws / "data" / "processed" / "markdown_agrupado" / "valledellili-org"

    p = argparse.ArgumentParser(
        description=(
            "Agrupa Markdown del corpus por patrones (fnmatch) y escribe un arbol derivado "
            "para indexar con scripts.indexar_corpus_qdrant."
        ),
    )
    p.add_argument(
        "--config",
        type=Path,
        default=cfg_def,
        help="Ruta al YAML de reglas de agrupacion (defecto: config/agrupacion_corpus_valledellili.yaml).",
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
        help="Directorio raiz de salida (defecto: data/processed/markdown_agrupado/valledellili-org).",
    )
    p.add_argument(
        "--solo-grupos",
        action="store_true",
        help="No copia archivos .md que no coincidan con ningun grupo (solo salidas agrupadas + manifiesto).",
    )
    p.add_argument(
        "--limpiar-salida",
        action="store_true",
        help=(
            "Elimina por completo el directorio --salida antes de escribir. "
            "Solo permitido si la ruta resuelta contiene el segmento 'markdown_agrupado'."
        ),
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

    _, grupos = cargar_configuracion_grupos(config_path)
    stats = ejecutar_agrupacion(
        ws,
        entrada,
        salida,
        grupos,
        solo_grupos=args.solo_grupos,
        limpiar_salida=args.limpiar_salida,
    )

    print("")
    print("=== Agrupacion Markdown ===")
    print(f"  Archivos .md en entrada:     {stats.archivos_leidos}")
    print(f"  Archivos asignados a grupos: {stats.archivos_en_grupos}")
    print(f"  Archivos copiados (resto):   {stats.archivos_copiados}")
    print(f"  Fuentes de grupo omitidas:   {stats.archivos_grupo_omitidos_yaml}")
    print(f"  Archivos agrupados escritos: {stats.grupos_escritos}")
    print(f"  Salida:                      {salida}")
    print(f"  Manifiesto:                  {salida / '_manifest_agrupacion.json'}")
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
