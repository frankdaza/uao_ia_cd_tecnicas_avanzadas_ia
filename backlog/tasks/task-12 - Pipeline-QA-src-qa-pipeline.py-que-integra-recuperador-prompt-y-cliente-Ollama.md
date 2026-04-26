---
id: TASK-12
title: >-
  Pipeline Q&A src/qa/pipeline.py que integra recuperador, prompt y cliente
  Ollama
status: Done
assignee: []
created_date: '2026-04-26 20:17'
updated_date: '2026-04-26 21:44'
labels:
  - llm
dependencies:
  - TASK-8
  - TASK-10
  - TASK-11
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Hasta ahora los módulos están aislados: el recuperador (`RecuperadorBm25`), el cliente (`ClienteOllama`) y el prompt (`componer_mensajes`). Necesitamos un **pipeline** que orqueste los tres y exponga una función única para la UI y la evaluación.

## Objetivo

Implementar `src/qa/pipeline.py` con `PipelineQa` y un facade simple para uso desde Gradio y scripts.

## Diseño propuesto

```python
@dataclass(frozen=True)
class RespuestaQa:
    texto: str
    archivo_fuente: Path
    source_url: str
    titulo: str
    modelo: str
    score_recuperacion: float
    latencia_ms: int
    prompt_sistema_usado: str

class PipelineQa:
    def __init__(
        self,
        recuperador: RecuperadorDocumento,
        cliente: ClienteOllama,
        prompt_sistema: str = PROMPT_SISTEMA_DEFECTO,
    ) -> None: ...

    def responder(self, pregunta: str, modelo: str | None = None) -> RespuestaQa: ...
```

## Detalles técnicos

1. `responder(pregunta)`:
   - `t_inicio = time.perf_counter()`
   - `documento = self.recuperador.buscar(pregunta)` (manejar `RecuperacionVaciaError` → devolver `RespuestaQa` con texto fijo "No tengo información suficiente" y `archivo_fuente=None`).
   - `mensajes = componer_mensajes(self.prompt_sistema, documento.contenido, pregunta, metadata={...})`
   - Si `modelo` se pasa, sobreescribir `self.cliente.configuracion.modelo` para esa llamada (sin mutar permanente).
   - `texto = self.cliente.chat(mensajes)`.
   - `latencia_ms = (time.perf_counter() - t_inicio) * 1000`.
   - Devolver `RespuestaQa(...)`.

2. Manejo de errores:
   - `RecuperacionVaciaError`: respuesta amable con la frase clave.
   - `OllamaNoAccesibleError` y `ModeloNoDisponibleError`: **propagar** (la UI muestra el mensaje al usuario, sin reintentar acá).

3. Inmutabilidad:
   - `prompt_sistema` se inyecta en el constructor pero `responder()` admite override por llamada vía un parámetro opcional `prompt_sistema: str | None = None` para que la UI pueda enviar un prompt editado en caliente sin reinstanciar el pipeline.

## Facade simple

```python
def construir_pipeline_por_defecto(
    directorio_markdown: Path = Path("data/markdown/valledellili-org"),
) -> PipelineQa:
    recuperador = RecuperadorBm25(directorio_markdown)
    cliente = ClienteOllama(ConfiguracionLlm())  # lee .env
    return PipelineQa(recuperador, cliente)
```

## Identificadores ASCII

- `PipelineQa`, `RespuestaQa`, `responder`, `construir_pipeline_por_defecto`.

## Tests

- `test_pipeline_responde_pregunta_valida`: usa fixture markdown + `ClienteOllama` mockeado; verifica que `archivo_fuente` apunta al `.md` esperado y `texto` es el simulado.
- `test_pipeline_recuperacion_vacia`: simular `RecuperacionVaciaError` → `texto == "No tengo información suficiente"`.
- `test_pipeline_propaga_errores_ollama`: simular `OllamaNoAccesibleError` → la excepción se propaga.
- `test_pipeline_acepta_prompt_override`: invocar `responder(pregunta, prompt_sistema="prompt custom")` y verificar que el cliente recibe ese prompt y no el por defecto.
- `test_pipeline_modelo_override`: invocar `responder(pregunta, modelo="gemma4:e2b")` y verificar que el body HTTP usa ese modelo (mock).

## Caso de negocio

La UI Gradio (task-13) llamará `pipeline.responder(pregunta, modelo=eleccion_radio, prompt_sistema=textbox_prompt)` y mostrará `RespuestaQa` con metadatos (archivo fuente, score, latencia) para que el evaluador pueda auditar la trazabilidad de la respuesta.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 PipelineQa.responder(pregunta) devuelve RespuestaQa con texto, archivo_fuente, source_url, modelo, score_recuperacion y latencia_ms
- [x] #2 Si el recuperador no encuentra documento, RespuestaQa.texto es 'No tengo información suficiente' y archivo_fuente es None
- [x] #3 responder() acepta override de modelo (e.g. 'gemma4:e2b') sin mutar el cliente permanentemente
- [x] #4 responder() acepta override de prompt_sistema para soportar la edición desde la UI
- [x] #5 Errores OllamaNoAccesibleError y ModeloNoDisponibleError se propagan sin transformación
- [x] #6 Existe construir_pipeline_por_defecto() que arma el pipeline con las dependencias estándar
- [x] #7 Tests unitarios en tests/qa/test_pipeline.py cubren los 5 casos definidos y pasan con uv run pytest
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Crear src/qa/pipeline.py con dataclasses
2) Implementar PipelineQa.responder con manejo de errores
3) Implementar construir_pipeline_por_defecto()
4) Tests con mocks (responder OK, recuperación vacía, errores Ollama, override de modelo y prompt)
5) Smoke test manual contra Ollama si está disponible
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado src/qa/pipeline.py: RespuestaQa, PipelineQa con responder() (latencia con perf_counter, override de modelo sin mutar, override de prompt_sistema, RecuperacionVaciaError con mensaje fijo y archivo_fuente None, propagacion de errores Ollama). construir_pipeline_por_defecto() usa RecuperadorBm25 y ConfiguracionLlm.desde_variables_entorno(). En cliente_ollama se agrego propiedad publica configuracion para alinear con el diseno. Tests en tests/qa/test_pipeline.py (7 casos) y tests/qa/conftest.py. Pytest: 60 passed. Smoke: pipeline+Ollama con corpus valledellili respondio no vacio.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin lógica de chunking, embeddings ni vector DB en el pipeline
- [x] #2 Latencia se mide en ms con time.perf_counter (no datetime.now)
- [x] #3 Smoke test manual contra Ollama real con llama3.1:8b devolviendo una respuesta no vacía
<!-- DOD:END -->
