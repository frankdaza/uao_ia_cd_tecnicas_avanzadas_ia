---
id: TASK-5
title: >-
  Script CLI scripts/scrape.py para ejecutar el crawler desde la línea de
  comandos
status: To Do
assignee: []
created_date: '2026-04-26 20:12'
labels:
  - scraping
  - setup
dependencies:
  - TASK-4
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Necesitamos un entry point ejecutable y reproducible que orqueste `GestorRobots` + `Crawler` desde la línea de comandos. Esto permite a cualquier integrante del equipo regenerar `data/raw/` con un solo comando documentado en el README.

## Objetivo

Crear `scripts/scrape.py` con interfaz `argparse` (o `typer` si el equipo lo prefiere) que ejecute el crawler con configuración por defecto sensata.

## Comando esperado

```bash
uv run python -m scripts.scrape \
  --url-inicio https://valledellili.org/ \
  --max-paginas 200 \
  --delay 1.5 \
  --profundidad-maxima 5
```

## Funcionalidad

1. Parsear argumentos (todos opcionales con defaults razonables; leer `URL_BASE_SITIO` de `.env` si existe).
2. Construir `GestorRobots(url_base=...)` y `Crawler(config, gestor_robots)`.
3. Iterar `crawler.ejecutar()` y por cada `ResultadoDescarga`:
   - Escribir una línea JSON en `data/raw/_log.jsonl` con: `{timestamp, url, http_status, hash_sha256, omitido_por_robots, omitido_por_hash, error}`.
   - Imprimir en stdout una línea legible: `[OK] https://... -> <slug>.html` o `[OMIT robots] https://...`.
4. Al final, imprimir un resumen:

   ```text
   Resumen:
     descargadas: N
     omitidas_por_robots: M
     omitidas_por_hash: K
     errores: E
     duración: HH:MM:SS
   ```

## Idempotencia y reanudación

- El log `data/raw/_log.jsonl` se appendea (no se reescribe). Si una URL ya tiene sidecar con el mismo hash, el crawler la omite (lógica delegada a task-4).
- Soporta interrupción con Ctrl+C: capturar `KeyboardInterrupt`, imprimir resumen parcial y salir con código 130.

## Configuración via .env

Cargar `.env` con `python-dotenv` o `os.environ` directo (decisión del equipo). Si no existe `.env`, usar valores por defecto.

## Identificadores ASCII

- `parsear_argumentos`, `ejecutar_scraping`, `escribir_log`, `imprimir_resumen`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv run python -m scripts.scrape --help muestra todos los argumentos disponibles
- [ ] #2 Una ejecución con --max-paginas 5 termina sin errores y produce 5 archivos en data/raw/valledellili-org/
- [ ] #3 data/raw/_log.jsonl contiene una línea JSON válida por URL procesada
- [ ] #4 stdout muestra resumen final con conteos de descargadas, omitidas_por_robots, omitidas_por_hash y errores
- [ ] #5 Ctrl+C produce salida limpia con código 130 y resumen parcial impreso
- [ ] #6 Segunda ejecución sin cambios reporta omitidas_por_hash > 0 y descargadas == 0 (idempotencia)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Crear scripts/scrape.py con argparse y main()
2) Cargar .env si existe
3) Construir GestorRobots y Crawler usando módulos de task-3 y task-4
4) Iterar ejecutar() y escribir _log.jsonl + stdout
5) Implementar manejador de KeyboardInterrupt
6) Imprimir resumen final con timedelta
7) Smoke test manual con --max-paginas 5
8) Documentar en README
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 El comando aparece documentado en el README en la sección 'Scraping'
- [ ] #2 uv add python-dotenv ejecutado si se decidió cargar .env
- [ ] #3 scripts/__init__.py existe para que python -m scripts.scrape funcione
<!-- DOD:END -->
