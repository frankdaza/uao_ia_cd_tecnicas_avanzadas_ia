"""
Ejecuta consultas de ejemplo contra RecuperadorDenso para revisar scores y fuentes.

Modo sin Qdrant (validacion de JSON):

    uv run python -m scripts.eval_recuperacion_consultas --solo-validar-json

Modo completo (requiere Qdrant accesible y embeddings configurados en .env):

    uv run python -m scripts.eval_recuperacion_consultas
    uv run python -m scripts.eval_recuperacion_consultas --collection mi_coleccion_ab
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from src.api.configuracion import obtener_configuracion
from src.rag.embeddings import obtener_embeddings
from src.rag.qdrant_store import obtener_vector_store, reiniciar_cliente_qdrant
from src.rag.recuperador_denso import RecuperadorDenso

logger = logging.getLogger(__name__)


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
        cfg = cfg_base.model_copy(update={"qdrant_collection": args.collection})
    else:
        cfg = cfg_base

    vector_store = obtener_vector_store(cfg)
    embeddings = obtener_embeddings(cfg)
    rec = RecuperadorDenso(
        vector_store=vector_store,
        embeddings=embeddings,
        top_k=cfg.rag_top_k,
        score_minimo=cfg.rag_score_minimo,
    )

    print("")
    print(
        f"Coleccion: {cfg.qdrant_collection} | top_k={cfg.rag_top_k} | "
        f"score_minimo={cfg.rag_score_minimo}"
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
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
