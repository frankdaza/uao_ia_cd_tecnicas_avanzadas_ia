# =============================================================================
# Stage 1: Build del frontend React (Node 22 Alpine)
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copiar manifiestos y lockfile primero para cachear instalación
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm@10 && pnpm install --frozen-lockfile

# Copiar el resto del frontend y construir
COPY frontend/ ./
RUN pnpm build

# =============================================================================
# Stage 2: Backend Python con FastAPI (Python 3.12 Slim)
# =============================================================================
FROM python:3.12-slim AS backend

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copiar manifiestos y codigo Python (uv_build requiere el modulo `src` en sync)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Sincronizar dependencias (sin el grupo dev)
RUN uv sync --frozen --no-dev

# Alembic (migraciones DB) y rutas de lectura M2 montadas o copiadas en compose
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY config/ ./config/

# Copiar los estáticos del frontend generados en el stage anterior
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Directorios de datos (Markdown del corpus opcional; structured/ FAQ en M2)
RUN mkdir -p data/markdown data/raw data/processed data/structured

# Puerto de exposición
EXPOSE 8000

# Comando por defecto
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
