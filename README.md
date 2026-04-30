# Sistema Q&A sobre la Fundación Valle del Lili — MVP fase 1

Asistente de preguntas y respuestas que responde **solo** con texto público ya descargado del sitio `valledellili.org`, usando recuperación BM25 sobre archivos Markdown completos y un modelo local vía Ollama. **No** sustituye canales oficiales ni garantiza vigencia de datos; **no** incluye chunking, embeddings ni base vectorial en esta fase.

## Descripción del problema

Hay necesidad de un canal de comunicación automatizado y preciso para la Fundación Valle del Lili: responder dudas frecuentes con trazabilidad a la fuente, reduciendo alucinaciones y manteniendo un stack reproducible para el curso.

## Planteamiento de la solución

Pipeline local: **scraping** (respetando `robots.txt`) → **Markdown** con front matter en `data/markdown/` → **BM25 a nivel archivo** (`rank-bm25`) → **Ollama** con el documento recuperado inyectado en el prompt.

Decisiones explícitas de esta fase:

- Sin chunking: cada unidad indexada es un `.md` completo.
- Sin embeddings ni base vectorial.
- Interfaz: **React 19 + Vite 7 + shadcn/ui** (`frontend/`) con backend **FastAPI + SSE** (`src/api/`). La interfaz Gradio original fue migrada y vive en `src/app/legacy/app_gradio.py` como referencia histórica.

El detalle arquitectónico queda registrado en [ADR-001](backlog/decisions/decision-1%20-%20MVP-BM25-Archivo-Completo.md) y [ADR-002](backlog/decisions/decision-2%20-%20Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md).

## Preparación de los datos

| Ubicación | Contenido |
| --- | --- |
| `data/raw/valledellili-org/` | HTML descargado del dominio `valledellili.org`, con registro en `data/raw/_log.jsonl`. |
| `data/markdown/valledellili-org/` | Un `.md` por página, con front matter YAML. |

Variables opcionales: `.env` (plantilla en `.env.example`), p. ej. `URL_BASE_SITIO`, `USER_AGENT`.

Comandos típicos (desde la raíz del repositorio):

```bash
uv run python -m scripts.scrape --max-paginas 200
uv run python -m scripts.export_markdown
```

Ayuda y opciones adicionales:

```bash
uv run python -m scripts.scrape --help
uv run python -m scripts.export_markdown --help
```

Referencia detallada de flags y orden del pipeline: [scripts/README.md](scripts/README.md).

## Modelado

- **Recuperación:** BM25 sobre el texto completo de cada archivo en `data/markdown/valledellili-org/`.
- **Generación:** modelos Ollama locales; en la app se ofrecen entre otros `llama3.1:8b` y `gemma4:e2b` (este último puede no existir en el catálogo público de Ollama; ver limitaciones).
- **Prompt:** instrucciones zero-shot anti-alucinación: uso estricto del contexto, respuesta literal *«No tengo información suficiente»* si no hay datos; tono profesional, cercano y con un toque amable en español colombiano (ver `src/qa/prompt.py`).

## Cómo correr la app

### Modo desarrollo (2 terminales)

Requisitos: Python **3.12.12**, [uv](https://docs.astral.sh/uv/), Node 22 LTS, pnpm 10.x y Ollama en ejecución.

**Terminal 1 — Backend FastAPI:**

```bash
uv python install 3.12.12
uv sync
ollama pull llama3.1:8b
uv run uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 — Frontend React:**

```bash
pnpm --dir frontend install
pnpm --dir frontend dev
```

El frontend queda disponible en `http://localhost:5173/`. El proxy de Vite reenvía `/api/*` al backend en `http://localhost:8000`.

**Nota:** si `gemma4:e2b` no está disponible en tu instalación de Ollama, omite ese `pull` y usa solo `llama3.1:8b` en la interfaz.

Variables opcionales: `OLLAMA_BASE_URL`, `MODELO_LLM_DEFECTO`, `OPENAI_API_KEY`, `ALLOWED_ORIGINS` (ver `.env.example`).

### Modo producción (Docker)

```bash
docker-compose up
```

El build multi-stage construye el frontend y lo sirve como estáticos desde FastAPI. Ver `Dockerfile` y `docker-compose.yml`.

### Experiencia en la UI (React + shadcn/ui)

- **Streaming token a token**: la respuesta del modelo aparece progresivamente en el área de chat mientras llega del backend vía Server-Sent Events (SSE).
- **Modo dual Ollama + OpenAI**: dos columnas side-by-side con una sola pasada BM25 compartida; aviso de coste dual visible.
- **Fuentes BM25**: panel de cards con archivo, score y URL clickable de los documentos recuperados.
- **Panel de configuración**: sidebar colapsable con selección de modelo, slider de `num_ctx`, editor del prompt del sistema y botón de recarga del corpus.
- **Modo oscuro**: toggle persistente entre tema claro y oscuro con paleta institucional Valle del Lili.
- **Accesibilidad**: ARIA labels en español; atajos `Cmd/Ctrl+Enter` (enviar), `Cmd/Ctrl+K` (foco en el campo de pregunta), `Cmd/Ctrl+B` (abrir/cerrar panel lateral).
- **Borrador y parámetros**: el borrador del input se recupera en la misma sesión; modelo, `num_ctx` y prompt se guardan en el navegador.

## Resultados

Los informes de evaluación automática (tarea de dataset ≥20 preguntas) se generan bajo:

**`data/processed/evaluaciones/`**

Cada corrida produce un Markdown por modelo, p. ej. `data/processed/evaluaciones/<slug-modelo>__YYYY-MM-DD.md`. El directorio conserva `.gitkeep`; los informes de ejecuciones locales suelen ignorarse en git salvo que se versionen a propósito.

Para regenerarlos (requiere Ollama y modelos instalados):

```bash
uv run python -m scripts.evaluar_qa --modelos llama3.1:8b gemma4:e2b
```

El dataset por defecto es `tests/qa/preguntas_evaluacion.yml` (23 ítems con categoría y, cuando aplica, `archivo_esperado`). Cada informe agrega, entre otros:

| Métrica (por modelo) | Origen en el informe |
| --- | --- |
| Número de preguntas ejecutadas | Tabla resumen |
| Aciertos en archivo recuperado | Comparación con `archivo_esperado` |
| Respuestas con «No tengo información suficiente» | Conteo en resumen |
| Latencia promedio | Estadística de ms por pregunta |

## Solución de problemas (streaming, CORS, Ollama)

| Síntoma | Qué revisar |
| --- | --- |
| El texto aparece **de golpe** en lugar de en streaming | Proxies/CDN pueden bufferizar SSE: en Nginx usar `proxy_buffering off`; con Cloudflare evita transformaciones en la respuesta (`Cache-Control: no-transform`). Verifica que ningún intermediario agrupe líneas SSE. |
| **CORS bloqueado** en el navegador | Configura `ALLOWED_ORIGINS` en `.env` con el origen exacto del frontend (p. ej. `http://localhost:5173`) y reinicia el backend. |
| **Ollama no responde** | Ejecuta `ollama serve`, revisa `OLLAMA_BASE_URL` y ejecuta `ollama pull llama3.1:8b` (u otro modelo que uses). Con Docker Compose, el job `ollama-init` ejecuta `ollama pull` cuando el demonio está saludable. |
| Difícil rastrear un fallo intermitente | Las respuestas incluyen cabecera `X-Request-ID`; búscala en los logs del API (middleware de peticiones). |

## Limitaciones conocidas

- Páginas muy largas pueden superar `num_ctx` (p. ej. 8192): Ollama puede **truncar** el contexto y afectar la respuesta.
- BM25 a nivel archivo puede recuperar la **página equivocada** cuando varias comparten mucho vocabulario.
- El tag `gemma4:e2b` puede no existir en el registro oficial de Ollama; si falla el `pull` o la inferencia, usar solo `llama3.1:8b` y documentar la limitación en la sustentación.

## Roadmap (Módulo 2)

- Chunking semántico del Markdown.
- Embeddings y base vectorial (p. ej. Chroma o FAISS).
- Re-ranking de candidatos recuperados.

## Paridad funcional con Gradio — smoke checklist

Verificar antes de la demo que la nueva UI cubre todas las funcionalidades de la interfaz Gradio original:

| Funcionalidad | Ruta en la nueva UI | Estado |
| --- | --- | --- |
| Streaming token a token — Ollama | Chat → enviar pregunta con motor Ollama activo | ✅ |
| Streaming token a token — OpenAI | Chat → motor OpenAI activo (requiere `OPENAI_API_KEY`) | ✅ |
| Modo dual secuencial (Ollama → OpenAI) | Settings → activar ambos motores → `DualResponseView` | ✅ |
| Selección de modelo Ollama | Settings → dropdown «Modelo Ollama» | ✅ |
| Selección de modelo OpenAI | Settings → dropdown «Modelo OpenAI» (solo visible si API key presente) | ✅ |
| Edición del prompt del sistema | Settings → accordion «Prompt del sistema» + botón Restaurar | ✅ |
| Recarga del corpus (índice BM25) | Settings → botón «Recargar corpus» | ✅ |
| Fuentes BM25 con score y URL | Panel de fuentes debajo de cada respuesta del asistente | ✅ |
| Respuesta prudente fuera de alcance | El modelo responde «No tengo información suficiente» | ✅ |
| Accesibilidad mínima | ARIA labels en español, navegación por teclado, modo oscuro | ✅ |

## Guía de demo (15 minutos)

| Tiempo | Contenido |
| --- | --- |
| **3 min** | Motivación del problema y recorrido del pipeline (raw → markdown → BM25 → FastAPI → React). Mostrar brevemente la arquitectura: sidebar de configuración, área de chat, panel de fuentes BM25. |
| **7 min** | Cuatro preguntas en vivo en la UI React: una institucional, una de servicios, una de contacto y una **fuera de alcance** (comprobar la respuesta prudente / «No tengo información suficiente»). Mostrar el streaming token a token y las cards de fuentes BM25 con scores y URLs. |
| **3 min** | Activar modo dual Ollama + OpenAI: mostrar las dos columnas con la misma pregunta, el aviso de coste dual y la diferencia de respuestas entre modelos. Editar el prompt del sistema en el accordion y restaurarlo. |
| **2 min** | Limitaciones (`num_ctx`, ambigüedad BM25, modelos) y roadmap del módulo 2 (chunking, embeddings, base vectorial). |

**Total: 15 minutos** (sin diapositivas; se usa la app React en `http://localhost:5173/` y, si aplica, el repositorio o informes en `data/processed/evaluaciones/`).

> **Decisión de arquitectura**: la migración de Gradio a React + FastAPI está documentada en [ADR-002](backlog/decisions/decision-2%20-%20Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md).
