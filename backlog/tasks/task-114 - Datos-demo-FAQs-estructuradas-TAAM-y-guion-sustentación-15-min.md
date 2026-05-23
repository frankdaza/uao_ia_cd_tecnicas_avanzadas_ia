---
id: TASK-114
title: 'Datos demo, FAQs estructuradas TAAM y guion sustentación 15 min'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
updated_date: '2026-05-22 00:51'
labels:
  - modulo-3
  - taam
  - demo
  - seed
milestone: m-0
dependencies:
  - TASK-107
  - TASK-111
  - TASK-112
  - TASK-113
references:
  - data/structured/taam_faqs.json
  - data/structured/taam_faqs.schema.json
  - data/taam/demo/colecistectomia-protocolo-sintetico.pdf
  - proyecto-2/src/persistencia/semilla_demo_taam.py
  - proyecto-2/scripts/sembrar_demo_taam.py
  - proyecto-2/tests/structured/test_taam_faqs_json_schema.py
  - backlog/docs/usecases/GUION-DEMO-TAAM.md
  - proyecto-2/README.md
modified_files:
  - data/structured/taam_faqs.json
  - data/structured/taam_faqs.schema.json
  - data/taam/demo/colecistectomia-protocolo-sintetico.pdf
  - .gitignore
  - proyecto-2/pyproject.toml
  - proyecto-2/src/persistencia/semilla_demo_taam.py
  - proyecto-2/src/persistencia/repositorios/casos_postoperatorio.py
  - proyecto-2/scripts/sembrar_demo_taam.py
  - proyecto-2/scripts/README.md
  - proyecto-2/tests/structured/test_taam_faqs_json_schema.py
  - proyecto-2/README.md
  - backlog/docs/usecases/GUION-DEMO-TAAM.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La sustentación M3 es **100% práctica** con el teléfono del profesor. Sin **semillas reproducibles**, **FAQs estructuradas** alineadas a `faq_postoperatorio` y un **guion minuto a minuto**, la demo falla aunque el código compile. Este paquete cierra el hilo de [TASK-97](backlog/tasks/task-97%20-%20Documento-casos-de-uso-TAAM-MVP-5-UC-matriz-trazabilidad-guion-demo.md) (secciones 9–10 del UC) y desbloquea UC-MVP-01..05 en vivo.

**Ámbito:** workspace `data/structured/`, `data/taam/demo/`, `proyecto-2/scripts/sembrar_demo_taam.py`, guion en `backlog/docs/usecases/`, sección README en `proyecto-2/README.md`.

**Dependencias:** TASK-107 (recordatorios/plantillas), TASK-111 (admin procedimientos + ingesta), TASK-112 (casos/código), TASK-113 (panel seguimiento). Staff demo previo: `scripts/sembrar_usuarios_staff_demo.py` (TASK-105).

## Objetivo

Entregar un **paquete demo idempotente** que deje Postgres TAAM + artefactos de workspace listos para el guion de 15 min, sin PHI real ni pasos manuales no documentados.

## Entregables

| # | Artefacto | Criterio |
|---|-----------|----------|
| 1 | `data/structured/taam_faqs.json` + `taam_faqs.schema.json` | 5–10 FAQs postoperatorias ficticias; validación JSON Schema (test) |
| 2 | `proyecto-2/scripts/sembrar_demo_taam.py` + `src/persistencia/semilla_demo_taam.py` | Staff demo, `COLE-LAP-001` + PDF, 2 casos, plantillas/recordatorios, vínculo/alerta/hilo caso A |
| 3 | `data/taam/demo/colecistectomia-protocolo-sintetico.pdf` | Texto sintético extraíble (sin datos reales de pacientes) |
| 4 | `backlog/docs/usecases/GUION-DEMO-TAAM.md` | Pasos 0–15 min, comandos `docker`/`uv`, logs/terminales, checklist pre-demo |
| 5 | `proyecto-2/README.md` — sección **Demo en vivo** | Flujo único: compose → migrate → sembrar → (opcional ingesta) → webhook |

## Datos sembrados (alineados al UC §10)

- **Procedimiento:** `COLE-LAP-001` — Colecistectomía laparoscópica (ficticio), `indexacion_estado=ok` (RAG opcional con `--con-ingesta`).
- **Caso A:** `PAC-DEMO-001` / Ana Ficticia López — cirugía hace 2 días; Telegram `111111111` vinculado; alerta `urgente` pendiente; hilo conversación en checkpointer.
- **Caso B:** `PAC-DEMO-002` / Bruno Ficticio Ruiz — cirugía hace 7 días; sin vínculo (código pendiente opcional para `/start` en vivo).
- **Staff:** reutiliza semilla TASK-105 (`asistente@`, `clinico@`, `admin@demo.taam`).

## Guion mínimo (5 pasos en vivo)

1. Admin: procedimiento demo ya indexado (o subida en vivo).
2. Asistente: caso A visible + código para caso B si se crea en pantalla.
3. Paciente: `/start CODIGO` en Telegram (caso B en vivo o A ya vinculado).
4. Pregunta FAQ + red flag → alerta urgente en panel.
5. Clínico: bandeja `/seguimiento` → marcar revisado.

## Fallas a evitar

- PHI real en repo o en semillas.
- Depender de OpenAI en **tests unitarios** (documentar mocks; ingesta/RAG en demo con clave real).
- Sembrar sin `alembic upgrade head` o sin `STAFF_JWT_SECRET`.
- Olvidar túnel HTTPS para webhook Telegram.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 Tras `uv run alembic upgrade head`, `uv run python -m scripts.sembrar_demo_taam` deja staff demo, `COLE-LAP-001` con PDF y `indexacion_estado=ok`, dos casos `PAC-DEMO-001` y `PAC-DEMO-002` activos distinguibles en `GET /api/staff/casos`, plantillas de recordatorio y (caso A) vínculo Telegram + alerta urgente no revisada + hilo en checkpointer
- [x] #2 #2 `data/structured/taam_faqs.json` cumple `taam_faqs.schema.json` (≥5 entradas); test en `proyecto-2/tests/structured/test_taam_faqs_json_schema.py` pasa con `uv run pytest`
- [x] #3 #3 `backlog/docs/usecases/GUION-DEMO-TAAM.md` documenta tiempos (tabla 15 min), comandos docker/uv/ngrok, credenciales demo referenciadas a `.env.example`, checklist pre-demo (webhook, token, Qdrant, MOCK en tests vs OpenAI en vivo)
- [x] #4 #4 Caso A sembrado con `vinculado_telegram=true` y al menos una alerta `revisado=false` severidad `urgente`; caso B listado sin confundir identidad (nombres/doc_id distintos)
- [x] #5 #5 `proyecto-2/README.md` incluye sección «Demo en vivo» con orden de comandos y enlace al guion UC/GUION-DEMO-TAAM
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **FAQs:** ampliar `taam_faqs.json` (intents demo: caminata, dieta, herida, fiebre, medicación, etc.); crear `taam_faqs.schema.json` (reutilizar forma de `faqs.schema.json`); test `jsonschema` en `proyecto-2/tests/structured/`.
2. **PDF demo:** generar `data/taam/demo/colecistectomia-protocolo-sintetico.pdf` con texto sintético; excepción `.gitignore` solo para ese archivo; `.gitkeep` en carpetas `data/taam/`.
3. **Semilla:** módulo `src/persistencia/semilla_demo_taam.py` (idempotente por `codigo`/`paciente_doc_id`); CLI `scripts/sembrar_demo_taam.py` con flags `--con-ingesta` y `--sin-conversacion`; invoca `sembrar_usuarios_staff_demo`.
4. **Guion:** `backlog/docs/usecases/GUION-DEMO-TAAM.md` (tabla minutos, checklist, preguntas sugeridas, fallbacks); enlace desde UC §9.
5. **README + scripts/README:** sección Demo en vivo; actualizar TASK-114 vía MCP al cerrar.
6. **Verificación:** `uv run pytest` (structured + smoke semilla si hay Postgres) y dry-run del script documentado.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Orden local:** `docker compose up -d` → `uv run alembic upgrade head` → `uv run python -m scripts.sembrar_usuarios_staff_demo` (si hace falta) → `uv run python -m scripts.sembrar_demo_taam` → opcional `--con-ingesta` con Qdrant + `OPENAI_API_KEY`.
- **Tool FAQ:** `src/agentes/tools/faq_postoperatorio.py` lee `data/structured/taam_faqs.json` vía `resolver_ruta_workspace`.
- **Chats ficticios:** `111111111` (caso A), `222222222` (reservado caso B / pruebas).
- **Preguntas demo UC-03:** «¿Cuándo puedo retomar caminatas leves?» (`info`); «Tengo sangrado abundante en la herida» (`urgente`).
- **Tests API:** usan `monkeypatch` sobre `invocar_agente`; no requieren OpenAI. Ingesta sí requiere clave en demo real.
- **Checkpointer:** tablas LangGraph en la misma BD TAAM; semilla conversación con `construir_agente_taam` + `aupdate_state`.
- **Skill:** `agente-modulo-2` / `uv-python-env` para entorno.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Paquete demo TAAM: `taam_faqs.json` (8 FAQs) + `taam_faqs.schema.json` y test jsonschema; PDF sintético en `data/taam/demo/`; `sembrar_demo_taam.py` + `semilla_demo_taam.py` (COLE-LAP-001, PAC-DEMO-001/002, vínculo/alerta/hilo, código DEMO2X); guion `GUION-DEMO-TAAM.md`; README y scripts/README con sección Demo en vivo. `uv run pytest` OK (72 passed).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin PHI ni tokens reales en el diff; contraseñas solo en `.env.example`
- [x] #2 `uv run pytest tests/structured/test_taam_faqs_json_schema.py` y tests afectados por semilla pasan
- [x] #3 Scripts y README en español latinoamericano; identificadores Python ASCII
- [x] #4 Tarea marcada Done en Backlog sin `task_complete`
<!-- DOD:END -->
