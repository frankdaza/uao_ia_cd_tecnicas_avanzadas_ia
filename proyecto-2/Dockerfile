# Backend TAAM (Python 3.12.12, alineado con pyproject.toml)
FROM python:3.12.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_PYTHON_INSTALL_DIR=/app/.uv/python

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN uv sync --frozen --no-dev

ENV UV_CACHE_DIR=/app/.cache/uv

RUN groupadd --system app \
    && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /home/app /app/.cache/uv \
    && chown -R app:app /app /home/app

USER app

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
