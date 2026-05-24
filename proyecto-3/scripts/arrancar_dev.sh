#!/usr/bin/env bash
# Arranque desarrollo end-to-end proyecto-3 (OpenFang + ingesta + Hand + Telegram).
# Uso: ./scripts/arrancar_dev.sh [--sin-telegram]
# Requiere: .env con OPENAI_API_KEY; TELEGRAM_BOT_TOKEN si no usas --sin-telegram

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SIN_TELEGRAM=0
INICIAMOS_DAEMON=0
OF_PID=""

mostrar_ayuda() {
  cat <<'EOF'
Uso: ./scripts/arrancar_dev.sh [opciones]

Arranque local unificado: valida .env, inicia OpenFang (si hace falta),
healthcheck, sincroniza prompt, registra agente, instala/activa Hand,
ingesta corpus y verifica el bot Telegram.

Opciones:
  --sin-telegram   Omite verificar_telegram_bot.sh (getMe)
  -h, --help       Muestra esta ayuda

Requisitos: .env (cp .env.example .env), OPENAI_API_KEY, openfang en PATH, uv sync.
EOF
}

limpiar() {
  if [[ "${INICIAMOS_DAEMON}" -eq 1 ]]; then
    echo ""
    echo "Interrupcion: deteniendo daemon OpenFang iniciado por este script..."
    if [[ -n "${OF_PID}" ]] && kill -0 "${OF_PID}" 2>/dev/null; then
      kill "${OF_PID}" 2>/dev/null || true
    fi
    openfang stop 2>/dev/null || true
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sin-telegram)
      SIN_TELEGRAM=1
      shift
      ;;
    -h|--help)
      mostrar_ayuda
      exit 0
      ;;
    *)
      echo "error: opcion desconocida: $1 (usa --help)" >&2
      exit 1
      ;;
  esac
done

trap limpiar INT TERM

cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "error: falta .env (copia .env.example a .env y completa las claves)." >&2
  exit 1
fi

export PATH="${HOME}/.openfang/bin:${PATH}"

# shellcheck disable=SC1091
set -a && source .env && set +a

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "error: OPENAI_API_KEY no esta definida en .env." >&2
  exit 1
fi

export OPENFANG_HOME="${OPENFANG_HOME:-./openfang/data}"
if [[ "${OPENFANG_HOME}" != /* ]]; then
  OPENFANG_HOME="$(cd "${ROOT_DIR}" && cd "${OPENFANG_HOME}" && pwd)"
  export OPENFANG_HOME
fi

API_BASE="${OPENFANG_API_URL:-http://127.0.0.1:4200}"
HEALTH_URL="${API_BASE%/}/api/health"

echo "=== proyecto-3 — Ruta B OpenFang (arranque dev) ==="
echo "OPENFANG_HOME=${OPENFANG_HOME}"
echo ""

"${SCRIPT_DIR}/validar_openfang_config.sh"

if ! command -v openfang >/dev/null 2>&1; then
  echo "error: instala OpenFang con ./scripts/instalar_openfang.sh" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv no esta en PATH (ejecuta uv sync en proyecto-3/)" >&2
  exit 1
fi

if openfang status 2>/dev/null | grep -qi "running"; then
  echo "Daemon OpenFang ya en ejecucion."
else
  echo "Iniciando openfang start (dashboard ${API_BASE})..."
  openfang start &
  OF_PID=$!
  INICIAMOS_DAEMON=1

  listo=0
  for _ in $(seq 1 30); do
    if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
      listo=1
      break
    fi
    sleep 1
  done

  if [[ "${listo}" -ne 1 ]]; then
    echo "error: healthcheck fallo tras 30s (${HEALTH_URL})" >&2
    limpiar
    exit 1
  fi
  echo "Healthcheck OK: ${HEALTH_URL}"
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
echo "Ingesta corpus -> memoria OpenFang (--permitir-db-en-vivo)..."
uv run python ingesta/indexar_corpus_openfang.py --permitir-db-en-vivo

echo ""
echo "Activando Hand taam_lili_hand (ticks cada 30s en demo)..."
openfang hand activate taam_lili_hand

if [[ "${SIN_TELEGRAM}" -eq 0 ]]; then
  echo ""
  echo "Verificando bot Telegram (getMe)..."
  "${SCRIPT_DIR}/verificar_telegram_bot.sh"
else
  echo ""
  echo "Omitiendo verificacion Telegram (--sin-telegram)."
fi

echo ""
echo "=== Listo ==="
echo "  Dashboard:     ${API_BASE}"
echo "  Salud API:     curl -fsS ${HEALTH_URL}"
echo "  Hand activo:   openfang hand deactivate taam_lili_hand   # al terminar demo"
echo "  Sesiones:      openfang sessions --json"
if [[ "${INICIAMOS_DAEMON}" -eq 1 ]]; then
  echo "  Daemon:        en ejecucion (Ctrl+C en este script lo detiene si lo inicio aqui)"
else
  echo "  Daemon:        en ejecucion (reutilizado; no detenido al salir)"
fi
