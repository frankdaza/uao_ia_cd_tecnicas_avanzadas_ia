"""
Ingesta del corpus Markdown hacia Qdrant: chunking con LlamaIndex
(SentenceSplitter o MarkdownNodeParser segun ``CHUNK_STRATEGY``)
e upsert idempotente por hash de contenido.

Los vectores se **normalizan L2 a norma 1** antes del upsert (idempotente si el
embedder ya los entrega unitarios, p. ej. OpenAI ``text-embedding-3-*``).

Ejecucion desde la raiz del repositorio:

    uv run python scripts/indexar_corpus_qdrant.py
    uv run python -m scripts.indexar_corpus_qdrant
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import yaml
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from qdrant_client.models import PointIdsList, PointStruct

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.embeddings import obtener_embeddings
from src.rag.extractor_metadata import (
    construir_headings_path,
    extraer_especialidades,
    extraer_h1_h2_h3_desde_nodo,
    extraer_nombre_medico,
    extraer_sedes,
    extraer_tags,
    inferir_subtipo,
    inferir_tipo_pagina,
)
from src.rag.qdrant_store import (
    asegurar_coleccion,
    distancia_desde_settings,
    obtener_qdrant_client,
    reiniciar_cliente_qdrant,
)

logger = logging.getLogger(__name__)

_EPS_NORM_VECTOR = 1e-12


def _normalizar_l2_lista(vec: list[float]) -> list[float]:
    """
    Normaliza el vector denso a norma euclidea 1.

    Es idempotente salvo error numerico si el modelo ya devuelve vectores
    unitarios. Vectores casi nulos se dejan sin escalar y se registra advertencia.
    """
    arr = np.asarray(vec, dtype=np.float64).ravel()
    n = float(np.linalg.norm(arr))
    if n < _EPS_NORM_VECTOR:
        logger.warning(
            "Embedding con norma casi cero (<%s) antes de upsert; se omite normalizar.",
            _EPS_NORM_VECTOR,
        )
        return [float(x) for x in arr.tolist()]
    salida = (arr / n).astype(np.float64)
    return [float(x) for x in salida.tolist()]


# Namespace fija para mapear el hash hex a UUID (Qdrant en memoria exige UUID).
_NAMESPACE_ID_CHUNK = uuid.UUID("00000000-0000-5000-8000-000000000001")


@dataclass
class EstadisticasIndexacion:
    """Contadores y tiempos al cerrar la corrida."""

    archivos_markdown: int = 0
    archivos_omitidos_aviso: int = 0
    chunks_totales: int = 0
    chunks_upsert: int = 0
    chunks_omitidos_sin_cambio: int = 0
    puntos_purgados: int = 0
    segundos_ingesta: float = 0.0
    segundos_embeddings: float = 0.0
    dimension_vector: int = 0
    advertencias: list[str] = field(default_factory=list)
    chunks_por_tipo_pagina: dict[str, int] = field(default_factory=dict)


@dataclass
class TrabajoChunk:
    """Un fragmento listo para vectorizar y subir a Qdrant."""

    id_chunk_hex: str
    id_punto_qdrant: str
    texto: str
    archivo: str
    titulo: str
    source_url: str
    seccion: str
    chunk_index: int
    content_hash: str
    tipo_pagina: str = "otro"
    subtipo: str | None = None
    especialidad: list[str] = field(default_factory=list)
    sedes: list[str] = field(default_factory=list)
    nombre_medico: str | None = None
    headings_path: str = ""
    h1: str | None = None
    h2: str | None = None
    h3: str | None = None
    tags: list[str] = field(default_factory=list)


def encontrar_raiz_repo(inicio: Path | None = None) -> Path:
    """Sube directorios hasta hallar ``pyproject.toml``; si no, usa ``cwd``."""
    p = (inicio or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "pyproject.toml").is_file():
            return cand
    return p


def parsear_front_matter_yaml(texto_completo: str) -> tuple[dict | None, str, str | None]:
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


def calcular_id_chunk_hex(archivo_posix: str, chunk_index: int, texto: str) -> str:
    """Idempotencia: mismo archivo, indice y texto producen el mismo id."""
    clave = f"{archivo_posix}:{chunk_index}:{texto}"
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def calcular_content_hash(texto: str) -> str:
    """Hash del texto del chunk para detectar cambios sin reembedir igualdad logica."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def id_punto_qdrant_desde_hex(id_chunk_hex: str) -> str:
    """Convierte el digest en UUID string compatible con Qdrant local (:memory:)."""
    return str(uuid.uuid5(_NAMESPACE_ID_CHUNK, id_chunk_hex))


def _metadata_documental(
    fm: dict,
    cuerpo: str,
    archivo_posix: str,
    titulo: str,
    seccion: str,
) -> tuple[str, str | None, str | None, list[str], list[str], list[str]]:
    """Clasificacion y listas base por archivo (se repiten en cada chunk)."""
    tipo = inferir_tipo_pagina(seccion, archivo_posix)
    sub = inferir_subtipo(archivo_posix)
    nombre = extraer_nombre_medico(titulo, fm) if tipo == "ficha_medico" else None
    espec = extraer_especialidades(cuerpo, fm)
    sedes = extraer_sedes(cuerpo, fm)
    tags = extraer_tags(fm, cuerpo)
    if tipo == "educacion" and not espec and "pediatr" in titulo.lower():
        espec = ["Pediatria"]
    return tipo, sub, nombre, list(espec), list(sedes), list(tags)


def construir_trabajos(
    rutas_md: list[Path],
    raiz: Path,
    chunk_size: int,
    chunk_overlap: int,
    chunk_strategy: Literal["sentence", "markdown"] = "sentence",
) -> tuple[list[TrabajoChunk], int, list[str]]:
    """
    Lee Markdown y arma la lista de ``TrabajoChunk``.

    Retorna ``(trabajos, archivos_omitidos, advertencias)``.
    """
    if chunk_strategy == "markdown":
        return construir_trabajos_markdown(
            rutas_md, raiz, chunk_size, chunk_overlap
        )
    return construir_trabajos_sentence(rutas_md, raiz, chunk_size, chunk_overlap)


def construir_trabajos_sentence(
    rutas_md: list[Path],
    raiz: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[list[TrabajoChunk], int, list[str]]:
    """Chunking retrocompatible: ``SentenceSplitter`` sobre el cuerpo completo."""
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    trabajos: list[TrabajoChunk] = []
    omitidos = 0
    advertencias: list[str] = []

    for ruta in rutas_md:
        archivo_posix = ruta.resolve().relative_to(raiz).as_posix()
        try:
            texto_completo = ruta.read_text(encoding="utf-8")
        except OSError as exc:
            omitidos += 1
            advertencias.append(f"{archivo_posix}: lectura fallida ({exc})")
            logger.warning("%s: lectura fallida: %s", archivo_posix, exc)
            continue

        fm, cuerpo, err = parsear_front_matter_yaml(texto_completo)
        if fm is None or err:
            omitidos += 1
            msg = err or "front matter ausente o invalido"
            advertencias.append(f"{archivo_posix}: {msg}")
            logger.warning("%s: %s", archivo_posix, msg)
            continue

        titulo = str(fm.get("titulo") or "")
        source_url = str(fm.get("source_url") or "")
        seccion = str(fm.get("seccion") or "")

        tipo, sub, nombre, espec, sedes, tags = _metadata_documental(
            fm, cuerpo, archivo_posix, titulo, seccion
        )

        doc = Document(text=cuerpo.strip() or cuerpo)
        nodos = splitter.get_nodes_from_documents([doc])
        if not nodos:
            advertencias.append(f"{archivo_posix}: sin chunks (cuerpo vacio)")
            logger.warning("%s: sin nodos tras chunking", archivo_posix)
            continue

        for chunk_index, nodo in enumerate(nodos):
            texto = nodo.get_content()
            id_hex = calcular_id_chunk_hex(archivo_posix, chunk_index, texto)
            trabajos.append(
                TrabajoChunk(
                    id_chunk_hex=id_hex,
                    id_punto_qdrant=id_punto_qdrant_desde_hex(id_hex),
                    texto=texto,
                    archivo=archivo_posix,
                    titulo=titulo,
                    source_url=source_url,
                    seccion=seccion,
                    chunk_index=chunk_index,
                    content_hash=calcular_content_hash(texto),
                    tipo_pagina=tipo,
                    subtipo=sub,
                    especialidad=list(espec),
                    sedes=list(sedes),
                    nombre_medico=nombre,
                    headings_path="",
                    h1=None,
                    h2=None,
                    h3=None,
                    tags=list(tags),
                )
            )

    return trabajos, omitidos, advertencias


def construir_trabajos_markdown(
    rutas_md: list[Path],
    raiz: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[list[TrabajoChunk], int, list[str]]:
    """Chunking estructural: ``MarkdownNodeParser`` + post-fractura por tamano."""
    md_parser = MarkdownNodeParser()
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    tope_max_caracteres = min(max(1200, chunk_size * 4), 16384)

    trabajos: list[TrabajoChunk] = []
    omitidos = 0
    advertencias: list[str] = []

    for ruta in rutas_md:
        archivo_posix = ruta.resolve().relative_to(raiz).as_posix()
        try:
            texto_completo = ruta.read_text(encoding="utf-8")
        except OSError as exc:
            omitidos += 1
            advertencias.append(f"{archivo_posix}: lectura fallida ({exc})")
            logger.warning("%s: lectura fallida: %s", archivo_posix, exc)
            continue

        fm, cuerpo, err = parsear_front_matter_yaml(texto_completo)
        if fm is None or err:
            omitidos += 1
            msg = err or "front matter ausente o invalido"
            advertencias.append(f"{archivo_posix}: {msg}")
            logger.warning("%s: %s", archivo_posix, msg)
            continue

        titulo = str(fm.get("titulo") or "")
        source_url = str(fm.get("source_url") or "")
        seccion = str(fm.get("seccion") or "")

        tipo, sub, nombre, espec, sedes, tags = _metadata_documental(
            fm, cuerpo, archivo_posix, titulo, seccion
        )

        doc = Document(text=cuerpo.strip() or cuerpo)
        nodos_md = md_parser.get_nodes_from_documents([doc])
        if not nodos_md:
            advertencias.append(f"{archivo_posix}: sin chunks (cuerpo vacio)")
            logger.warning("%s: sin nodos tras MarkdownNodeParser", archivo_posix)
            continue

        nodos_expandidos: list = []
        for nodo in nodos_md:
            texto_n = nodo.get_content()
            if len(texto_n) <= tope_max_caracteres:
                nodos_expandidos.append(nodo)
                continue
            meta_base = dict(getattr(nodo, "metadata", None) or {})
            sub_doc = Document(text=texto_n, metadata=meta_base)
            partes = splitter.get_nodes_from_documents([sub_doc])
            if not partes:
                nodos_expandidos.append(nodo)
            else:
                nodos_expandidos.extend(partes)

        for chunk_index, nodo in enumerate(nodos_expandidos):
            texto = nodo.get_content()
            id_hex = calcular_id_chunk_hex(archivo_posix, chunk_index, texto)
            hpath = construir_headings_path(nodo)
            h1, h2, h3 = extraer_h1_h2_h3_desde_nodo(nodo)
            trabajos.append(
                TrabajoChunk(
                    id_chunk_hex=id_hex,
                    id_punto_qdrant=id_punto_qdrant_desde_hex(id_hex),
                    texto=texto,
                    archivo=archivo_posix,
                    titulo=titulo,
                    source_url=source_url,
                    seccion=seccion,
                    chunk_index=chunk_index,
                    content_hash=calcular_content_hash(texto),
                    tipo_pagina=tipo,
                    subtipo=sub,
                    especialidad=list(espec),
                    sedes=list(sedes),
                    nombre_medico=nombre,
                    headings_path=hpath,
                    h1=h1,
                    h2=h2,
                    h3=h3,
                    tags=list(tags),
                )
            )

    return trabajos, omitidos, advertencias


def _payload_desde_trabajo(t: TrabajoChunk) -> dict:
    return {
        "archivo": t.archivo,
        "titulo": t.titulo,
        "source_url": t.source_url,
        "seccion": t.seccion,
        "chunk_index": t.chunk_index,
        "content_hash": t.content_hash,
        "id_chunk": t.id_chunk_hex,
        "texto": t.texto,
        "tipo_pagina": t.tipo_pagina,
        "subtipo": t.subtipo,
        "especialidad": list(t.especialidad),
        "sedes": list(t.sedes),
        "nombre_medico": t.nombre_medico,
        "headings_path": t.headings_path,
        "h1": t.h1,
        "h2": t.h2,
        "h3": t.h3,
        "tags": list(t.tags),
    }


def _recuperar_hashes_existentes(
    cliente,
    coleccion: str,
    ids_puntos: list[str],
    tam_lote: int,
) -> dict[str, str | None]:
    """Mapa id_punto_qdrant -> content_hash en Qdrant (None si no existe)."""
    salida: dict[str, str | None] = dict.fromkeys(ids_puntos, None)
    for i in range(0, len(ids_puntos), tam_lote):
        lote = ids_puntos[i : i + tam_lote]
        puntos = cliente.retrieve(
            collection_name=coleccion,
            ids=lote,
            with_payload=True,
        )
        for p in puntos:
            pl = p.payload or {}
            salida[str(p.id)] = pl.get("content_hash") if isinstance(pl, dict) else None
    return salida


def ejecutar_indexacion(
    raiz: Path,
    cfg: Configuracion,
    markdown_dir: Path,
    patron_glob: str,
    *,
    purgar: bool,
    limite_archivos: int | None,
    tam_lote_embed: int,
    tam_lote_retrieve: int,
) -> EstadisticasIndexacion:
    """Pipeline principal: chunks, embeddings selectivos, upsert y purga opcional."""
    t0 = time.perf_counter()
    stats = EstadisticasIndexacion()

    if not markdown_dir.is_dir():
        raise FileNotFoundError(
            f"No existe el directorio de Markdown: {markdown_dir}"
        )

    rutas = sorted(markdown_dir.glob(patron_glob))
    rutas = [p for p in rutas if p.is_file()]
    if limite_archivos is not None:
        rutas = rutas[: max(0, limite_archivos)]

    stats.archivos_markdown = len(rutas)

    trabajos, omit_fm, adv_const = construir_trabajos(
        rutas,
        raiz,
        cfg.chunk_size,
        cfg.chunk_overlap,
        cfg.chunk_strategy,
    )
    stats.archivos_omitidos_aviso = omit_fm
    stats.advertencias.extend(adv_const)
    stats.chunks_totales = len(trabajos)
    stats.chunks_por_tipo_pagina = dict(Counter(t.tipo_pagina for t in trabajos))

    cliente = obtener_qdrant_client(cfg)
    distancia = distancia_desde_settings(cfg.qdrant_distance)
    asegurar_coleccion(
        cliente,
        cfg.qdrant_collection,
        cfg.embedding_dims,
        distancia,
        configuracion=cfg,
    )

    embedder = obtener_embeddings(cfg)

    ids_unicos = list({t.id_punto_qdrant for t in trabajos})
    existentes = _recuperar_hashes_existentes(
        cliente,
        cfg.qdrant_collection,
        ids_unicos,
        tam_lote_retrieve,
    )

    pendientes: list[TrabajoChunk] = []
    for t in trabajos:
        prev_hash = existentes.get(t.id_punto_qdrant)
        if prev_hash is not None and str(prev_hash) == t.content_hash:
            stats.chunks_omitidos_sin_cambio += 1
        else:
            pendientes.append(t)

    t_embed0 = time.perf_counter()
    for i in range(0, len(pendientes), tam_lote_embed):
        lote = pendientes[i : i + tam_lote_embed]
        textos = [x.texto for x in lote]
        vectores = embedder.get_text_embedding_batch(textos)
        if not stats.dimension_vector and vectores:
            stats.dimension_vector = len(vectores[0])
        puntos = [
            PointStruct(
                id=t.id_punto_qdrant,
                vector=_normalizar_l2_lista(vec),
                payload=_payload_desde_trabajo(t),
            )
            for t, vec in zip(lote, vectores, strict=True)
        ]
        cliente.upsert(collection_name=cfg.qdrant_collection, points=puntos)
        stats.chunks_upsert += len(puntos)
    stats.segundos_embeddings = time.perf_counter() - t_embed0

    prefijo_corpus = markdown_dir.resolve().relative_to(raiz).as_posix()
    ids_esperados = {t.id_punto_qdrant for t in trabajos}

    if purgar:
        if limite_archivos is not None:
            msg = "--purgar se ignora cuando --limit esta definido (evita borrado masivo en pruebas)"
            stats.advertencias.append(msg)
            logger.warning(msg)
        else:
            stats.puntos_purgados = _purgar_huerfanos(
                cliente,
                cfg.qdrant_collection,
                prefijo_corpus,
                ids_esperados,
            )

    stats.segundos_ingesta = time.perf_counter() - t0
    return stats


def _punto_huerfano_bajo_prefijo(
    punto: object,
    prefijo_archivo: str,
    ids_esperados: set[str],
) -> str | None:
    """
    Retorna el id del punto como str si debe purgarse; si no aplica, ``None``.
    """
    pl = getattr(punto, "payload", None) or {}
    if not isinstance(pl, dict):
        return None
    arch = pl.get("archivo")
    if not isinstance(arch, str):
        return None
    if not (arch == prefijo_archivo or arch.startswith(prefijo_archivo + "/")):
        return None
    pid = str(getattr(punto, "id", ""))
    if pid in ids_esperados:
        return None
    return pid


def _purgar_huerfanos(
    cliente,
    coleccion: str,
    prefijo_archivo: str,
    ids_esperados: set[str],
) -> int:
    """
    Elimina puntos bajo ``prefijo_archivo`` cuyo id ya no aparece en el corpus actual.

    Solo considera payloads con campo ``archivo`` (str) que empieza por ``prefijo_archivo/``
    o es igual a ``prefijo_archivo`` (defensivo).
    """
    borrar: list[str] = []
    offset = None
    while True:
        puntos, offset = cliente.scroll(
            collection_name=coleccion,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in puntos:
            pid = _punto_huerfano_bajo_prefijo(p, prefijo_archivo, ids_esperados)
            if pid is not None:
                borrar.append(pid)
        if offset is None:
            break

    for i in range(0, len(borrar), 256):
        lote = borrar[i : i + 256]
        cliente.delete(
            collection_name=coleccion,
            points_selector=PointIdsList(points=lote),
        )
    return len(borrar)


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz_def = encontrar_raiz_repo()
    md_def = raiz_def / "data" / "markdown" / "valledellili-org"
    p = argparse.ArgumentParser(
        description=(
            "Indexa Markdown del corpus en Qdrant con chunking LlamaIndex "
            "(``sentence``: SentenceSplitter; ``markdown``: MarkdownNodeParser) "
            "y upsert idempotente por hash de contenido."
        ),
    )
    p.add_argument(
        "--markdown-dir",
        type=Path,
        default=md_def,
        help=(
            "Directorio base del corpus Markdown "
            "(defecto: data/markdown/valledellili-org relativo a la raiz del repo)."
        ),
    )
    p.add_argument(
        "--glob",
        dest="patron_glob",
        default="**/*.md",
        help='Patron glob relativo a --markdown-dir (defecto: "**/*.md").',
    )
    p.add_argument(
        "--purgar",
        action="store_true",
        help=(
            "Elimina en Qdrant los puntos del prefijo de este corpus cuyo id ya no "
            "existe en la indexacion actual. No compatible con --limit (se ignora)."
        ),
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Procesa como maximo N archivos Markdown (orden estable por ruta).",
    )
    p.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Sobrescribe el nombre de la coleccion Qdrant (equivale a QDRANT_COLLECTION).",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=32,
        metavar="K",
        help="Tamano de lote para embeddings y upsert (defecto: 32).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logs de depuracion en stderr.",
    )
    return p.parse_args(argv)


def _imprimir_resumen(stats: EstadisticasIndexacion, cfg: Configuracion) -> None:
    print("")
    print("=== Indexacion Qdrant ===")
    print(f"  Estrategia chunking (env):      {cfg.chunk_strategy}")
    print(f"  Archivos Markdown considerados: {stats.archivos_markdown}")
    print(f"  Archivos omitidos (YAML/aviso): {stats.archivos_omitidos_aviso}")
    print(f"  Chunks totales en corpus:       {stats.chunks_totales}")
    print(f"  Chunks upsert (nuevo/cambio):   {stats.chunks_upsert}")
    print(f"  Chunks omitidos (sin cambio):   {stats.chunks_omitidos_sin_cambio}")
    print(f"  Puntos purgados:                {stats.puntos_purgados}")
    print(f"  Dimension vector informada:   {stats.dimension_vector or cfg.embedding_dims}")
    print(f"  Tiempo embeddings + upsert:   {stats.segundos_embeddings:.2f} s")
    print(f"  Tiempo total:                   {stats.segundos_ingesta:.2f} s")
    if stats.chunks_por_tipo_pagina:
        print("")
        print("  Chunks por tipo_pagina:")
        for tipo in sorted(stats.chunks_por_tipo_pagina.keys()):
            print(f"    - {tipo}: {stats.chunks_por_tipo_pagina[tipo]}")
    if stats.advertencias:
        print("")
        print("Advertencias:")
        for a in stats.advertencias[:20]:
            print(f"  - {a}")
        if len(stats.advertencias) > 20:
            print(f"  ... y {len(stats.advertencias) - 20} mas")
    print("")


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    raiz = encontrar_raiz_repo()
    markdown_dir = args.markdown_dir
    if not markdown_dir.is_absolute():
        markdown_dir = (raiz / markdown_dir).resolve()

    obtener_configuracion.cache_clear()
    cfg_base = obtener_configuracion()
    if args.collection:
        cfg = cfg_base.model_copy(update={"qdrant_collection": args.collection})
    else:
        cfg = cfg_base

    reiniciar_cliente_qdrant()
    stats = ejecutar_indexacion(
        raiz,
        cfg,
        markdown_dir,
        args.patron_glob,
        purgar=args.purgar,
        limite_archivos=args.limit,
        tam_lote_embed=max(1, args.batch_size),
        tam_lote_retrieve=max(1, min(128, args.batch_size * 4)),
    )

    _imprimir_resumen(stats, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
