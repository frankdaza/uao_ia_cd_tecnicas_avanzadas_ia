# Frontend TAAM (`proyecto-2/frontend`)

Panel web staff del **Módulo 3 (TAAM)**. Es un proyecto **independiente** del agente conversacional M2 en `proyecto-1/frontend/`.

## Separación respecto a proyecto-1

| Aspecto | proyecto-1 (M2) | proyecto-2 (TAAM) |
| --- | --- | --- |
| Propósito | Chat RAG + sesiones paciente | Panel staff posoperatorio |
| Vite (dev) | `5173` | **`5174`** |
| API FastAPI | `8000` | **`8001`** |
| Paquete | `qa-valledellili-ui` | `taam-frontend` |

**No** importar componentes TypeScript desde `proyecto-1/frontend`. La línea visual comparte **tokens CSS** FVL (`src/styles/globals.css`), copiados del diseño M2 y documentados aquí.

## Requisitos

- Node.js 22 LTS
- [pnpm](https://pnpm.io/) **11.1.1** (pin en `packageManager` de `package.json`)

## Arranque en desarrollo

1. Levantar el backend TAAM en el puerto **8001** (desde `proyecto-2/`):

   ```bash
   uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001
   ```

2. Instalar dependencias y abrir Vite:

   ```bash
   cd proyecto-2/frontend
   pnpm install
   pnpm dev
   ```

3. Abrir [http://127.0.0.1:5174](http://127.0.0.1:5174). Las peticiones a `/api/*` se reenvían a `http://127.0.0.1:8001` vía proxy de Vite (`vite.config.ts`).

Comprobar salud: el pie de página consulta `GET /api/salud` y debe mostrar `proyecto: taam`.

## Inicio de sesión staff (JWT)

1. En el backend, configure `STAFF_JWT_SECRET` y sembre usuarios demo (ver `proyecto-2/.env.example` y `scripts/sembrar_usuarios_staff_demo.py`).
2. Abra [http://127.0.0.1:5174/login](http://127.0.0.1:5174/login) e ingrese correo y contraseña (p. ej. `asistente@demo.taam` con la contraseña demo del `.env`).
3. Tras un login correcto, la app redirige a `/` y guarda el JWT en **sessionStorage** (`taam-staff-auth-v1`). La contraseña **no** se persiste.
4. Las peticiones autenticadas futuras deben usar `apiFetch` desde `src/lib/api.ts` (cabecera `Authorization: Bearer`).
5. «Cerrar sesión» borra el token y vuelve a `/login`. Un 401/403 en cualquier `apiFetch` limpia la sesión y muestra un toast.

## Catálogo de procedimientos (admin, UC-MVP-01)

Requiere usuario staff con **`rol=admin`** (p. ej. `admin@demo.taam` tras sembrar demo en el backend).

| Ruta | Descripción |
| --- | --- |
| `/admin/procedimientos` | Listado con formato (PDF / Markdown) y estado de indexación |
| `/admin/procedimientos/nuevo` | Alta multipart: metadata JSON + protocolo PDF o `.md` |
| `/admin/procedimientos/{uuid}` | Detalle, editar metadatos, reemplazar protocolo, reindexar |

- Las peticiones usan `apiFetch` con JWT Bearer (no `X-Admin-Key` en el navegador).
- Validación en cliente: PDF o Markdown (`.md`) ≤ 10 MB, nombre de archivo ASCII; mismos MIME que el backend.
- El listado y el detalle muestran badge de formato (`formato_protocolo`) además del estado de indexación.
- Mientras hay indexación `pendiente`, el listado y el detalle refrescan cada 3 s.

## Catálogo de médicos (admin)

Requiere usuario staff con **`rol=admin`** (p. ej. **`admin@demo.taam`** y la contraseña demo del `.env` del backend, tras `scripts/sembrar_usuarios_staff_demo.py`).

| Ruta | Descripción |
| --- | --- |
| `/admin/medicos` | Listado paginado: código, nombre, especialidad, estado activo, fecha de alta |
| `/admin/medicos/nuevo` | Alta JSON (`codigo_registro`, `nombre_completo`, `especialidad` opcional) |
| `/admin/medicos/{uuid}` | Detalle, editar datos (`PATCH`), desactivar (`DELETE` con confirmación) |

- Las peticiones usan `apiFetch` con JWT Bearer (no `X-Admin-Key` en el navegador).
- Validación en cliente: `codigo_registro` ASCII `[A-Za-z0-9._-]+`; campos obligatorios en alta.
- Si el médico tiene casos postoperatorio activos, la desactivación responde 409 y el panel muestra un mensaje claro en español.

## Casos postoperatorio y emparejamiento (asistente, UC-MVP-02)

Cualquier usuario staff autenticado (p. ej. `asistente@demo.taam`).

| Ruta | Descripción |
| --- | --- |
| `/casos` | Listado de casos activos, indicador Telegram vinculado/pendiente, regenerar código |
| `/casos/nuevo` | Alta de caso + modal con código de emparejamiento y TTL |

- Combobox de procedimiento: solo tipos con `indexacion_estado=ok` (`GET /api/staff/tipos-procedimiento`); filtro por nombre o código.
- Combobox de cirujano: médicos activos del catálogo (`GET /api/staff/medicos`); filtro por nombre, código o especialidad; al registrar se envían `cirujano_id` = `codigo_registro` y `cirujano_nombre` = `nombre_completo`. Si el catálogo está vacío, mensaje en español y enlace a `/admin/medicos` solo para `rol=admin`.
- Tras crear el caso se genera el código automáticamente (`POST .../codigo-emparejamiento`).
- Opcional en `.env` del frontend (o `.env.local`): `VITE_TELEGRAM_BOT_USERNAME` (sin `@`) para mostrar enlace `t.me/{bot}?start={CODIGO}`.

## Seguimiento: alertas y conversaciones (clínico, UC-MVP-05)

Cualquier usuario staff autenticado; flujo demo con `clinico@demo.taam` (caso vinculado y alertas sembradas en backend).

| Ruta | Descripción |
| --- | --- |
| `/seguimiento` | Bandeja de alertas pendientes (`revisado=false`), filtros por severidad, polling 30 s |
| `/seguimiento/casos` | Casos activos con badge de alertas pendientes por caso |
| `/seguimiento/caso/{uuid}` | Resumen, alertas pendientes del caso, hilo conversación (solo lectura), **Marcar revisado** |

- API: `GET/PATCH /api/staff/alertas`, `GET /api/staff/casos/{id}/conversacion`, `GET .../resumen`.
- Sin responder al paciente desde el panel (control deshabilitado; MVP solo lectura + marcar revisado).

## Scripts

| Comando | Descripción |
| --- | --- |
| `pnpm dev` | Servidor de desarrollo (puerto 5174) |
| `pnpm build` | `tsc -b` + build de producción en `dist/` |
| `pnpm preview` | Vista previa del build |
| `pnpm lint` | ESLint (flat config) |

## Estructura relevante

```
src/
  components/     AppShell, ThemeToggle, ApiStatusFooter, ui/button|input|label
  features/
    auth/                 AuthContext, StaffLoginScreen (`/login`)
    admin-procedimientos/ Catálogo protocolo PDF/Markdown + indexación (`/admin/procedimientos`)
    admin-medicos/          Catálogo médicos/cirujanos (`/admin/medicos`)
    casos/                Registro casos y código Telegram (`/casos`)
    seguimiento/          Bandeja alertas y conversación (`/seguimiento`)
    settings/             SettingsPanel (navegación)
    shell/                PlaceholderHome
  hooks/          useSalud
  lib/            api, authStorage, schemas, cn, useAppPath
  styles/         globals.css (tokens FVL)
```

## Tema claro/oscuro

`next-themes` persiste la preferencia en `localStorage` (clave `taam-theme`).

## CORS

En desarrollo use el **proxy** de Vite; no hace falta configurar CORS en el navegador. Si llama a la API directamente desde otro origen, incluya `http://localhost:5174` en `ALLOWED_ORIGINS` del backend (`proyecto-2/.env`).

## Tareas relacionadas

- **TASK-109** — este scaffold
- **TASK-110** — login staff JWT y cliente API autenticado (implementado)
- **TASK-111** — catálogo admin procedimientos y PDF (implementado)
- **TASK-135** — catálogo admin: protocolos PDF o Markdown equivalentes (implementado)
- **TASK-112** — registro casos y código emparejamiento (implementado)
- **TASK-113** — panel seguimiento alertas y conversaciones (implementado)
