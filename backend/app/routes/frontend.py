from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response

from app.session import current_user

router = APIRouter()

FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend_dist"


def _frontend_file(path: str) -> Path:
    normalized = path.lstrip("/")
    candidate = FRONTEND_DIST_DIR / normalized

    if not candidate.resolve().is_relative_to(FRONTEND_DIST_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Not found")

    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.exists():
        return candidate
    return FRONTEND_DIST_DIR / "index.html"


@router.get("/", include_in_schema=False)
def home(request: Request) -> Response:
    if current_user(request) is None:
        return RedirectResponse(url="/login", status_code=302)

    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Frontend build not found")
    return FileResponse(index_file)


@router.get("/{full_path:path}", include_in_schema=False)
def frontend_routes(request: Request, full_path: str) -> Response:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if full_path.startswith("auth/") or full_path in ("login", "register"):
        raise HTTPException(status_code=404, detail="Not found")

    if current_user(request) is None:
        return RedirectResponse(url="/login", status_code=302)

    file_path = _frontend_file(full_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(file_path)
