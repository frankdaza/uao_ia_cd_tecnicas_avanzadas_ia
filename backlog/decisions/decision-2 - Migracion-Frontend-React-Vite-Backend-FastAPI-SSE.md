---
id: decision-2
title: Migración del frontend de Gradio a React 19 + Vite 7 y adición de backend FastAPI + SSE
date: '2026-04-30'
status: accepted
---

## Contexto

En la fase 1 del proyecto (ver [decision-1 — MVP BM25 a nivel archivo](decision-1%20-%20MVP-BM25-Archivo-Completo.md)) se usó **Gradio** como interfaz de prototipado rápido. Gradio cumplió su función durante el desarrollo inicial pero presenta limitaciones para la entrega final y el módulo 2:

- **Restricciones de diseño visual**: los temas de Gradio no permiten implementar una identidad visual institucional (paleta Valle del Lili, tipografía, modo oscuro completo, animaciones de calidad).
- **Acoplamiento del proceso**: Gradio y el pipeline Python corren en el mismo proceso; no hay separación entre capa de datos y capa de presentación.
- **Sin API HTTP**: otros consumidores (scripts de evaluación con análisis, herramientas externas, módulo 2 con chunking + embeddings) no pueden llamar al pipeline directamente.
- **Limitaciones de UX**: el modo dual (Ollama + OpenAI con streaming paralelo) requiere lógica personalizada difícil de implementar limpiamente en Gradio.
- **Extensibilidad**: agregar nuevas vistas (historial de conversaciones, métricas de recuperación, comparativa de modelos) es muy costoso en Gradio.

El equipo necesita una interfaz de **alto impacto visual** para la sustentación y una arquitectura más limpia para el módulo 2.

## Decisión

### Backend HTTP

Introducir una capa HTTP en `src/api/` con:

- **FastAPI** como framework web ASGI por su ecosistema Python, integración nativa con Pydantic v2 y soporte de async.
- **Uvicorn** con extras `standard` como servidor ASGI.
- **sse-starlette** para endpoints de streaming Server-Sent Events (SSE), que permiten streaming token a token desde Ollama y OpenAI sin WebSockets.
- **pydantic-settings** para cargar configuración desde `.env` con validación.
- El `PipelineQa` de `src/qa/pipeline.py` se reutiliza **íntegramente** sin modificar; FastAPI lo envuelve como servicio HTTP.

### Frontend

Reemplazar `src/app/app_gradio.py` por una SPA en `frontend/` con:

- **React 19** + **Vite 7** + **TypeScript 5** (strict) — stack estándar de la industria para SPAs.
- **Tailwind CSS v4** (plugin Vite) — utilities-first con soporte nativo para variables CSS y modo oscuro.
- **shadcn/ui** (Radix UI + lucide-react) — componentes accesibles y altamente personalizables con identidad visual propia.
- **Vercel AI SDK** (`ai`, `@ai-sdk/react`) con transport personalizado — patrón moderno para chat con LLMs y streaming.
- **@tanstack/react-query v5** — cache y sincronización de datos del backend.
- **next-themes** — modo oscuro persistente.
- **react-markdown** + **remark-gfm** + **shiki** — render de Markdown enriquecido con syntax highlighting.
- **pnpm 11.1.1** (pin en `packageManager` de `frontend/package.json`) como gestor de paquetes del frontend.

### Estrategia de streaming

`EventSource` nativo del navegador no soporta `POST` con body JSON. La decisión es usar `fetch + ReadableStream + TextDecoderStream` para parsear eventos SSE del servidor. Este patrón es compatible con todos los browsers modernos y permite enviar el body completo de la petición.

### Arquitectura monorepo ligero

- `frontend/` en la raíz del repositorio, junto a `src/`.
- En desarrollo: Vite en puerto 5173 con proxy `/api` → `localhost:8000` (FastAPI).
- En producción: `pnpm build` genera `frontend/dist/`; FastAPI lo sirve como `StaticFiles`.

### Preservación de Gradio

`src/app/app_gradio.py` se mueve a `src/app/legacy/app_gradio.py` como referencia histórica. No se elimina del repositorio. `gradio` puede mantenerse como dependencia opcional para los scripts de evaluación batch si el equipo lo decide.

## Consecuencias

### Positivas

- **Alta calidad visual**: UI institucional con paleta Valle del Lili, modo oscuro, animaciones, skeleton loaders y diseño responsive mobile-first.
- **Streaming mejorado**: SSE nativo en el navegador, sin polling ni long-polling; tokens aparecen inmediatamente.
- **Separación de responsabilidades**: el backend Python es ahora un servicio HTTP independiente; el frontend es una SPA desacoplada.
- **API reutilizable**: `src/api/` puede ser consumida por scripts de evaluación, notebooks y el módulo 2.
- **Modo dual limpio**: una sola pasada BM25 (`preparar_contexto_inferencia`) compartida entre Ollama y OpenAI; el frontend diferencia respuestas por campo `motor` en los eventos SSE.
- **Accesibilidad**: Radix UI garantiza ARIA correcto; shadcn/ui facilita componentes a prueba de accesibilidad.
- **Tests independientes**: el backend FastAPI puede testearse con `httpx` sin levantar el frontend; el frontend con Vitest + Playwright.

### Negativas / Riesgos

- **Doble dependencia**: el entorno de desarrollo necesita Python (uv) **y** Node (pnpm). Puede complicar onboarding de nuevos colaboradores.
- **`EventSource` no soporta POST**: requiere implementación manual de SSE con `fetch + ReadableStream`. Más código de infraestructura en el frontend.
- **CORS en desarrollo**: configurar `CORSMiddleware` correctamente; riesgo de errores al cambiar puertos.
- **Tamaño del repo**: `frontend/node_modules` (ignorado en git), `frontend/dist` — añadir a `.gitignore`.
- **Identificadores en inglés**: en `frontend/**/*.{ts,tsx}` los identificadores usan convención inglesa (React/TS), lo que contrasta con la convención español-ASCII del código Python. Documentado en `language-conventions.mdc` como excepción explícita.

## Alternativas consideradas

| Alternativa | Razón de rechazo |
| --- | --- |
| **Next.js** en lugar de Vite | Overhead de SSR innecesario para una SPA académica; configuración más compleja; no agrega valor para este proyecto. |
| **Streamlit** | Mismas limitaciones de diseño que Gradio; no resuelve el problema de la identidad visual. |
| **WebSockets** en lugar de SSE | Bidireccional pero innecesario para streaming unidireccional LLM → usuario. SSE es más simple, funciona sobre HTTP/1.1 y tiene mejor soporte en proxies. |
| **Mantener Gradio** | No satisface el requisito de alto impacto visual ni la separación de capas. |
| **Django + DRF** | Más pesado que FastAPI para una API JSON/SSE; menor ecosistema async nativo. |
| **Litestar** | Alternativa moderna a FastAPI pero ecosistema más pequeño; menor adopción en el curso. |

## Referencias

- [doc-002 — Guía de arquitectura de la migración](../docs/doc-002%20-%20Migracion-Frontend-React-Vite-Backend-FastAPI.md)
- [doc-001 — MVP Fase 1 con Gradio y BM25](../docs/doc-001%20-%20MVP-Fase-1-Proyecto-Final-QA-BM25.md)
- [decision-1 — MVP usa BM25 a nivel archivo](decision-1%20-%20MVP-BM25-Archivo-Completo.md)
- Skills: `.claude/skills/react-vite-qa-ui/SKILL.md`, `.claude/skills/fastapi-sse-api/SKILL.md`
- Reglas: `.cursor/rules/frontend-style.mdc`, `.cursor/rules/api-fastapi.mdc`, `.cursor/rules/language-conventions.mdc`
