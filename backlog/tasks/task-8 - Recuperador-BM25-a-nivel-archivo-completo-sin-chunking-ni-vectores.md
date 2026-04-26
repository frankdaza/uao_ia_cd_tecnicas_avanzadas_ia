---
id: TASK-8
title: Recuperador BM25 a nivel archivo completo (sin chunking ni vectores)
status: Done
assignee: []
created_date: '2026-04-26 20:14'
updated_date: '2026-04-26 22:00'
labels:
  - retrieval
dependencies:
  - TASK-7
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El requerimiento del MVP **prohíbe explícitamente** chunking, embeddings y bases de datos vectoriales. La recuperación se hace evaluando **archivos Markdown completos** y devolviendo el de mayor relevancia estadística para la pregunta.

## Objetivo

Implementar `src/retrieval/recuperador.py` con:

1. Un contrato (`Protocol`) `RecuperadorDocumento` para permitir reemplazar la implementación en futuras fases (chunking + vector DB).
2. La implementación concreta `RecuperadorBm25` usando `rank_bm25.BM25Okapi`.

## Diseño propuesto

```python
from pathlib import Path
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class DocumentoRecuperado:
    ruta: Path
    titulo: str
    source_url: str
    contenido: str
    score: float

class RecuperadorDocumento(Protocol):
    def buscar(self, pregunta: str) -> DocumentoRecuperado: ...
    def recargar(self) -> None: ...

class RecuperadorBm25(RecuperadorDocumento):
    def __init__(
        self,
        directorio_markdown: Path,
        glob: str = "**/*.md",
    ) -> None: ...

    def buscar(self, pregunta: str) -> DocumentoRecuperado: ...
    def recargar(self) -> None: ...
```

## Detalles técnicos

### Carga del corpus

- Recorrer `directorio_markdown` con `glob` (default `**/*.md`).
- Para cada `.md`:
  - Parsear el front matter YAML.
  - Separar **cuerpo** (texto después del segundo `---`).
  - Indexar **solo el cuerpo** (no el front matter) más el `titulo` del front matter para mejorar el score por título.

### Tokenización

- Función `tokenizar(texto: str) -> list[str]`:
  - lowercase.
  - Quitar acentos (`unicodedata.normalize('NFKD', ...)`).
  - Dividir en palabras con regex `\w+`.
  - Filtrar tokens de longitud < 2.
  - **Opcional**: lista corta de stopwords en español (`de`, `la`, `el`, `en`, `y`, `que`, `los`, `las`, `del`, `un`, `una`, `por`, `con`, `para`, `se`, `su`, `es`, `al`, `lo`, `a`, `o`).

### Búsqueda

- `BM25Okapi` con tokens del corpus.
- `buscar(pregunta)`:
  - Tokenizar pregunta con la misma función.
  - `bm25.get_scores(tokens_pregunta)` → array de scores.
  - `np.argmax` → índice del documento ganador.
  - Devolver `DocumentoRecuperado` único (no lista).
- Si todos los scores son 0, devolver el primer documento o lanzar `RecuperacionVaciaError` (decisión: lanzar excepción para que el pipeline pueda manejar el caso).

### Recarga

- `recargar()` permite re-leer el corpus de disco (útil tras regenerar `data/markdown/`).

### Restricciones explícitas

- **Prohibido importar**: `sklearn`, `faiss`, `chromadb`, `qdrant_client`, `langchain.embeddings`, `llama_index.embeddings`, `sentence_transformers`.
- **Prohibido implementar**: chunking, splitting, sliding window, embeddings.
- Comentar en el módulo: `# MVP fase 1: BM25 a nivel archivo. NO usar embeddings/chunking aquí.`

## Identificadores ASCII

- `RecuperadorDocumento`, `RecuperadorBm25`, `DocumentoRecuperado`, `RecuperacionVaciaError`, `tokenizar`, `cargar_corpus`, `parsear_markdown`.

## Dependencias a agregar

```bash
uv add rank-bm25 numpy
```

## Caso de negocio

Una pregunta del usuario como "¿Cuáles son los servicios de cardiología?" debe devolver la ruta del .md de la sección de cardiología, no un fragmento. Ese .md completo se inyectará como contexto al LLM (task-11).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 RecuperadorBm25.buscar(pregunta) devuelve un único DocumentoRecuperado (no lista)
- [x] #2 El módulo NO importa sklearn, faiss, chromadb, qdrant_client, sentence_transformers ni langchain.embeddings (verificable con un test de import-guard)
- [x] #3 El módulo NO contiene funciones de chunking ni splitting (verificable por inspección + test)
- [x] #4 tokenizar() es determinista, lowercase, sin tildes, y filtra stopwords básicas en español
- [x] #5 El front matter YAML de cada .md se parsea correctamente y el cuerpo se indexa sin él
- [x] #6 Si todos los scores son 0, buscar() lanza RecuperacionVaciaError
- [x] #7 recargar() re-lee el directorio sin necesidad de reinstanciar el recuperador
- [x] #8 El contrato RecuperadorDocumento (Protocol) permite intercambiar la implementación en una fase futura
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv add rank-bm25 numpy
2) Crear src/retrieval/recuperador.py con dataclasses y Protocol
3) Implementar parsear_markdown (front matter + cuerpo)
4) Implementar tokenizar (lowercase + sin acentos + stopwords ES)
5) Implementar cargar_corpus (lista de Path -> lista de docs tokenizados)
6) Implementar RecuperadorBm25 con BM25Okapi y buscar() devolviendo el top-1
7) Implementar RecuperacionVaciaError y recargar()
8) Smoke test manual contra data/markdown/
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Smoke manual: `uv run python` con `RecuperadorBm25(data/markdown/valledellili-org)` y pregunta sobre servicios de cardiología → `departamentos-y-servicios-cardiologia.md`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se añadieron dependencias rank-bm25 y numpy (pyproject/uv.lock). Nuevo módulo src/retrieval/recuperador.py: DocumentoRecuperado, RecuperacionVaciaError, RecuperadorDocumento (Protocol), RecuperadorBm25 con BM25Okapi, tokenizar (NFKD, stopwords ES), parsear_markdown (front matter con regex + yaml.safe_load), texto_indexable (título + cuerpo) y cargar_corpus. buscar() usa np.argmax y lanza RecuperacionVaciaError si no hay términos o todos los scores son ≤0. recargar() reindexa leyendo de disco. Paquete src/retrieval/__init__.py exporta la API. Smoke: pregunta sobre cardiología devuelve departamentos-y-servicios-cardiologia.md (score ≈ 10,34 en prueba local).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv add rank-bm25 numpy ejecutado y reflejado en pyproject.toml + uv.lock
- [x] #2 Comentario explícito en el módulo prohibiendo embeddings/chunking en esta fase
- [x] #3 Smoke test contra data/markdown/valledellili-org/ real con al menos 1 pregunta esperando un archivo conocido
<!-- DOD:END -->
