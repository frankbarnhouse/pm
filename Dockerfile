FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev

COPY backend/ ./
COPY --from=frontend-builder /app/frontend/out ./frontend_dist

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/backend/data && \
    chown -R appuser:appuser /app/backend
USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
