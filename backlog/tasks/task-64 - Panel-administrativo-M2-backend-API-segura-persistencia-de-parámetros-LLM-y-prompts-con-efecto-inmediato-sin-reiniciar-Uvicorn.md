---
id: TASK-64
title: >-
  Panel administrativo M2 (backend): API segura, persistencia de parámetros LLM
  y prompts con efecto inmediato sin reiniciar Uvicorn
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-13 00:00'
updated_date: '2026-05-13 06:03'
labels:
  - modulo-2
  - fastapi
  - admin
  - postgres
  - langgraph
dependencies:
  - TASK-55
  - TASK-56
  - TASK-49
  - TASK-47
references:
  - src/api/main.py
  - src/api/factoria_grafo_agente.py
  - src/api/routers/agente.py
  - src/api/configuracion.py
  - src/agentes/router.py
  - src/agentes/meta_prompt.py
  - src/agentes/prompt_institucional.py
  - src/persistencia/modelos.py
  - src/persistencia/repositorios/usuarios.py
  - scripts/README.md
  - alembic/versions/0002_config_admin_m2.py
  - src/api/routers/admin.py
  - src/api/servicios/agente_m2_config.py
  - tests/api/test_admin_router.py
documentation:
  - .claude/skills/fastapi-sse-api/SKILL.md
  - .claude/skills/agente-modulo-2/SKILL.md
priority: high
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Contexto

Hoy el agente M2 se compila en el `lifespan` de FastAPI con `ChatOpenAI` y temperaturas fijas en código ([`src/api/factoria_grafo_agente.py`](src/api/factoria_grafo_agente.py)), el meta-prompt del router vive en JSON con recarga por `mtime` ([`src/agentes/meta_prompt.py`](src/agentes/meta_prompt.py)) y el texto institucional base del compositor en [`src/agentes/prompt_institucional.py`](src/agentes/prompt_institucional.py). No existe API administrativa ni garantía de que los cambios desde una UI afecten a las sesiones ya conectadas sin reinicio.

### Objetivo

Entregar la **capa backend** de un panel administrativo alineada a buenas prácticas (separación de capas, OpenAPI, validación Pydantic v2, pruebas automatizadas) que permita:

1. **Autenticación y autorización de administración** (mínimo viable seguro): p. ej. clave estática `ADMIN_API_KEY` en entorno + cabecera dedicada (`X-Admin-Key` o similar), documentada en `.env.example`, sin exponer la clave en logs ni en respuestas. Dejar extensible a roles/SSO en tareas futuras si el producto lo exige.

2. **Persistencia versionada de parámetros runtime** en PostgreSQL (no solo en memoria): migración Alembic con tabla dedicada (p. ej. fila singleton `config_admin_m2` o esquema clave-valor con `updated_at` y `version`), almacenando al menos:
   - identificadores de modelo OpenAI para **router** y **compositor** (strings);
   - `temperature`, `top_p` por rol (router vs compositor);
   - `model_kwargs` opcional serializado (JSON) para parámetros adicionales del proveedor cuando aplique (**nota**: muchos modelos de la API OpenAI de chat no exponen `top_k` como en Ollama; documentar en API qué campos se ignoran o se mapean a `model_kwargs`).

3. **Prompts editables** con las mismas reglas de negocio que hoy impone el dominio:
   - Contenido equivalente al schema de [`MetaPromptConfig`](src/agentes/meta_prompt.py) (o subconjunto acordado: `system_prompt`, `reglas_decision`, textos de herramientas, `saludo_template`, etc.) respetando validaciones existentes (p. ej. `respuesta_sin_contexto` canónico, herramientas obligatorias, placeholder `{nombre}`).
   - Texto base institucional del compositor (hoy `PROMPT_SISTEMA_DEFECTO` o paramétrico desde DB con fallback al archivo).

4. **Efecto inmediato sin reiniciar el proceso del servidor** para los chats de usuarios finales: tras `PATCH`/`PUT` exitoso, las **siguientes** invocaciones del grafo (p. ej. el siguiente `POST /api/agente/stream`) deben usar el snapshot actualizado. Patrones aceptables (elegir e documentar uno en ADR o doc-003):
   - lectura de snapshot al inicio de cada petición de streaming desde servicio async + construcción de instancias `ChatOpenAI` por request; o
   - objeto mutable con referencia compartida y reemplazo atómico bajo `asyncio.Lock` tras guardar en DB; o
   - `RunnableConfig` / `configurable` en LangGraph si el stack lo soporta de forma estable.

   Queda **fuera de alcance** exigir que un stream **ya abierto** cambie a mitad de tokens; el criterio es el siguiente turno o siguiente conexión SSE.

5. **Listado de usuarios registrados** (solo admin): endpoint paginado que devuelva datos mínimos desde [`Usuario`](src/persistencia/modelos.py): `id`, `nombre`, `documento_identidad` (evaluar máscara parcial en respuesta JSON por minimización de PII), `created_at`, `updated_at`, `last_login_at`. Orden estable, `limit`/`cursor` o `offset` acotados (máximo razonable).

6. **Endpoints de métricas ligeras** para alimentar un dashboard en el frontend (TASK-65): p. ej. conteo total de usuarios, usuarios activos últimos 7 días (según `last_login_at`), opcionalmente conteo de sesiones/mensajes si existe modelo o query barata sin full table scan en tablas masivas; si no hay datos, devolver ceros documentados.

7. **OpenAPI** con tags `admin`, esquemas de error coherentes (`HTTPException` con `detail` en español latinoamericano), sin volcar stack traces.

8. **Tests** con `httpx.AsyncClient`, overrides de dependencias y base de prueba o transacciones rollback según patrón del repo; casos: 401 sin clave admin, 200 lista usuarios, PATCH parámetros y luego invocación simulada o lectura de snapshot que demuestre el nuevo valor (sin llamada real a OpenAI en CI).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Migración Alembic y modelo SQLAlchemy para configuración runtime admin; `uv run alembic upgrade head` aplicable en entorno limpio
- [x] #2 Router FastAPI bajo prefijo acordado (p. ej. `/api/admin/...`) protegido por dependencia de admin; 401/403 sin credencial válida
- [x] #3 `GET` devuelve estado actual fusionado: defaults desde [`Configuracion`](src/api/configuracion.py) + overrides persistidos (documentar precedencia en docstring o README)
- [x] #4 `PATCH`/`PUT` valida rangos (`temperature` 0–2, `top_p` 0–1, modelos no vacíos) y persiste; respuesta incluye `updated_at` o `version`
- [x] #5 Tras guardar, una segunda petición (test o script) observa los nuevos valores sin reiniciar Uvicorn (mismo proceso)
- [x] #6 Listado de usuarios paginado con campos básicos acordados; sin exponer secretos ni claves
- [x] #7 Endpoint(s) de agregados para dashboard (conteos) con límites de tiempo de consulta documentados
- [x] #8 Prompts/meta-prompt editables cumplen validaciones Pydantic existentes o extensión explícita del schema
- [x] #9 `uv run pytest` verde en tests nuevos/actualizados; `ruff check` sin regresiones en archivos tocados
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Diseñar modelo de datos (tabla + enums si aplica) y migración Alembic; semilla inicial desde valores actuales de código y JSON.
2. Implementar `RepositorioConfigAdmin` (o nombre ASCII en español) y servicio de dominio async que centralice lectura/escritura y emisión de “versión” para invalidación opcional de caché en memoria.
3. Refactor mínimo en factoría del grafo o en el router de streaming: inyectar resolución de LLM y meta-prompt desde el servicio runtime en cada petición (o patrón de holder documentado).
4. Extender o encapsular [`cargar_meta_prompt_config`](src/agentes/meta_prompt.py) para aceptar fuente DB además de archivo, manteniendo validación única.
5. Añadir router `admin.py`, registrar en `main.py`, variables en `configuracion.py` y `.env.example`.
6. Tests de seguridad y de hot-reload observacional; documentar limitación de streams ya abiertos.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Seguridad**: nunca registrar el valor de `ADMIN_API_KEY`; considerar rate limiting en follow-up; CORS ya restringe orígenes — el panel admin solo debe usarse desde orígenes de confianza o VPN.
- **PII**: el listado de usuarios es datos personales; acotar retención en logs de acceso admin (auditoría opcional en tabla `admin_audit_log` como mejora futura).
- **OpenAI vs Ollama**: el producto M2 es OpenAI-first; `top_k` puede no aplicar — documentar en OpenAPI y omitir o mapear a `model_kwargs` según documentación del proveedor vigente.
- **Concurrencia**: PATCH concurrente debe dejar un único estado coherente (transacción + bloqueo optimista por `version` recomendado).
- **Compatibilidad**: con `MOCK_LLM=1`, documentar si los overrides se ignoran o se aplican parcialmente para no romper laboratorios.
- Coordinación con **TASK-65**: contrato JSON estable y versionado; cambios breaking requieren acuerdo en ambas tareas.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Backend del panel admin M2: router FastAPI bajo /api/admin con X-Admin-Key y ADMIN_API_KEY; tabla config_admin_m2 (Alembic 0002) y ServicioAgenteM2Config con fusion DB > JSON > .env; PATCH con version optimista y validacion de rangos; GET config, usuarios paginados y metricas/resumen; RuntimeAgenteBundle por peticion en /api/agente/stream. Documentacion operativa en scripts/README.md y ADMIN_API_KEY en .env.example. Tests httpx: 503 sin clave, 401 clave incorrecta o sin cabecera, 200 config/usuarios, PATCH+GET mismo proceso con sesion en memoria.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Código fusionado en rama principal del equipo con revisión de pares (si aplica al flujo del curso)
- [x] #2 Migración revisada y reversible (`downgrade` coherente)
- [x] #3 Documentación operativa mínima: variables de entorno nuevas y ejemplo de `curl` para PATCH/GET admin
- [x] #4 Pruebas automatizadas cubren auth negativa y al menos un flujo de actualización + lectura consistente
<!-- DOD:END -->
