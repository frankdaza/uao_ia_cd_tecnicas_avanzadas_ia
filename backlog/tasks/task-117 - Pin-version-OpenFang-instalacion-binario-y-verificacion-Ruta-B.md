---
id: TASK-117
title: 'Pin version OpenFang, instalacion binario y verificacion Ruta B'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - config
milestone: m-1
dependencies: []
references:
  - backlog/decisions/decision-8 - Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/docs/doc-007 - Evaluacion-OpenFang-Proyecto-2-TAAM.md
  - proyecto-3/scripts/instalar_openfang.sh
  - proyecto-3/README.md
modified_files:
  - proyecto-3/scripts/instalar_openfang.sh
  - proyecto-3/README.md
priority: high
ordinal: 1170
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
- [ ] #1 Tras `./scripts/instalar_openfang.sh`, `openfang --version` imprime la versión pinneada documentada en README (misma cadena en ambos)
- [ ] #2 `openfang start --help` termina con código 0 y muestra subcomandos esperados (`start`, `hand`, etc.)
- [ ] #3 **Negativo:** si el instalador no tiene red, el script sale con código distinto de 0 y mensaje claro (no deja binario corrupto a medias)
- [ ] #4 **Alterno:** README documenta paso manual si `curl` falla (descarga directa del release) y variable `OPENFANG_BIN` para override
- [ ] #5 README incluye subsección **Fallback Ollama**: cuándo usarlo, variables `OLLAMA_BASE_URL`, que Ruta B prioriza OpenAI según decision-8
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
Ejemplo esqueleto del script:

```bash
#!/usr/bin/env bash
set -euo pipefail
OPENFANG_VERSION="${OPENFANG_VERSION:-0.1.0}"
INSTALAR_URL="https://releases.openfang.sh/v${OPENFANG_VERSION}/install.sh"

main() {
  if [[ "${1:-}" == "--verificar-only" ]]; then
    openfang --version
    openfang start --help
    exit 0
  fi
  curl -fsSL "${INSTALAR_URL}" | bash
  openfang --version
}
main "$@"
```

Fallback Ollama (solo documentación en README):

```markdown
## Fallback Ollama (opcional)
Si OpenAI no está disponible, documentar en openfang.toml `provider = "ollama"` y `OLLAMA_BASE_URL`.
No es el camino principal de la demo Ruta B.
```

**Riesgo:** API del instalador pre-1.0 — si cambia, actualizar URL en el mismo PR y bump del pin.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Script ejecutable (`chmod +x`) y probado en al menos un entorno Unix
- [ ] #2 Sin secretos ni tokens en el diff
- [ ] #3 README en español latinoamericano; identificadores y rutas ASCII
- [ ] #4 Tarea marcada **Done** en Backlog sin invocar `task_complete`
<!-- DOD:END -->
