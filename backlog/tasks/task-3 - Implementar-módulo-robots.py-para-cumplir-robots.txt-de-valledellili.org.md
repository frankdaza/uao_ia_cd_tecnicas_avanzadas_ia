---
id: TASK-3
title: Implementar módulo robots.py para cumplir robots.txt de valledellili.org
status: Done
assignee: []
created_date: '2026-04-26 20:11'
updated_date: '2026-04-26 20:52'
labels:
  - scraping
dependencies:
  - TASK-2
references:
  - .cursor/rules/scraping-ethics.mdc
  - .cursor/skills/web-scraping/SKILL.md
ordinal: 38
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Antes de descargar cualquier página debemos respetar el archivo `robots.txt` del sitio. Esta task crea un módulo aislado y reutilizable que el crawler (task-4) consultará antes de cada `GET`.

## Objetivo

Implementar `src/scraping/robots.py` con dos funciones puras y testeables, sin acoplamiento al crawler.

## Diseño propuesto

```python
from urllib.robotparser import RobotFileParser

USER_AGENT_DEFECTO = "uao-tecnicas-ia-bot/1.0 (+contacto@example.org)"

class GestorRobots:
    def __init__(self, url_base: str, user_agent: str = USER_AGENT_DEFECTO) -> None:
        ...
    def puede_descargar(self, url: str) -> bool: ...
    def obtener_crawl_delay(self) -> float: ...
```

## Detalles técnicos

- Usar `urllib.robotparser.RobotFileParser` (estándar). No requiere dependencias adicionales.
- Resolver la URL del `robots.txt` a partir de la URL base (`https://valledellili.org/robots.txt`).
- Cachear el parser en memoria por instancia (lectura única por sesión de scraping).
- `obtener_crawl_delay()` devuelve el `Crawl-delay` declarado para el `user_agent`; si no está declarado, retornar **1.0** segundos por defecto.
- Errores de red al cargar `robots.txt` deben ser explícitos: si no se puede leer, asumir **conservador**: `puede_descargar` devuelve `False` para todo y registrar el motivo.

## Identificadores

- ASCII puro: `GestorRobots`, `puede_descargar`, `obtener_crawl_delay`, `cargar_robots`, `url_base`, `user_agent`.

## Caso de negocio

Evitar sanciones legales/éticas y respetar la voluntad expresa del sitio público. Documentar en el informe que sí cumplimos `robots.txt`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Función puede_descargar(url) retorna False para rutas listadas en Disallow
- [x] #2 Función puede_descargar(url) retorna True para rutas permitidas
- [x] #3 obtener_crawl_delay() devuelve el valor declarado en robots.txt o 1.0 por defecto
- [x] #4 Si la carga del robots.txt falla (timeout, 5xx), GestorRobots queda en modo conservador y puede_descargar retorna False
- [x] #5 Test unitario en tests/scraping/test_robots.py con un robots.txt de fixture cubre los 3 casos: permitido, denegado, crawl-delay
- [x] #6 El módulo no realiza I/O en import (solo en construcción explícita o primera llamada)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv add nada (urllib.robotparser es stdlib); confirmar que no se necesitan deps extra
2) Crear src/scraping/robots.py con clase GestorRobots
3) Implementar carga perezosa (lazy) en primera llamada
4) Implementar puede_descargar() y obtener_crawl_delay() usando RobotFileParser
5) Crear tests/scraping/test_robots.py y tests/scraping/fixtures/robots_ejemplo.txt
6) Validar con uv run pytest tests/scraping
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/scraping/test_robots.py pasa en local
- [x] #2 Cobertura mínima del módulo robots.py >= 90% según pytest --cov (si hay coverage configurado, opcional)
- [x] #3 Sin warnings de deprecación al importar
<!-- DOD:END -->
