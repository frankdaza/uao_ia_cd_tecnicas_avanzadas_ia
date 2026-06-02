---
id: TASK-134
title: >-
  Backend TAAM: catálogo acepta protocolos médicos PDF y Markdown (UC-MVP-01
  dual-format)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-06-02 01:47'
updated_date: '2026-06-02 01:47'
labels:
  - modulo-3
  - taam
  - fastapi
  - rag
  - markdown
milestone: m-0
dependencies: []
references:
  - >-
    backlog/completed/task-100 -
    API-catálogo-procedimientos-subida-PDF-almacenamiento-y-metadatos-UC-MVP-01.md
  - >-
    backlog/completed/task-101 -
    Ingesta-PDF-a-vector-store-LangChain-RecursiveCharacterTextSplitter-Qdrant-TAAM.md
documentation:
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - .claude/skills/markdown-knowledge-base/SKILL.md
  - proyecto-2/src/api/routers/admin_procedimientos.py
  - proyecto-2/src/ingesta/protocolo_pdf.py
  - >-
    backlog/completed/task-100 -
    API-catálogo-procedimientos-subida-PDF-almacenamiento-y-metadatos-UC-MVP-01.md
  - >-
    backlog/completed/task-101 -
    Ingesta-PDF-a-vector-store-LangChain-RecursiveCharacterTextSplitter-Qdrant-TAAM.md
modified_files:
  - proyecto-2/pyproject.toml
  - proyecto-2/uv.lock
  - proyecto-2/alembic/versions/0004_formato_protocolo_taam.py
  - proyecto-2/src/persistencia/modelos.py
  - proyecto-2/src/persistencia/repositorios/tipos_procedimiento.py
  - proyecto-2/src/api/esquemas_procedimientos.py
  - proyecto-2/src/api/routers/admin_procedimientos.py
  - proyecto-2/src/api/servicios/almacenamiento_protocolo.py
  - proyecto-2/src/api/servicios/almacenamiento_pdf.py
  - proyecto-2/src/api/servicios/ingesta_protocolo.py
  - proyecto-2/src/ingesta/protocolo_ingesta.py
  - proyecto-2/src/ingesta/extractores/pdf.py
  - proyecto-2/src/ingesta/extractores/markdown.py
  - proyecto-2/scripts/ingestar_protocolo_pdf.py
  - proyecto-2/src/persistencia/semilla_demo_taam.py
  - proyecto-2/tests/api/conftest.py
  - proyecto-2/tests/api/test_admin_procedimientos.py
  - proyecto-2/tests/api/test_ingesta_background.py
  - proyecto-2/tests/ingesta/test_protocolo_pdf.py
  - proyecto-2/README.md
  - proyecto-2/scripts/README.md
priority: high
ordinal: 13400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Intención del producto

Al registrar un tipo de procedimiento postoperatorio (protocolo médico general UC-MVP-01), el administrador debe poder subir el documento en **PDF o Markdown** — formatos **equivalentes**, no un reemplazo del otro.

| Formato | Extensión | Objetivo |
|---------|-----------|----------|
| PDF | .pdf | Se mantiene (paridad completa, cero regresiones) |
| Markdown | .md | Nuevo, misma experiencia de subida e indexación |

**Principios:** (1) dualidad simétrica PDF/MD; (2) un procedimiento = un archivo activo (.pdf o .md); (3) mismo flujo multipart → disco → Qdrant → casos; (4) PATCH permite intercambiar formatos; (5) fuera de alcance: ambos archivos a la vez o ingesta bulk desde data/markdown/ M2.

## Contexto

UC-MVP-01 (TASK-100/101/111): hoy backend e ingesta son **PDF-only**. El equipo tiene protocolos en PDF y Markdown.

**Prerequisitos completados:** TASK-100 (API catálogo PDF), TASK-101 (ingesta Qdrant). UI en TASK-135.

## Objetivo

Extender `POST/PATCH /api/admin/procedimientos` (sin endpoint nuevo) para aceptar **PDF y Markdown por igual**. Respuesta incluye `formato_protocolo`. Comportamiento PDF existente **no debe degradarse**.

## Modelo (Alembic 0004_formato_protocolo_taam.py)

- Columna `formato_protocolo` VARCHAR(16) NOT NULL DEFAULT 'pdf' CHECK IN ('pdf','markdown').
- Mantener `ruta_pdf` y `hash_pdf` (hash del archivo, cualquier formato).
- Rutas: `data/taam/procedimientos/{id}/protocolo.pdf` | `protocolo.md`.

## Diseño SOLID/DRY

| Pieza | Responsabilidad |
|-------|------------------|
| almacenamiento_protocolo.py | Validar, hash, guardar, borrar archivo previo |
| ingesta/extractores/pdf.py | pdfplumber |
| ingesta/extractores/markdown.py | UTF-8, front matter opcional |
| protocolo_ingesta.py | Orquestador vía fila.ruta_pdf + formato |
| Compartido | dividir_en_chunks, Qdrant, ingesta_protocolo_background |

## Mitigaciones de bugs (obligatorias)

1. **Ingesta:** usar `resolver_ruta_workspace(fila.ruta_pdf)`, NO `ruta_absoluta_protocolo(tipo_id)` hardcodeado a .pdf.
2. **PATCH cambio formato:** eliminar archivo anterior en disco (test PDF↔MD).
3. **`uv add pyyaml`** — no está en pyproject.toml hoy.
4. **Front matter opcional** (no parser estricto M2); YAML inválido → 422 en upload; delimitadores seguros; BOM UTF-8; rechazar bytes nulos.
5. **MIME MD:** aceptar vacío, text/plain, text/markdown, application/octet-stream si extensión .md.
6. **Invariante:** formato_protocolo coincide con extensión en ruta_pdf.
7. Renombrar excepción a ArchivoProtocoloInvalidoError; shim almacenamiento_pdf.py.
8. No renombrar TAAM_PDF_MAX_MB (documentar que aplica a ambos formatos).

## Validación e ingesta Markdown

Upload: extensión .md, UTF-8, tamaño ≤ TAAM_PDF_MAX_MB, nombre ASCII. Ingesta: RecursiveCharacterTextSplitter 800/120; `_MIN_CARACTERES_TEXTO` en ingesta.

## Fuera de alcance

UI (TASK-135), OCR, extensión .markdown, preview MD en API.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Migración Alembic 0004 con formato_protocolo default pdf; alembic upgrade head OK en Docker y host; demo existente sigue indexando PDF sin intervención
- [ ] #2 uv add pyyaml en proyecto-2/pyproject.toml y uv.lock versionado
- [ ] #3 POST con .md válido → 201, formato_protocolo=markdown, archivo en protocolo.md, ruta_pdf apunta a .md, indexacion_estado=pendiente
- [ ] #4 POST con PDF → regresión idéntica a TASK-100 (formato_protocolo=pdf); mismos códigos HTTP y validaciones que antes
- [ ] #5 Un mismo procedimiento nunca almacena .pdf y .md a la vez tras PATCH de reemplazo (solo el formato activo en disco)
- [ ] #6 PATCH reemplaza PDF↔MD: actualiza formato/ruta/hash, incrementa versión vectorial, elimina archivo del formato anterior, encola ingesta
- [ ] #7 Ingesta lee ruta desde fila.ruta_pdf (test que guarda .md y verifica que no intenta abrir protocolo.pdf hardcodeado)
- [ ] #8 Ingesta MD y PDF dejan indexacion_estado=ok cuando el contenido es válido; consultar_protocolo_rag recupera fragmentos de ambos formatos en tests
- [ ] #9 MD con front matter YAML inválido → 422 en POST (sin fila creada)
- [ ] #10 MD con cuerpo vacío post-FM → indexacion_estado=error tras ingesta con mensaje en español (no 422 post-201)
- [ ] #11 POST .../reindexar funciona con protocolos PDF y MD; mensaje genérico sin archivo de protocolo si falta ruta_pdf
- [ ] #12 uv run pytest pasa en tests/api/ y tests/ingesta/ incluyendo suite de regresión PDF completa
- [ ] #13 proyecto-2/README.md y scripts/README.md documentan PDF o Markdown como formatos equivalentes, con ejemplos curl para ambos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. `uv add pyyaml`; Alembic `0004_formato_protocolo_taam.py` (columna + CHECK); modelo SQLAlchemy y repositorio (`formato_protocolo` en crear/actualizar).
2. `almacenamiento_protocolo.py`: `leer_y_validar_archivo_protocolo()`, `ruta_relativa_protocolo(id, formato)`, `guardar_protocolo_en_disco()` con borrado del archivo previo; shim `almacenamiento_pdf.py`.
3. `ingesta/extractores/pdf.py` y `markdown.py`; evolucionar `protocolo_pdf.py` → `protocolo_ingesta.py`; **corregir ingesta para leer `fila.ruta_pdf` vía workspace**.
4. Router `admin_procedimientos.py`: detectar formato por extensión/MIME; persistir invariante BD↔disco; PATCH PDF↔MD; mensajes HTTP neutros (no solo «PDF»); `ProcedimientoVista.formato_protocolo`.
5. Actualizar `ingesta_protocolo.py`, CLI `ingestar_protocolo_pdf.py` (ambos formatos), `semilla_demo_taam.py`.
6. Tests: `MD_FIXTURE_MINIMO` en conftest; POST/PATCH/ingesta MD; regresión PDF; PDF→MD y MD→PDF; test anti-hardcode de ruta .pdf.
7. Documentar en `proyecto-2/README.md` y `scripts/README.md` con curl PDF y curl MD.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Endpoints:** mismo prefijo `/api/admin/procedimientos` (POST/GET/PATCH/reindexar).

**Dependencia:** `uv add pyyaml` en proyecto-2 (no está en pyproject.toml).

**Contrato API:** `ProcedimientoVista` incluye `formato_protocolo` en todas las respuestas; estable para TASK-135.

**Semilla demo:** `semilla_demo_taam.py` debe setear `formato_protocolo='pdf'` al crear COLE-LAP-001.

**Shim:** `almacenamiento_pdf.py` re-exporta desde `almacenamiento_protocolo.py` para imports legacy.

**Importadores a actualizar:** admin_procedimientos.py, protocolo_ingesta.py, semilla_demo_taam.py, tests/api/test_admin_procedimientos.py, tests/ingesta/test_protocolo_pdf.py.

**Idioma:** identificadores Python ASCII; mensajes y docstrings en español latinoamericano.

**No importar** código de proyecto-1 en runtime.

### Ejemplo: resolución de ruta en ingesta

```python
def resolver_ruta_archivo_protocolo(fila: TipoProcedimiento) -> Path:
    if not fila.ruta_pdf:
        raise ValueError("Sin ruta de protocolo en BD.")
    return resolver_ruta_workspace(fila.ruta_pdf)

async def ingestar_tipo_procedimiento(...):
    ruta = resolver_ruta_archivo_protocolo(fila)
    if not ruta.is_file():
        ...
    extractor = obtener_extractor(fila.formato_protocolo)
    documentos, unidades = extractor.extraer(ruta)
```

### Ejemplo: front matter opcional

```python
def parsear_markdown_protocolo(texto: str) -> tuple[dict[str, object], str]:
    texto = texto.lstrip("\ufeff")
    if not texto.startswith("---\n"):
        return {}, texto
    resto = texto[4:]
    fin = resto.find("\n---\n")
    if fin <= 0:
        raise ArchivoProtocoloInvalidoError("Front matter Markdown mal cerrado.")
    bloque = resto[:fin]
    cuerpo = resto[fin + 5 :]
    meta = yaml.safe_load(bloque) or {}
    if not isinstance(meta, dict):
        raise ArchivoProtocoloInvalidoError("Front matter debe ser un mapa YAML.")
    return meta, cuerpo
```

### Ejemplo: guardar con limpieza de archivo previo

```python
def guardar_protocolo_en_disco(
    tipo_id: uuid.UUID,
    contenido: bytes,
    formato: Literal["pdf", "markdown"],
    ruta_anterior: str | None = None,
) -> Path:
    destino = ruta_absoluta_por_formato(tipo_id, formato)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    if ruta_anterior:
        anterior = resolver_ruta_workspace(ruta_anterior)
        if anterior.is_file() and anterior != destino:
            anterior.unlink(missing_ok=True)
    return destino
```

### Fixture test (tests/api/conftest.py)

```python
MD_FIXTURE_MINIMO = b"""---
titulo: Protocolo demo colecistectomia
idioma: es
---
## Cuidados postoperatorios
Repita las indicaciones de su equipo tratante.
""" + b"Texto util del protocolo. " * 20
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Migración aplicada en entorno Docker documentado en README
- [ ] #2 Cero regresiones tests PDF
- [ ] #3 Tarea en Backlog con status Done al cerrar; no usar task_complete salvo pedido explícito del usuario
<!-- DOD:END -->
