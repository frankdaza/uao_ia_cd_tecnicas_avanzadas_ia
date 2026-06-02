#!/usr/bin/env bash
set -euo pipefail

_normalizar_bool() {
  case "${1,,}" in true|1|yes|on) return 0 ;; *) return 1 ;; esac
}

echo "[entrypoint] Aplicando migraciones Alembic (TAAM)..."
uv run alembic upgrade head

if _normalizar_bool "${TAAM_SEMBRAR_DEMO_HABILITADO:-false}"; then
  echo "[entrypoint] Sembrando demo TAAM..."
  args=()
  if _normalizar_bool "${TAAM_SEMBRAR_DEMO_CON_INGESTA:-true}"; then
    args+=(--con-ingesta)
  fi
  uv run python -m scripts.sembrar_demo_taam "${args[@]}"
fi

echo "[entrypoint] Iniciando uvicorn en 0.0.0.0:8001..."
exec uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8001
