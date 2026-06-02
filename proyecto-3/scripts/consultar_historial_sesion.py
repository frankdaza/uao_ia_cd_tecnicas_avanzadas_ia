#!/usr/bin/env python3
"""Consulta historial JSONL por session_id (UC4 — alternativa a jq)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.configuracion import obtener_configuracion  # noqa: E402
from src.openfang.historial_jsonl import filtrar_por_session_id  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Imprime eventos JSONL de una sesion (NDJSON en stdout)"
    )
    parser.add_argument(
        "--session-id",
        required=True,
        help='Ej. telegram:900001',
    )
    parser.add_argument(
        "--incluir-audit",
        action="store_true",
        help="Incluir archivos audit/hand_*.jsonl",
    )
    args = parser.parse_args()

    cfg = obtener_configuracion()
    raiz = cfg.openfang_home_absoluto()
    if not raiz.is_dir():
        print(f"openfang_home_inexistente: {raiz}", file=sys.stderr)
        return 2

    registros = filtrar_por_session_id(
        raiz,
        args.session_id,
        incluir_audit=args.incluir_audit,
    )
    if not registros:
        print(f"sin_registros: session_id={args.session_id!r} bajo {raiz}", file=sys.stderr)
        return 1

    for registro in registros:
        print(json.dumps(registro, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
