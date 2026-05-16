---
id: doc-005
title: Auditoria de imports hacia src/rag, src/qa y src/app (baseline migracion clean-enough M2)
type: reference
created_date: '2026-05-16'
modulo: 2
status: vigente
---

# Auditoria de imports hacia `src/rag`, `src/qa` y `src/app`

Este documento cumple la tarea **TASK-85**: inventario reproducible de quien referencia los paquetes sensibles a la migracion incremental descrita en [decision-6 — Migracion incremental Clean Architecture M2](../decisions/decision-6%20-%20Migracion-Incremental-Clean-Architecture-M2.md), alineado al estudio [doc-004](doc-004%20-%20Estudio-Migracion-Clean-Architecture.md).

## 1. Resumen

| Paquete | Consumo desde nucleo M2 (`src/agentes`, `src/api` fuera de settings) | Scripts | Tests | Notas |
| --- | --- | --- | --- | --- |
| `src.rag` | Si: herramientas RAG/listados, router (imports diferidos), `main.py` (reranker) | Si (ingesta y eval) | Amplio | `src.rag` **importa** `src.api.configuracion` (dependencia hacia la capa HTTP de settings). |
| `src.qa` | No hay imports directos en `src/agentes` ni `src/api` | No | Si (`tests/qa`, prueba de router con `importlib`) | Paquete acotado a laboratorio M1 y pruebas; el runtime del agente M2 no lo importa por ruta estable actual. |
| `src.app` | Ninguno con patron `from src.app` / `import src.app` | No | No | Arbol residual (`__init__.py` en `src/app/` y `src/app/legacy/`); retiro previsto en TASK-87. |

**Notebooks:** no hay `.ipynb` en el repositorio (busqueda `**/*.ipynb` vacia).

**CI:** workflows bajo `.github/` sin coincidencias de `src.rag`, `src.qa` ni `src.app` en el momento de la auditoria.

## 2. Tabla modulo-consumidor — `src.rag`

| Area consumidora | Rol | Archivos representativos |
| --- | --- | --- |
| `src/agentes/herramientas/` | Tool RAG denso y listados estructurados | `rag_tool.py`, `listar_estructurado_tool.py` |
| `src/agentes/router.py` | Inferencia de intencion y filtros (imports **dentro de funciones**) | Lineas con `from src.rag.intencion`, `filtros_listado_heuristica` |
| `src/api/main.py` | Carga opcional de reranker | `RerankerCrossEncoder` (import condicional en lifespan o similar) |
| `src/rag/` | Autoreferencias del paquete | `__init__.py`, `recuperador_denso.py` (imports diferidos locales), `recuperador_listados.py`, `filtros_listado_heuristica.py` |
| `scripts/` | Ingesta Qdrant y evaluacion batch | `indexar_corpus_qdrant.py`, `eval_metricas_rag.py`, `eval_recuperacion_consultas.py`, `verificar_sedes_en_qdrant.py` |
| `tests/agentes/` | Pruebas de tools que tocan listados | `test_listar_estructurado_tool.py` |
| `tests/api/admin/` | E2E admin / bundle | `test_admin_e2e.py` |
| `tests/rag/` | Cobertura unitaria e integracion RAG | Multiples modulos `test_*.py` (embeddings, Qdrant, recuperador, MMR, metricas, etc.) |
| `tests/scripts/` | Ingesta y reintentos | `test_indexar_corpus_qdrant.py`, `test_indexar_corpus_qdrant_markdown.py`, `test_ingesta_retry.py` |
| `backlog/tasks/` | Documentacion de smoke futuro | `task-86` menciona import de verificacion post-reorganizacion (no es codigo ejecutable del producto) |

### 2.1. Dependencia inversa (riesgo de capas)

Varios modulos bajo `src/rag/` importan **`src.api.configuracion`** (`Configuracion`, `obtener_configuracion`): por ejemplo `qdrant_store.py`, `embeddings.py`, `recuperador_denso.py`. No se detecto `src.rag` → `src.agentes`, pero el enlace **RAG → API (settings)** implica que una reorganizacion de `src/rag` debe mantener o sustituir ese acceso a configuracion (puerto hacia infraestructura).

### 2.2. Imports diferidos y estilo

- **`src/agentes/router.py`**: varios `from src.rag...` dentro del cuerpo de funciones (carga perezosa / acoplamiento local).
- **`src/rag/recuperador_denso.py`**: imports locales en metodos para embeddings, vector store, MMR y reranker.

Estos patrones **no aparecen** con una simple busqueda estatica de dependencias entre modulos de primer nivel; conviene tenerlos en cuenta en TASK-86.

## 3. Tabla modulo-consumidor — `src.qa`

| Area consumidora | Rol | Archivos representativos |
| --- | --- | --- |
| `src/qa/` | Autoreferencias del paquete laboratorio | `__init__.py`, `prompt.py` |
| `tests/qa/` | Pruebas de clientes Ollama/OpenAI y prompts | `test_cliente_ollama.py`, `test_cliente_openai.py`, `test_prompt.py`, `test_cliente_ollama_num_ctx_override.py` |
| `tests/qa/` | Dataset / evaluacion textual | `test_preguntas_evaluacion_dataset.py` |
| `tests/agentes/` | Carga dinamica del modulo prompt para pruebas del grafo | `test_router_grafo.py` (`importlib.import_module("src.qa.prompt")`, manipulacion de `sys.modules`) |

**Nucleo M2:** no hay coincidencias de `src.qa` bajo `src/agentes/` ni `src/api/` (salvo cadenas en tests que parchean `src.qa.*`).

## 4. Tabla modulo-consumidor — `src.app`

| Area consumidora | Patron `from src.app` / `import src.app` |
| --- | --- |
| Codigo Python (`src/`, `scripts/`, `tests/`) | **Ninguno** |
| Estado del arbol | `src/app/__init__.py`, `src/app/legacy/__init__.py` (paquetes vacios de codigo ejecutable) |

Referencias historicas en **documentacion y backlog** (comandos `python -m src.app.app_gradio`, tareas completadas) no constituyen imports de runtime; TASK-87 cubre retiro y alineacion documental.

## 5. Riesgos para TASK-86 y siguientes

| Riesgo | Detalle |
| --- | --- |
| Imports diferidos | `router.py` y `recuperador_denso.py`: el grafo o el recuperador pueden ocultar dependencias a `src.rag` respecto a herramientas estaticas ingenuas. |
| Import dinamico | `tests/agentes/test_router_grafo.py` usa `importlib` sobre `src.qa.prompt`; un renombre de paquete (TASK-89) debe actualizar cadenas y `sys.modules`. |
| Cadenas y parches | Tests que usan `patch("src.qa.cliente_openai.OpenAI", ...)` dependen del nombre de modulo completo. |
| Acoplamiento RAG ↔ settings HTTP | `src.rag` depende de `src.api.configuracion`; mover `rag` sin mover settings exige extraer un modulo de configuracion neutro (o aceptar el acoplamiento documentado). |
| `pyproject.toml` | No define paquetes extra como consumidores de estos modulos; entrypoints actuales no apuntan a `src.app` en el codigo auditado. |
| Ciclos | No se observo `src.rag` importando `src.agentes`; el flujo principal sigue siendo agente/API → rag. |

## 6. Comandos reproducibles (ripgrep)

Desde la raiz del repositorio:

```bash
rg "from src\\.rag|import src\\.rag" --glob '!**/.git/**'
rg "from src\\.qa|import src\\.qa" --glob '!**/.git/**'
rg "from src\\.app|import src\\.app" --glob '!**/.git/**'
```

Búsqueda complementaria para referencias textuales o rutas:

```bash
rg "src\\.app" --glob '!**/.git/**' --glob '*.py'
```

## 7. Anexo: conteo resumido de coincidencias (2026-05-16)

Los comandos de la seccion 6 produjeron, en este arbol:

- **`src.rag` / `import src.rag`**: decenas de lineas en `src/rag`, `src/agentes`, `src/api/main.py`, `scripts/`, `tests/` y una mencion en `backlog/tasks/task-86`.
- **`src.qa`**: pocas lineas en `src/qa`, `tests/qa` y uso dinamico en `tests/agentes/test_router_grafo.py`; entradas adicionales en **backlog completado** y docs historicos (no son imports del runtime M2).
- **`src.app` (import directo)**: **0** coincidencias en codigo de producto, scripts y tests.

## 8. Baseline de pruebas (`uv run pytest`)

| Campo | Valor |
| --- | --- |
| Comando | `uv run pytest` (raiz del repo) |
| Fecha | 2026-05-16 |
| Entorno | Python 3.12.12 (pytest 9.x segun sesion) |
| Resultado | **1 failed**, **375 passed**, **9 skipped** |
| Fallo | `tests/api/test_admin_router.py::test_admin_config_503_cuando_no_hay_clave` — se esperaba HTTP 503 y se obtuvo **401** cuando `ADMIN_API_KEY` esta vacia. |

La auditoria de imports **no modifica** ese comportamiento; el fallo queda como **riesgo conocido del baseline** para migraciones posteriores (ejecutar de nuevo `uv run pytest` tras cambios en TASK-86).

## 9. Referencias

- [doc-003 — Arquitectura operativa del agente M2](doc-003%20-%20Arquitectura-Agente-Modulo-2.md)
- [doc-004 — Estudio de migracion](doc-004%20-%20Estudio-Migracion-Clean-Architecture.md)
- [decision-6 — Migracion incremental](../decisions/decision-6%20-%20Migracion-Incremental-Clean-Architecture-M2.md)
