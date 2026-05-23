#!/usr/bin/env bash
# Arranque desarrollo proyecto-3 (OpenFang + agente TAAM + Hand)
# Uso: ./scripts/arrancar_dev.sh
# Requiere: .env con OPENAI_API_KEY; TELEGRAM_BOT_TOKEN para bridge en vivo

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

export PATH="${HOME}/.openfang/bin:${PATH}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

export OPENFANG_HOME="${OPENFANG_HOME:-./openfang/data}"
if [[ "${OPENFANG_HOME}" != /* ]]; then
  OPENFANG_HOME="$(cd "${ROOT_DIR}" && cd "${OPENFANG_HOME}" && pwd)"
  export OPENFANG_HOME
fi

echo "=== proyecto-3 — Ruta B OpenFang ==="
echo "OPENFANG_HOME=${OPENFANG_HOME}"
echo ""

"${SCRIPT_DIR}/validar_openfang_config.sh"

if ! command -v openfang >/dev/null 2>&1; then
  echo "error: instala OpenFang con ./scripts/instalar_openfang.sh" >&2
  exit 1
fi

if openfang status 2>/dev/null | grep -qi "running"; then
  echo "Daemon OpenFang ya en ejecucion."
else
  echo "Iniciando openfang start (dashboard http://127.0.0.1:4200)..."
  openfang start
fi

AGENT_MANIFEST="${ROOT_DIR}/openfang/agents/bot_lili_taam/agent.toml"
HAND_DIR="${ROOT_DIR}/openfang/hands/taam_lili_hand"

echo ""
echo "Sincronizando prompt system.md -> agent.toml..."
uv run python "${SCRIPT_DIR}/sincronizar_prompt_agente.py"

echo ""
echo "Registrando agente bot_lili_taam..."
openfang agent spawn "${AGENT_MANIFEST}" || true

echo ""
echo "Instalando Hand taam_lili_hand (si aun no esta)..."
openfang hand install "${HAND_DIR}" 2>/dev/null || true

echo ""
echo "=== Listo ==="
echo "  Dashboard:  http://127.0.0.1:4200"
echo "  Salud API:  curl -s http://127.0.0.1:4200/api/health"
echo "  Ingesta:    uv run python ingesta/indexar_corpus_openfang.py"
echo "  Hand cron:  openfang hand activate taam_lili_hand"
echo "  Telegram:   bot dedicado (token distinto a proyecto-2)"
