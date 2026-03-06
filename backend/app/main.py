from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Project Management MVP API")

FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend_dist"

if (FRONTEND_DIST_DIR / "_next").exists():
        app.mount(
                "/_next",
                StaticFiles(directory=FRONTEND_DIST_DIR / "_next"),
                name="next-assets",
        )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


def _frontend_file(path: str) -> Path:
    normalized = path.lstrip("/")
    candidate = FRONTEND_DIST_DIR / normalized

    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.exists():
        return candidate
    return FRONTEND_DIST_DIR / "index.html"


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Frontend build not found")
    return FileResponse(index_file)


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_routes(full_path: str) -> FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    file_path = _frontend_file(full_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(file_path)
