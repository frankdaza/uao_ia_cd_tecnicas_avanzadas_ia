#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Aplicando migraciones Alembic (TAAM)..."
uv run alembic upgrade head

echo "[entrypoint] Iniciando uvicorn en 0.0.0.0:8001..."
exec uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8001
