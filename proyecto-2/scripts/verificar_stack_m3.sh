#!/usr/bin/env bash
# Verifica cadenas obligatorias de la rubrica M3 en proyecto-2 (decision-7).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/src/agentes"

buscar() {
  local patron="$1"
  if grep -rq "$patron" "${SRC}" 2>/dev/null; then
    echo "OK: ${patron}"
    return 0
  fi
  echo "FALTA: ${patron} en src/agentes/"
  return 1
}

fallo=0
buscar "create_agent" || fallo=1
buscar "PostgresSaver" || fallo=1
buscar "HumanInTheLoopMiddleware" || fallo=1
buscar "init_chat_model" || fallo=1
buscar "dynamic_prompt" || fallo=1

for tool in obtener_contexto_caso consultar_protocolo_rag faq_postoperatorio clasificar_triage escalar_a_equipo; do
  if grep -rq "\"${tool}\"" "${SRC}/tools" 2>/dev/null || grep -rq "@tool(\"${tool}\"" "${SRC}/tools" 2>/dev/null; then
    echo "OK tool: ${tool}"
  else
    echo "FALTA tool: ${tool}"
    fallo=1
  fi
done

if grep -rq "RecursiveCharacterTextSplitter" "${ROOT}/src/ingesta" 2>/dev/null; then
  echo "OK: RecursiveCharacterTextSplitter (ingesta)"
else
  echo "AVISO: RecursiveCharacterTextSplitter no encontrado en ingesta"
fi

exit "${fallo}"
