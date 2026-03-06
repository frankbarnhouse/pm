#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="udemy-pm-mvp"
CONTAINER_NAME="udemy-pm-mvp"
PORT="8000"
DATA_DIR="$(pwd)/backend/data"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed or not on PATH"
  exit 1
fi

echo "Building image ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" .

mkdir -p "${DATA_DIR}"

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
  echo "Removing existing container ${CONTAINER_NAME}..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

echo "Starting container ${CONTAINER_NAME} on http://localhost:${PORT}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --env-file .env \
  -v "${DATA_DIR}:/app/backend/data" \
  -p "${PORT}:8000" \
  "${IMAGE_NAME}" >/dev/null

echo "App started: http://localhost:${PORT}"
