"""
Evaluacion cuantitativa del RAG contra un golden set (TASK-72).

Validacion sin red ni Qdrant:

    uv run python -m scripts.eval_metricas_rag --solo-validar-golden

Ejecucion completa (Qdrant + embeddings segun .env):

    uv run python -m scripts.eval_metricas_rag --golden data/eval/golden_set_rag.jsonl --config baseline

Comparar dos corridas (archivos ``*.results.jsonl``) con umbrales de regresion:

    uv run python -m scripts.eval_metricas_rag --comparar A.results.jsonl B.results.jsonl --umbral-mrr 0.0

Cuatro presets en una sola corrida (reporte + CSV bajo ``data/eval/reportes/``):

    uv run python -m scripts.eval_metricas_rag --config todas --fail-if-empty
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, cast

from jsonschema import Draft7Validator

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.runtime.embeddings import obtener_embeddings
from src.rag.evaluacion.metricas_eval import (
    hit_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from src.rag.runtime.qdrant_store import (
    contar_puntos_en_coleccion,
    obtener_qdrant_client,
    obtener_vector_store,
    reiniciar_cliente_qdrant,
)
from src.rag.runtime.recuperador_denso import RecuperadorDenso

logger = logging.getLogger(__name__)

TipoConfigEval = Literal[
    "baseline",
    "limpio",
    "markdown",
    "mmr",
    "reranker",
    "combinado",
    "adaptativo",
]

PRESETS_EVAL_TODAS: tuple[TipoConfigEval, ...] = ("baseline", "mmr", "reranker", "combinado")


def obtener_commit_git(raiz: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(raiz), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return "(no disponible)"


def sha256_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def encontrar_raiz_repo(inicio: Path | None = None) -> Path:
    p = (inicio or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "pyproject.toml").is_file():
            return cand
    return p


def ruta_schema_golden(raiz: Path) -> Path:
    return raiz / "data" / "eval" / "golden_set.schema.json"


def cargar_schema(raiz: Path) -> dict[str, Any]:
    ruta = ruta_schema_golden(raiz)
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_golden_jsonl(ruta: Path) -> list[dict[str, Any]]:
    lineas = ruta.read_text(encoding="utf-8").strip().splitlines()
    salida: list[dict[str, Any]] = []
    for i, ln in enumerate(lineas, start=1):
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Linea {i}: JSON invalido ({exc})") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"Linea {i}: se esperaba un objeto JSON")
        salida.append(obj)
    return salida


def validar_golden_completo(
    entradas: list[dict[str, Any]],
    schema: dict[str, Any],
) -> None:
    validator = Draft7Validator(schema)
    for i, ent in enumerate(entradas, start=1):
        errores = sorted(validator.iter_errors(ent), key=lambda e: e.path)
        if errores:
            msg = "; ".join(f"{list(e.path)}: {e.message}" for e in errores[:5])
            raise ValueError(f"Golden linea {i} (id={ent.get('id')}): {msg}")


def _overrides_rag_por_etiqueta(nombre: TipoConfigEval) -> dict[str, object]:
    """Flags MMR/reranker alineados a experimentos TASK-71 (baseline = camino legacy)."""
    if nombre == "baseline":
        return {"rag_mmr_habilitado": False, "rag_reranker_habilitado": False}
    if nombre == "mmr":
        return {"rag_mmr_habilitado": True, "rag_reranker_habilitado": False}
    if nombre == "reranker":
        return {"rag_mmr_habilitado": False, "rag_reranker_habilitado": True}
    if nombre == "combinado":
        return {"rag_mmr_habilitado": True, "rag_reranker_habilitado": True}
    return {}


def ajustar_configuracion_eval(
    nombre: TipoConfigEval,
    collection_cli: str | None,
) -> Configuracion:
    """
    Mapea la etiqueta de experimento a parametros de ``Configuracion``.

    Las rutas ``mmr``, ``reranker`` y ``combinado`` aplican overrides de TASK-71
    ademas de ``QDRANT_COLLECTION`` cuando se pasa ``--collection``.
    """
    obtener_configuracion.cache_clear()
    base = obtener_configuracion()
    updates: dict[str, object] = {}
    coleccion = collection_cli
    if nombre == "baseline":
        updates.update(_overrides_rag_por_etiqueta("baseline"))
    elif nombre == "limpio":
        coleccion = coleccion or "corpus_fvl_v2"
    elif nombre == "markdown":
        coleccion = coleccion or "corpus_fvl_v2"
    elif nombre in ("mmr", "reranker", "combinado"):
        coleccion = coleccion or base.qdrant_collection
        updates.update(_overrides_rag_por_etiqueta(nombre))
    elif nombre == "adaptativo":
        coleccion = coleccion or base.qdrant_collection
    if coleccion:
        updates["qdrant_collection"] = coleccion
    if updates:
        return base.model_copy(update=updates)
    return base


def notas_por_config(nombre: TipoConfigEval) -> list[str]:
    notas: list[str] = []
    if nombre in ("mmr", "reranker", "combinado"):
        notas.append(
            f"Overrides RAG TASK-71: MMR={nombre in ('mmr', 'combinado')}, "
            f"reranker={nombre in ('reranker', 'combinado')} (ver ``Configuracion`` / ``.env``)."
        )
    if nombre == "adaptativo":
        notas.append(
            "Configuracion adaptativa (listar_estructurado): TASK-70; las filas "
            "listado/conteo siguen marcadas como no aplicables en esta corrida."
        )
    if nombre in ("limpio", "markdown"):
        notas.append(
            "Se asume coleccion alternativa si no pasas --collection; ver TASK-68/69."
        )
    return notas


def _clave_metrica(nombre: str, k: int) -> str:
    return f"{nombre}@{k}"


def ejecutar_fila_factual(
    rec: RecuperadorDenso,
    fila: dict[str, Any],
) -> dict[str, Any]:
    k = int(fila["k_evaluacion"])
    consulta = str(fila["consulta"])
    relevantes = list(fila["archivos_relevantes"] or [])
    salida = rec.consultar(consulta, top_k=k)
    archivos_por_chunk = [f.archivo for f in salida.fuentes]
    return {
        "qid": fila["id"],
        "consulta": consulta,
        "tipo": fila["tipo"],
        "k_evaluacion": k,
        "archivos_relevantes": relevantes,
        "archivos_por_chunk": archivos_por_chunk,
        _clave_metrica("hit", k): hit_at_k(archivos_por_chunk, relevantes, k),
        _clave_metrica("precision", k): precision_at_k(archivos_por_chunk, relevantes, k),
        _clave_metrica("recall", k): recall_at_k(archivos_por_chunk, relevantes, k),
        "mrr": mrr(archivos_por_chunk, relevantes, k),
        _clave_metrica("ndcg", k): ndcg_at_k(archivos_por_chunk, relevantes, k),
        "recall_conteo": None,
        "listado_na": False,
        "notas": [],
    }


def ejecutar_fila_listado_conteo(fila: dict[str, Any]) -> dict[str, Any]:
    k = int(fila["k_evaluacion"])
    return {
        "qid": fila["id"],
        "consulta": str(fila["consulta"]),
        "tipo": fila["tipo"],
        "k_evaluacion": k,
        "archivos_relevantes": None,
        "archivos_por_chunk": [],
        _clave_metrica("hit", k): None,
        _clave_metrica("precision", k): None,
        _clave_metrica("recall", k): None,
        "mrr": None,
        _clave_metrica("ndcg", k): None,
        "recall_conteo": None,
        "listado_na": True,
        "notas": [
            "Tipo listado/conteo: integracion con listar_estructurado pendiente (TASK-70). "
            "No se ejecuto recuperacion densa para esta fila."
        ],
    }


def agregar_metricas_factual(resultados: list[dict[str, Any]]) -> dict[str, float]:
    """Promedio solo sobre filas factuales con metricas numericas."""
    claves_num: defaultdict[str, list[float]] = defaultdict(list)
    patron = re.compile(r"^(hit|precision|recall|ndcg)@\d+$|^mrr$")
    for r in resultados:
        if r.get("listado_na"):
            continue
        for clave, val in r.items():
            if not patron.match(clave):
                continue
            if val is None:
                continue
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                claves_num[clave].append(float(val))
    return {c: statistics.mean(vals) for c, vals in claves_num.items() if vals}


def fragmentos_contexto_ejecucion(cfg: Configuracion) -> list[str]:
    """Lineas de contexto reproducible (sin secretos)."""
    rer_txt = (
        f"`{cfg.rag_reranker_modelo}` (top_n entrada `{cfg.rag_reranker_top_n_entrada}`)"
        if cfg.rag_reranker_habilitado
        else "desactivado"
    )
    return [
        f"- **Coleccion Qdrant**: `{cfg.qdrant_collection}`",
        f"- **Embeddings (proveedor / modelo)**: `{cfg.embedding_provider}` / `{cfg.embedding_model}` (dims `{cfg.embedding_dims}`)",
        f"- **Reranker cross-encoder**: {rer_txt}",
        f"- **RAG_SCORE_MINIMO** (evaluacion): `{cfg.rag_score_minimo}`",
        f"- **RAG_TOP_K** (constructor recuperador): `{cfg.rag_top_k}`",
        f"- **RAG_TOP_K_INICIAL**: `{cfg.rag_top_k_inicial}`",
        f"- **RAG_MMR_HABILITADO** / **RAG_MMR_LAMBDA**: `{cfg.rag_mmr_habilitado}` / `{cfg.rag_mmr_lambda}`",
        f"- **RAG_RERANKER_HABILITADO**: `{cfg.rag_reranker_habilitado}`",
    ]


def lineas_tablas_metricas_reporte(
    resultados: list[dict[str, Any]],
    agregados: dict[str, float],
) -> list[str]:
    """Secciones de tablas agregadas + por consulta + apendices (reuso reporte simple y consolidado)."""
    lineas: list[str] = []
    lineas.extend(["## Tabla agregada (promedio, solo factual)", "", "| metrica | valor |", "| --- | --- |"])
    if not agregados:
        lineas.append("| (sin datos factuales) | — |")
    else:
        for clave in sorted(agregados):
            lineas.append(f"| `{clave}` | {agregados[clave]:.4f} |")
    lineas.append("")

    lineas.extend(
        [
            "## Tabla por consulta",
            "",
            "| qid | tipo | k | hit | precision | recall | mrr | ndcg | preview top archivos |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for r in resultados:
        k = int(r["k_evaluacion"])
        if r.get("listado_na"):
            lineas.append(
                f"| {r['qid']} | {r['tipo']} | {k} | N/A | N/A | N/A | N/A | N/A | — |"
            )
            continue
        tops = r.get("archivos_por_chunk") or []
        prev = ", ".join(tops[:4])
        if len(prev) > 120:
            prev = prev[:117] + "..."
        lineas.append(
            "| {qid} | {tipo} | {k} | {hit} | {prec} | {rec} | {mrr} | {ndcg} | `{preview}` |".format(
                qid=r["qid"],
                tipo=r["tipo"],
                k=k,
                hit=r[_clave_metrica("hit", k)],
                prec=f"{r[_clave_metrica('precision', k)]:.4f}",
                rec=f"{r[_clave_metrica('recall', k)]:.4f}",
                mrr=f"{r['mrr']:.4f}",
                ndcg=f"{r[_clave_metrica('ndcg', k)]:.4f}",
                preview=prev.replace("|", "/").replace("`", "'"),
            )
        )
    lineas.append("")

    fallidas = [
        r
        for r in resultados
        if not r.get("listado_na") and int(r[_clave_metrica("hit", int(r["k_evaluacion"]))]) == 0
    ]
    lineas.extend(["## Apendice: consultas factuales con hit@k = 0", ""])
    if not fallidas:
        lineas.append("(ninguna)")
    else:
        for r in fallidas:
            lineas.append(f"- **{r['qid']}**: {r['consulta']}")
    lineas.append("")

    na_listado = [r for r in resultados if r.get("listado_na")]
    lineas.extend(["## Apendice: consultas agregativas (no aplicables aun)", ""])
    if not na_listado:
        lineas.append("(ninguna)")
    else:
        for r in na_listado:
            lineas.append(
                f"- **{r['qid']}** ({r['tipo']}): pendiente TASK-70 / `listar_estructurado`."
            )
    lineas.append("")
    return lineas


def render_markdown_reporte(
    *,
    config: TipoConfigEval,
    cfg: Configuracion,
    resultados: list[dict[str, Any]],
    agregados: dict[str, float],
    notas_config: list[str],
    versiones_cmd: str,
    commit_git: str,
    golden_sha256: str,
    ruta_golden: Path,
) -> str:
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lineas: list[str] = [
        f"# Evaluacion RAG — {config}",
        "",
        f"- **Entradas golden**: {len(resultados)}",
        "",
        "## Contexto de ejecucion (reproducibilidad)",
        "",
        f"- **Timestamp (UTC)**: {ahora}",
        f"- **Commit (git rev-parse HEAD)**: `{commit_git}`",
        f"- **Golden**: `{ruta_golden}`",
        f"- **Golden (SHA256)**: `{golden_sha256}`",
        *fragmentos_contexto_ejecucion(cfg),
        "",
        "> Re-ejecutar con los mismos valores de entorno y la misma ingesta en Qdrant "
        "para comparar deltas entre tareas (TASK-68 en adelante).",
        "",
        "## Notas de configuracion",
        "",
    ]
    if notas_config:
        for n in notas_config:
            lineas.append(f"- {n}")
    else:
        lineas.append("- (sin notas adicionales)")
    lineas.extend(["", "## Versiones (referencia)", "", "```", versiones_cmd.strip() or "(no disponible)", "```", ""])

    lineas.extend(lineas_tablas_metricas_reporte(resultados, agregados))
    return "\n".join(lineas) + "\n"


def render_markdown_consolidado_todas(
    *,
    bloques: list[tuple[TipoConfigEval, list[dict[str, Any]], dict[str, float], Configuracion]],
    cfg_contexto: Configuracion,
    versiones_cmd: str,
    commit_git: str,
    golden_sha256: str,
    ruta_golden: Path,
) -> str:
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lineas: list[str] = [
        "# Evaluacion RAG — presets baseline, mmr, reranker, combinado (una corrida)",
        "",
        f"- **Entradas golden**: {len(bloques[0][1]) if bloques else 0}",
        "",
        "## Contexto de ejecucion (reproducibilidad)",
        "",
        f"- **Timestamp (UTC)**: {ahora}",
        f"- **Commit (git rev-parse HEAD)**: `{commit_git}`",
        f"- **Golden**: `{ruta_golden}`",
        f"- **Golden (SHA256)**: `{golden_sha256}`",
        *fragmentos_contexto_ejecucion(cfg_contexto),
        "",
        "> Re-ejecutar con los mismos valores de entorno y la misma ingesta en Qdrant "
        "para comparar deltas entre tareas (TASK-68 en adelante).",
        "",
        "## Versiones (referencia)",
        "",
        "```",
        versiones_cmd.strip() or "(no disponible)",
        "```",
        "",
        "## Tabla comparativa (promedios agregados por preset)",
        "",
    ]
    metricas = sorted({m for _, _, agg, _ in bloques for m in agg})
    encabezado = "| metrica | " + " | ".join(p for p, _, _, _ in bloques) + " |"
    sep = "| --- | " + " | ".join("---" for _ in bloques) + " |"
    lineas.extend([encabezado, sep])
    for m in metricas:
        celdas = []
        for preset, _, agg, _ in bloques:
            v = agg.get(m)
            celdas.append(f"{v:.4f}" if v is not None else "—")
        lineas.append("| `" + m + "` | " + " | ".join(celdas) + " |")
    lineas.append("")

    for preset, res, agg, cfg_i in bloques:
        lineas.extend(
            [
                f"## Preset: {preset}",
                "",
                "### Parametros efectivos (override del preset)",
                "",
                *fragmentos_contexto_ejecucion(cfg_i),
                "",
                "### Notas",
                "",
            ]
        )
        notas_cfg = notas_por_config(preset)
        for n in notas_cfg:
            lineas.append(f"- {n}")
        if not notas_cfg:
            lineas.append("- (sin notas adicionales)")
        lineas.append("")
        lineas.extend([f"### Detalle metrico: {preset}", ""])
        lineas.extend(lineas_tablas_metricas_reporte(res, agg))

    return "\n".join(lineas) + "\n"


def filas_csv_desde_resultados(
    preset: str,
    resultados: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filas planas para CSV (UTF-8 sin BOM): una fila por consulta y preset."""
    salida: list[dict[str, Any]] = []
    omitir = {"archivos_por_chunk", "archivos_relevantes", "notas"}
    for r in resultados:
        fila: dict[str, Any] = {
            "preset": preset,
            "query_id": r["qid"],
            "tipo": r["tipo"],
            "k_evaluacion": r["k_evaluacion"],
        }
        for clave, val in r.items():
            if clave in omitir or clave in fila:
                continue
            if isinstance(val, (list, dict)):
                continue
            fila[clave] = val
        salida.append(fila)
    return salida


def escribir_csv_metricas(ruta: Path, filas: list[dict[str, Any]]) -> None:
    """Escribe CSV UTF-8 sin BOM (compatible con pandas / Excel con importacion UTF-8)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not filas:
        ruta.write_text("", encoding="utf-8")
        return
    claves = sorted({k for fila in filas for k in fila})
    preferidas = ["preset", "query_id", "tipo", "k_evaluacion"]
    orden = [c for c in preferidas if c in claves]
    orden.extend(c for c in claves if c not in orden)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=orden, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({k: ("" if fila.get(k) is None else fila[k]) for k in orden})


def _ejecutar_un_preset(
    nombre: TipoConfigEval,
    entradas: list[dict[str, Any]],
    collection_cli: str | None,
) -> tuple[list[dict[str, Any]], dict[str, float], Configuracion]:
    cfg = ajustar_configuracion_eval(nombre, collection_cli)
    vector_store = obtener_vector_store(cfg)
    embeddings = obtener_embeddings(cfg)
    rec = RecuperadorDenso.desde_configuracion(
        cfg, vector_store=vector_store, embeddings=embeddings
    )
    resultados: list[dict[str, Any]] = []
    for fila in entradas:
        if fila["tipo"] == "factual":
            resultados.append(ejecutar_fila_factual(rec, fila))
        else:
            resultados.append(ejecutar_fila_listado_conteo(fila))
    return resultados, agregar_metricas_factual(resultados), cfg


def escribir_results_jsonl(ruta: Path, filas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def resolver_ruta_comparacion(raiz: Path, p: Path) -> Path:
    """Acepta ``*.results.jsonl`` o ``*.md`` (usa el JSONL hermano con el mismo stem)."""
    r = p if p.is_absolute() else (raiz / p).resolve()
    if r.suffix.lower() == ".md":
        candidato = r.with_suffix(".results.jsonl")
        if candidato.is_file():
            return candidato
        raise FileNotFoundError(
            f"No se encontro resultados JSONL junto al reporte: {candidato}"
        )
    return r


def leer_results_jsonl(ruta: Path) -> list[dict[str, Any]]:
    return cargar_golden_jsonl(ruta)


def _promedios_desde_resultados(filas: list[dict[str, Any]]) -> dict[str, float]:
    return agregar_metricas_factual(filas)


def comparar_resultados_jsonl(
    ruta_a: Path,
    ruta_b: Path,
    *,
    umbral_mrr: float = 0.0,
    umbral_recall_k: float = 0.0,
    umbral_ndcg_k: float = 0.0,
    umbral_regresion_mrr: float | None = None,
) -> tuple[str, bool]:
    """
    Compara promedios agregados (B - A). Regresion si el delta cae por debajo del umbral
    correspondiente (umbrales tipicamente 0.0 o negativos pequenos para tolerar ruido).
    """
    umbral_mrr_efectivo = -float(umbral_regresion_mrr) if umbral_regresion_mrr is not None else umbral_mrr

    a = leer_results_jsonl(ruta_a)
    b = leer_results_jsonl(ruta_b)
    por_qid_a = {str(x["qid"]): x for x in a}
    por_qid_b = {str(x["qid"]): x for x in b}
    qids = sorted(set(por_qid_a) & set(por_qid_b))
    prom_a = _promedios_desde_resultados(a)
    prom_b = _promedios_desde_resultados(b)

    lineas: list[str] = [
        "# Comparacion de evaluaciones RAG",
        "",
        f"- **A**: `{ruta_a}`",
        f"- **B**: `{ruta_b}`",
        f"- **Umbral MRR (delta B-A; falla si delta < umbral)**: {umbral_mrr_efectivo:.4f}",
        f"- **Umbral recall@k (cada metrica recall@N)**: {umbral_recall_k:.4f}",
        f"- **Umbral nDCG@k (cada metrica ndcg@N)**: {umbral_ndcg_k:.4f}",
        "",
        "## Delta agregado (B - A)",
        "",
        "| metrica | A | B | delta |",
        "| --- | --- | --- | --- |",
    ]
    regresion_critica = False
    motivos: list[str] = []
    todas = sorted(set(prom_a) | set(prom_b))
    for m in todas:
        va = prom_a.get(m)
        vb = prom_b.get(m)
        if va is None or vb is None:
            continue
        delta = vb - va
        lineas.append(f"| `{m}` | {va:.4f} | {vb:.4f} | {delta:+.4f} |")
        if m == "mrr" and delta < umbral_mrr_efectivo:
            regresion_critica = True
            motivos.append(f"MRR: delta {delta:+.4f} < umbral {umbral_mrr_efectivo:.4f}")
        elif m.startswith("recall@") and delta < umbral_recall_k:
            regresion_critica = True
            motivos.append(f"{m}: delta {delta:+.4f} < umbral recall {umbral_recall_k:.4f}")
        elif m.startswith("ndcg@") and delta < umbral_ndcg_k:
            regresion_critica = True
            motivos.append(f"{m}: delta {delta:+.4f} < umbral ndcg {umbral_ndcg_k:.4f}")
    lineas.append("")

    if motivos:
        lineas.extend(["## Regresiones detectadas", ""])
        for m in motivos:
            lineas.append(f"- {m}")
        lineas.append("")

    lineas.extend(["## Delta por consulta (solo factual con metricas en ambas)", ""])
    for qid in qids:
        fa, fb = por_qid_a[qid], por_qid_b[qid]
        if fa.get("listado_na") or fb.get("listado_na"):
            continue
        cambios: list[str] = []
        k = int(fa["k_evaluacion"])
        if int(fa["k_evaluacion"]) != int(fb["k_evaluacion"]):
            continue
        for nombre in ("hit", "precision", "recall", "mrr", "ndcg"):
            if nombre == "mrr":
                ca, cb = fa.get("mrr"), fb.get("mrr")
            else:
                ck = _clave_metrica(nombre, k)
                ca, cb = fa.get(ck), fb.get(ck)
            if ca is None or cb is None:
                continue
            if float(ca) != float(cb):
                cambios.append(f"{nombre}: {ca} -> {cb}")
        if cambios:
            lineas.append(f"- **{qid}**: " + "; ".join(cambios))
    lineas.append("")
    texto = "\n".join(lineas) + "\n"
    return texto, regresion_critica


def capturar_versiones_pip() -> str:
    try:
        proc = subprocess.run(
            ["uv", "pip", "list"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=encontrar_raiz_repo(),
            check=False,
        )
        salida = proc.stdout or ""
        filtrada = [ln for ln in salida.splitlines() if re.search(r"llama-index|qdrant|sentence-transformers", ln, re.I)]
        return "\n".join(filtrada[:40]) if filtrada else salida[:2000]
    except OSError:
        return ""


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz = encontrar_raiz_repo()
    golden_def = raiz / "data" / "eval" / "golden_set_rag.jsonl"
    p = argparse.ArgumentParser(description="Evaluacion cuantitativa RAG (golden set + metricas).")
    p.add_argument("--golden", type=Path, default=golden_def, help="Ruta al golden set JSONL.")
    p.add_argument(
        "--config",
        choices=[
            "baseline",
            "limpio",
            "markdown",
            "mmr",
            "reranker",
            "combinado",
            "adaptativo",
            "todas",
        ],
        default="baseline",
        help="Etiqueta de experimento; 'todas' ejecuta baseline, mmr, reranker y combinado en serie.",
    )
    p.add_argument("--collection", type=str, default=None, help="Sobrescribe QDRANT_COLLECTION.")
    p.add_argument("--k", type=int, default=None, help="Ignorado: se usa k_evaluacion por fila del golden.")
    p.add_argument("--reporte-out", type=Path, default=None, help="Ruta del reporte Markdown de salida.")
    p.add_argument(
        "--fail-if-empty",
        action="store_true",
        help="Sale con codigo 1 si la coleccion Qdrant no existe o tiene 0 puntos (no crea coleccion).",
    )
    p.add_argument(
        "--solo-validar-golden",
        action="store_true",
        help="Valida el golden contra el schema y termina (sin red ni Qdrant).",
    )
    p.add_argument(
        "--comparar",
        nargs=2,
        type=Path,
        metavar=("A", "B"),
        help="Dos archivos .results.jsonl (o .md del mismo stem) para comparar deltas.",
    )
    p.add_argument(
        "--umbral-mrr",
        type=float,
        default=0.0,
        help="Comparar: falla si delta MRR (B-A) es menor que este valor (default 0.0 = sin caida).",
    )
    p.add_argument(
        "--umbral-recall-k",
        type=float,
        default=0.0,
        help="Comparar: falla si el delta de alguna metrica recall@N cae por debajo de este valor.",
    )
    p.add_argument(
        "--umbral-ndcg-k",
        type=float,
        default=0.0,
        help="Comparar: falla si el delta de alguna metrica ndcg@N cae por debajo de este valor.",
    )
    p.add_argument(
        "--umbral-regresion-mrr",
        type=float,
        default=None,
        help="Obsoleto: si se define, equivale a --umbral-mrr=-VALOR (sobrescribe --umbral-mrr solo para MRR).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    raiz = encontrar_raiz_repo()

    if args.comparar:
        ruta_a = resolver_ruta_comparacion(raiz, args.comparar[0])
        ruta_b = resolver_ruta_comparacion(raiz, args.comparar[1])
        umbral_mrr = (
            -float(args.umbral_regresion_mrr)
            if args.umbral_regresion_mrr is not None
            else float(args.umbral_mrr)
        )
        texto, regresion = comparar_resultados_jsonl(
            ruta_a,
            ruta_b,
            umbral_mrr=umbral_mrr,
            umbral_recall_k=float(args.umbral_recall_k),
            umbral_ndcg_k=float(args.umbral_ndcg_k),
            umbral_regresion_mrr=None,
        )
        print(texto)
        return 1 if regresion else 0

    ruta_golden = args.golden if args.golden.is_absolute() else (raiz / args.golden).resolve()
    schema = cargar_schema(raiz)
    entradas = cargar_golden_jsonl(ruta_golden)
    validar_golden_completo(entradas, schema)
    if args.solo_validar_golden:
        print(f"Golden validado: {len(entradas)} entradas OK ({ruta_golden})")
        return 0

    reiniciar_cliente_qdrant()
    cfg_base = ajustar_configuracion_eval("baseline", args.collection)
    if args.fail_if_empty:
        cliente = obtener_qdrant_client(cfg_base)
        nombre_col = cfg_base.qdrant_collection
        cnt = contar_puntos_en_coleccion(cliente, nombre_col)
        if cnt is None:
            logger.error(
                "La coleccion Qdrant %r no existe. Ejecuta scripts/indexar_corpus_qdrant.py antes de evaluar.",
                nombre_col,
            )
            return 1
        if cnt == 0:
            logger.error(
                "La coleccion Qdrant %r esta vacia (count=0). Ejecuta scripts/indexar_corpus_qdrant.py.",
                nombre_col,
            )
            return 1

    commit_git = obtener_commit_git(raiz)
    golden_sha = sha256_archivo(ruta_golden)
    versiones = capturar_versiones_pip()

    if args.config == "todas":
        bloques: list[tuple[TipoConfigEval, list[dict[str, Any]], dict[str, float], Configuracion]] = []
        filas_csv: list[dict[str, Any]] = []
        filas_jsonl: list[dict[str, Any]] = []
        for preset in PRESETS_EVAL_TODAS:
            res, agg, cfg_i = _ejecutar_un_preset(preset, entradas, args.collection)
            bloques.append((preset, res, agg, cfg_i))
            filas_csv.extend(filas_csv_desde_resultados(preset, res))
            for fila in res:
                fila_out = dict(fila)
                fila_out["preset"] = preset
                filas_jsonl.append(fila_out)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dir_rep = raiz / "data" / "eval" / "reportes"
        if args.reporte_out:
            ruta_md = (
                args.reporte_out
                if args.reporte_out.is_absolute()
                else (raiz / args.reporte_out).resolve()
            )
        else:
            ruta_md = dir_rep / f"eval_rag_{stamp}.md"
        ruta_csv = ruta_md.with_suffix(".csv")
        ruta_jsonl = ruta_md.with_suffix(".results.jsonl")

        cfg_ctx = bloques[0][3] if bloques else cfg_base
        md = render_markdown_consolidado_todas(
            bloques=bloques,
            cfg_contexto=cfg_ctx,
            versiones_cmd=versiones,
            commit_git=commit_git,
            golden_sha256=golden_sha,
            ruta_golden=ruta_golden,
        )
        escribir_results_jsonl(ruta_jsonl, filas_jsonl)
        escribir_csv_metricas(ruta_csv, filas_csv)
        ruta_md.parent.mkdir(parents=True, exist_ok=True)
        ruta_md.write_text(md, encoding="utf-8")
        print(f"Reporte Markdown: {ruta_md}")
        print(f"CSV metricas: {ruta_csv}")
        print(f"Resultados JSONL: {ruta_jsonl}")
        return 0

    etiqueta = cast(TipoConfigEval, args.config)
    resultados, agregados, cfg = _ejecutar_un_preset(etiqueta, entradas, args.collection)
    md = render_markdown_reporte(
        config=etiqueta,
        cfg=cfg,
        resultados=resultados,
        agregados=agregados,
        notas_config=notas_por_config(etiqueta),
        versiones_cmd=versiones,
        commit_git=commit_git,
        golden_sha256=golden_sha,
        ruta_golden=ruta_golden,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if args.reporte_out:
        ruta_md = args.reporte_out if args.reporte_out.is_absolute() else (raiz / args.reporte_out).resolve()
    else:
        ruta_md = raiz / "data" / "eval" / "reportes" / f"eval-{stamp}-{args.config}.md"
    ruta_jsonl = ruta_md.with_suffix(".results.jsonl")

    escribir_results_jsonl(ruta_jsonl, resultados)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)
    ruta_md.write_text(md, encoding="utf-8")
    print(f"Reporte Markdown: {ruta_md}")
    print(f"Resultados JSONL: {ruta_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
