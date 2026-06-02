---
id: TASK-138
title: 'Backend TAAM: opciones de médicos para staff y validación en alta de caso'
status: Done
assignee:
  - Frank Daza
created_date: '2026-06-02 06:12'
updated_date: '2026-06-02 06:20'
labels:
  - modulo-3
  - taam
  - fastapi
  - postgres
  - staff
milestone: m-0
dependencies:
  - TASK-136
references:
  - backlog/tasks/task-136 - Backend-TAAM-catálogo-CRUD-médicos-admin.md
  - >-
    backlog/tasks/task-112 -
    Frontend-TAAM-registro-casos-postoperatorio-y-código-emparejamiento-UC-MVP-02.md
  - proyecto-2/src/api/routers/staff_casos.py
documentation:
  - proyecto-2/README.md
  - .claude/skills/fastapi-sse-api/SKILL.md
  - proyecto-2/src/api/esquemas_casos.py
modified_files:
  - proyecto-2/src/api/esquemas_casos.py
  - proyecto-2/src/api/routers/staff_casos.py
  - proyecto-2/src/api/servicios/casos_staff.py
  - proyecto-2/tests/api/test_staff_medicos.py
  - proyecto-2/tests/api/test_staff_casos.py
  - proyecto-2/README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**TASK-136** expone el catálogo CRUD `/api/admin/medicos` (solo rol admin). **UC-MVP-02** (`POST /api/staff/casos`) sigue aceptando `cirujano_id` y `cirujano_nombre` como texto libre. La pantalla `/casos/nuevo` es accesible a **todo** staff autenticado (`SettingsPanel` → Casos), no solo admin; por tanto el frontend **no** puede consumir `/api/admin/medicos` para el select de cirujano.

**TASK-137** dejó explícitamente fuera de alcance el select de médico en casos. Esta tarea cierra el hueco en backend.

## Objetivo

1. `GET /api/staff/medicos` — listado **solo lectura** de médicos **activos** para cualquier JWT staff (`Depends(obtener_staff_actual)`), análogo a `GET /api/staff/tipos-procedimiento`.
2. Validar en `POST /api/staff/casos` que `cirujano_id` (= `medicos.codigo_registro`) exista, esté activo y que `cirujano_nombre` coincida con `nombre_completo` del catálogo.

**No** incluye: migraciones, FK en casos, cambio del contrato JSON del POST (siguen dos campos denormalizados).

## Mapeo de datos

| Catálogo `medicos` | Campo en caso |
|--------------------|---------------|
| `codigo_registro` | `cirujano_id` |
| `nombre_completo` | `cirujano_nombre` |

Semilla demo: `DOC-DEMO-001` / Dr. Demo TAAM (TASK-136).

## Contrato HTTP nuevo

| Método | Ruta | Auth | Respuesta |
|--------|------|------|------------|
| GET | `/api/staff/medicos` | JWT staff | `{ items: MedicoOpcion[] }` |

**MedicoOpcion:** `codigo_registro`, `nombre_completo`, `especialidad` (nullable). Solo filas `activo=true`. `limit` default 100 (mismo tope que tipos-procedimiento).

## Fuera de alcance

- FK `medico_id` en `casos_postoperatorio`
- Frontend combobox (TASK-139)
- Exponer médicos inactivos al staff
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 GET /api/staff/medicos con JWT staff válido devuelve 200 y items solo con activo=true, orden estable (nombre_completo ASC)
- [x] #2 Cada ítem incluye codigo_registro, nombre_completo y especialidad (nullable)
- [x] #3 Sin token staff responde 401/403 según patrón existente en rutas staff
- [x] #4 POST /api/staff/casos con cirujano_id inexistente o médico inactivo responde 422 con detail en español
- [x] #5 POST con cirujano_id válido pero cirujano_nombre distinto al catálogo responde 422
- [x] #6 POST con par válido crea caso y programa recordatorios sin regresión UC-MVP-02
- [x] #7 Tests en proyecto-2/tests/api/test_staff_medicos.py (o ampliación test_staff_casos) cubren listado, 422 y happy path
- [x] #8 proyecto-2/README.md documenta GET /api/staff/medicos en tabla API staff
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Esquemas** en `proyecto-2/src/api/esquemas_casos.py`: `MedicoOpcion`, `ListadoMedicosOpcionRespuesta` (frozen, campos mínimos).
2. **Router** en `proyecto-2/src/api/routers/staff_casos.py`: `GET /medicos` con `RepositorioMedicos.listar(activo=True, limite=limit)`; query `limit` 1-100 default 100.
3. **Servicio** `proyecto-2/src/api/servicios/casos_staff.py` (o módulo existente): `validar_cirujano_en_catalogo(sesion, cirujano_id, cirujano_nombre)` usando `RepositorioMedicos.obtener_por_codigo` — sin duplicar SQL (DRY).
4. **crear_caso**: invocar validación antes de `RepositorioCasosPostoperatorio.crear`; HTTP 422 con mensajes en español.
5. **Orden listado**: `nombre_completo` ASC en repositorio o sort en memoria si el repo no ordena aún.
6. **Tests** `proyecto-2/tests/api/test_staff_medicos.py`: fixture médico activo/inactivo vía admin API o repo; listado; POST 422; happy path con semilla `DOC-DEMO-001`.
7. **Actualizar** tests existentes en `test_staff_casos.py` que usen `MED-10` libre → médico del catálogo.
8. **README** `proyecto-2/README.md`: fila en tabla staff.
9. Verificación: `cd proyecto-2 && uv run pytest tests/api/test_staff_medicos.py tests/api/test_staff_casos.py -q`
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Patrón de referencia (DRY)

Espejar `listar_tipos_procedimiento_para_alta` en `staff_casos.py` (líneas ~73-88): mismo router, mismo `Depends(obtener_staff_actual)` vía prefijo del router.

## Ejemplo esquemas

```python
class MedicoOpcion(BaseModel):
    model_config = ConfigDict(frozen=True)
    codigo_registro: str
    nombre_completo: str
    especialidad: str | None

class ListadoMedicosOpcionRespuesta(BaseModel):
    model_config = ConfigDict(frozen=True)
    items: list[MedicoOpcion]
```

## Ejemplo endpoint

```python
@router.get("/medicos", response_model=ListadoMedicosOpcionRespuesta)
async def listar_medicos_para_alta(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> ListadoMedicosOpcionRespuesta:
    repo = RepositorioMedicos(sesion)
    filas = await repo.listar(limite=limit, offset=0, activo=True)
    return ListadoMedicosOpcionRespuesta(
        items=[
            MedicoOpcion(
                codigo_registro=f.codigo_registro,
                nombre_completo=f.nombre_completo,
                especialidad=f.especialidad,
            )
            for f in filas
        ]
    )
```

## Ejemplo validación

```python
async def validar_cirujano_en_catalogo(
    sesion: AsyncSession, cirujano_id: str, cirujano_nombre: str
) -> None:
    repo = RepositorioMedicos(sesion)
    medico = await repo.obtener_por_codigo(cirujano_id)
    if medico is None or not medico.activo:
        raise HTTPException(
            status_code=422,
            detail="El cirujano seleccionado no existe o está inactivo.",
        )
    if medico.nombre_completo != cirujano_nombre:
        raise HTTPException(
            status_code=422,
            detail="El nombre del cirujano no coincide con el catálogo.",
        )
```

## Tests pytest (referencia)

```python
@pytest.mark.asyncio
async def test_listar_medicos_staff_solo_activos(
    cliente_api, cabecera_staff, medico_activo_codigo: str
):
    r = await cliente_api.get("/api/staff/medicos", headers=cabecera_staff)
    assert r.status_code == 200
    codigos = {i["codigo_registro"] for i in r.json()["items"]}
    assert medico_activo_codigo in codigos

@pytest.mark.asyncio
async def test_crear_caso_cirujano_inactivo_422(cliente_api, cabecera_staff, tipo_procedimiento_ok):
    body = _cuerpo_caso(tipo_id=tipo_procedimiento_ok, cirujano_id="NO-EXISTE", cirujano_nombre="X")
    r = await cliente_api.post("/api/staff/casos", json=body, headers=cabecera_staff)
    assert r.status_code == 422
```

## SOLID

- **SRP:** validación en servicio; router solo orquesta.
- **OCP:** extender staff sin tocar admin_medicos.
- **DIP:** repositorio inyectado vía sesión DB existente.

## RBAC

No usar `requerir_acceso_admin`. Cualquier rol staff con JWT válido puede listar opciones para alta de caso.

## Dependencias

**Bloqueante:** TASK-136 (tabla `medicos`, `RepositorioMedicos`). **Consumidor:** TASK-139 (frontend).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Backend TAAM: GET /api/staff/medicos (solo activos, orden nombre_completo ASC) para cualquier JWT staff; validación en POST /api/staff/casos vía validar_cirujano_en_catalogo en casos_staff.py. Esquemas MedicoOpcion/ListadoMedicosOpcionRespuesta; tests test_staff_medicos.py; fixtures medico_activo_catalogo; README actualizado. pytest tests/api/test_staff_medicos.py test_staff_casos.py test_admin_medicos.py test_recordatorios.py test_staff_seguimiento.py en verde.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin migraciones Alembic nuevas
- [x] #2 uv run pytest en tests API TAAM afectados en verde
- [x] #3 Sin regresión en test_admin_medicos.py
<!-- DOD:END -->
