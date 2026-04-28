---
id: TASK-18
title: 'Recuperador BM25: pasar top-3 documentos al LLM'
status: Done
assignee: []
created_date: '2026-04-28 03:54'
updated_date: '2026-04-28 04:00'
labels:
  - retrieval
  - qa
dependencies:
  - TASK-8
  - TASK-11
  - TASK-12
references:
  - src/retrieval/recuperador.py
  - src/qa/pipeline.py
  - src/qa/prompt.py
  - src/app/app_gradio.py
  - scripts/evaluar_qa.py
  - tests/retrieval/test_recuperador_bm25.py
  - backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md
ordinal: 0.0152587890625
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Hoy `RecuperadorBm25.buscar` en `src/retrieval/recuperador.py` (lineas 177-196) hace `np.argmax(scores)` y devuelve un unico `DocumentoRecuperado` (top-1). El pipeline `PipelineQa.responder` y `responder_stream` en `src/qa/pipeline.py` toman ese unico documento y lo inyectan como contexto del prompt mediante `componer_mensajes` (`src/qa/prompt.py`). En consecuencia el LLM recibe **un solo** archivo Markdown como CONTEXTO.

## Objetivo

Pasar al LLM los **3 documentos con mayor score BM25** (top-3, score > 0), concatenados en el mensaje de sistema como bloques numerados `[DOCUMENTO 1..N]` con `titulo` y `URL` por bloque, manteniendo el contrato externo del pipeline para no romper la UI Gradio ni el script de evaluacion.

## Decisiones de diseno

- Top-k **fijo a 3** con umbral `score > 0`.
- Si menos de 3 documentos tienen `score > 0`, se pasan los disponibles (1 o 2). Si ninguno, se mantiene `RecuperacionVaciaError`.
- Formato del contexto: bloques numerados con encabezado por documento, separados por una linea `---`.
- `RespuestaQa` **no** cambia su forma: sigue exponiendo una unica fuente, que apuntara al documento top-1 (mayor score). Esto preserva compatibilidad con `src/app/app_gradio.py` y `scripts/evaluar_qa.py`. Limitacion conocida: la UI no listara las 3 fuentes en esta tarea (mejora futura opcional).

## Diseno propuesto

### 1. `src/retrieval/recuperador.py`

- Extender el `Protocol` `RecuperadorDocumento` y la clase `RecuperadorBm25` con:

```python
def buscar_top(self, pregunta: str, k: int = 3) -> list[DocumentoRecuperado]: ...
```

- `buscar_top` tokeniza la pregunta con la misma funcion `tokenizar`, calcula `bm25.get_scores`, ordena por score descendente, filtra `score > 0` y retorna los primeros `k`.
- Si la lista resultante esta vacia, lanza `RecuperacionVaciaError`.
- Mantener `buscar()` por compatibilidad: implementarlo como `return self.buscar_top(pregunta, k=1)[0]`.

### 2. `src/qa/prompt.py`

- Agregar `componer_mensajes_multi(prompt_sistema, documentos: list[DocumentoRecuperado], pregunta) -> list[dict[str, str]]`.
- Bloque por documento (formato sugerido):

```text
[DOCUMENTO 1] titulo: <titulo>
URL: <source_url o "sin URL">

<contenido_md>
```

- Bloques separados por una linea con `---`.
- Encabezado del contexto: `CONTEXTO (N documentos ordenados por relevancia BM25):` y al final la instruccion: `Responde la pregunta del usuario usando solo estos CONTEXTOS. Si la respuesta no aparece en ninguno, responde: "No tengo informacion suficiente".`
- Mantener `componer_mensajes` actual o reimplementarla internamente como `componer_mensajes_multi([doc])`.

### 3. `src/qa/pipeline.py`

- Constante `K_TOP_DOCUMENTOS = 3`.
- `responder` y `responder_stream` llaman a `self._recuperador.buscar_top(pregunta, k=K_TOP_DOCUMENTOS)` en vez de `buscar`.
- Construir `RespuestaQa` con los datos del documento top-1 (`documentos[0]`): `archivo_fuente`, `source_url`, `titulo`, `score_recuperacion` reflejan al ganador.
- El bloque de contexto se arma con `componer_mensajes_multi(ps, documentos, pregunta)`.
- El catch de `RecuperacionVaciaError` sigue devolviendo "No tengo informacion suficiente".

## Identificadores ASCII

- `buscar_top`, `componer_mensajes_multi`, `K_TOP_DOCUMENTOS`.

## Restricciones del MVP

- Sigue **prohibido** importar `sklearn`, `faiss`, `chromadb`, `qdrant_client`, `sentence_transformers`, ni submodulos de embeddings de LangChain/LlamaIndex.
- Sigue **prohibido** chunking, splitting o sliding window. Se concatenan archivos `.md` completos.

## Riesgos / notas

- El contexto puede exceder `num_ctx` del modelo al concatenar 3 `.md` completos. Documentar como riesgo conocido; mitigacion futura = chunking (fuera de Fase 1 MVP).
- `RespuestaQa` solo expone una fuente (top-1). Mostrar las 3 fuentes en la UI es mejora futura.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 RecuperadorBm25.buscar_top(pregunta, k=3) devuelve hasta 3 DocumentoRecuperado ordenados por score descendente, todos con score > 0
- [x] #2 Si menos de 3 documentos tienen score > 0, buscar_top devuelve los disponibles (1 o 2). Si ninguno, lanza RecuperacionVaciaError
- [x] #3 RecuperadorBm25.buscar(pregunta) sigue devolviendo el top-1 y los tests previos en tests/retrieval/test_recuperador_bm25.py siguen pasando
- [x] #4 componer_mensajes_multi produce un mensaje system con encabezados [DOCUMENTO i] para i=1..N, separados por una linea ---, incluyendo titulo y URL por bloque
- [x] #5 PipelineQa.responder y responder_stream invocan buscar_top(..., k=K_TOP_DOCUMENTOS) y componen el contexto con componer_mensajes_multi
- [x] #6 RespuestaQa mantiene su forma actual; sus campos de fuente reflejan al documento top-1 (documentos[0])
- [x] #7 El modulo src/retrieval/recuperador.py sigue cumpliendo el import-guard del MVP (sin embeddings, chunking ni vector DB)
- [x] #8 Nuevos tests cubren: orden por score y truncamiento a k en buscar_top; caso con un unico doc score>0; componer_mensajes_multi con 3 docs incluye los marcadores [DOCUMENTO 1..3] y separadores ---
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado RecuperadorBm25.buscar_top(pregunta, k) con orden BM25 descendente, filtro score>0 y limite k; buscar() delega en buscar_top(k=1). Prompt: componer_mensajes_multi con bloques [DOCUMENTO i], separadores --- y encabezado CONTEXTO; componer_mensajes reutiliza multi con un documento. Pipeline: K_TOP_DOCUMENTOS=3, responder/responder_stream usan buscar_top + componer_mensajes_multi; RespuestaQa sigue tomando metadatos del top-1. Tests nuevos en retrieval y prompt; pytest verde (76 passed). Smoke: evaluar_qa --solo-pregunta 1 generó data/processed/evaluaciones/llama3.1-8b__2026-04-27.md. Documentación: doc-001 actualizado (diagrama y §6 BM25/top-3).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest pasa (tests previos + nuevos)
- [x] #2 Smoke manual con src/app/app_gradio.py o test de pipeline mockeando ClienteOllama: el mensaje system contiene tres bloques [DOCUMENTO i]
- [x] #3 Re-ejecutar scripts/evaluar_qa.py con un modelo y guardar el reporte en data/processed/evaluaciones/ confirmando que la UI/script no se rompen
- [x] #4 README o backlog/docs/doc-001 mencionan que el contexto pasa top-3 archivos completos (1 frase)
<!-- DOD:END -->
