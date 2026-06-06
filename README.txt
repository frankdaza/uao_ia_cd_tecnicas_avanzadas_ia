================================================================================
  TÉCNICAS AVANZADAS DE IA — UNIVERSIDAD AUTÓNOMA DE OCCIDENTE (UAO)
  Maestría en Inteligencia Artificial y Ciencia de Datos
================================================================================

REPOSITORIO
  https://github.com/frankdaza/uao_ia_cd_tecnicas_avanzadas_ia

INTEGRANTES DEL GRUPO
  - Viviana Valle Fernández
  - Alvaro Julian Barco Ocampo
  - Andrés Fernando López Rendón
  - Frank Edward Daza González

--------------------------------------------------------------------------------
RESUMEN DEL WORKSPACE
--------------------------------------------------------------------------------

Este repositorio es un monorepo del curso Técnicas Avanzadas de IA Aplicadas
a Modelos de Lenguaje. Contiene tres proyectos ejecutables (proyecto-1,
proyecto-2 y proyecto-3), un corpus y datos compartidos en data/, y la gestión
de tareas y decisiones arquitectónicas en backlog/. Cada proyecto corresponde
a una fase o variante del trabajo del grupo sobre asistentes conversacionales
para la Fundación Valle del Lili.

Estructura general:

  data/ (corpus compartido)
    |
    +-- proyecto-1/  -->  M2: agente institucional (LangGraph + Qdrant + React)
    |
    +-- proyecto-2/  -->  M3 FINAL: TAAM Ruta A (LangChain + FastAPI + Telegram)
    |
    +-- proyecto-3/  -->  M3 paralelo: TAAM Ruta B (OpenFang + Telegram)

--------------------------------------------------------------------------------
PROYECTO 1 — proyecto-1/ (Módulo 2)
--------------------------------------------------------------------------------

Asistente conversacional institucional sobre contenido público de la Fundación
Valle del Lili. Evoluciona el trabajo del Módulo 1 (scraping, corpus en
data/markdown/) hacia un agente productivo con memoria persistente y RAG denso.

Stack principal:
  - LangGraph (router del agente)
  - LangChain (herramientas y memoria con langchain-postgres)
  - LlamaIndex + Qdrant (recuperación densa por embeddings)
  - PostgreSQL (usuarios e historial conversacional)
  - FastAPI + SSE (POST /api/sesiones, POST /api/agente/stream)
  - Frontend React 19 + Vite 8 + Tailwind v4 + shadcn/ui

Rol en el repositorio: producto del Módulo 2. Permanece operativo e
independiente; no es el entregable final del Módulo 3.

--------------------------------------------------------------------------------
PROYECTO 2 — proyecto-2/ (Módulo 3 — PROYECTO FINAL)
--------------------------------------------------------------------------------

Bot posoperatorio TAAM (Bot Lili): seguimiento postoperatorio de pacientes
mediante Telegram y panel web para personal clínico (staff). Aplicación
independiente del asistente M2 en proyecto-1/.

Ruta A — Arquitectura Tradicional (adoptada como proyecto final):
  - LangChain: create_agent, function calling estricto con esquemas Pydantic,
    PostgresSaver (memoria/checkpointer), HumanInTheLoopMiddleware en triage
    urgente, RAG con vector stores de LangChain.
  - API REST FastAPI: POST /chat (conversación del agente) y webhook Telegram
    vía 2 (integración en el mismo servicio, sin N8N).
  - Canal MVP: Telegram (webhook en FastAPI).
  - PostgreSQL dedicado (base taam, aislada de M2) y Qdrant con colección
    taam_protocolos para protocolos médicos.
  - Frontend React propio para administración clínica.

Comparte con el workspace solo la carpeta data/ (vía rutas_workspace); no
importa código de proyecto-1/ en runtime.

--------------------------------------------------------------------------------
PROYECTO 3 — proyecto-3/ (Módulo 3 — exploración paralela)
--------------------------------------------------------------------------------

Implementación demostrativa del Módulo 3 usando OpenFang como Agent OS
(Ruta B). Incluye chat del paciente por Telegram, Hand autónomo
(taam_lili_hand), ingesta de corpus hacia memoria del OS y análisis opcional
t-SNE sobre historial de sesiones.

Rol en el repositorio: exploración paralela de la Ruta B para comparación y
sustentación. No sustituye el MVP evaluable ni el proyecto final en
proyecto-2/. Usa un bot de Telegram distinto al de la Ruta A.

--------------------------------------------------------------------------------
DECISIÓN FINAL
--------------------------------------------------------------------------------

Tras evaluar las dos rutas arquitectónicas del Módulo 3, el grupo adoptó
como proyecto final la carpeta proyecto-2/, siguiendo la RUTA A: Arquitectura
Tradicional (LangChain, API REST y Telegram).

Esta decisión queda registrada en backlog/decisions/decision-7 (status:
accepted). El canal de mensajería implementado en el MVP es Telegram vía 2
(webhook y envío de mensajes en el mismo servicio FastAPI), en lugar de
WhatsApp o N8N, según lo documentado en la arquitectura del proyecto.

El proyecto-3/ permanece como trabajo paralelo de Ruta B (OpenFang) para
demostración comparativa en sustentación, sin reemplazar el entregable
principal.

--------------------------------------------------------------------------------
REFERENCIAS
--------------------------------------------------------------------------------

Documentación operativa:
  - proyecto-1/README.md
  - proyecto-2/README.md
  - proyecto-3/README.md
  - README.md (índice del workspace)

Decisiones arquitectónicas:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - backlog/decisions/decision-7 - Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - backlog/decisions/decision-8 - Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md

Guías de arquitectura:
  - backlog/docs/doc-004 - Arquitectura-M3-Bot-Posoperatorio-TAAM.md
  - backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md

================================================================================
