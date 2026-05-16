"""
Ejecuta consultas de ejemplo contra RecuperadorDenso para revisar scores y fuentes.

Modo sin Qdrant (validacion de JSON):

    uv run python -m scripts.eval_recuperacion_consultas --solo-validar-json

Modo completo (requiere Qdrant accesible y embeddings configurados en .env):

    uv run python -m scripts.eval_recuperacion_consultas
    uv run python -m scripts.eval_recuperacion_consultas --collection mi_coleccion_ab

Comparar presets TASK-71 (misma corrida, bloques consecutivos en consola):

    uv run python -m scripts.eval_recuperacion_consultas --config todas
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.runtime.embeddings import obtener_embeddings
from src.rag.runtime.qdrant_store import obtener_vector_store, reiniciar_cliente_qdrant
from src.rag.runtime.recuperador_denso import RecuperadorDenso

logger = logging.getLogger(__name__)


def _overrides_preset(nombre: str) -> dict[str, object]:
    if nombre == "baseline":
        return {"rag_mmr_habilitado": False, "rag_reranker_habilitado": False}
    if nombre == "mmr":
        return {"rag_mmr_habilitado": True, "rag_reranker_habilitado": False}
    if nombre == "reranker":
        return {"rag_mmr_habilitado": False, "rag_reranker_habilitado": True}
    if nombre == "combinado":
        return {"rag_mmr_habilitado": True, "rag_reranker_habilitado": True}
    raise ValueError(f"preset desconocido: {nombre!r}")


def encontrar_raiz_repo(inicio: Path | None = None) -> Path:
    p = (inicio or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "pyproject.toml").is_file():
            return cand
    return p


def cargar_consultas(ruta: Path) -> list[str]:
    data = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El JSON raiz debe ser un objeto")
    raw = data.get("consultas")
    if not isinstance(raw, list) or not raw:
        raise ValueError("Clave 'consultas': debe ser una lista no vacia")
    salida: list[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"consultas[{i}]: cada elemento debe ser un string no vacio")
        salida.append(item.strip())
    return salida


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz = encontrar_raiz_repo()
    json_def = raiz / "config" / "evaluacion_rag_consultas_ejemplo.json"
    p = argparse.ArgumentParser(
        description=(
            "Valida el JSON de consultas de evaluacion RAG y, opcionalmente, "
            "ejecuta RecuperadorDenso contra Qdrant."
        ),
    )
    p.add_argument(
        "--consultas-json",
        type=Path,
        default=json_def,
        help="Ruta al JSON con clave 'consultas' (lista de strings).",
    )
    p.add_argument(
        "--solo-validar-json",
        action="store_true",
        help="Solo valida el JSON y termina (no requiere Qdrant ni claves).",
    )
    p.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Sobrescribe QDRANT_COLLECTION para pruebas A/B.",
    )
    p.add_argument(
        "--config",
        choices=["baseline", "mmr", "reranker", "combinado", "todas"],
        default="baseline",
        help=(
            "Preset de flags MMR/reranker (TASK-71). ``todas`` imprime los cuatro "
            "presets en secuencia para comparacion manual."
        ),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activa logs de depuracion en stderr.",
    )
    return p.parse_args(argv)


def _imprimir_bloque_consultas(
    etiqueta: str,
    cfg: Configuracion,
    consultas: list[str],
) -> None:
    vector_store = obtener_vector_store(cfg)
    embeddings = obtener_embeddings(cfg)
    rec = RecuperadorDenso.desde_configuracion(cfg, vector_store=vector_store, embeddings=embeddings)
    print("")
    print("=" * 72)
    print(f"CONFIG: {etiqueta}")
    print("=" * 72)
    print(
        f"Coleccion: {cfg.qdrant_collection} | top_k={cfg.rag_top_k} | "
        f"score_minimo={cfg.rag_score_minimo} | top_k_inicial={cfg.rag_top_k_inicial}"
    )
    print(
        f"MMR={cfg.rag_mmr_habilitado} lambda={cfg.rag_mmr_lambda} | "
        f"reranker={cfg.rag_reranker_habilitado} top_n={cfg.rag_reranker_top_n_entrada} "
        f"modelo={cfg.rag_reranker_modelo!r}"
    )
    print("")
    for q in consultas:
        salida = rec.consultar(q)
        print("---")
        print(f"Consulta: {q}")
        if not salida.fuentes:
            print("  (sin fuentes por encima del umbral)")
            print(f"  contexto: {salida.respuesta_contexto[:200]}...")
            continue
        for f in salida.fuentes:
            print(f"  score={f.score:.4f} archivo={f.archivo} url={f.source_url!r}")


def main(argv: list[str] | None = None) -> int:
    args = parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    raiz = encontrar_raiz_repo()
    ruta_json = args.consultas_json
    if not ruta_json.is_absolute():
        ruta_json = (raiz / ruta_json).resolve()

    consultas = cargar_consultas(ruta_json)
    print(f"Consultas cargadas: {len(consultas)} desde {ruta_json}")

    if args.solo_validar_json:
        print("Validacion JSON: OK")
        return 0

    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    cfg_base = obtener_configuracion()
    if args.collection:
        cfg_base = cfg_base.model_copy(update={"qdrant_collection": args.collection})

    presets: list[str]
    if args.config == "todas":
        presets = ["baseline", "mmr", "reranker", "combinado"]
    else:
        presets = [args.config]

    for nombre in presets:
        extra = _overrides_preset(nombre)
        cfg_run = cfg_base.model_copy(update=extra)
        _imprimir_bloque_consultas(nombre, cfg_run, consultas)

    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
