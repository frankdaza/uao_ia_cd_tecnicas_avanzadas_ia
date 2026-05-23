#!/usr/bin/env bash
# Valida openfang.toml y sincroniza config bajo OPENFANG_HOME (sin levantar daemon largo)
# Uso: ./scripts/validar_openfang_config.sh

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

CONFIG_VERSIONADO="${ROOT_DIR}/openfang/openfang.toml"
CONFIG_RUNTIME="${OPENFANG_HOME}/config.toml"

if [[ ! -f "${CONFIG_VERSIONADO}" ]]; then
  echo "error: no existe ${CONFIG_VERSIONADO}" >&2
  exit 1
fi

mkdir -p "${OPENFANG_HOME}"
cp -f "${CONFIG_VERSIONADO}" "${CONFIG_RUNTIME}"

# El kernel resuelve default_agent bajo OPENFANG_HOME/agents/<nombre>/
AGENTS_SOURCE="${ROOT_DIR}/openfang/agents"
AGENTS_RUNTIME="${OPENFANG_HOME}/agents"
if [[ -d "${AGENTS_SOURCE}" ]]; then
  mkdir -p "${AGENTS_RUNTIME}"
  for agente_dir in "${AGENTS_SOURCE}"/*/; do
    [[ -d "${agente_dir}" ]] || continue
    nombre_agente="$(basename "${agente_dir}")"
    ln -sfn "${agente_dir}" "${AGENTS_RUNTIME}/${nombre_agente}"
  done
fi

if ! command -v openfang >/dev/null 2>&1; then
  echo "error: openfang no esta en PATH. Ejecuta ./scripts/instalar_openfang.sh" >&2
  exit 1
fi

echo "=== validar OpenFang config ==="
echo "OPENFANG_HOME=${OPENFANG_HOME}"
echo "config runtime: ${CONFIG_RUNTIME}"
echo ""

# doctor puede salir distinto de 0 si faltan API keys; exigimos que el TOML deserialice
if ! openfang doctor 2>&1 | tee /tmp/openfang-doctor-task119.txt; then
  if grep -q "Config deserializes into KernelConfig" /tmp/openfang-doctor-task119.txt; then
    echo ""
    echo "Config TOML valida (avisos de API keys o daemon son esperables sin .env completo)."
    exit 0
  fi
  exit 1
fi
