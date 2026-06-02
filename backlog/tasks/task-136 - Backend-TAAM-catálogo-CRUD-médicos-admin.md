---
id: TASK-136
title: 'Backend TAAM: catálogo CRUD médicos (admin)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-06-02 05:05'
updated_date: '2026-06-02 05:05'
labels:
  - modulo-3
  - taam
  - fastapi
  - postgres
  - admin
milestone: m-0
dependencies: []
references:
  - >-
    backlog/completed/task-99 -
    Esquema-Postgres-TAAM-y-migraciones-Alembic-procedimientos-casos-alertas-Telegram.md
  - >-
    backlog/tasks/task-110 -
    Frontend-TAAM-login-staff-y-cliente-API-autenticado.md
documentation:
  - proyecto-2/src/api/routers/admin_procedimientos.py
  - >-
    backlog/completed/task-100 -
    API-catálogo-procedimientos-subida-PDF-almacenamiento-y-metadatos-UC-MVP-01.md
  - proyecto-2/README.md
modified_files:
  - proyecto-2/alembic/versions/0005_medicos.py
  - proyecto-2/src/persistencia/modelos.py
  - proyecto-2/src/persistencia/repositorios/medicos.py
  - proyecto-2/src/api/esquemas_medicos.py
  - proyecto-2/src/api/routers/admin_medicos.py
  - proyecto-2/src/api/main.py
  - proyecto-2/src/persistencia/semilla_demo_taam.py
  - proyecto-2/tests/api/test_admin_medicos.py
  - proyecto-2/README.md
priority: high
ordinal: 13600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El panel TAAM (`proyecto-2/`) ya permite al **Admin Demo** (`admin@demo.taam`, `rol=admin`) gestionar el catálogo de procedimientos (UC-MVP-01, TASK-100/111). Los casos postoperatorio (UC-MVP-02) guardan cirujano como **texto denormalizado** (`cirujano_id`, `cirujano_nombre` en `casos_postoperatorio`); la semilla demo usa `DOC-DEMO-001` / Dr. Demo TAAM.

Esta tarea introduce un **catálogo OLTP de médicos/cirujanos** administrable vía API, sin Qdrant ni archivos, reutilizando el patrón de `admin_procedimientos` y `requerir_acceso_admin` (JWT admin o `X-Admin-Key`).

**Prerequisitos (completados en repo):** esquema Postgres/Alembic TAAM (TASK-99), login staff JWT (TASK-110).

## Objetivo

Tabla `medicos`, migración Alembic, repositorio, esquemas Pydantic, router REST `/api/admin/medicos`, semilla demo idempotente y tests API.

## Fuera de alcance

- FK `medico_id` en casos o migración de `cirujano_*` (tarea futura)
- Select de médico en formulario de casos (frontend asistente)
- Gestión de usuarios staff / RBAC completo

## Contrato HTTP

Prefijo `/api/admin/medicos`, auth `Depends(requerir_acceso_admin)`.

| Método | Ruta | Notas |
|--------|------|-------|
| GET | `/medicos` | Query `limit` (1-100), `offset`, `activo` opcional → `{ items, total }` |
| POST | `/medicos` | JSON body → 201 |
| GET | `/medicos/{id}` | UUID → 200/404 |
| PATCH | `/medicos/{id}` | JSON parcial → 200; 409 código duplicado |
| DELETE | `/medicos/{id}` | Baja lógica `activo=false` → 204; 409 si hay caso **activo** con `cirujano_id == codigo_registro` |

**MedicoVista:** `id`, `codigo_registro`, `nombre_completo`, `especialidad`, `activo`, `created_at`, `updated_at`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Migración Alembic `0005_*` crea tabla `medicos` con índice único en `codigo_registro` y aplica con `uv run alembic upgrade head` en entorno TAAM
- [ ] #2 POST /api/admin/medicos con JSON válido crea fila y responde 201 con MedicoVista; código duplicado responde 409
- [ ] #3 GET listado paginado devuelve `items` y `total`; filtro `activo` opcional funciona
- [ ] #4 GET/PATCH por UUID devuelven 404 si no existe; PATCH actualiza `updated_at`
- [ ] #5 DELETE desactiva médico (activo=false); si existe caso_postoperatorio activo con mismo cirujano_id responde 409
- [ ] #6 Endpoints sin JWT admin ni X-Admin-Key válida responden 401/403 según patrón existente
- [ ] #7 Semilla demo incluye upsert idempotente DOC-DEMO-001 alineado con casos demo
- [ ] #8 Tests en proyecto-2/tests/api/test_admin_medicos.py pasan con uv run pytest
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Migración Alembic** `alembic/versions/0005_medicos.py`: tabla `medicos` (id UUID PK, codigo_registro UNIQUE, nombre_completo, especialidad nullable, activo default true, created_at, updated_at). Índice en `activo` si filtra listados.
2. **Modelo ORM** en `src/persistencia/modelos.py`: clase `Medico` con `__tablename__ = "medicos"`.
3. **Repositorio** `src/persistencia/repositorios/medicos.py`: `crear`, `obtener_por_id`, `obtener_por_codigo`, `listar` (limite/offset/activo), `contar`, `actualizar`, `existe_caso_activo_con_cirujano_id` (join o select count en `casos_postoperatorio` donde `estado='activo'`).
4. **Esquemas Pydantic** `src/api/esquemas_medicos.py`: `MedicoCuerpo`, `MedicoParche`, `MedicoVista`, `ListadoMedicosRespuesta`.
5. **Router** `src/api/routers/admin_medicos.py`: prefijo `/admin`, tag `admin-medicos`, `dependencies=[Depends(requerir_acceso_admin)]`, helper `_a_vista`.
6. **Registrar** en `src/api/main.py`: `app.include_router(admin_medicos.router, prefix="/api")`.
7. **Semilla** `semilla_demo_taam.py`: upsert médico `DOC-DEMO-001` / nombre demo existente.
8. **Tests** `tests/api/test_admin_medicos.py`: fixture JWT admin (copiar de `test_admin_procedimientos.py`), casos POST/GET/PATCH/DELETE/409/auth.
9. **README** `proyecto-2/README.md`: tabla de endpoints y ejemplo curl JSON.
10. **Verificación:** `cd proyecto-2 && uv run pytest tests/api/test_admin_medicos.py` y `uv run alembic upgrade head` en Docker si aplica.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Modelo de datos

| Campo | Tipo | Reglas |
|-------|------|--------|
| id | UUID PK | gen_random_uuid() |
| codigo_registro | String(64) UNIQUE | ASCII [A-Za-z0-9._-]+; alineado con cirujano_id en casos |
| nombre_completo | String(512) NOT NULL | |
| especialidad | String(256) NULL | |
| activo | Boolean default true | Baja lógica en DELETE |
| created_at / updated_at | timestamptz | actualizar updated_at en PATCH |

## Ejemplos de código

**Pydantic** (`esquemas_medicos.py`):
```python
class MedicoCuerpo(BaseModel):
    codigo_registro: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    nombre_completo: str = Field(..., min_length=1, max_length=512)
    especialidad: str | None = Field(None, max_length=256)

class MedicoParche(BaseModel):
    codigo_registro: str | None = Field(None, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    nombre_completo: str | None = Field(None, min_length=1, max_length=512)
    especialidad: str | None = None
    activo: bool | None = None
```

**Router** (esqueleto):
```python
router = APIRouter(
    prefix="/admin",
    tags=["admin-medicos"],
    dependencies=[Depends(requerir_acceso_admin)],
)

@router.post("/medicos", status_code=201)
async def crear_medico(cuerpo: MedicoCuerpo, sesion: AsyncSession = Depends(obtener_sesion_db)):
    repo = RepositorioMedicos(sesion)
    if await repo.obtener_por_codigo(cuerpo.codigo_registro):
        raise HTTPException(409, detail="codigo_registro ya existe")
    fila = await repo.crear(**cuerpo.model_dump())
    await sesion.commit()
    return _a_vista(fila)
```

**main.py:**
```python
from src.api.routers import admin_medicos
app.include_router(admin_medicos.router, prefix="/api")
```

## SOLID / DRY

- **SRP:** router HTTP; repositorio persistencia; esquemas validación.
- **OCP:** reutilizar `requerir_acceso_admin` sin duplicar auth.
- **DRY:** mismo shape de listado `{ items, total }` que procedimientos; copiar estilo de `admin_procedimientos.py` y `RepositorioTiposProcedimiento`.

## DELETE y casos activos

Antes de `activo=False`, consultar si existe `CasoPostoperatorio` con `estado='activo'` y `cirujano_id == fila.codigo_registro`. Si sí → HTTP 409 con mensaje en español.

## Migración reversible

En notas de revisión: `downgrade()` debe eliminar tabla `medicos`; documentar en comentario de migración.

## Auth en tests

Usar JWT con claims `rol=admin` o cabecera `X-Admin-Key` según fixture existente en `tests/api/conftest.py` o `test_admin_procedimientos.py`.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Router `/api/admin/medicos` registrado en `src/api/main.py` con lifespan DB existente
- [ ] #2 `uv run pytest` en `proyecto-2/` pasa incluyendo `tests/api/test_admin_medicos.py`
- [ ] #3 `proyecto-2/README.md` documenta endpoints JSON, auth admin y tabla medicos
- [ ] #4 Sin secretos en código ni en notas de tarea; migración Alembic versionada en repo
<!-- DOD:END -->
