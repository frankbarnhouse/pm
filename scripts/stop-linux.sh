#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="udemy-pm-mvp"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed or not on PATH"
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
  echo "Stopping and removing ${CONTAINER_NAME}..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null
  echo "Stopped."
else
  echo "Container ${CONTAINER_NAME} does not exist."
fi
