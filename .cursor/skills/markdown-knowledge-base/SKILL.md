---
name: markdown-knowledge-base
description: Convierte artefactos crudos en data/raw/ (HTML, JSON, XML, PDF) a Markdown legible con front matter YAML en data/markdown/. Usar despues de cada descarga o al regenerar el corpus.
---

# Base documental en Markdown

> Mantener el mismo contenido en `.cursor/skills/markdown-knowledge-base/` y `.claude/skills/markdown-knowledge-base/`.

## Cuando usar

- Siempre **despues** de guardar contenido en **`data/raw/`** (formato nativo de la descarga o de la libreria).
- Objetivo: producir **`data/markdown/<dominio>/<slug-en-ascii>.md`** como **fuente de verdad textual** antes del chunking.

## Dependencias (uv)

```bash
uv add markdownify pyyaml
# opcional: uv add html2text
# opcional si hay PDF: uv add pdfplumber
```

- **HTML a Markdown**: preferir **`markdownify`**; **`html2text`** solo si el equipo documenta por que cambia.
- **YAML front matter**: **`pyyaml`** (u otra libreria compatible) para escribir el bloque entre `---` y el cuerpo.

## Conversion por formato

| Formato en `raw/` | Enfoque |
|-------------------|---------|
| HTML | Limpiar nav/footer/scripts con BeautifulSoup; luego `markdownify` (o `html2text`). |
| JSON | Recorrer el esquema conocido; renderizar titulos (`#`), listas y tablas Markdown desde campos clave. |
| XML | Parsear con `xml.etree.ElementTree` o lxml si se agrega; plantilla fija a Markdown. |
| PDF | Extraer texto con `pdfplumber`; encabezados por pagina o seccion segun heuristica del equipo. |

## Front matter YAML obligatorio

Cada `.md` debe comenzar con (campos minimos; valores ejemplo):

```yaml
---
source_url: "https://ejemplo.com/pagina"
titulo: "Titulo legible del recurso"
seccion: "quienes-somos"
fecha_extraccion: "2026-04-26"
idioma: "es"
hash: "sha256_del_contenido_crudo_o_normalizado"
---
```

- **`source_url`** y **`titulo`**: obligatorios.
- **`hash`**: recomendado para detectar cambios entre corridas (recalcular desde bytes o texto normalizado del `raw/`).

## Rutas y slugs

- **Slug**: kebab-case, **solo ASCII** (sin tildes ni ene). Ejemplo dominio `empresa.com` -> `data/markdown/empresa-com/sobre-nosotros.md`.
- Evitar colisiones: si hay varias paginas similares, anadir sufijo numerico (`-2`, `-3`).

## Limpieza antes de convertir

- Quitar scripts, estilos, cookies banners obvios y bloques de navegacion repetitiva del HTML.
- Normalizar espacios en blanco; conservar listas y encabezados utiles para el chunking posterior.

## Validacion

- Cada archivo en `markdown/` debe tener front matter parseable y cuerpo no vacio (salvo documentacion explicita de pagina vacia).
- Si falla la conversion, registrar el error y no sobrescribir un `.md` previo valido sin backup o sin flag de fuerza documentado.

## Identificadores de codigo

- Espanol **ASCII**: `convertir_html_a_md`, `escribir_markdown`, `slug_ascii`, `calcular_hash_archivo`, `ruta_markdown_para_url`.
