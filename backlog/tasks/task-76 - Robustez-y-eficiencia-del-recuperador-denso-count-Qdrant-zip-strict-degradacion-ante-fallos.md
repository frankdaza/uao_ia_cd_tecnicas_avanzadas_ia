---
id: TASK-76
title: >-
  Robustez y eficiencia del recuperador denso (count Qdrant, zip strict,
  degradacion ante fallos)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-14 23:26'
updated_date: '2026-05-14 23:27'
labels:
  - rag
  - robustness
  - performance
  - modulo-2
dependencies:
  - TASK-75
references:
  - src/rag/recuperador_denso.py
  - src/rag/qdrant_store.py
  - tests/rag/test_recuperador_denso_pipeline.py
  - src/agentes/router.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria encontro tres problemas que afectan robustez y latencia del recuperador denso:

1. **count Qdrant por consulta**. `RecuperadorDenso.consultar` ejecuta `cliente.count(collection_name=..., exact=True)` antes de pedir vecinos (lineas 357-365 de `src/rag/recuperador_denso.py`). En colecciones grandes esto es un RTT + coste O(n) por **cada** consulta del agente, sin beneficio real (solo se usa para distinguir colecciones vacias).
2. **zip estricto sin captura**. En las lineas 213-223, `zip(nodos, sims, strict=True)` levanta `ValueError` si LlamaIndex/Qdrant devuelven listas con cardinalidades distintas. La excepcion propaga al router (`src/agentes/router.py`), que la convierte en `agente_error` SSE generico, sin contexto.
3. **Sin degradacion explicita**. Excepciones de `get_query_embedding` (proveedor offline, rate limit) o de `vector_store.query` (Qdrant caido, timeout) rompen el SSE del agente sin contexto operativo. El usuario recibe `agente_error` opaco.

## Objetivo

- Quitar el `count(..., exact=True)` por consulta.
- Manejar `ValueError` del `zip` con degradacion explicita (salida vacia + log).
- Capturar excepciones de embeddings y Qdrant en `consultar` con degradacion estructurada: `SalidaRecuperacionRagDenso(fuentes=[], razon=...)` y log con contexto.

## Ejemplo de degradacion deseada

```python
try:
    embedding_consulta = self._embeddings.get_query_embedding(consulta_limpia)
except Exception:
    logger.exception(
        "rag.consultar.embeddings_fallo",
        extra={"consulta_hash": hashlib.sha256(consulta.encode()).hexdigest()[:16]},
    )
    return SalidaRecuperacionRagDenso(fuentes=[], razon="embeddings_fallo")
```

## Alcance

Solo `src/rag/recuperador_denso.py`, su test asociado y posiblemente `src/rag/qdrant_store.py` (cache lazy de coleccion vacia). No cambia el contrato externo de `SalidaRecuperacionRagDenso` (solo se documenta el nuevo campo opcional `razon`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 El count(..., exact=True) por consulta queda eliminado. Alternativa documentada: (a) flag cacheado coleccion_vacia: bool | None en RecuperadorDenso, o (b) inferir vacia si la primera query devuelve 0 resultados.
- [ ] #2 El zip(nodos, sims, strict=True) ahora maneja ValueError: devuelve SalidaRecuperacionRagDenso(fuentes=[], razon='qdrant_response_mismatch') y emite log con exc_info.
- [ ] #3 Excepciones de get_query_embedding y de vector_store.query se capturan en consultar con degradacion estructurada: SalidaRecuperacionRagDenso vacio + log estructurado con categoria, consulta_hash truncado, tipo de excepcion.
- [ ] #4 Tests mock-driven nuevos en tests/rag/test_recuperador_denso_pipeline.py: (a) FakeVectorStore.query lanza RuntimeError -> consultar no propaga; (b) embeddings.get_query_embedding lanza Exception -> consultar no propaga; (c) zip mismatch -> razon='qdrant_response_mismatch'.
- [ ] #5 Bench manual: latencia p50 (50 consultas) menor o igual a la baseline previa (sin el count por consulta).
- [ ] #6 SalidaRecuperacionRagDenso documenta el campo razon en docstring.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Eliminar el `count(..., exact=True)` por consulta:
   - Opcion (a) recomendada: introducir flag `_coleccion_vacia: bool | None = None` en `RecuperadorDenso`. La primera vez que `consultar` no obtiene resultados, marca `True`; cuando se reinicia o se detecta indexacion, vuelve a `None`.
   - Opcion (b) alternativa: simplemente tratar 0 resultados de la query como `SalidaRecuperacionRagDenso` vacia con `razon='coleccion_vacia'` y log informativo (sin count especifico).
2. Envolver `zip(nodos, sims, strict=True)` en `try/except ValueError`:
   ```python
   try:
       pares = list(zip(nodos, sims, strict=True))
   except ValueError:
       logger.exception(
           "rag.consultar.qdrant_response_mismatch",
           extra={"nodos": len(nodos), "sims": len(sims)},
       )
       return SalidaRecuperacionRagDenso(fuentes=[], razon="qdrant_response_mismatch")
   ```
3. Estructurar `consultar` con captura jerarquica:
   ```python
   try:
       embedding_consulta = ...
   except Exception:
       logger.exception(...)
       return SalidaRecuperacionRagDenso(fuentes=[], razon="embeddings_fallo")
   try:
       nodos, sims = self._consultar_vector_store(...)
   except Exception:
       logger.exception(...)
       return SalidaRecuperacionRagDenso(fuentes=[], razon="qdrant_fallo")
   ```
4. Anadir o ampliar `SalidaRecuperacionRagDenso` con campo `razon: str | None = None` (Pydantic) y documentar en docstring los valores posibles: `coleccion_vacia`, `embeddings_fallo`, `qdrant_fallo`, `qdrant_response_mismatch`.
5. Anadir tests en `tests/rag/test_recuperador_denso_pipeline.py`:
   - `test_consultar_embeddings_fallo` -> mock embeddings que lanza, aserta `razon='embeddings_fallo'`.
   - `test_consultar_qdrant_fallo` -> mock `vector_store.query` que lanza, aserta `razon='qdrant_fallo'`.
   - `test_consultar_zip_mismatch` -> nodos y sims de tamanos distintos, aserta `razon='qdrant_response_mismatch'`.
6. Bench manual con 50 consultas en script local; documentar p50 antes/despues en `Implementation Notes` o `Final Summary`.
7. `ReadLints` sobre los archivos modificados.
8. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Capturas finas primero (excepciones especificas de Qdrant/OpenAI cuando se conozcan), luego `Exception` como red de seguridad. Usar `logger.exception(..., extra={...})` para conservar traceback. No silenciar logs: el operador debe poder ver el contexto. Considerar incluir mensaje user-friendly en `razon` (string corto, snake_case) que la TASK-81 pueda exponer al modelo del agente como contexto. La degradacion estructurada permite a la tool `rag_denso` (TASK-81) generar un mensaje de cara al usuario sin tracebacks. Conservar back-compat: el campo `razon` es opcional y default `None` para no romper consumidores.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run pytest tests/rag/test_recuperador_denso_pipeline.py -v en verde.
- [ ] #2 ReadLints sobre archivos modificados sin nuevos errores.
- [ ] #3 Tarea con status: Done sin archivar.
<!-- DOD:END -->
