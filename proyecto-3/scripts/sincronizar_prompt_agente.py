#!/usr/bin/env python3
"""Sincroniza system.md -> agent.toml (system_prompt de bot_lili_taam)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.prompts.validar import (  # noqa: E402
    sincronizar_agent_toml_desde_system_md,
    validar_prompt_sistema,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincronizar prompt Bot Lili a agent.toml")
    parser.add_argument(
        "--solo-verificar",
        action="store_true",
        help="No escribe agent.toml; solo valida system.md",
    )
    args = parser.parse_args()
    prompt, agent_toml = sincronizar_agent_toml_desde_system_md(
        ROOT,
        escribir=not args.solo_verificar,
    )
    faltantes = validar_prompt_sistema(prompt)
    if faltantes:
        print("error: prompt incompleto, faltan:", ", ".join(faltantes), file=sys.stderr)
        return 1
    if args.solo_verificar:
        print(f"OK: system.md valido ({len(prompt)} caracteres)")
    else:
        print(f"OK: sincronizado -> {agent_toml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
