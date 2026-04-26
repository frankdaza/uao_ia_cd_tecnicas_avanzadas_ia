---
name: web-scraping
description: Extrae contenido publico de sitios web con requests, BeautifulSoup y Selenium cuando haga falta. Usar al implementar src/scraping o al depurar descargas.
---

# Web scraping para la base de conocimiento

> Mantener el mismo contenido en `.cursor/skills/web-scraping/` y `.claude/skills/web-scraping/`.

## Cuando usar cada herramienta

- **`requests` + `BeautifulSoup`**: HTML estatico, listados y enlaces visibles en la respuesta inicial.
- **`Selenium`**: contenido cargado por JavaScript, scroll infinito o interacciones minimas (aceptar cookies, expandir acordeon).

## Patron base (requests)

- Headers con `User-Agent` claro.
- `timeout` (por ejemplo 30 s).
- Guardar la respuesta **tal cual** (HTML, JSON, XML u otro) en **`data/raw/`** con extension coherente (`.html`, `.json`, `.xml`, etc.) antes de parsear o convertir.
- Respetar pausas entre URLs (ver rule de etica de scraping).

## Siguiente paso: base documental en Markdown

- Tras persistir en `data/raw/`, ejecutar el flujo de la skill **`markdown-knowledge-base`** para generar o actualizar archivos **`.md`** legibles en **`data/markdown/`** (fuente de verdad textual antes del chunking).

## Identificadores

- Nombres de funciones y variables en espanol **ASCII** (`descargar_pagina`, `parsear_html`), sin tildes ni ene en identificadores.

## Entrega

- Codigo reproducible: URLs base configurables, sin credenciales en el repo.
- Documentar en README como ejecutar el scraping con `uv run`.
