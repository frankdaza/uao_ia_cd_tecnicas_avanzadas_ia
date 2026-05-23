---
id: TASK-75
title: 'BUG: eliminar doble llamada de embedding por consulta en recuperador denso'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 23:26'
updated_date: '2026-05-15 01:01'
labels:
  - rag
  - performance
  - bug
  - modulo-2
dependencies: []
references:
  - src/rag/recuperador_denso.py
  - src/rag/embeddings.py
  - tests/rag/test_recuperador_denso_pipeline.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

En `src/rag/recuperador_denso.py`, `RecuperadorDenso.consultar` invoca `embeddings.get_query_embedding(consulta_limpia)` (lineas 367-372). Dentro del mismo flujo, `_pares_filtrados` (lineas 187-188) vuelve a invocar `get_query_embedding(consulta_limpia)`. El resultado: **dos llamadas al proveedor de embeddings por consulta** (OpenAI o local), duplicando coste, latencia y exposicion a no-determinismo si el proveedor llegara a devolver vectores ligeramente distintos.

## Estado actual (simplificado)

```python
def consultar(self, consulta: str, ...) -> SalidaRecuperacionRagDenso:
    ...
    embedding_consulta = self._embeddings.get_query_embedding(consulta_limpia)
    pares = self._pares_filtrados(consulta_limpia, ...)  # vuelve a calcular embedding
    ...
```

## Estado deseado

```python
def consultar(self, consulta: str, ...) -> SalidaRecuperacionRagDenso:
    ...
    embedding_consulta = self._embeddings.get_query_embedding(consulta_limpia)
    pares = self._pares_filtrados(
        consulta_limpia, ..., query_embedding=embedding_consulta
    )
    ...

def _pares_filtrados(
    self,
    consulta: str,
    ...,
    query_embedding: list[float] | None = None,
) -> list[tuple[NodeWithScore, float]]:
    emb = (
        query_embedding
        if query_embedding is not None
        else self._embeddings.get_query_embedding(consulta)
    )
    ...
```

## Beneficio

- Coste de embeddings dividido a la mitad por consulta.
- Latencia menor; menos llamadas remotas.
- Determinismo asegurado dentro de una sola consulta (el mismo vector se reusa).

## Alcance

Solo `src/rag/recuperador_denso.py` y su test asociado. No cambia la API publica de `RecuperadorDenso.consultar` ni el contrato de `SalidaRecuperacionRagDenso`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Un spy/mock sobre embeddings.get_query_embedding registra exactamente una invocacion por llamada a RecuperadorDenso.consultar (medible con MagicMock count_calls).
- [x] #2 Tests existentes en tests/rag/test_recuperador_denso_pipeline.py siguen verdes sin modificaciones.
- [x] #3 Test nuevo test_consultar_embeddea_consulta_una_sola_vez en tests/rag/test_recuperador_denso_pipeline.py verifica el comportamiento (regresion).
- [x] #4 API publica del recuperador no cambia: firma y semantica de consultar() identicas para los llamadores.
- [x] #5 El embedding ya calculado se reutiliza tambien por MMR si esta habilitado (no se vuelve a pedir).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer integramente `src/rag/recuperador_denso.py` para mapear todas las llamadas a `get_query_embedding`.
2. Anadir parametro opcional `query_embedding: list[float] | None = None` a `_pares_filtrados`. Si llega `None`, calcular embedding internamente como antes (back-compat).
3. En `consultar`, calcular `embedding_consulta` una sola vez al inicio y pasarlo como `query_embedding=embedding_consulta` a `_pares_filtrados`.
4. Si MMR esta habilitado y el codigo actualmente llama a `get_query_embedding` para MMR aparte, refactorizar para reusar el `embedding_consulta` ya calculado.
5. Anadir test nuevo `test_consultar_embeddea_consulta_una_sola_vez` en `tests/rag/test_recuperador_denso_pipeline.py`:
   - Crear un `MagicMock` o subclase de `BaseEmbedding` que cuente llamadas a `get_query_embedding`.
   - Llamar `RecuperadorDenso.consultar("que es la fundacion?")`.
   - Aserrar `mock.get_query_embedding.call_count == 1`.
6. Ejecutar `uv run pytest tests/rag/test_recuperador_denso_pipeline.py -v` y confirmar verde.
7. `ReadLints` sobre el archivo modificado.
8. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
No introducir cache global (clave por hash del texto): anade complejidad sin beneficio frente a la solucion por parametro. La solucion por parametro tiene la ventaja de mantener `_pares_filtrados` usable de forma independiente en tests. Si futuras tareas (TASK-78) cambian el orden del pipeline, mantener el contrato: el embedding se calcula una vez en `consultar` y se pasa a las etapas que lo necesiten.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se elimino la doble llamada a get_query_embedding: consultar calcula el vector una vez y lo pasa a _pares_filtrados como query_embedding opcional (retrocompatible si es None). MMR sigue recibiendo el mismo vector en _pipeline_post_filtrado. Test test_consultar_embeddea_consulta_una_sola_vez con MagicMock verifica call_count == 1 con y sin MMR. pytest tests/rag/test_recuperador_denso_pipeline.py en verde.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/rag/test_recuperador_denso_pipeline.py -v en verde.
- [x] #2 ReadLints sobre src/rag/recuperador_denso.py sin nuevos errores.
- [x] #3 Tarea con status: Done sin archivar.
<!-- DOD:END -->
