from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routes.kb_route import router as kb_router
from routes.query_doc_route import router as query_doc_router
from utils.initilize_service_func import initialize_services

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not initialize_services():
        print("Warning: Services failed to initialize properly.")
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Amplio Services — Knowledge API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(kb_router)
app.include_router(query_doc_router)


@app.get("/")
async def serve_frontend():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
