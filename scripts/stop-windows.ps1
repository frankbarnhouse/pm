$ErrorActionPreference = "Stop"

$containerName = "udemy-pm-mvp"

$exists = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$containerName$"
if ($exists) {
  Write-Host "Stopping and removing $containerName..."
  docker rm -f $containerName | Out-Null
  Write-Host "Stopped."
} else {
  Write-Host "Container $containerName does not exist."
}
