FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app/backend

COPY backend/ ./

RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
