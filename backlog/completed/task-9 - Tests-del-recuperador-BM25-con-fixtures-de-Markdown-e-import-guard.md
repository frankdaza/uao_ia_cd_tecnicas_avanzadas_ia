---
id: TASK-9
title: Tests del recuperador BM25 con fixtures de Markdown e import-guard
status: Done
assignee: []
created_date: '2026-04-26 20:15'
updated_date: '2026-04-26 21:38'
labels:
  - tests
  - retrieval
dependencies:
  - TASK-8
ordinal: 32
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El recuperador es el componente más sensible: si recupera un archivo equivocado, el LLM contestará con el contexto incorrecto o dirá "No tengo información suficiente" cuando sí debería responder. Esta task asegura calidad mínima con un set de pruebas reproducibles.

## Objetivo

Crear `tests/retrieval/test_recuperador_bm25.py` con tests unitarios y un test de import-guard que falla si alguien introduce embeddings/chunking en `src/retrieval/`.

## Estructura

```
tests/
├── conftest.py
└── retrieval/
    ├── __init__.py
    ├── test_recuperador_bm25.py
    └── fixtures/
        └── markdown/
            ├── inicio.md
            ├── quienes-somos.md
            ├── servicios-cardiologia.md
            ├── servicios-pediatria.md
            └── contacto.md
```

Cada fixture es un `.md` con front matter mínimo y un cuerpo corto pero realista sobre la fundación.

## Casos de prueba

1. **Tokenización**:
   - `tokenizar("Cardiología")` → `["cardiologia"]` (lowercase + sin tildes).
   - `tokenizar("¿Dónde queda?")` → `["donde", "queda"]` (filtra signos).
   - Stopwords filtradas: `tokenizar("la fundación es")` no contiene "la" ni "es".

2. **Recuperación correcta**:

   | Pregunta | Archivo esperado |
   | --- | --- |
   | "¿Cuáles son los servicios de cardiología?" | `servicios-cardiologia.md` |
   | "¿Atienden a niños?" o "pediatría" | `servicios-pediatria.md` |
   | "¿Cuál es la historia de la fundación?" | `quienes-somos.md` |
   | "¿Cómo los puedo contactar?" | `contacto.md` |
   | "¿Quiénes son?" | `quienes-somos.md` |

   AC: ≥4/5 deben acertar.

3. **Pregunta sin match**:
   - `buscar("blockchain quantum NFT")` con scores=0 → lanza `RecuperacionVaciaError`.

4. **Recarga**:
   - Crear un `.md` adicional en un tmp_path, llamar `recargar()`, validar que aparece como recuperado para una pregunta dirigida a su contenido.

5. **Import-guard** (test crítico):

   ```python
   def test_recuperador_no_importa_embeddings():
       import src.retrieval.recuperador as mod
       prohibidos = [
           "sklearn", "faiss", "chromadb", "qdrant_client",
           "sentence_transformers", "langchain.embeddings",
           "llama_index.embeddings",
       ]
       for nombre in prohibidos:
           assert nombre not in sys.modules, f"{nombre} fue importado"
       fuente = inspect.getsource(mod)
       for nombre in prohibidos:
           assert nombre not in fuente, f"{nombre} aparece en el código"
   ```

6. **Sin chunking**:
   - Verificar por inspección del módulo que no existen funciones cuyo nombre contenga `chunk`, `split_text`, `sliding`, `tokenize_chunks`.

## Identificadores ASCII

- `test_tokenizacion_basica`, `test_buscar_devuelve_archivo_esperado`, `test_recuperacion_vacia_lanza_excepcion`, `test_recargar_reindexa`, `test_recuperador_no_importa_embeddings`, `test_no_existe_chunking`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 tests/retrieval/test_recuperador_bm25.py existe y todos los tests pasan con uv run pytest tests/retrieval
- [x] #2 Existen ≥5 fixtures .md en tests/retrieval/fixtures/markdown/ con front matter válido y contenido realista
- [x] #3 Test parametrizado con 5 preguntas->archivos esperados acierta en ≥4/5 casos
- [x] #4 Test de import-guard valida que sklearn, faiss, chromadb, qdrant_client, sentence_transformers, langchain.embeddings y llama_index.embeddings no aparecen en el código ni son importados
- [x] #5 Test de no-chunking valida que el módulo no contiene 'chunk', 'split_text' ni 'sliding'
- [x] #6 Test de RecuperacionVaciaError cubre el caso de scores todos 0
- [x] #7 Test de recargar() valida que reindexa nuevos archivos sin reinstanciar
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Crear tests/retrieval/__init__.py y conftest.py
2) Crear 5 fixtures .md con contenido temático distinto
3) Test de tokenización (3-4 casos)
4) Test parametrizado de buscar() con preguntas->archivo esperado
5) Test de RecuperacionVaciaError
6) Test de recargar() con tmp_path
7) Test de import-guard inspeccionando sys.modules + getsource
8) Test de no-chunking inspeccionando dir(modulo) y getsource
9) Validar uv run pytest tests/retrieval
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego tests/retrieval/test_recuperador_bm25.py con tokenizacion, busqueda BM25 (>=4/5 aciertos con 5 casos), RecuperacionVaciaError, recargar() sobre copia en tmp, import-guard y prueba de nombres/fuente sin chunking. Fixtures: 5 .md bajo tests/retrieval/fixtures/markdown/. conftest con dir_fixtures_markdown. Comentario en recuperador.py reformulado para no incluir cadenas prohibidas que el test de guard valida. Cobertura de src/retrieval >=92% en recuperador con pytest-cov (paquete src.retrieval).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/retrieval pasa en local
- [x] #2 Cobertura del módulo recuperador.py >= 85%
- [x] #3 Los fixtures están commiteados en git (no en .gitignore)
<!-- DOD:END -->
