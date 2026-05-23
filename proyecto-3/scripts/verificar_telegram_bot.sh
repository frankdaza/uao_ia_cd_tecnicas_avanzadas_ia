#!/usr/bin/env bash
# Verifica TELEGRAM_BOT_TOKEN contra getMe (sin imprimir el token).
# Uso: ./scripts/verificar_telegram_bot.sh
#      TELEGRAM_BOT_TOKEN='000000000:INVALID' ./scripts/verificar_telegram_bot.sh  # prueba negativa

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

token_previo="${TELEGRAM_BOT_TOKEN:-}"
if [[ -z "${token_previo}" && -f .env ]]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

token="${TELEGRAM_BOT_TOKEN:-}"
token="${token//[[:space:]]/}"

if [[ -z "${token}" ]]; then
  echo "error: TELEGRAM_BOT_TOKEN no esta definido." >&2
  echo "  Copia .env.example a .env y usa un bot distinto al de proyecto-2." >&2
  exit 1
fi

url="https://api.telegram.org/bot${token}/getMe"
resp="$(curl -sS -w "\n%{http_code}" "${url}")"
http_code="$(echo "${resp}" | tail -n1)"
body="$(echo "${resp}" | sed '$d')"

if [[ "${http_code}" == "401" ]] || echo "${body}" | grep -qiE 'unauthorized|401'; then
  echo "error: token rechazado por Telegram (401 Unauthorized)." >&2
  echo "  Respuesta: ${body}" >&2
  exit 1
fi

if ! echo "${body}" | grep -q '"ok":true'; then
  echo "error: getMe fallo (HTTP ${http_code})." >&2
  echo "  Respuesta: ${body}" >&2
  exit 1
fi

username="$(echo "${body}" | sed -n 's/.*"username":"\([^"]*\)".*/\1/p' | head -n1)"
bot_id="$(echo "${body}" | sed -n 's/.*"id":\([0-9]*\).*/\1/p' | head -n1)"
echo "OK: bot @${username:-desconocido} (id=${bot_id:-?})"
