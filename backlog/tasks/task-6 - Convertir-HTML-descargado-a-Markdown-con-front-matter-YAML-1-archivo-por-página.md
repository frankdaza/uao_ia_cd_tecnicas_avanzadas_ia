---
id: TASK-6
title: >-
  Convertir HTML descargado a Markdown con front matter YAML (1 archivo por
  página)
status: Done
assignee: []
created_date: '2026-04-26 20:13'
updated_date: '2026-04-26 21:17'
labels:
  - markdown
dependencies:
  - TASK-4
references:
  - .cursor/skills/markdown-knowledge-base/SKILL.md
ordinal: 35
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

`data/raw/valledellili-org/*.html` es el formato nativo de descarga, pero el corpus textual canónico que alimenta el recuperador y el LLM es **Markdown** con front matter YAML en `data/markdown/valledellili-org/`. Cumplimos así con el requerimiento: **1 archivo .md por página**, organizado por dominio.

## Objetivo

Implementar `src/markdown_export/conversion.py` con la función pura `convertir_html_a_md(ruta_html, ruta_metadata) -> ContenidoMarkdown` y utilidades para escribirlo a disco.

## Diseño propuesto

```python
@dataclass
class ContenidoMarkdown:
    front_matter: dict
    cuerpo: str

    def serializar(self) -> str:
        # Devuelve "---\n<yaml>\n---\n\n<cuerpo>"
        ...

def convertir_html_a_md(ruta_html: Path, ruta_metadata: Path) -> ContenidoMarkdown: ...
def escribir_markdown(contenido: ContenidoMarkdown, ruta_destino: Path) -> None: ...
```

## Detalles técnicos

### Limpieza del HTML

Antes de convertir, con `BeautifulSoup`:
- Remover etiquetas: `<script>`, `<style>`, `<noscript>`, `<iframe>`.
- Remover bloques de navegación repetitiva: `<nav>`, `<header>`, `<footer>`, banners de cookies (selectores comunes: `.cookie`, `#cookie-banner`, `[class*="cookie"]`).
- Conservar: encabezados (h1-h6), párrafos, listas, tablas, enlaces.

### Conversión

- Usar `markdownify` con configuración:
  - `heading_style="ATX"` (encabezados con `#`).
  - `strip=["a"]` **NO** (queremos preservar enlaces para trazabilidad).
  - `bullets="-"`.

### Front matter YAML obligatorio

```yaml
---
source_url: "https://valledellili.org/quienes-somos/historia"
titulo: "Historia | Fundación Valle del Lili"
seccion: "quienes-somos"
fecha_extraccion: "2026-04-26"
idioma: "es"
hash: "<sha256 del HTML crudo>"
---
```

- `source_url`: leído del sidecar JSON.
- `titulo`: extraído de `<title>` o primer `<h1>`; si está vacío, usar el slug.
- `seccion`: primer segmento del path de la URL (`/quienes-somos/historia/` → `quienes-somos`); si es la raíz, usar `inicio`.
- `fecha_extraccion`: del sidecar JSON (`fecha_extraccion`).
- `idioma`: `"es"` por defecto.
- `hash`: del sidecar JSON (`hash_sha256`).

### Salida

- Ruta: `data/markdown/valledellili-org/<mismo-slug-que-html>.md`.
- Codificación UTF-8.
- Cuerpo no debe contener líneas en blanco consecutivas (>2).

## Identificadores ASCII

- `convertir_html_a_md`, `escribir_markdown`, `limpiar_html`, `extraer_titulo`, `derivar_seccion`, `ContenidoMarkdown`.

## Dependencias a agregar

```bash
uv add markdownify pyyaml
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Para una página HTML real del sitio, convertir_html_a_md genera un .md con front matter YAML válido (parseable con yaml.safe_load)
- [x] #2 El cuerpo del .md preserva encabezados (con #) y listas (con -)
- [x] #3 Etiquetas <script>, <style>, <nav>, <footer> y banners de cookies son removidas antes de convertir
- [x] #4 El hash del front matter coincide con el hash_sha256 del sidecar JSON original
- [x] #5 El slug del .md coincide con el slug del .html origen
- [x] #6 Tests unitarios cubren: HTML mínimo válido, HTML con script/style, HTML sin <title>, HTML con tablas y listas anidadas
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv add markdownify pyyaml
2) Crear src/markdown_export/conversion.py
3) Implementar limpiar_html con BeautifulSoup
4) Implementar extraer_titulo y derivar_seccion (utilidades puras)
5) Implementar convertir_html_a_md leyendo HTML + sidecar JSON
6) Implementar ContenidoMarkdown.serializar (yaml.safe_dump + cuerpo)
7) Implementar escribir_markdown a disco UTF-8
8) Tests unitarios con HTML de fixture en tests/markdown_export/fixtures/
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv add markdownify pyyaml ejecutado y reflejado en pyproject.toml + uv.lock
- [x] #2 Sin uso de chunking ni embeddings en el módulo (verificar que no se importen sklearn, faiss, etc.)
- [x] #3 Funciones públicas tienen docstrings en español con descripción y ejemplo
<!-- DOD:END -->
