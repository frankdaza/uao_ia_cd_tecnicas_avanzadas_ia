#!/usr/bin/env bash
# Detiene el daemon OpenFang de desarrollo (mismo OPENFANG_HOME que arrancar_dev.sh).
# Uso: ./scripts/detener_dev.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

mostrar_ayuda() {
  cat <<'EOF'
Uso: ./scripts/detener_dev.sh

Detiene el Hand de demo, el daemon OpenFang registrado bajo OPENFANG_HOME
y, si hace falta, el proceso que escucha en OPENFANG_API_URL (puerto por defecto 4200).

Requisitos: .env con OPENFANG_HOME (cp .env.example .env), openfang en PATH.
EOF
}

puerto_desde_url() {
  local url="$1"
  if [[ "${url}" =~ :([0-9]+)(/|$) ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
  else
    printf '%s' "4200"
  fi
}

matar_escuchador_puerto() {
  local puerto="$1"
  local pids

  if ! command -v lsof >/dev/null 2>&1; then
    echo "  aviso: lsof no disponible; no se puede forzar cierre por puerto ${puerto}" >&2
    return 1
  fi

  pids="$(lsof -t -iTCP:"${puerto}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "${pids}" ]]; then
    return 1
  fi

  echo "  Forzando cierre del proceso en puerto ${puerto} (PID: ${pids//$'\n'/, })..."
  # shellcheck disable=SC2086
  kill -TERM ${pids} 2>/dev/null || true
  sleep 1
  if lsof -t -iTCP:"${puerto}" -sTCP:LISTEN >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    kill -KILL ${pids} 2>/dev/null || true
  fi
  return 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "error: falta .env (copia .env.example a .env)." >&2
  exit 1
fi

export PATH="${HOME}/.openfang/bin:${PATH}"

# shellcheck disable=SC1091
set -a && source .env && set +a

export OPENFANG_HOME="${OPENFANG_HOME:-./openfang/data}"
if [[ "${OPENFANG_HOME}" != /* ]]; then
  OPENFANG_HOME="$(cd "${ROOT_DIR}" && cd "${OPENFANG_HOME}" && pwd)"
  export OPENFANG_HOME
fi

API_BASE="${OPENFANG_API_URL:-http://127.0.0.1:4200}"
HEALTH_URL="${API_BASE%/}/api/health"
PUERTO="$(puerto_desde_url "${API_BASE}")"

if ! command -v openfang >/dev/null 2>&1; then
  echo "error: openfang no esta en PATH (./scripts/instalar_openfang.sh)" >&2
  exit 1
fi

echo "=== proyecto-3 — detener OpenFang (dev) ==="
echo "OPENFANG_HOME=${OPENFANG_HOME}"
echo ""

echo "Desactivando Hand taam_lili_hand (si estaba activo)..."
openfang hand deactivate taam_lili_hand 2>/dev/null || true

echo "Deteniendo daemon OpenFang (openfang stop)..."
if openfang stop 2>/dev/null; then
  echo "  openfang stop: OK"
else
  echo "  openfang stop: sin daemon registrado bajo OPENFANG_HOME"
fi

if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
  echo "Healthcheck aun responde (${HEALTH_URL}); intentando cierre por puerto..."
  matar_escuchador_puerto "${PUERTO}" || true
fi

if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
  echo "error: el API sigue activo en ${HEALTH_URL}" >&2
  echo "  Revisa: lsof -nP -iTCP:${PUERTO} -sTCP:LISTEN" >&2
  exit 1
fi

echo ""
echo "=== OpenFang detenido ==="
echo "  Comprobar: curl -fsS ${HEALTH_URL}  # debe fallar"
echo "  Reiniciar: ./scripts/arrancar_dev.sh"
