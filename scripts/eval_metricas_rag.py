"""
Evaluacion cuantitativa del RAG contra un golden set (TASK-72).

Validacion sin red ni Qdrant:

    uv run python -m scripts.eval_metricas_rag --solo-validar-golden

Ejecucion completa (Qdrant + embeddings segun .env):

    uv run python -m scripts.eval_metricas_rag --golden data/eval/golden_set_rag.jsonl --config baseline

Comparar dos corridas (archivos ``*.results.jsonl``):

    uv run python -m scripts.eval_metricas_rag --comparar data/eval/reportes/a.results.jsonl data/eval/reportes/b.results.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft7Validator

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.embeddings import obtener_embeddings
from src.rag.metricas_eval import (
    hit_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from src.rag.qdrant_store import obtener_vector_store, reiniciar_cliente_qdrant
from src.rag.recuperador_denso import RecuperadorDenso

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
    return [
        f"- **Coleccion Qdrant**: `{cfg.qdrant_collection}`",
        f"- **Proveedor embeddings**: `{cfg.embedding_provider}` / modelo `{cfg.embedding_model}` / dims `{cfg.embedding_dims}`",
        f"- **RAG_SCORE_MINIMO** (evaluacion): `{cfg.rag_score_minimo}`",
        f"- **RAG_TOP_K** (constructor recuperador): `{cfg.rag_top_k}`",
        f"- **RAG_TOP_K_INICIAL**: `{cfg.rag_top_k_inicial}`",
        f"- **RAG_MMR_HABILITADO** / **RAG_MMR_LAMBDA**: `{cfg.rag_mmr_habilitado}` / `{cfg.rag_mmr_lambda}`",
        f"- **RAG_RERANKER_HABILITADO** / modelo / top_n: `{cfg.rag_reranker_habilitado}` / "
        f"`{cfg.rag_reranker_modelo}` / `{cfg.rag_reranker_top_n_entrada}`",
    ]


def render_markdown_reporte(
    *,
    config: TipoConfigEval,
    cfg: Configuracion,
    resultados: list[dict[str, Any]],
    agregados: dict[str, float],
    notas_config: list[str],
    versiones_cmd: str,
) -> str:
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lineas: list[str] = [
        f"# Evaluacion RAG — {config}",
        "",
        f"- **Timestamp (UTC)**: {ahora}",
        f"- **Entradas golden**: {len(resultados)}",
        "",
        "## Contexto de ejecucion (reproducibilidad)",
        "",
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

    lineas.extend(["## Tabla agregada (promedio, solo factual)", "", "| metrica | valor |", "| --- | --- |"])
    if not agregados:
        lineas.append("| (sin datos factuales) | — |")
    else:
        for clave in sorted(agregados):
            lineas.append(f"| `{clave}` | {agregados[clave]:.4f} |")
    lineas.append("")

    lineas.extend(["## Tabla por consulta", "", "| qid | tipo | k | hit | precision | recall | mrr | ndcg | preview top archivos |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
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
    return "\n".join(lineas) + "\n"


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
    umbral_regresion_mrr: float,
) -> tuple[str, bool]:
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
        f"- **Umbral regresion MRR (B - A)**: {-umbral_regresion_mrr:.4f}",
        "",
        "## Delta agregado (B - A)",
        "",
        "| metrica | A | B | delta |",
        "| --- | --- | --- | --- |",
    ]
    regresion_critica = False
    todas = sorted(set(prom_a) | set(prom_b))
    for m in todas:
        va = prom_a.get(m)
        vb = prom_b.get(m)
        if va is None or vb is None:
            continue
        delta = vb - va
        lineas.append(f"| `{m}` | {va:.4f} | {vb:.4f} | {delta:+.4f} |")
        if m == "mrr" and delta < -umbral_regresion_mrr:
            regresion_critica = True
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
        choices=["baseline", "limpio", "markdown", "mmr", "reranker", "combinado", "adaptativo"],
        default="baseline",
        help="Etiqueta de experimento (afecta coleccion por defecto y notas).",
    )
    p.add_argument("--collection", type=str, default=None, help="Sobrescribe QDRANT_COLLECTION.")
    p.add_argument("--k", type=int, default=None, help="Ignorado: se usa k_evaluacion por fila del golden.")
    p.add_argument("--reporte-out", type=Path, default=None, help="Ruta del reporte Markdown de salida.")
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
        "--umbral-regresion-mrr",
        type=float,
        default=0.05,
        help="Si MRR medio B cae mas que este valor respecto a A, exit code 1.",
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
        texto, regresion = comparar_resultados_jsonl(
            ruta_a,
            ruta_b,
            umbral_regresion_mrr=args.umbral_regresion_mrr,
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
    cfg = ajustar_configuracion_eval(args.config, args.collection)
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

    agregados = agregar_metricas_factual(resultados)
    versiones = capturar_versiones_pip()
    md = render_markdown_reporte(
        config=args.config,
        cfg=cfg,
        resultados=resultados,
        agregados=agregados,
        notas_config=notas_por_config(args.config),
        versiones_cmd=versiones,
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
