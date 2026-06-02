#!/usr/bin/env bash
# Instala el binario OpenFang (Agent OS) con version pinneada — Ruta B Modulo 3
# Uso:
#   ./scripts/instalar_openfang.sh
#   ./scripts/instalar_openfang.sh --verificar-only
#   ./scripts/instalar_openfang.sh --force
# Documentacion: https://openfang.sh/

set -euo pipefail

readonly REPO="RightNow-AI/openfang"
readonly INSTALL_DIR="${HOME}/.openfang"
readonly BIN_DIR="${INSTALL_DIR}/bin"
readonly BINARY_NAME="openfang"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/.openfang-version"

say() {
  printf "  \033[1;36mopenfang\033[0m %s\n" "$1"
}

err() {
  printf "  \033[1;36mopenfang\033[0m \033[1;31merror:\033[0m %s\n" "$1" >&2
  exit 1
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "se requiere el comando '$1' (no encontrado)"
  fi
}

leer_version_pin() {
  if [[ -n "${OPENFANG_VERSION:-}" ]]; then
    printf '%s' "${OPENFANG_VERSION}"
    return
  fi
  if [[ -f "${VERSION_FILE}" ]]; then
    tr -d ' \r\n' < "${VERSION_FILE}"
    return
  fi
  printf '%s' "0.6.9"
}

normalizar_tag() {
  local ver="$1"
  if [[ "${ver}" == v* ]]; then
    printf '%s' "${ver}"
  else
    printf 'v%s' "${ver}"
  fi
}

version_sin_prefijo_v() {
  local ver="$1"
  if [[ "${ver}" == v* ]]; then
    printf '%s' "${ver#v}"
  else
    printf '%s' "${ver}"
  fi
}

resolver_binario() {
  if [[ -n "${OPENFANG_BIN:-}" ]]; then
    if [[ ! -x "${OPENFANG_BIN}" ]]; then
      err "OPENFANG_BIN no es ejecutable: ${OPENFANG_BIN}"
    fi
    printf '%s' "${OPENFANG_BIN}"
    return
  fi
  if [[ -x "${BIN_DIR}/${BINARY_NAME}" ]]; then
    printf '%s' "${BIN_DIR}/${BINARY_NAME}"
    return
  fi
  if command -v "${BINARY_NAME}" >/dev/null 2>&1; then
    command -v "${BINARY_NAME}"
    return
  fi
  err "no se encontro '${BINARY_NAME}'. Ejecuta ./scripts/instalar_openfang.sh o exporta OPENFANG_BIN"
}

version_instalada() {
  local bin="$1"
  "${bin}" --version 2>/dev/null || true
}

version_coincide() {
  local salida="$1"
  local pin="$2"
  local pin_core
  pin_core="$(version_sin_prefijo_v "${pin}")"
  case "${salida}" in
    *"${pin_core}"*) return 0 ;;
    *"v${pin_core}"*) return 0 ;;
    *) return 1 ;;
  esac
}

detectar_target() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "${os}" in
    Linux)
      case "${arch}" in
        x86_64|amd64) printf '%s' "x86_64-unknown-linux-gnu" ;;
        aarch64|arm64) printf '%s' "aarch64-unknown-linux-gnu" ;;
        *) err "arquitectura no soportada: ${arch} (${os})" ;;
      esac
      ;;
    Darwin)
      case "${arch}" in
        x86_64|amd64) printf '%s' "x86_64-apple-darwin" ;;
        aarch64|arm64) printf '%s' "aarch64-apple-darwin" ;;
        *) err "arquitectura no soportada: ${arch} (${os})" ;;
      esac
      ;;
    *)
      err "SO no soportado: ${os} (en Windows usar install.ps1 desde openfang.sh)"
      ;;
  esac
}

url_descarga() {
  local tag="$1"
  local target="$2"
  if [[ -n "${OPENFANG_DOWNLOAD_URL:-}" ]]; then
    printf '%s' "${OPENFANG_DOWNLOAD_URL}"
    return
  fi
  printf 'https://github.com/%s/releases/download/%s/openfang-%s.tar.gz' \
    "${REPO}" "${tag}" "${target}"
}

instalar_binario() {
  local tag="$1"
  local target="$2"
  local url tmpdir archive bin_en_tmp dest

  need_cmd curl
  need_cmd tar
  need_cmd find

  url="$(url_descarga "${tag}" "${target}")"
  tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t openfang)"
  archive="${tmpdir}/openfang.tar.gz"

  say "Detectado: $(uname -s) $(uname -m) -> ${target}"
  say "Descargando: ${url}"

  if ! curl -fsSL --connect-timeout 30 --max-time 600 "${url}" -o "${archive}"; then
    err "fallo la descarga (sin red o URL invalida). Revisa ${url} o instala manualmente (ver README)"
  fi

  if [[ ! -s "${archive}" ]] || [[ "$(wc -c < "${archive}")" -lt 1000 ]]; then
    err "archivo descargado invalido o demasiado pequeno; no se instalo un binario corrupto"
  fi

  say "Extrayendo..."
  tar -xzf "${archive}" -C "${tmpdir}"

  bin_en_tmp="$(find "${tmpdir}" -name "${BINARY_NAME}" -type f 2>/dev/null | head -1)"
  if [[ -z "${bin_en_tmp}" ]]; then
    err "no se encontro el binario '${BINARY_NAME}' en el tarball"
  fi

  mkdir -p "${BIN_DIR}"
  dest="${BIN_DIR}/${BINARY_NAME}"
  cp "${bin_en_tmp}" "${dest}"
  chmod +x "${dest}"
  rm -rf "${tmpdir}"
  say "Instalado en: ${dest}"
}

recordar_path() {
  say "Anade al PATH de tu sesion:"
  printf '  export PATH="%s:$PATH"\n' "${BIN_DIR}"
  say "O usa: export OPENFANG_BIN=\"${BIN_DIR}/${BINARY_NAME}\""
}

ejecutar_smoke() {
  local bin="$1"
  local pin="$2"
  local ver_salida

  ver_salida="$(version_instalada "${bin}")"
  if [[ -z "${ver_salida}" ]]; then
    err "no se pudo leer la version con '${bin} --version'"
  fi
  say "Version: ${ver_salida}"

  if ! version_coincide "${ver_salida}" "${pin}"; then
    err "version instalada ('${ver_salida}') no coincide con el pin '${pin}' (ver ${VERSION_FILE})"
  fi

  if ! "${bin}" start --help >/dev/null 2>&1; then
    err "fallo 'openfang start --help' (smoke)"
  fi
  say "Smoke OK: start --help"
}

main() {
  local modo="${1:-}"
  local pin tag target bin ver_actual forzar=false

  pin="$(leer_version_pin)"
  tag="$(normalizar_tag "${pin}")"

  case "${modo}" in
    --verificar-only)
      bin="$(resolver_binario)"
      ejecutar_smoke "${bin}" "${pin}"
      exit 0
      ;;
    --force)
      forzar=true
      ;;
    "")
      ;;
    *)
      err "argumento desconocido: ${modo} (usa --verificar-only o --force)"
      ;;
  esac

  target="$(detectar_target)"
  bin="${BIN_DIR}/${BINARY_NAME}"

  if [[ "${forzar}" == false ]] && [[ -x "${bin}" ]]; then
    ver_actual="$(version_instalada "${bin}")"
    if version_coincide "${ver_actual}" "${pin}"; then
      say "Ya instalado (${ver_actual}); usa --force para reinstalar"
      ejecutar_smoke "${bin}" "${pin}"
      recordar_path
      exit 0
    fi
  fi

  instalar_binario "${tag}" "${target}"
  bin="$(resolver_binario)"
  ejecutar_smoke "${bin}" "${pin}"
  recordar_path
}

main "$@"
