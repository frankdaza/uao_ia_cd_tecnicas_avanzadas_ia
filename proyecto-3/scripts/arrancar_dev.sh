#!/usr/bin/env bash
# Arranque desarrollo proyecto-3 (OpenFang + Hand TAAM)
# Uso: ./scripts/arrancar_dev.sh
# Requiere: .env con OPENAI_API_KEY y TELEGRAM_BOT_TOKEN

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

export OPENFANG_HOME="${OPENFANG_HOME:-./openfang/data}"

echo "=== proyecto-3 — Ruta B OpenFang ==="
echo "OPENFANG_HOME=${OPENFANG_HOME}"
echo ""
echo "Pasos manuales (implementacion futura):"
echo "  1. openfang start          # kernel + dashboard :4200"
echo "  2. uv run python ingesta/indexar_corpus_openfang.py"
echo "  3. openfang hand activate taam_lili_hand"
echo "  4. Probar Telegram con el bot dedicado (token distinto a proyecto-2)"
echo ""
echo "TODO: automatizar cuando openfang.toml este descomentado y validado."
