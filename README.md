# Sistema Q&A sobre la Fundación Valle del Lili — MVP fase 1

Asistente de preguntas y respuestas que responde **solo** con texto público ya descargado del sitio `valledellili.org`, usando recuperación BM25 sobre archivos Markdown completos y un modelo local vía Ollama. **No** sustituye canales oficiales ni garantiza vigencia de datos; **no** incluye chunking, embeddings ni base vectorial en esta fase.

## Descripción del problema

Hay necesidad de un canal de comunicación automatizado y preciso para la Fundación Valle del Lili: responder dudas frecuentes con trazabilidad a la fuente, reduciendo alucinaciones y manteniendo un stack reproducible para el curso.

## Planteamiento de la solución

Pipeline local: **scraping** (respetando `robots.txt`) → **Markdown** con front matter en `data/markdown/` → **BM25 a nivel archivo** (`rank-bm25`) → **Ollama** con el documento recuperado inyectado en el prompt.

Decisiones explícitas de esta fase:

- Sin chunking: cada unidad indexada es un `.md` completo.
- Sin embeddings ni base vectorial.
- Interfaz de prueba: **Gradio** únicamente (`src/app/app_gradio.py`).

El detalle arquitectónico queda registrado en [ADR-0001](backlog/decisions/decision-1%20-%20MVP-BM25-Archivo-Completo.md).

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

Requisitos: Python **3.12.12** y [uv](https://docs.astral.sh/uv/). Ollama en ejecución con los modelos instalados.

```bash
uv python install 3.12.12
uv sync
ollama pull llama3.1:8b
ollama pull gemma4:e2b
```

**Nota:** si `gemma4:e2b` no está disponible en tu instalación de Ollama, omite ese `pull` y usa solo `llama3.1:8b` en la interfaz.

Variables opcionales: `OLLAMA_BASE_URL`, `MODELO_LLM_DEFECTO` (ver `.env.example`).

```bash
uv run python -m src.app.app_gradio
```

La consola muestra la URL local (por defecto `http://127.0.0.1:7860/`).

### Experiencia en la UI

- **Streaming token a token**: la respuesta del modelo aparece progresivamente en el bloque de Markdown a medida que Ollama la genera (no hay que esperar a que termine para ver texto).
- **Indicador de carga**: al presionar **Preguntar**, el botón se deshabilita y cambia su texto a `Pensando...` durante toda la consulta; vuelve a `Preguntar` cuando finaliza, incluso si Ollama no estaba accesible o el modelo no existe.
- **Formato Markdown enriquecido**: el prompt de sistema instruye al modelo a usar títulos (`##`), listas con viñetas, **negritas**, `código en línea` y enlaces `[texto](URL)` cuando aporte claridad. La columna de respuesta usa CSS mínimo para tipografía y espaciado más legibles.

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

## Limitaciones conocidas

- Páginas muy largas pueden superar `num_ctx` (p. ej. 8192): Ollama puede **truncar** el contexto y afectar la respuesta.
- BM25 a nivel archivo puede recuperar la **página equivocada** cuando varias comparten mucho vocabulario.
- El tag `gemma4:e2b` puede no existir en el registro oficial de Ollama; si falla el `pull` o la inferencia, usar solo `llama3.1:8b` y documentar la limitación en la sustentación.

## Roadmap (Módulo 2)

- Chunking semántico del Markdown.
- Embeddings y base vectorial (p. ej. Chroma o FAISS).
- Re-ranking de candidatos recuperados.

## Guía de demo (15 minutos)

| Tiempo | Contenido |
| --- | --- |
| **3 min** | Motivación del problema y recorrido del pipeline (raw → markdown → BM25 → Ollama → Gradio). |
| **7 min** | Cuatro preguntas en vivo: una institucional, una de servicios, una de contacto y una **fuera de alcance** (comprobar la respuesta prudente / «No tengo información suficiente»). |
| **3 min** | Editar el prompt del sistema en la UI y mostrar cómo cambia el comportamiento (tono o reglas). |
| **2 min** | Limitaciones (`num_ctx`, ambigüedad BM25, modelos) y roadmap del módulo 2. |

**Total: 15 minutos** (sin diapositivas; se usa la app y, si aplica, el repositorio o informes en `data/processed/evaluaciones/`).
