---
id: TASK-4
title: Crawler descarga.py con requests + BeautifulSoup para valledellili.org
status: Done
assignee: []
created_date: '2026-04-26 20:12'
updated_date: '2026-04-26 20:55'
labels:
  - scraping
dependencies:
  - TASK-3
references:
  - .cursor/rules/scraping-ethics.mdc
  - .cursor/skills/web-scraping/SKILL.md
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Con `GestorRobots` listo (task-3), implementamos el crawler que descarga páginas HTML del dominio `valledellili.org` y las persiste en `data/raw/` con un sidecar JSON de metadatos.

## Objetivo

Módulo `src/scraping/descarga.py` que recorra el sitio en BFS, respete robots.txt y guarde cada página HTML como archivo independiente (un archivo por URL) listo para la conversión a Markdown.

## Diseño propuesto

```python
@dataclass
class ResultadoDescarga:
    url: str
    ruta_html: Path
    ruta_metadata: Path
    http_status: int
    hash_sha256: str
    omitido_por_robots: bool
    error: str | None

@dataclass
class ConfiguracionCrawler:
    url_inicio: str
    dominio_permitido: str = "valledellili.org"
    max_paginas: int = 200
    profundidad_maxima: int = 5
    delay_segundos: float = 1.5
    user_agent: str = USER_AGENT_DEFECTO
    timeout: int = 30
    reintentos: int = 3

class Crawler:
    def __init__(self, config: ConfiguracionCrawler, gestor_robots: GestorRobots) -> None: ...
    def ejecutar(self) -> Iterator[ResultadoDescarga]: ...
```

## Detalles técnicos

- **HTTP**: `requests.Session` con `User-Agent` claro, `timeout=30`.
- **Reintentos**: backoff exponencial (1s, 2s, 4s) usando `urllib3.util.Retry` o lógica manual.
- **Delay entre requests**: `max(gestor_robots.obtener_crawl_delay(), config.delay_segundos)`.
- **BFS por dominio**: extraer enlaces con BeautifulSoup; filtrar a `valledellili.org` (mismo host); descartar URLs con extensiones binarias salvo `.html`/`.htm`/sin extensión; descartar fragmentos `#...`.
- **Slug**: kebab-case ASCII derivado del path (ej. `https://valledellili.org/quienes-somos/historia` → `quienes-somos-historia`); si colisiona, sufijo `-2`, `-3`. Reservar `index` para la raíz `/`.
- **Persistencia**:
  - HTML crudo en `data/raw/valledellili-org/<slug>.html`.
  - Sidecar `data/raw/valledellili-org/<slug>.json` con: `{url, http_status, content_type, fecha_extraccion (ISO 8601), hash_sha256, profundidad, headers_relevantes}`.
- **Idempotencia**: si el sidecar ya existe y el `hash_sha256` del nuevo contenido coincide, **no reescribir**; reportar `omitido=True` en el resultado.
- **Política de robots**: antes de cada `GET`, llamar `gestor_robots.puede_descargar(url)`. Si retorna False, registrar y omitir.

## Identificadores ASCII

- `Crawler`, `ConfiguracionCrawler`, `ResultadoDescarga`, `descargar_pagina`, `extraer_enlaces`, `calcular_slug`, `normalizar_url`, `calcular_hash`.

## Dependencias a agregar

```bash
uv add requests beautifulsoup4
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Una corrida real contra https://valledellili.org/ descarga >= 30 páginas HTML válidas (status 200)
- [x] #2 Cero requests a URLs marcadas como Disallow en robots.txt (verificable por el log y por que no haya sidecar para esas URLs)
- [x] #3 Cada HTML descargado tiene su sidecar JSON con campos: url, http_status, content_type, fecha_extraccion, hash_sha256, profundidad
- [x] #4 Segunda corrida sobre el mismo sitio (sin cambios) reporta 'omitido_por_hash' para los archivos cuyos hashes coinciden y no reescribe el .html
- [x] #5 Reintentos exponenciales aplican a errores 5xx y timeouts (3 intentos: 1s, 2s, 4s)
- [x] #6 BFS limita el dominio a 'valledellili.org' (no descarga subdominios externos ni dominios de terceros)
- [x] #7 Slugs son ASCII kebab-case sin tildes ni eñes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv add requests beautifulsoup4
2) Crear src/scraping/descarga.py con dataclasses y clase Crawler
3) Implementar normalizar_url, calcular_slug, calcular_hash
4) Implementar bucle BFS con cola y set de URLs visitadas
5) Integrar GestorRobots antes de cada GET
6) Implementar persistencia HTML + sidecar JSON con detección de cambios por hash
7) Reintentos con backoff
8) Tests unitarios para utilidades (sin red) + 1 test de integración opcional
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv add requests beautifulsoup4 ejecutado y reflejado en pyproject.toml + uv.lock
- [x] #2 Tests unitarios para extraer_enlaces, calcular_slug y normalizar_url pasan
- [x] #3 Test de integración (skippable con marker @pytest.mark.network) que valida descarga de la home
- [x] #4 Documentación inline (docstring) del módulo describe el flujo BFS y la política de idempotencia
<!-- DOD:END -->
