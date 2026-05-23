---
id: TASK-117
title: 'Pin version OpenFang, instalacion binario y verificacion Ruta B'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 05:17'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - config
milestone: m-1
dependencies: []
references:
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/docs/doc-007 - Evaluacion-OpenFang-Proyecto-2-TAAM.md
  - proyecto-3/scripts/instalar_openfang.sh
  - proyecto-3/README.md
  - 'https://github.com/RightNow-AI/openfang/releases/tag/v0.6.9'
  - 'https://www.openfang.sh/install'
  - proyecto-3/.openfang-version
modified_files:
  - proyecto-3/scripts/instalar_openfang.sh
  - proyecto-3/README.md
  - proyecto-3/.openfang-version
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La **Ruta B** del Módulo 3 exige [OpenFang](https://www.openfang.sh/) como Agent OS (binario único). El script [`proyecto-3/scripts/instalar_openfang.sh`](../../proyecto-3/scripts/instalar_openfang.sh) hoy es placeholder. Sin pin de versión y smoke test, las tareas siguientes (config, bridge Telegram, Hands) fallan de forma opaca.

**ADR:** [decision-8](../decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) (`accepted`).

## Objetivo

Instalar y verificar el binario `openfang` en macOS/Linux de desarrollo, documentar **versión fijada** en README y **fallback Ollama** (solo documentado, no implementar salvo bloqueo de OpenAI).

## Entregables

| # | Artefacto | Criterio |
| --- | --- | --- |
| 1 | `scripts/instalar_openfang.sh` | Descarga/instala vía canal oficial; idempotente; `set -euo pipefail` |
| 2 | `README.md` — sección OpenFang | Versión pinneada, requisitos OS, comando de verificación |
| 3 | Smoke | `openfang --version` y `openfang start --help` sin error |

## Ámbito

Solo `proyecto-3/scripts/` y documentación; **no** configurar `openfang.toml` ni tokens (task-119+).

**Skill:** `uv-python-env` (convenciones de entorno del monorepo).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tras `./scripts/instalar_openfang.sh`, `openfang --version` imprime la versión pinneada documentada en README (misma cadena en ambos)
- [x] #2 `openfang start --help` termina con código 0 y muestra subcomandos esperados (`start`, `hand`, etc.)
- [x] #3 **Negativo:** si el instalador no tiene red, el script sale con código distinto de 0 y mensaje claro (no deja binario corrupto a medias)
- [x] #4 **Alterno:** README documenta paso manual si `curl` falla (descarga directa del release) y variable `OPENFANG_BIN` para override
- [x] #5 README incluye subsección **Fallback Ollama**: cuándo usarlo, variables `OLLAMA_BASE_URL`, que Ruta B prioriza OpenAI según decision-8
- [x] #6 #6 Si existe proyecto-3/.openfang-version, --verificar-only falla con mensaje claro si openfang --version no contiene esa version (tolerancia prefijo v)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Consultar release estable en documentación OpenFang; elegir tag (ej. `v0.x.y`) y fijarlo en constante del script.
2. Implementar `instalar_openfang.sh`: detectar OS/arch, descargar artefacto, instalar en `~/.local/bin` o ruta acordada, actualizar `PATH` en mensaje post-instalación.
3. Añadir flag `--verificar-only` que solo ejecuta smoke sin reinstalar.
4. Documentar en `proyecto-3/README.md`: prerequisitos, instalación, verificación, fallback Ollama.
5. Ejecutar smoke en máquina de desarrollo y capturar salida de ejemplo en notas de la tarea al cerrar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pin v0.6.9 (GitHub RightNow-AI/openfang). Instalador upstream sin pin: curl -fsSL https://openfang.sh/install | sh (usa latest; solo referencia).

URL pinneada por arquitectura:
https://github.com/RightNow-AI/openfang/releases/download/v0.6.9/openfang-${TARGET}.tar.gz

Binario: $HOME/.openfang/bin/openfang. Variables: OPENFANG_VERSION, OPENFANG_BIN, OPENFANG_DOWNLOAD_URL (prueba error red).

Esqueleto wrapper:
```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENFANG_VERSION="${OPENFANG_VERSION:-$(tr -d ' \r\n' < "${ROOT}/.openfang-version")}"
# --verificar-only | --force | instalar pinneado
```

Fallback Ollama (solo README): provider ollama en openfang.toml, OLLAMA_BASE_URL; Ruta B prioriza OpenAI.

Riesgo pre-1.0: bump .openfang-version si cambia formato de --version.

Smoke macOS arm64 (2026-05-23): openfang 0.6.9; target aarch64-apple-darwin; idempotente OK; OPENFANG_DOWNLOAD_URL invalido -> exit 1 sin tocar binario.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado pin OpenFang 0.6.9: .openfang-version, instalar_openfang.sh (descarga GitHub pinneada, idempotente, --verificar-only, --force, OPENFANG_BIN/OPENFANG_DOWNLOAD_URL) y README con instalacion manual y fallback Ollama. Probado en Darwin arm64: openfang 0.6.9, start --help OK, caso sin red exit 1.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Script ejecutable (`chmod +x`) y probado en al menos un entorno Unix
- [x] #2 Sin secretos ni tokens en el diff
- [x] #3 README en español latinoamericano; identificadores y rutas ASCII
- [x] #4 Tarea marcada **Done** en Backlog sin invocar `task_complete`
<!-- DOD:END -->
