---
id: TASK-124
title: Hand cron recordatorio postoperatorio UC6 pruebas positivas y negativas
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:36'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - hand
milestone: m-1
dependencies:
  - TASK-122
  - TASK-123
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/scripts/disparar_recordatorio_hand.py
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/src/hand/__init__.py
  - proyecto-3/scripts/disparar_recordatorio_hand.py
  - proyecto-3/tests/hand/test_recordatorio_postop.py
  - proyecto-3/tests/fixtures/openfang_sesion_ejemplo.jsonl
  - proyecto-3/openfang/hands/taam_lili_hand/SKILL.md
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
priority: high
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC6 (milestone m-1)** = recordatorios proactivos postoperatorio. En el documento canónico del cliente equivale a **UC-MVP-04** ([Caso de Uso TAAM](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): mensajes por Telegram sin email ni OLTP.

**Ruta A** (`proyecto-2/`): plantillas Postgres, `programado_at`, `motivo_omitido` en `integracion/recordatorios/`.

**Ruta B (esta tarea):** tick del Hand `taam_lili_hand` (`every_secs = 30` en demo) + playbook [`recordatorio_postop.md`](../../proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md); sesiones `telegram:{chat_id}` en JSONL bajo `OPENFANG_HOME`. Sin `plantillas_recordatorio` ni `vinculos_telegram`.

## Objetivo TASK-124

Adaptador Python **testeable** (`ejecutar_recordatorio_postop`) para orquestar UC6 en CI sin depender del daemon OpenFang; playbook con ramas negativa y edge; auditoría en `{OPENFANG_HOME}/audit/hand_recordatorio.jsonl`; prueba manual documentada.

## Entregado por TASK-123

Manifesto `HAND.toml`, `SKILL.md`, validación estática (`validar_hand.py`, `test_hand_taam_lili.py`), playbooks mínimos.

## Fuera de alcance

- Cron matutino de producción (decision-8 futuro).
- `debe_escalar()` y KV `escalado` → TASK-126.
- `pendiente_evidencia` y reintentos evidencia → TASK-125.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 **Positivo:** con mock de ≥1 sesión activa (`session_id` `telegram:*`), `ejecutar_recordatorio_postop()` devuelve `enviados >= 1`; texto con disclaimer (“no reemplaza” / “medico tratante”); sin patrón de dosis (`\d+\s*(mg|ml|mcg)`).
- [x] #2 **Negativo:** `listar_sesiones_activas` → `[]` ⇒ `enviados == 0`, `motivo == "sin_sesiones_activas"`, log `recordatorio_omitido_sin_sesiones`.
- [x] #3 **Edge:** sesión con `tiene_contexto_reciente=False` ⇒ mensaje genérico de autocuidado; sin fármacos, horarios ni datos clínicos inventados (`redactar_mensaje_recordatorio` en pytest).
- [x] #4 **Auditoría:** tras ejecutar el adaptador, línea JSON en `{OPENFANG_HOME}/audit/hand_recordatorio.jsonl` con `tipo: "hand_recordatorio"`.
- [x] #5 **Automatizado:** `uv run pytest tests/hand/test_recordatorio_postop.py tests/test_hand_taam_lili.py -q` verde (17 passed).
- [x] #6 **Manual (DoD):** `uv run python scripts/disparar_recordatorio_hand.py --solo-simular` OK; envío Telegram real pendiente de sesión activa en demo (guion actualizado).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Módulo [`proyecto-3/src/hand/recordatorio_postoperatorio.py`](../../proyecto-3/src/hand/recordatorio_postoperatorio.py): `ResultadoRecordatorioPostop`, `SesionActiva`, `listar_sesiones_activas`, `redactar_mensaje_recordatorio`, `validar_mensaje_recordatorio`, `ejecutar_recordatorio_postop`, `registrar_auditoria_hand_recordatorio`.
2. Script [`proyecto-3/scripts/disparar_recordatorio_hand.py`](../../proyecto-3/scripts/disparar_recordatorio_hand.py) (disparo manual; envío Telegram solo con token).
3. Ampliar [`recordatorio_postop.md`](../../proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md): sin sesiones activas; sin contexto reciente.
4. Tests [`proyecto-3/tests/hand/test_recordatorio_postop.py`](../../proyecto-3/tests/hand/test_recordatorio_postop.py) + fixture JSONL.
5. Manual: `openfang hand activate taam_lili_hand` o script Python (no usar `hand run` hasta verificar en `openfang hand --help` 0.6.9).
6. Actualizar SKILL.md, README.md, guion demo.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Auditoría:** `{OPENFANG_HOME}/audit/hand_recordatorio.jsonl` (campo `tipo: "hand_recordatorio"`).

**Contexto reciente:** `HORAS_CONTEXTO_RECIENTE = 48` en el módulo Python.

```python
from src.hand.recordatorio_postoperatorio import ejecutar_recordatorio_postop

def test_recordatorio_sin_sesiones_no_envia(monkeypatch):
    monkeypatch.setattr(
        "src.hand.recordatorio_postoperatorio.listar_sesiones_activas",
        lambda *_a, **_k: [],
    )
    resultado = ejecutar_recordatorio_postop(enviar=lambda *_: None)
    assert resultado.enviados == 0
    assert resultado.motivo == "sin_sesiones_activas"
```

```bash
cd proyecto-3
uv run pytest tests/hand/test_recordatorio_postop.py tests/test_hand_taam_lili.py -q
uv run python scripts/disparar_recordatorio_hand.py --solo-simular
```

**Cierre 2026-05-23:** 9 tests UC6 + 8 estáticos HAND; módulo `src/hand/recordatorio_postoperatorio.py`; disparo manual documentado en SKILL, README y guion demo.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Adaptador + script disparo documentados
- [x] #2 Pytest hand + estáticos verdes
- [x] #3 Corrida manual: 2026-05-23 `--solo-simular` → `enviados=0`, `sin_sesiones_activas`, audit JSONL escrito
- [x] #4 Tarea **Done** sin archivar (`task_complete`)
<!-- DOD:END -->
