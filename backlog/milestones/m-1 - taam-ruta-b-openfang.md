---
id: m-1
title: "TAAM Ruta B (OpenFang + Telegram + t-SNE)"
---

## Description

Milestone del **Bot posoperatorio TAAM — Ruta B (Módulo 3)** en [`proyecto-3/`](../../proyecto-3/): implementación **paralela** del Bot Lili con **OpenFang** como Agent OS (chat reactivo, Hands con cron, memoria del OS, bridge Telegram nativo) y bonus **Ruta Transversal B** (t-SNE/UMAP sobre historial JSONL/SQLite del OS).

No sustituye el producto M2 en `proyecto-1/` ni el MVP **Ruta A** en `proyecto-2/` agrupado en milestone **m-0**.

## ADR y documentación de referencia

- **ADR vigente:** [decision-8 — Arquitectura M3 TAAM en proyecto-3 (Ruta B)](../decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md) (`status: accepted`)
- **Guía operativa Ruta B:** [doc-008 — Arquitectura M3 TAAM Ruta B OpenFang](../docs/doc-008%20-%20Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md) (cierre TASK-133)
- **Evaluación previa:** [doc-007 — Evaluación OpenFang](../docs/doc-007%20-%20Evaluacion-OpenFang-Proyecto-2-TAAM.md)
- **Guion demo 15 min:** [guion-demo-ruta-b.md](../../proyecto-3/docs/guion-demo-ruta-b.md)
- **Casos de uso TAAM:** [Caso de Uso TAAM — Bot Posoperatorio](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)
- **Actividad M3:** [Actividad del Módulo 3](../docs/actividades/Actividad%20del%20M%C3%B3dulo%203_%20Productizaci%C3%B3n%2C%20Despliegue%20Avanzado%20y%20Sistemas%20Ag%C3%A9nticos.md)

## Casos de uso TAAM cubiertos (Ruta B)

| UC | Cobertura en `proyecto-3` |
| --- | --- |
| UC1 Ingesta conocimiento | **Parcial** — script Python → Vector Store + Structured KV OpenFang |
| UC4 Panel seguimiento | **Parcial** — dashboard OpenFang + consulta JSONL (sin panel React) |
| UC6 Recordatorios | **Cubierto** — Hand `taam_lili_hand` cron |
| UC7 Evidencias | **Parcial** — solo texto (MVP Ruta B) |
| UC8 Chat paciente | **Cubierto** — Telegram + RAG memoria semántica |
| UC2, UC3, UC5, UC9 | **Fuera de alcance** — documentado en decision-8 |

## Rúbrica Módulo 3 — Ruta B

- Agent OS (OpenFang) con ingesta de conocimiento corporativo
- Hand autónomo (`HAND.toml` + prompts)
- Canal Telegram (token BotFather dedicado)
- Bonus transversal: notebook t-SNE sobre sesiones del OS

## Tareas del milestone

Tareas **task-117** … **task-133** (17 ítems), asignadas a Frank Daza, dependencias estrictamente ascendentes por número. El cierre documental del milestone es **TASK-133** (README, guion demo, doc-008).

## Relación con m-0

- **m-0:** Ruta A LangChain + FastAPI + Postgres/Qdrant en `proyecto-2/` (task-95..task-116)
- **m-1:** Ruta B OpenFang en `proyecto-3/` (task-117..task-133)
