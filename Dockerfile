# =============================================================================
# Stage 1: Build del frontend React (Node 22 Alpine)
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copiar manifiestos y lockfile primero para cachear instalación
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm@11.1.1 && pnpm install --frozen-lockfile

# Copiar el resto del frontend y construir
COPY frontend/ ./
RUN pnpm build

# =============================================================================
# Stage 2: Backend Python con FastAPI (Python 3.12.12 Slim, alineado con pyproject)
# =============================================================================
FROM python:3.12.12-slim-bookworm AS backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gestión de dependencias
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Python gestionado por uv bajo /app: el venv apunta al intérprete; si queda en /root/.local, el usuario `app` no puede resolverlo.
ENV UV_PYTHON_INSTALL_DIR=/app/.uv/python

# Copiar manifiestos y codigo Python (uv_build requiere el modulo `src` en sync)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Sincronizar dependencias (sin el grupo dev)
RUN uv sync --frozen --no-dev

# Alembic (migraciones DB) y rutas de lectura M2 montadas o copiadas en compose
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY config/ ./config/

# Copiar los estáticos del frontend generados en el stage anterior
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Directorios de datos (Markdown del corpus opcional; structured/ FAQ en M2)
RUN mkdir -p data/markdown data/raw data/processed data/structured \
    && groupadd --system app \
    && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /home/app \
    && chown app:app /home/app \
    && chown -R app:app /app

USER app

# Puerto de exposición
EXPOSE 8000

# Comando por defecto
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
