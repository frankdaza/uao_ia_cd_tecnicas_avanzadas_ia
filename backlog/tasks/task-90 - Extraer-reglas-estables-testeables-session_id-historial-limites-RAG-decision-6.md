---
id: TASK-90
title: >-
  Extraer reglas estables testeables (session_id, historial, limites RAG) -
  decision-6
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 17:31'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - dominio-delgado
  - agentes
dependencies:
  - TASK-85
  - TASK-86
references:
  - src/agentes/memoria/historial.py
  - src/agentes/router.py
  - src/agentes/
  - src/agentes/reglas.py
  - tests/agentes/test_reglas.py
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
priority: high
ordinal: 0.30517578125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 5 de decision-6: puertos explicitos solo donde hay reglas estables reutilizables; evitar interfaces vacias.

## Objetivo

Centralizar en un modulo pequeno y testeable: normalizacion de session_id, politica de ventana de historial (HISTORIAL_DIAS_MAX) y topes de recuperacion RAG, desacoplados de lectura cruda de entorno en multiples sitios.

## Ejemplo de API (orientativa)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LimitesHistorial:
    dias_max: int

def normalizar_session_id(valor: str) -> str: ...
```

## Fuera de alcance

Crear paquete `puertos/` completo o capa aplicacion generica.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Existe modulo dedicado (p. ej. src/agentes/reglas.py) con funciones puras o dataclasses para: normalizacion de session_id, ventana HISTORIAL_DIAS_MAX como regla de dominio, limites k_inicial_max y k_final_max con validacion.
- [x] #2 Los consumidores (p. ej. historial, router, tools RAG) leen limites desde el modulo nuevo sin leer os.environ directamente en el caso de uso.
- [x] #3 Tests unitarios nuevos en tests/agentes/ cubren casos borde (session_id vacio, limites fuera de rango).
- [x] #4 `uv run pytest tests/agentes tests/api` verde.
- [x] #5 No se introducen Protocol/ABC genericos sin segundo consumidor (criterio de stop decision-6).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Localizar lecturas dispersas de env / magic numbers para historial y RAG k.
2. Disenar API minima en `src/agentes/reglas.py` (o nombre acordado ASCII).
3. Inyectar o construir DTOs desde capa existente (config) sin duplicar pydantic models innecesariamente.
4. Refactor mecanico de consumidores + tests de regresion.
5. Anadir tests unitarios de reglas puras.
6. `uv run pytest tests/agentes tests/api`.
7. PR con descripcion que cita decision-6 sub-decision 5.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- La configuracion runtime sigue viniendo de `Configuracion` / env en el borde (FastAPI); el modulo de reglas recibe valores ya parseados o un pequeno DTO inyectado desde dependencias.
- Mantener LangGraph en la periferia: no extraer nodos completos a dominio puro.
- Documentar en docstring del modulo el criterio YAGNI de decision-6.
- Revisar `src/agentes/memoria/historial.py` para HISTORIAL_DIAS_MAX y session_id segun estado actual del repo.

Coercion defensiva duplicada en capas (bundle + recuperador) es intencional para rutas de prueba que instancian componentes sin pydantic-settings.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego el modulo `src/agentes/reglas.py` con reglas puras (normalizacion de session_id, LimitesHistorial + coercion, top_k final e inicial RAG) alineadas a decision-6 sub-decision 5 sin Protocol/ABC nuevos. `MemoriaUsuario` dejo de llamar `obtener_configuracion` en el caso de uso: recibe `LimitesHistorial` desde los routers HTTP o valores por defecto del modulo. Router, bundle runtime, recuperador denso, tool RAG y `_limites_rag` consumen los topes desde `reglas`. Pruebas: `tests/agentes/test_reglas.py` y `uv run pytest tests/agentes tests/api` verde.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Identificadores Python ASCII.
- [x] #2 Sin secretos en backlog ni codigo.
<!-- DOD:END -->
