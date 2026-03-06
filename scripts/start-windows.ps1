$ErrorActionPreference = "Stop"

$imageName = "udemy-pm-mvp"
$containerName = "udemy-pm-mvp"
$port = 8000
$dataPath = Join-Path (Get-Location) "backend/data"

New-Item -ItemType Directory -Path $dataPath -Force | Out-Null

Write-Host "Building image $imageName..."
docker build -t $imageName .

$exists = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$containerName$"
if ($exists) {
  Write-Host "Removing existing container $containerName..."
  docker rm -f $containerName | Out-Null
}

Write-Host "Starting container $containerName on http://localhost:$port..."
docker run -d --name $containerName --env-file .env -v "${dataPath}:/app/backend/data" -p "${port}:8000" $imageName | Out-Null

Write-Host "App started: http://localhost:$port"
