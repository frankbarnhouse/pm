from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import initialize_database
from app.routes import api, auth, frontend

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Project Management MVP API", lifespan=lifespan)

if (frontend.FRONTEND_DIST_DIR / "_next").exists():
    app.mount(
        "/_next",
        StaticFiles(directory=frontend.FRONTEND_DIST_DIR / "_next"),
        name="next-assets",
    )

app.include_router(api.router)
app.include_router(auth.router)
app.include_router(frontend.router)
