"""
Cuenta puntos en Qdrant con payload ``tipo_pagina == "sede"`` y muestra rutas ``archivo``.

Sirve para verificar en despliegue que la ingesta incluyo paginas ``sedes-*.md``.
Ejecucion desde la raiz del repositorio::

    uv run python scripts/verificar_sedes_en_qdrant.py
"""

from __future__ import annotations

import argparse
from collections import Counter

from src.api.configuracion import obtener_configuracion
from src.rag.runtime.qdrant_store import obtener_qdrant_client, reiniciar_cliente_qdrant
from src.rag.runtime.recuperador_listados import RecuperadorListados


def main() -> int:
    p = argparse.ArgumentParser(description="Verifica puntos Qdrant tipo_pagina=sede.")
    p.add_argument(
        "--limite-muestra",
        type=int,
        default=30,
        metavar="N",
        help="Maximo de rutas ``archivo`` distintas a listar (defecto: 30).",
    )
    args = p.parse_args()

    reiniciar_cliente_qdrant()
    obtener_configuracion.cache_clear()
    cfg = obtener_configuracion()
    rec = RecuperadorListados(
        cliente=obtener_qdrant_client(cfg),
        nombre_coleccion=cfg.qdrant_collection,
    )
    res = rec.listar(
        {"tipo_pagina": "sede"}, limite=max(1, min(args.limite_muestra, 500))
    )
    archivos = Counter(
        (it.archivo or "").strip() for it in res.items if (it.archivo or "").strip()
    )
    print(f"Coleccion: {cfg.qdrant_collection}")
    print(
        f"Total deduplicado (scroll listar_estructurado, tipo_pagina=sede): {res.conteo}"
    )
    if res.muestra_truncada:
        print(
            f"(Muestra truncada a {len(res.items)} filas; aumente --limite-muestra para ver mas.)"
        )
    for arch, k in sorted(archivos.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k:4d}  {arch}")
    if res.conteo == 0:
        print(
            "Aviso: cero puntos. Revise ingesta (scripts/indexar_corpus_qdrant.py), "
            "QDRANT_COLLECTION y que existan Markdown sedes-*.md en el directorio indexado."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
