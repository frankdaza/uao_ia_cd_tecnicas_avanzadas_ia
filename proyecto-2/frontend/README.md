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
  components/     AppShell, ThemeToggle, ApiStatusFooter, ui/button
  features/
    auth/         AuthContext (stub), AuthPlaceholder — login real en TASK-110
    settings/     SettingsPanel (navegación)
    shell/        PlaceholderHome, PlaceholderCasos
  hooks/          useSalud
  lib/            api, schemas, cn, useAppPath
  styles/         globals.css (tokens FVL)
```

## Tema claro/oscuro

`next-themes` persiste la preferencia en `localStorage` (clave `taam-theme`).

## CORS

En desarrollo use el **proxy** de Vite; no hace falta configurar CORS en el navegador. Si llama a la API directamente desde otro origen, incluya `http://localhost:5174` en `ALLOWED_ORIGINS` del backend (`proyecto-2/.env`).

## Tareas relacionadas

- **TASK-109** — este scaffold
- **TASK-110** — login staff JWT y cliente API autenticado
